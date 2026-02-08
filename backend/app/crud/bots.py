from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.bot import Bot
from app.models.bot_version import BotVersion
from app.services.code_hash import code_hash_py


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

    v1 = BotVersion(bot_id=bot.id, version_num=1, code=code, code_hash=code_hash_py(code))
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

    # Prevent saving syntactically identical versions (ignore whitespace + comments)
    # by comparing AST-hashes.
    try:
        ch = code_hash_py(code)
    except SyntaxError:
        # Let validation happen elsewhere (or return a clearer error later).
        raise

    exists = db.scalar(select(BotVersion.id).where(BotVersion.bot_id == bot_id, BotVersion.code_hash == ch).limit(1))
    if exists is not None:
        raise ValueError("duplicate_code")

    next_num = db.scalar(select(func.coalesce(func.max(BotVersion.version_num), 0) + 1).where(BotVersion.bot_id == bot_id))
    v = BotVersion(bot_id=bot_id, version_num=int(next_num), code=code, code_hash=ch)
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


def delete_bot(db: Session, *, user_id: int, bot_id: int) -> None:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")
    db.delete(bot)
    db.commit()


def delete_version(db: Session, *, user_id: int, bot_id: int, version_id: int) -> None:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")

    if bot.active_version_id == version_id:
        raise ValueError("cannot_delete_active_version")

    v = db.scalar(select(BotVersion).where(BotVersion.bot_id == bot_id, BotVersion.id == version_id))
    if v is None:
        raise ValueError("version_not_found")

    db.delete(v)
    db.commit()


def submit_bot(db: Session, *, user_id: int, bot_id: int, env_id: str) -> Bot:
    bot = get_bot(db, user_id, bot_id)
    if bot is None:
        raise ValueError("bot_not_found")
    if bot.active_version_id is None:
        raise ValueError("no_active_version")

    bot.submitted_env = env_id
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

