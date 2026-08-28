from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.filing import Filing


class FilingSection(Base):
    """One ordered, parsed section from an SEC filing."""

    __tablename__ = "filing_sections"

    id: Mapped[int] = mapped_column(primary_key=True)

    filing_id: Mapped[int] = mapped_column(
        ForeignKey("filings.id", ondelete="CASCADE"),
        nullable=False,
    )

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_type: Mapped[str] = mapped_column(String(32), nullable=False)

    item_code: Mapped[str | None] = mapped_column(String(32))
    heading: Mapped[str | None] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    filing: Mapped[Filing] = relationship(back_populates="sections")

    __table_args__ = (
        CheckConstraint(
            "sequence_number >= 0",
            name="nonnegative_sequence_number",
        ),
        CheckConstraint(
            "section_type IN ('risk_factors', 'mda', 'other')",
            name="valid_filing_section_type",
        ),
        UniqueConstraint(
            "filing_id",
            "sequence_number",
            name="uq_filing_sections_filing_sequence",
        ),
        Index(
            "ix_filing_sections_filing_section_type",
            "filing_id",
            "section_type",
        ),
    )
