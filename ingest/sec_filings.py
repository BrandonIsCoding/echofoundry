from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Collection


@dataclass(frozen=True, slots=True)
class FilingMetadata:
    """Validated metadata for one SEC filing."""

    cik: str
    accession_number: str
    filing_date: date
    report_date: date | None
    accepted_at: datetime
    form_type: str
    primary_document: str


def parse_recent_filings(
    submissions: dict[str, Any],
) -> list[FilingMetadata]:
    """Convert SEC recent-filings JSON into typed filing records."""
    cik = str(submissions["cik"]).zfill(10)
    recent = submissions["filings"]["recent"]

    required_fields = (
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "form",
        "primaryDocument",
    )

    missing_fields = [
        field
        for field in required_fields
        if field not in recent
    ]

    if missing_fields:
        raise ValueError(
            f"SEC response is missing required fields: {missing_fields}"
        )

    field_lengths = {
        field: len(recent[field])
        for field in required_fields
    }

    if len(set(field_lengths.values())) != 1:
        raise ValueError(
            f"SEC filing fields have inconsistent lengths: {field_lengths}"
        )

    filings: list[FilingMetadata] = []

    for index in range(field_lengths["accessionNumber"]):
        report_date_text = recent["reportDate"][index]
        accepted_at_text = recent["acceptanceDateTime"][index]

        accepted_at = datetime.fromisoformat(
            accepted_at_text.replace("Z", "+00:00")
        )

        if accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
            raise ValueError(
                f"Filing at index {index} has no acceptance timezone."
            )

        filing = FilingMetadata(
            cik=cik,
            accession_number=recent["accessionNumber"][index],
            filing_date=date.fromisoformat(
                recent["filingDate"][index]
            ),
            report_date=(
                date.fromisoformat(report_date_text)
                if report_date_text
                else None
            ),
            accepted_at=accepted_at,
            form_type=recent["form"][index],
            primary_document=recent["primaryDocument"][index],
        )

        filings.append(filing)

    return filings


def filter_filings(
    filings: list[FilingMetadata],
    forms: Collection[str] | None = None,
    include_amendments: bool = False,
) -> list[FilingMetadata]:
    """Select filing forms without changing availability timestamps."""
    base_forms = (
        {"10-K", "10-Q"}
        if forms is None
        else {form.strip().upper() for form in forms}
    )

    if not base_forms:
        raise ValueError("At least one filing form must be requested.")

    if any(form.endswith("/A") for form in base_forms):
        raise ValueError(
            "Pass base forms such as '10-K' or '10-Q'. "
            "Use include_amendments=True to include amendments."
        )

    accepted_forms = set(base_forms)

    if include_amendments:
        accepted_forms.update(
            f"{form}/A"
            for form in base_forms
        )

    selected = [
        filing
        for filing in filings
        if filing.form_type.upper() in accepted_forms
    ]

    return sorted(
        selected,
        key=lambda filing: filing.accepted_at,
        reverse=True,
    )


def filings_available_as_of(
    filings: list[FilingMetadata],
    cutoff_at: datetime,
) -> list[FilingMetadata]:
    """Return only filings accepted by the SEC on or before a cutoff."""
    if cutoff_at.tzinfo is None or cutoff_at.utcoffset() is None:
        raise ValueError("cutoff_at must include timezone information.")

    available = [
        filing
        for filing in filings
        if filing.accepted_at <= cutoff_at
    ]

    return sorted(
        available,
        key=lambda filing: filing.accepted_at,
        reverse=True,
    )