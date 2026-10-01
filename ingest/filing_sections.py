from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

import warnings

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# SEC primary documents are Inline XBRL (iXBRL): valid XHTML with embedded,
# namespaced XBRL tags, which makes BeautifulSoup guess it might be XML.
# Verified safe for our purposes (plain-text extraction, not XBRL parsing).
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# General "Item N[letter]." heading, used only to find where the TARGET
# section ENDS (the next Item heading of any kind).
# Anchored to the start of a line (re.MULTILINE + ^) on purpose: filings
# are full of inline cross-references like "...described in Item 1A of
# the 2025 Form 10-K..." which are NOT section boundaries. A real heading
# in this document always starts its own line; a cross-reference never
# does. html_to_text() already strips leading whitespace from every line.
ITEM_BOUNDARY_RE = re.compile(
    r"^item\s+\d+[a-z]?\.?", re.IGNORECASE | re.MULTILINE
)

# Section-specific heading patterns, keyed by form type because 10-K and
# 10-Q number Risk Factors and MD&A differently.
SECTION_HEADINGS: dict[str, dict[str, tuple[str, re.Pattern[str]]]] = {
    "10-K": {
        "risk_factors": (
            "1A",
            re.compile(r"item\s+1a\.?\s*risk\s+factors", re.IGNORECASE),
        ),
        "mda": (
            "7",
            re.compile(
                r"item\s+7\.?\s*management.?s\s+discussion",
                re.IGNORECASE,
            ),
        ),
    },
    "10-Q": {
        "mda": (
            "2",
            re.compile(
                r"item\s+2\.?\s*management.?s\s+discussion",
                re.IGNORECASE,
            ),
        ),
        "risk_factors": (
            "1A",
            re.compile(r"item\s+1a\.?\s*risk\s+factors", re.IGNORECASE),
        ),
    },
}

# A table-of-contents reference to a heading is short (just a page
# number); a real section runs thousands of characters. This threshold
# separates the two.
MIN_SECTION_CHARS = 500


@dataclass(frozen=True, slots=True)
class ExtractedSection:
    """One parsed section, ready to become a FilingSection row."""

    section_type: str
    item_code: str
    heading: str
    text: str
    content_hash: str


def html_to_text(raw_html: str) -> str:
    """Strip an SEC filing's HTML down to normalized plain text."""
    soup = BeautifulSoup(raw_html, "lxml")

    for tag in soup(["script", "style"]):
        tag.decompose()

    lines = [
        line.strip()
        for line in soup.get_text(separator="\n").splitlines()
    ]

    return "\n".join(line for line in lines if line)


def _best_match(
    text: str,
    pattern: re.Pattern[str],
) -> tuple[re.Match[str], int] | None:
    """Return the heading match with the longest run of content after it.

    A heading is usually mentioned twice: once in the table of contents
    (a short line, just a page reference) and once at the real section
    (long, followed by paragraphs of content). Picking whichever match has
    the most text before the next Item heading reliably selects the real
    section over the table-of-contents reference.
    """
    best_match: re.Match[str] | None = None
    best_content_end = 0
    best_length = 0

    for match in pattern.finditer(text):
        content_start = match.end()
        next_boundary = ITEM_BOUNDARY_RE.search(text, pos=content_start)
        content_end = next_boundary.start() if next_boundary else len(text)
        length = content_end - content_start

        if length > best_length:
            best_match = match
            best_content_end = content_end
            best_length = length

    if best_match is None or best_length < MIN_SECTION_CHARS:
        return None

    return best_match, best_content_end


def extract_sections(
    raw_html: str,
    form_type: str,
) -> list[ExtractedSection]:
    """Extract Risk Factors and MD&A from one filing's raw HTML.

    Returns an empty list if the form type isn't recognized, or if a
    section never reaches MIN_SECTION_CHARS. Callers should treat that as
    "nothing confidently found," not as a parsing error. Sections come
    back in document order.
    """
    headings = SECTION_HEADINGS.get(form_type.upper())

    if not headings:
        return []

    text = html_to_text(raw_html)
    found: list[tuple[int, ExtractedSection]] = []

    for section_type, (item_code, pattern) in headings.items():
        result = _best_match(text, pattern)

        if result is None:
            continue

        match, content_end = result
        heading = " ".join(match.group(0).split())
        section_text = text[match.end():content_end].strip()

        found.append((
            match.start(),
            ExtractedSection(
                section_type=section_type,
                item_code=item_code,
                heading=heading,
                text=section_text,
                content_hash=hashlib.sha256(
                    section_text.encode("utf-8")
                ).hexdigest(),
            ),
        ))

    found.sort(key=lambda pair: pair[0])

    return [section for _, section in found]
