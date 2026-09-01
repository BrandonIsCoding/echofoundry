from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Price(Base):
    """One daily OHLCV price bar with provenance and corporate actions."""

    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)

    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)

    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[float | None] = mapped_column(Float)

    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)

    dividend: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0",
    )

    split_factor: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="1",
    )

    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "open_price >= 0 AND high_price >= 0 "
            "AND low_price >= 0 AND close_price >= 0",
            name="nonnegative_ohlc_prices",
        ),
        CheckConstraint(
            "high_price >= low_price",
            name="valid_high_low_range",
        ),
        CheckConstraint(
            "open_price BETWEEN low_price AND high_price",
            name="open_within_daily_range",
        ),
        CheckConstraint(
            "close_price BETWEEN low_price AND high_price",
            name="close_within_daily_range",
        ),
        CheckConstraint(
            "adjusted_close IS NULL OR adjusted_close >= 0",
            name="nonnegative_adjusted_close",
        ),
        CheckConstraint(
            "volume >= 0",
            name="nonnegative_volume",
        ),
        CheckConstraint(
            "dividend >= 0",
            name="nonnegative_dividend",
        ),
        CheckConstraint(
            "split_factor > 0",
            name="positive_split_factor",
        ),
        UniqueConstraint(
            "ticker",
            "price_date",
            "source",
            name="uq_price_ticker_date_source",
        ),
        Index("ix_price_price_date", "price_date"),
    )
