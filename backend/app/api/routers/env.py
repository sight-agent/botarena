from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.docker_ipd_runner import DockerRunConfig
from app.services.ipd_leaderboard import compute_ipd_leaderboard

router = APIRouter(prefix="/env", tags=["env"])


@router.get("/ipd/leaderboard")
def ipd_leaderboard(db: Session = Depends(get_db)):
    """IPD leaderboard.

    Score definition (requested): for each submitted bot, score is the average
    score across matches against every other submitted bot.

    MVP implementation: we cache directional duels (A->B and B->A) for the current
    code snapshots, and compute each bot's mean score.
    """

    cfg = DockerRunConfig(image=settings.runner_image)
    return compute_ipd_leaderboard(db, cfg=cfg, limit=50)
