from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, Filing, FilingSection
from ingest.raw_storage import PROJECT_ROOT, ArchivedFiling
from ingest.sec_client import DownloadedFiling, build_primary_document_url
from ingest.sec_filings import FilingMetadata
from ingest.filing_sections import ExtractedSection


EVENT_SOURCE = "sec_edgar"
EVENT_TYPE = "sec_filing"


@dataclass(frozen=True, slots=True)
class PersistedFiling:
    """Identifiers of the rows written (or found) for one filing."""

    filing_id: int
    event_id: int
    already_existed: bool


def persist_filing(
    session: Session,
    *,
    ticker: str,
    filing: FilingMetadata,
    downloaded: DownloadedFiling,
    archived: ArchivedFiling,
) -> PersistedFiling:
    """Insert the Event and Filing rows for one archived SEC filing.

    Idempotent: a filing already stored under the same accession number is
    verified against its content hash and returned, never duplicated.
    The caller owns the transaction; this function flushes but never commits.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("ticker cannot be empty.")

    if downloaded.source_url != build_primary_document_url(filing):
        raise ValueError(
            "Downloaded document URL does not match the filing metadata."
        )

    if downloaded.content_hash != archived.content_hash:
        raise ValueError(
            "Downloaded content hash does not match the archived file hash."
        )

    existing = session.scalar(
        select(Filing).where(
            Filing.accession_number == filing.accession_number
        )
    )

    if existing is not None:
        if existing.content_hash != archived.content_hash:
            raise ValueError(
                f"Filing {filing.accession_number} is already stored "
                "with different content."
            )

        return PersistedFiling(
            filing_id=existing.id,
            event_id=existing.event_id,
            already_existed=True,
        )

    # Strict decode: fail loudly rather than store text that no longer
    # matches the hashed bytes.
    raw_text = downloaded.content.decode("utf-8")

    if "\x00" in raw_text:
        raise ValueError("Filing text contains NUL bytes; Postgres rejects them.")

    event = session.scalar(
        select(Event).where(
            Event.source == EVENT_SOURCE,
            Event.external_id == filing.accession_number,
        )
    )

    if event is None:
        event = Event(
            ticker=ticker,
            event_type=EVENT_TYPE,
            event_at=filing.accepted_at,
            available_at=filing.accepted_at,
            source=EVENT_SOURCE,
            external_id=filing.accession_number,
        )
        session.add(event)
        session.flush()

    row = Filing(
        event_id=event.id,
        cik=filing.cik,
        accession_number=filing.accession_number,
        form_type=filing.form_type,
        period_end=filing.report_date,
        filed_on=filing.filing_date,
        accepted_at=filing.accepted_at,
        retrieved_at=downloaded.retrieved_at,
        source_url=downloaded.source_url,
        content_hash=archived.content_hash,
        raw_text=raw_text,
        raw_storage_path=archived.path.relative_to(PROJECT_ROOT).as_posix(),
    )
    session.add(row)
    session.flush()

    return PersistedFiling(
        filing_id=row.id,
        event_id=event.id,
        already_existed=False,
    )


@dataclass(frozen=True, slots=True)
class PersistedSection:
    """Identifier of the row written (or found) for one parsed section."""

    filing_section_id: int
    already_existed: bool


def persist_filing_sections(
    session: Session,
    *,
    filing_id: int,
    sections: list[ExtractedSection],
) -> list[PersistedSection]:
    """Insert parsed FilingSection rows for one filing.

    Idempotent per (filing_id, section_type): a section already stored is
    verified against its content hash and returned, never duplicated. New
    sections are numbered after any that already exist, so a partial retry
    can never collide with an existing sequence_number.
    """
    existing_by_type = {
        row.section_type: row
        for row in session.scalars(
            select(FilingSection).where(FilingSection.filing_id == filing_id)
        )
    }

    next_sequence = (
        max(
            (row.sequence_number for row in existing_by_type.values()),
            default=-1,
        )
        + 1
    )

    results: list[PersistedSection] = []

    for section in sections:
        existing = existing_by_type.get(section.section_type)

        if existing is not None:
            if existing.content_hash != section.content_hash:
                raise ValueError(
                    f"Filing {filing_id} section '{section.section_type}' "
                    "is already stored with different content."
                )

            results.append(
                PersistedSection(
                    filing_section_id=existing.id,
                    already_existed=True,
                )
            )
            continue

        row = FilingSection(
            filing_id=filing_id,
            sequence_number=next_sequence,
            section_type=section.section_type,
            item_code=section.item_code,
            heading=section.heading,
            text=section.text,
            content_hash=section.content_hash,
        )
        session.add(row)
        session.flush()
        next_sequence += 1

        results.append(
            PersistedSection(filing_section_id=row.id, already_existed=False)
        )

    return results
