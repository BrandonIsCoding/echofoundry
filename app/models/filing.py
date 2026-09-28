from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.filing_section import FilingSection


class Filing(Base):
    """SEC filing metadata and immutable raw filing text."""

    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    cik: Mapped[str] = mapped_column(String(10), nullable=False)
    accession_number: Mapped[str] = mapped_column(String(32), nullable=False)
    form_type: Mapped[str] = mapped_column(String(16), nullable=False)

    period_end: Mapped[date | None] = mapped_column(Date)
    filed_on: Mapped[date] = mapped_column(Date, nullable=False)

    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    raw_storage_path: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    event: Mapped[Event] = relationship(back_populates="filings")

    sections: Mapped[list[FilingSection]] = relationship(
        back_populates="filing",
        cascade="all, delete-orphan",
        order_by="FilingSection.sequence_number",
    )

    __table_args__ = (
        CheckConstraint(
            "form_type IN ('10-K', '10-K/A', '10-Q', '10-Q/A')",
            name="valid_filing_form_type",
        ),
        UniqueConstraint(
            "accession_number",
            name="uq_filings_accession_number",
        ),
        Index("ix_filings_event_id", "event_id"),
        Index("ix_filings_cik_accepted_at", "cik", "accepted_at"),
        Index("ix_filings_content_hash", "content_hash"),
    )
