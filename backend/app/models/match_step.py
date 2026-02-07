from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class MatchStep(Base):
    __tablename__ = "match_steps"
    __table_args__ = (UniqueConstraint("match_id", "round", name="uq_match_steps_match_id_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)

    round: Mapped[int] = mapped_column(Integer, nullable=False)

    # Use JSONB on Postgres, generic JSON elsewhere (sqlite in tests).
    obs_a: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    act_a: Mapped[str] = mapped_column(String(1), nullable=False)
    obs_b: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    act_b: Mapped[str] = mapped_column(String(1), nullable=False)

    reward_a: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_b: Mapped[int] = mapped_column(Integer, nullable=False)
    cum_a: Mapped[int] = mapped_column(Integer, nullable=False)
    cum_b: Mapped[int] = mapped_column(Integer, nullable=False)

    match = relationship("Match", back_populates="steps")

