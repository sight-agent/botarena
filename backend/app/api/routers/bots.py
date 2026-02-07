from fastapi import APIRouter, Depends, HTTPException, status
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
from app.schemas.bot import (
    BotCreateIn,
    BotOut,
    BotVersionCreateIn,
    BotVersionOut,
    BotWithVersionsOut,
    SetActiveVersionIn,
)

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
def bots_run_test(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Sandbox execution is intentionally not implemented in this scaffold.
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="not_implemented")


@router.post("/{bot_id}/submit")
def bots_submit(bot_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Ranked submission/evaluation is intentionally not implemented in this scaffold.
    bot = get_bot(db, user.id, bot_id)
    if bot is None:
        raise HTTPException(status_code=404, detail="bot_not_found")
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="not_implemented")

