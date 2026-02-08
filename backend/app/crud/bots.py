from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.bot import Bot


def list_bots(db: Session, user_id: int) -> list[Bot]:
    return list(db.scalars(select(Bot).where(Bot.user_id == user_id).order_by(desc(Bot.updated_at))))


def get_bot(db: Session, user_id: int, bot_id: int) -> Bot | None:
    return db.scalar(select(Bot).where(Bot.user_id == user_id, Bot.id == bot_id))


def create_bot(
    db: Session, *, user_id: int, env_id: str, name: str, description: str | None, code: str
) -> Bot:
    bot = Bot(user_id=user_id, env_id=env_id, name=name, description=description, code=code, submitted=False)
    db.add(bot)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(bot)
    return bot


def update_bot_code(db: Session, *, user_id: int, bot_id: int, code: str) -> Bot:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")
    bot.code = code
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


def delete_bot(db: Session, *, user_id: int, bot_id: int) -> None:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")
    db.delete(bot)
    db.commit()


def submit_bot(db: Session, *, user_id: int, bot_id: int) -> Bot:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")
    bot.submitted = True
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot
