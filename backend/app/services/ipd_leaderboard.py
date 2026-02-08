from __future__ import annotations

import hashlib

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.bot import Bot
from app.models.ipd_duel import IpdDuel
from app.models.user import User
from app.services.code_hash import code_hash_py
from app.services.docker_ipd_runner import DockerRunConfig, run_ipd_in_docker


def _stable_seed(a: str, b: str) -> int:
    h = hashlib.sha256((a + "|" + b).encode("utf-8")).digest()
    return int.from_bytes(h[:4], "big") & 0x7FFFFFFF


def ensure_ipd_duel(*, db: Session, cfg: DockerRunConfig, bot_x: Bot, bot_y: Bot) -> IpdDuel:
    """Ensure a duel exists for the (unordered) pair.

    We store the duel as (bot1_id < bot2_id) and run exactly one sandbox match,
    with history normalized per-bot ([my_action, opp_action]).
    """

    if bot_x.id == bot_y.id:
        raise ValueError("same_bot")

    # order by id for stability
    if bot_x.id < bot_y.id:
        b1, b2 = bot_x, bot_y
        flip = False
    else:
        b1, b2 = bot_y, bot_x
        flip = True

    h1 = code_hash_py(b1.code)
    h2 = code_hash_py(b2.code)

    existing = db.scalar(
        select(IpdDuel)
        .where(
            IpdDuel.bot1_id == b1.id,
            IpdDuel.bot2_id == b2.id,
            IpdDuel.bot1_hash == h1,
            IpdDuel.bot2_hash == h2,
        )
        .limit(1)
    )
    if existing is not None:
        return existing

    seed = _stable_seed(h1, h2)
    result = run_ipd_in_docker(cfg=cfg, bot_a_code=b1.code, bot_b_code=b2.code, seed=seed)
    if result.error_log:
        raise RuntimeError(f"ipd_duel_failed: {result.error_log}")

    duel = IpdDuel(
        bot1_id=b1.id,
        bot2_id=b2.id,
        bot1_hash=h1,
        bot2_hash=h2,
        seed=seed,
        score1=int(result.cum_a),
        score2=int(result.cum_b),
        exec_ms_1=int(result.exec_ms_a),
        exec_ms_2=int(result.exec_ms_b),
    )
    db.add(duel)
    db.commit()
    db.refresh(duel)
    return duel


def compute_ipd_leaderboard(db: Session, *, cfg: DockerRunConfig, limit: int = 50):
    bots = list(db.scalars(select(Bot).where(Bot.env_id == "ipd", Bot.submitted.is_(True)).order_by(Bot.id.asc())))

    # Ensure duels exist for current code snapshots
    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            ensure_ipd_duel(db=db, cfg=cfg, bot_x=bots[i], bot_y=bots[j])

    rows = []
    for b in bots:
        bh = code_hash_py(b.code)

        # Collect scores and exec times from both sides of the undirected duel.
        # When b is bot1: use score1/exec_ms_1, when b is bot2: use score2/exec_ms_2.
        score_expr = case(
            (IpdDuel.bot1_id == b.id, IpdDuel.score1),
            else_=IpdDuel.score2,
        )
        exec_expr = case(
            (IpdDuel.bot1_id == b.id, IpdDuel.exec_ms_1 / 200.0),
            else_=IpdDuel.exec_ms_2 / 200.0,
        )

        hash_ok = or_(
            and_(IpdDuel.bot1_id == b.id, IpdDuel.bot1_hash == bh),
            and_(IpdDuel.bot2_id == b.id, IpdDuel.bot2_hash == bh),
        )

        q = (
            select(
                func.avg(score_expr).label("avg_score"),
                func.avg(exec_expr).label("avg_exec_ms"),
                func.count(IpdDuel.id).label("duels"),
            )
            .where(or_(IpdDuel.bot1_id == b.id, IpdDuel.bot2_id == b.id))
            .where(hash_ok)
        )
        r = db.execute(q).mappings().one()

        creator = db.scalar(select(User.username).where(User.id == b.user_id))

        opponents = max(len(bots) - 1, 0)
        rows.append(
            {
                "bot_id": int(b.id),
                "bot_name": str(b.name),
                "creator": str(creator or ""),
                "avg_score": float(r["avg_score"] or 0.0),
                "avg_exec_ms": float(r["avg_exec_ms"] or 0.0),
                "duels": int(r["duels"] or 0),
                "opponents": int(opponents),
            }
        )

    rows.sort(key=lambda x: (-x["avg_score"], x["avg_exec_ms"], -x["opponents"], x["bot_id"]))
    return rows[:limit]
