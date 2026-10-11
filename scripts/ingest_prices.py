import argparse
from datetime import date, timedelta

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Event
from ingest.price_persistence import persist_prices
from ingest.prices import fetch_price_history


def default_window(session, ticker: str) -> tuple[date, date] | None:
    """Derive a price window from this ticker's existing events.

    Ties price coverage directly to what the backtest will need: some
    history before the earliest event and room after the latest one for
    the event window, rather than an arbitrary fixed range.
    """
    min_at, max_at = session.execute(
        select(func.min(Event.event_at), func.max(Event.event_at)).where(
            Event.ticker == ticker.strip().upper()
        )
    ).one()

    if min_at is None:
        return None

    start = min_at.date() - timedelta(days=10)
    end = min(max_at.date() + timedelta(days=15), date.today())

    return start, end


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and store daily OHLCV prices for one ticker."
    )
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--start", type=date.fromisoformat, default=None)
    parser.add_argument("--end", type=date.fromisoformat, default=None)
    args = parser.parse_args()

    with SessionLocal() as session:
        start, end = args.start, args.end

        if start is None or end is None:
            derived = default_window(session, args.ticker)

            if derived is None:
                parser.error(
                    "No events stored for this ticker yet; "
                    "pass --start and --end explicitly."
                )

            start = start or derived[0]
            end = end or derived[1]

        print(f"Fetching {args.ticker} prices from {start} to {end}...")
        bars = fetch_price_history(args.ticker, start, end)

        if not bars:
            print("No price bars returned.")
            return

        result = persist_prices(session, bars)
        session.commit()

        print(
            f"{len(bars)} trading days fetched | "
            f"inserted={result.inserted} already_existed={result.already_existed}"
        )


if __name__ == "__main__":
    main()
