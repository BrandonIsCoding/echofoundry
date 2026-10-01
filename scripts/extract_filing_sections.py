import argparse

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Filing
from ingest.filing_persistence import persist_filing_sections
from ingest.filing_sections import extract_sections


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse Risk Factors / MD&A from a stored filing."
    )
    parser.add_argument(
        "--accession",
        help="Accession number; defaults to the most recently stored filing.",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        if args.accession:
            filing = session.scalar(
                select(Filing).where(Filing.accession_number == args.accession)
            )
        else:
            filing = session.scalar(
                select(Filing).order_by(Filing.id.desc()).limit(1)
            )

        if filing is None:
            print("No matching filing found.")
            return

        sections = extract_sections(filing.raw_text, filing.form_type)

        if not sections:
            print(
                f"No sections confidently extracted from "
                f"{filing.form_type} {filing.accession_number}."
            )
            return

        results = persist_filing_sections(
            session, filing_id=filing.id, sections=sections
        )
        session.commit()

        for section, result in zip(sections, results):
            preview = " ".join(section.text.split())[:200]
            print(
                f"{section.section_type} (Item {section.item_code}) | "
                f"{len(section.text)} chars | "
                f"already_existed={result.already_existed} | "
                f"id={result.filing_section_id}"
            )
            print(f"  preview: {preview}...")


if __name__ == "__main__":
    main()
