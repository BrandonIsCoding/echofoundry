import argparse
import time

from app.db import SessionLocal
from ingest.filing_persistence import persist_filing
from ingest.raw_storage import archive_filing
from ingest.sec_client import download_primary_document, get_company_submissions
from ingest.sec_filings import filter_filings, parse_recent_filings


# SEC allows 10 requests/second; this keeps us far below that.
REQUEST_PAUSE_SECONDS = 0.5


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch, archive, and store recent SEC filings for one company."
    )
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--cik", default="320193")
    parser.add_argument("--form", default="10-Q", choices=["10-K", "10-Q"])
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    submissions = get_company_submissions(args.cik)
    filings = filter_filings(
        parse_recent_filings(submissions),
        forms=[args.form],
    )[: args.limit]

    if not filings:
        print(f"No {args.form} filings found for CIK {args.cik}.")
        return

    with SessionLocal() as session:
        for filing in filings:
            time.sleep(REQUEST_PAUSE_SECONDS)

            downloaded = download_primary_document(filing)
            archived = archive_filing(filing, downloaded)
            result = persist_filing(
                session,
                ticker=args.ticker,
                filing=filing,
                downloaded=downloaded,
                archived=archived,
            )
            session.commit()

            print(
                f"{filing.form_type} {filing.accession_number} "
                f"accepted {filing.accepted_at.isoformat()} | "
                f"file_existed={archived.already_existed} "
                f"row_existed={result.already_existed} "
                f"filing_id={result.filing_id} event_id={result.event_id}"
            )


if __name__ == "__main__":
    main()
