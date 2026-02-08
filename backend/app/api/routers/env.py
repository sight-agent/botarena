from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.bot import Bot
from app.models.match import Match
from app.models.match_step import MatchStep

router = APIRouter(prefix="/env", tags=["env"])

# Keep in sync with runner/env for now.
IPD_ROUNDS = 200


@router.get("/ipd/leaderboard")
def ipd_leaderboard(db: Session = Depends(get_db)):
    """Simple leaderboard for IPD.

    MVP definition: best (max) cumulative score achieved by each bot
    across completed matches (vs baseline).
    """

    # Subquery: per match, take the last step cumulative score for bot A.
    last_step = (
        select(
            MatchStep.match_id.label("match_id"),
            MatchStep.cum_a.label("cum_a"),
        )
        .where(MatchStep.round == IPD_ROUNDS)
        .subquery()
    )

    q = (
        select(
            Bot.id.label("bot_id"),
            Bot.name.label("bot_name"),
            func.max(last_step.c.cum_a).label("best_score"),
            func.count(Match.id).label("matches"),
        )
        .join(Match, Match.bot_id == Bot.id)
        .join(last_step, last_step.c.match_id == Match.id)
        .where(Match.env_id == "ipd", Match.status == "completed")
        .group_by(Bot.id, Bot.name)
        .order_by(func.max(last_step.c.cum_a).desc(), func.count(Match.id).desc(), Bot.id.asc())
        .limit(50)
    )

    rows = db.execute(q).mappings().all()
    return [
        {
            "bot_id": int(r["bot_id"]),
            "bot_name": str(r["bot_name"]),
            "best_score": int(r["best_score"] or 0),
            "matches": int(r["matches"] or 0),
        }
        for r in rows
    ]
