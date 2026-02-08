from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IpdDuel(Base):
    __tablename__ = "ipd_duels"
    __table_args__ = (
        UniqueConstraint("bot_a_id", "bot_b_id", "bot_a_hash", "bot_b_hash", name="uq_ipd_duels_pair_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    bot_a_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)
    bot_b_id: Mapped[int] = mapped_column(ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, index=True)

    bot_a_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    bot_b_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    score_a: Mapped[int] = mapped_column(Integer, nullable=False)
    score_b: Mapped[int] = mapped_column(Integer, nullable=False)

    # Total execution time in ms (approx) spent waiting for each bot's responses.
    exec_ms_a: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    exec_ms_b: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
