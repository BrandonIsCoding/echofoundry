from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    """A market-relevant corporate event with temporal provenance."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ticker: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    fiscal_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    fiscal_quarter: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('earnings_release', 'earnings_call', 'sec_filing')",
            name="valid_event_type",
        ),
        CheckConstraint(
            "fiscal_quarter IS NULL OR fiscal_quarter BETWEEN 1 AND 4",
            name="valid_fiscal_quarter",
        ),
        CheckConstraint(
            "available_at >= event_at",
            name="valid_availability_time",
        ),
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_events_source_external_id",
        ),
        Index(
            "ix_events_ticker_available_at",
            "ticker",
            "available_at",
        ),
    )
