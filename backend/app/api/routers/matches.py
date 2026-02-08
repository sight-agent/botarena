from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.match import Match
from app.models.match_step import MatchStep
from app.schemas.match import MatchOut, MatchStepOut

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/{match_id}", response_model=MatchOut)
def matches_get(match_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.scalar(select(Match).where(Match.id == match_id, Match.user_id == user.id))
    if m is None:
        raise HTTPException(status_code=404, detail="match_not_found")

    steps = list(db.scalars(select(MatchStep).where(MatchStep.match_id == m.id).order_by(MatchStep.round.asc())))
    return MatchOut(
        id=m.id,
        env_id=m.env_id,
        bot_id=m.bot_id,
        bot_code_hash=m.bot_code_hash,
        opponent_name=m.opponent_name,
        seed=m.seed,
        status=m.status,
        started_at=m.started_at,
        finished_at=m.finished_at,
        error_log=m.error_log,
        steps=[
            MatchStepOut(
                round=s.round,
                obs_a=s.obs_a,
                act_a=s.act_a,
                obs_b=s.obs_b,
                act_b=s.act_b,
                reward_a=s.reward_a,
                reward_b=s.reward_b,
                cum_a=s.cum_a,
                cum_b=s.cum_b,
            )
            for s in steps
        ],
    )

