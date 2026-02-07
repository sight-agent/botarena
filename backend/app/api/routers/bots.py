from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.bots import (
    create_bot_with_initial_version,
    create_version,
    get_bot,
    list_bots,
    set_active_version,
)
from app.db.session import get_db
from app.models.bot_version import BotVersion
from app.models.match import Match
from app.models.match_step import MatchStep
from app.core.config import settings
from app.services.docker_ipd_runner import DockerRunConfig, run_ipd_in_docker
from app.schemas.bot import (
    BotCreateIn,
    BotOut,
    BotVersionCreateIn,
    BotVersionOut,
    BotWithVersionsOut,
    SetActiveVersionIn,
)
from app.schemas.match import RunTestOut

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("", response_model=list[BotOut])
def bots_list(db: Session = Depends(get_db), user=Depends(get_current_user)):
    bots = list_bots(db, user.id)
    return [
        BotOut(
            id=b.id,
            name=b.name,
            description=b.description,
            active_version_id=b.active_version_id,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in bots
    ]


@router.post("", response_model=BotOut, status_code=201)
def bots_create(payload: BotCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        bot = create_bot_with_initial_version(
            db, user_id=user.id, name=payload.name, description=payload.description, code=payload.code
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="bot_name_taken")
    return BotOut(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        active_version_id=bot.active_version_id,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.get("/{bot_id}", response_model=BotWithVersionsOut)
def bots_get(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")
    versions = list(db.query(BotVersion).filter(BotVersion.bot_id == bot.id).order_by(BotVersion.version_num.asc()).all())
    return BotWithVersionsOut(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        active_version_id=bot.active_version_id,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
        versions=[
            BotVersionOut(id=v.id, version_num=v.version_num, code=v.code, created_at=v.created_at) for v in versions
        ],
    )


@router.post("/{bot_id}/versions", response_model=BotVersionOut, status_code=201)
def bots_create_version(
    bot_id: int, payload: BotVersionCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    try:
        v = create_version(db, user_id=user.id, bot_id=bot_id, code=payload.code)
    except ValueError as e:
        if str(e) == "bot_not_found":
            raise HTTPException(status_code=404, detail="bot_not_found")
        raise
    return BotVersionOut(id=v.id, version_num=v.version_num, code=v.code, created_at=v.created_at)


@router.post("/{bot_id}/active_version", response_model=BotOut)
def bots_set_active(
    bot_id: int, payload: SetActiveVersionIn, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    try:
        bot = set_active_version(db, user_id=user.id, bot_id=bot_id, version_id=payload.version_id)
    except ValueError as e:
        if str(e) == "bot_not_found":
            raise HTTPException(status_code=404, detail="bot_not_found")
        if str(e) == "version_not_found":
            raise HTTPException(status_code=404, detail="version_not_found")
        raise
    return BotOut(
        id=bot.id,
        name=bot.name,
        description=bot.description,
        active_version_id=bot.active_version_id,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.post("/{bot_id}/run-test")
def bots_run_test(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> RunTestOut:
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")
    if bot.active_version_id is None:
        raise HTTPException(status_code=400, detail="no_active_version")

    active = db.scalar(
        select(BotVersion).where(BotVersion.id == bot.active_version_id, BotVersion.bot_id == bot.id)
    )
    if active is None:
        raise HTTPException(status_code=400, detail="active_version_missing")

    seed = secrets.randbelow(2**31 - 1)
    baseline_code = "def act(observation, state):\n    return 'C', state\n"

    match = Match(
        env_id="ipd",
        user_id=user.id,
        bot_id=bot.id,
        bot_version_id=active.id,
        opponent_name="always_cooperate",
        seed=seed,
        status="running",
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    cfg = DockerRunConfig(image=settings.runner_image)
    result = run_ipd_in_docker(cfg=cfg, bot_a_code=active.code, bot_b_code=baseline_code, seed=seed)

    if result.error_log:
        match.status = "failed"
        match.finished_at = datetime.now(timezone.utc)
        match.error_log = result.error_log
        db.add(match)
        db.commit()
        raise HTTPException(status_code=500, detail="runner_failed")

    steps = []
    for s in result.steps:
        steps.append(
            MatchStep(
                match_id=match.id,
                round=int(s["round"]),
                obs_a=s["obs_a"],
                act_a=str(s["act_a"]),
                obs_b=s["obs_b"],
                act_b=str(s["act_b"]),
                reward_a=int(s["reward_a"]),
                reward_b=int(s["reward_b"]),
                cum_a=int(s["cum_a"]),
                cum_b=int(s["cum_b"]),
            )
        )

    match.status = "completed"
    match.finished_at = datetime.now(timezone.utc)
    db.add(match)
    db.add_all(steps)
    db.commit()

    return RunTestOut(match_id=match.id, cum_a=int(result.cum_a), cum_b=int(result.cum_b))


@router.post("/{bot_id}/submit")
def bots_submit(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Ranked submission/evaluation is intentionally not implemented in this scaffold.
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="not_implemented")
