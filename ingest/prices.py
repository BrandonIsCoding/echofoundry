from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import yfinance as yf


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One validated daily OHLCV observation, ready to become a Price row."""

    ticker: str
    price_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    adjusted_close: float | None
    volume: int
    dividend: float
    split_factor: float
    retrieved_at: datetime


def _validate_bar(bar: PriceBar) -> None:
    """Raise ValueError if a bar would violate the prices table's constraints.

    Catching this here gives a clear, named error instead of a raw
    Postgres CheckViolation once the row reaches the database.
    """
    if bar.high_price < bar.low_price:
        raise ValueError(f"{bar.ticker} {bar.price_date}: high < low")
    if not (bar.low_price <= bar.open_price <= bar.high_price):
        raise ValueError(f"{bar.ticker} {bar.price_date}: open outside [low, high]")
    if not (bar.low_price <= bar.close_price <= bar.high_price):
        raise ValueError(f"{bar.ticker} {bar.price_date}: close outside [low, high]")
    if bar.volume < 0:
        raise ValueError(f"{bar.ticker} {bar.price_date}: negative volume")
    if bar.split_factor <= 0:
        raise ValueError(f"{bar.ticker} {bar.price_date}: non-positive split_factor")


def fetch_price_history(
    ticker: str,
    start: date,
    end: date,
) -> list[PriceBar]:
    """Fetch and validate daily OHLCV bars for one ticker, inclusive of `end`.

    Uses auto_adjust=False so raw OHLC and a separate adjusted close are
    both available; the prices table stores both.
    """
    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("ticker cannot be empty.")

    if start > end:
        raise ValueError("start must not be after end.")

    # yfinance's `end` is exclusive; +1 day makes the caller's range inclusive.
    history = yf.Ticker(ticker).history(
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        auto_adjust=False,
        actions=True,
    )

    if history.empty:
        return []

    retrieved_at = datetime.now(timezone.utc)
    bars: list[PriceBar] = []

    for index, row in history.iterrows():
        adj_raw = row.get("Adj Close")
        adjusted_close = (
            None
            if adj_raw is None or math.isnan(adj_raw)
            else float(adj_raw)
        )

        split_raw = float(row.get("Stock Splits", 0.0) or 0.0)
        split_factor = split_raw if split_raw > 0 else 1.0

        bar = PriceBar(
            ticker=ticker,
            price_date=index.date(),
            open_price=float(row["Open"]),
            high_price=float(row["High"]),
            low_price=float(row["Low"]),
            close_price=float(row["Close"]),
            adjusted_close=adjusted_close,
            volume=int(row["Volume"]),
            dividend=float(row.get("Dividends", 0.0) or 0.0),
            split_factor=split_factor,
            retrieved_at=retrieved_at,
        )
        _validate_bar(bar)
        bars.append(bar)

    return bars
