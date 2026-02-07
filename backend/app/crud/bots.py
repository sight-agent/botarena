from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.bot import Bot
from app.models.bot_version import BotVersion


def list_bots(db: Session, user_id: int) -> list[Bot]:
    return list(db.scalars(select(Bot).where(Bot.user_id == user_id).order_by(desc(Bot.updated_at))))


def get_bot(db: Session, user_id: int, bot_id: int) -> Bot | None:
    return db.scalar(select(Bot).where(Bot.user_id == user_id, Bot.id == bot_id))


def create_bot_with_initial_version(
    db: Session, *, user_id: int, name: str, description: str | None, code: str
) -> Bot:
    bot = Bot(user_id=user_id, name=name, description=description)
    db.add(bot)
    db.flush()  # assigns bot.id

    v1 = BotVersion(bot_id=bot.id, version_num=1, code=code)
    db.add(v1)
    db.flush()

    bot.active_version_id = v1.id
    db.commit()
    db.refresh(bot)
    return bot


def create_version(db: Session, *, user_id: int, bot_id: int, code: str) -> BotVersion:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")

    next_num = db.scalar(select(func.coalesce(func.max(BotVersion.version_num), 0) + 1).where(BotVersion.bot_id == bot_id))
    v = BotVersion(bot_id=bot_id, version_num=int(next_num), code=code)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def set_active_version(db: Session, *, user_id: int, bot_id: int, version_id: int) -> Bot:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")

    version = db.scalar(select(BotVersion).where(BotVersion.bot_id == bot_id, BotVersion.id == version_id))
    if version is None:
        raise ValueError("version_not_found")

    bot.active_version_id = version.id
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

