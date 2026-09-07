from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.trade import Trade


class Signal(Base):
    """An auditable feature score or model prediction for an event."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )

    signal_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    signal_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    signal_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    trades: Mapped[list[Trade]] = relationship(
    back_populates="signal",
    cascade="all, delete-orphan",
)

    model_name: Mapped[str | None] = mapped_column(String(64))
    model_version: Mapped[str | None] = mapped_column(String(64))

    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)

    horizon_trading_days: Mapped[int | None] = mapped_column(Integer)

    information_cutoff_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    config_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    features_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    event: Mapped[Event] = relationship(back_populates="signals")

    __table_args__ = (
        CheckConstraint(
            "signal_type IN "
            "('feature_score', 'model_prediction', 'composite_signal')",
            name="valid_signal_type",
        ),
        CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 0 AND 1",
            name="valid_signal_confidence",
        ),
        CheckConstraint(
            "horizon_trading_days IS NULL OR horizon_trading_days > 0",
            name="positive_signal_horizon",
        ),
        CheckConstraint(
            "char_length(config_hash) = 64",
            name="valid_signal_config_hash",
        ),
        CheckConstraint(
            "information_cutoff_at <= generated_at",
            name="valid_signal_information_cutoff",
        ),
        Index(
            "ix_signals_event_id",
            "event_id",
        ),
        Index(
            "ix_signals_name_cutoff",
            "signal_name",
            "information_cutoff_at",
        ),
    )
