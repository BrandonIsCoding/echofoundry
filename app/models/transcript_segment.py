from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.transcript import Transcript


class TranscriptSegment(Base):
    """One ordered speaker turn within a transcript."""

    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)

    transcript_id: Mapped[int] = mapped_column(
        ForeignKey("transcripts.id", ondelete="CASCADE"),
        nullable=False,
    )

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    speaker_name: Mapped[str | None] = mapped_column(String(128))
    speaker_role: Mapped[str | None] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text, nullable=False)

    transcript: Mapped[Transcript] = relationship(back_populates="segments")

    __table_args__ = (
        CheckConstraint(
            "sequence_number >= 0",
            name="nonnegative_sequence_number",
        ),
        CheckConstraint(
            "section IN "
            "('prepared_remarks', 'guidance', 'qa', 'operator', 'other')",
            name="valid_transcript_section",
        ),
        UniqueConstraint(
            "transcript_id",
            "sequence_number",
            name="uq_transcript_segments_transcript_sequence",
        ),
        Index(
            "ix_transcript_segments_transcript_section",
            "transcript_id",
            "section",
        ),
    )
