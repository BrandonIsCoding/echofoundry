from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Price
from ingest.prices import PriceBar


PRICE_SOURCE = "yfinance"


@dataclass(frozen=True, slots=True)
class PricePersistResult:
    """Counts from one persist_prices() call."""

    inserted: int
    already_existed: int


def persist_prices(
    session: Session,
    bars: list[PriceBar],
) -> PricePersistResult:
    """Insert daily price bars, skipping dates already stored for this source.

    Idempotent per (ticker, price_date, source): existing rows are left
    untouched and counted, never overwritten. Assumes all bars share one
    ticker, which holds since fetch_price_history() returns one ticker
    per call.
    """
    if not bars:
        return PricePersistResult(inserted=0, already_existed=0)

    ticker = bars[0].ticker
    dates = [bar.price_date for bar in bars]

    existing_dates = set(
        session.scalars(
            select(Price.price_date).where(
                Price.ticker == ticker,
                Price.source == PRICE_SOURCE,
                Price.price_date.in_(dates),
            )
        )
    )

    inserted = 0

    for bar in bars:
        if bar.price_date in existing_dates:
            continue

        session.add(
            Price(
                ticker=bar.ticker,
                price_date=bar.price_date,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price,
                close_price=bar.close_price,
                adjusted_close=bar.adjusted_close,
                volume=bar.volume,
                dividend=bar.dividend,
                split_factor=bar.split_factor,
                currency="USD",
                source=PRICE_SOURCE,
                retrieved_at=bar.retrieved_at,
            )
        )
        inserted += 1

    session.flush()

    return PricePersistResult(
        inserted=inserted,
        already_existed=len(bars) - inserted,
    )
