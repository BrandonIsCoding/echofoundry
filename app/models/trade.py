from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.signal import Signal


class Trade(Base):
    """A completed simulated trade linked to its originating signal."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True)

    signal_id: Mapped[int] = mapped_column(
        ForeignKey("signals.id", ondelete="CASCADE"),
        nullable=False,
    )

    side: Mapped[str] = mapped_column(String(8), nullable=False)

    intended_entry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    entry_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    exit_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)

    gross_return: Mapped[float] = mapped_column(Float, nullable=False)

    transaction_cost_return: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0",
    )

    net_return: Mapped[float] = mapped_column(Float, nullable=False)

    slippage_bps: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        server_default="0",
    )

    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)

    config_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    signal: Mapped[Signal] = relationship(back_populates="trades")

    __table_args__ = (
        CheckConstraint(
            "side IN ('long', 'short')",
            name="valid_trade_side",
        ),
        CheckConstraint(
            "entry_at >= intended_entry_at",
            name="valid_trade_entry_time",
        ),
        CheckConstraint(
            "exit_at > entry_at",
            name="valid_trade_exit_time",
        ),
        CheckConstraint(
            "entry_price > 0 AND exit_price > 0",
            name="positive_trade_prices",
        ),
        CheckConstraint(
            "quantity > 0",
            name="positive_trade_quantity",
        ),
        CheckConstraint(
            "transaction_cost_return >= 0",
            name="nonnegative_transaction_cost_return",
        ),
        CheckConstraint(
            "slippage_bps >= 0",
            name="nonnegative_trade_slippage",
        ),
        CheckConstraint(
            "char_length(config_hash) = 64",
            name="valid_trade_config_hash",
        ),
        Index("ix_trades_signal_id", "signal_id"),
        Index(
            "ix_trades_strategy_entry_at",
            "strategy_name",
            "entry_at",
        ),
    )
