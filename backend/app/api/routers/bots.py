from __future__ import annotations

from datetime import datetime, timezone
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.crud.bots import create_bot, delete_bot, get_bot, list_bots, submit_bot, update_bot_code
from app.db.session import get_db
from app.models.match import Match
from app.models.match_step import MatchStep
from app.schemas.bot import BotCreateIn, BotDetailOut, BotOut, BotUpdateCodeIn
from app.schemas.match import RunTestOut
from app.services.code_hash import code_hash_py
from app.services.docker_ipd_runner import DockerRunConfig, run_ipd_in_docker

router = APIRouter(prefix="/bots", tags=["bots"])


@router.get("", response_model=list[BotOut])
def bots_list(db: Session = Depends(get_db), user=Depends(get_current_user)):
    bots = list_bots(db, user.id)
    return [
        BotOut(
            id=b.id,
            env_id=b.env_id,
            name=b.name,
            description=b.description,
            submitted=bool(b.submitted),
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in bots
    ]


@router.post("", response_model=BotOut, status_code=201)
def bots_create(payload: BotCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        bot = create_bot(
            db,
            user_id=user.id,
            env_id=payload.env_id,
            name=payload.name,
            description=payload.description,
            code=payload.code,
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="bot_name_taken")

    return BotOut(
        id=bot.id,
        env_id=bot.env_id,
        name=bot.name,
        description=bot.description,
        submitted=bool(bot.submitted),
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.get("/{bot_id}", response_model=BotDetailOut)
def bots_get(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")

    return BotDetailOut(
        id=bot.id,
        env_id=bot.env_id,
        name=bot.name,
        description=bot.description,
        submitted=bool(bot.submitted),
        code=bot.code,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.put("/{bot_id}", response_model=BotDetailOut)
def bots_update_code(
    bot_id: int, payload: BotUpdateCodeIn, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    try:
        bot = update_bot_code(db, user_id=user.id, bot_id=bot_id, code=payload.code)
    except ValueError as e:
        if str(e) == "bot_not_found":
            raise HTTPException(status_code=404, detail="bot_not_found")
        raise

    return BotDetailOut(
        id=bot.id,
        env_id=bot.env_id,
        name=bot.name,
        description=bot.description,
        submitted=bool(bot.submitted),
        code=bot.code,
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.post("/{bot_id}/run-test")
def bots_run_test(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)) -> RunTestOut:
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")

    if bot.env_id != "ipd":
        raise HTTPException(status_code=400, detail="unsupported_env")

    seed = secrets.randbelow(2**31 - 1)
    baseline_code = "def act(observation, state):\n    return 'C', state\n"

    bot_hash = code_hash_py(bot.code)

    match = Match(
        env_id="ipd",
        user_id=user.id,
        bot_id=bot.id,
        bot_code_hash=bot_hash,
        opponent_name="always_cooperate",
        seed=seed,
        status="running",
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    cfg = DockerRunConfig(image=settings.runner_image)
    result = run_ipd_in_docker(cfg=cfg, bot_a_code=bot.code, bot_b_code=baseline_code, seed=seed)

    if result.error_log:
        match.status = "failed"
        match.finished_at = datetime.now(timezone.utc)
        match.error_log = result.error_log
        db.add(match)
        db.commit()
        raise HTTPException(status_code=500, detail="runner_failed")

    steps = [
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
        for s in result.steps
    ]

    match.status = "completed"
    match.finished_at = datetime.now(timezone.utc)
    db.add(match)
    db.add_all(steps)
    db.commit()

    return RunTestOut(match_id=match.id, cum_a=int(result.cum_a), cum_b=int(result.cum_b))


@router.post("/{bot_id}/submit", response_model=BotOut)
def bots_submit(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        bot = submit_bot(db, user_id=user.id, bot_id=bot_id)
    except ValueError as e:
        if str(e) == "bot_not_found":
            raise HTTPException(status_code=404, detail="bot_not_found")
        raise

    return BotOut(
        id=bot.id,
        env_id=bot.env_id,
        name=bot.name,
        description=bot.description,
        submitted=bool(bot.submitted),
        created_at=bot.created_at,
        updated_at=bot.updated_at,
    )


@router.delete("/{bot_id}")
def bots_delete(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        delete_bot(db, user_id=user.id, bot_id=bot_id)
    except ValueError as e:
        if str(e) == "bot_not_found":
            raise HTTPException(status_code=404, detail="bot_not_found")
        raise
    return {"ok": True}
