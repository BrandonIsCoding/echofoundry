from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.transcript_segment import TranscriptSegment


class Transcript(Base):
    """Source metadata and raw text for an earnings-call transcript."""

    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    language: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default="en",
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    event: Mapped[Event] = relationship(back_populates="transcripts")

    segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.sequence_number",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            name="uq_transcripts_provider_external_id",
        ),
        Index("ix_transcripts_event_id", "event_id"),
        Index("ix_transcripts_published_at", "published_at"),
    )
