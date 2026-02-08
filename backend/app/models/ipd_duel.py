from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IpdDuel(Base):
    __tablename__ = "ipd_duels"
    __table_args__ = (
        CheckConstraint("bot1_id < bot2_id", name="ck_ipd_duels_bot_order"),
        UniqueConstraint("bot1_id", "bot2_id", "bot1_hash", "bot2_hash", name="uq_ipd_duels_pair_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    bot1_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    bot2_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)

    bot1_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    bot2_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    seed: Mapped[int] = mapped_column(Integer, nullable=False)

    # Scores from the perspective of each bot (history is normalized per-bot)
    score1: Mapped[int] = mapped_column(Integer, nullable=False)
    score2: Mapped[int] = mapped_column(Integer, nullable=False)

    # Total execution time in ms (approx) spent waiting for each bot's responses.
    exec_ms_1: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    exec_ms_2: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
