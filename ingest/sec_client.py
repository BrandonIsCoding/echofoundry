import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from ingest.sec_filings import FilingMetadata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

SUBMISSIONS_BASE_URL = "https://data.sec.gov/submissions"
ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

load_dotenv(dotenv_path=ENV_PATH)

@dataclass(frozen=True, slots=True)
class DownloadedFiling:
    """Immutable result of downloading one SEC filing document."""

    source_url: str
    content: bytes
    content_type: str | None
    retrieved_at: datetime
    content_hash: str

def normalize_cik(cik: str | int) -> str:
    """Return an SEC CIK as a ten-digit, zero-padded string."""
    cik_text = str(cik).strip()

    if not cik_text.isdigit():
        raise ValueError("CIK must contain only digits.")

    if len(cik_text) > 10:
        raise ValueError("CIK cannot contain more than 10 digits.")

    return cik_text.zfill(10)


def get_company_submissions(
    cik: str | int,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Retrieve a company's submission metadata from the SEC."""
    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            f"SEC_USER_AGENT is not set. Expected to load it from {ENV_PATH}."
        )

    normalized_cik = normalize_cik(cik)
    url = f"{SUBMISSIONS_BASE_URL}/CIK{normalized_cik}.json"

    response = requests.get(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        timeout=timeout_seconds,
    )

    response.raise_for_status()
    return response.json()


def build_primary_document_url(
    filing: FilingMetadata,
) -> str:
    """Construct the EDGAR archive URL for a filing's primary document."""
    normalized_cik = normalize_cik(filing.cik)
    cik_without_leading_zeros = str(int(normalized_cik))

    accession_without_hyphens = filing.accession_number.replace("-", "")

    if not accession_without_hyphens.isdigit():
        raise ValueError(
            "Accession number must contain only digits and hyphens."
        )

    primary_document = filing.primary_document.strip()

    if not primary_document:
        raise ValueError("Primary document filename cannot be empty.")

    if "/" in primary_document or "\\" in primary_document:
        raise ValueError(
            "Primary document must be a filename, not a path."
        )

    return (
        f"{ARCHIVES_BASE_URL}/"
        f"{cik_without_leading_zeros}/"
        f"{accession_without_hyphens}/"
        f"{primary_document}"
    )

def download_primary_document(
    filing: FilingMetadata,
    timeout_seconds: float = 30.0,
) -> DownloadedFiling:
    """Download and preserve one filing's primary SEC document."""
    user_agent = os.getenv("SEC_USER_AGENT")

    if not user_agent:
        raise RuntimeError(
            f"SEC_USER_AGENT is not set. Expected to load it from {ENV_PATH}."
        )

    source_url = build_primary_document_url(filing)

    response = requests.get(
        source_url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html, application/xhtml+xml",
        },
        timeout=timeout_seconds,
    )

    response.raise_for_status()

    content = response.content

    if not content:
        raise ValueError(
            f"SEC returned an empty primary document: {source_url}"
        )

    return DownloadedFiling(
        source_url=source_url,
        content=content,
        content_type=response.headers.get("Content-Type"),
        retrieved_at=datetime.now(timezone.utc),
        content_hash=hashlib.sha256(content).hexdigest(),
    )

