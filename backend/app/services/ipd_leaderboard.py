from __future__ import annotations

import hashlib

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.bot import Bot
from app.models.ipd_duel import IpdDuel
from app.services.code_hash import code_hash_py
from app.services.docker_ipd_runner import DockerRunConfig, run_ipd_in_docker


def _stable_seed(a: str, b: str) -> int:
    h = hashlib.sha256((a + "|" + b).encode("utf-8")).digest()
    # fit in signed 31-bit for consistency
    return int.from_bytes(h[:4], "big") & 0x7FFFFFFF


def ensure_ipd_duel(
    *,
    db: Session,
    cfg: DockerRunConfig,
    bot_a: Bot,
    bot_b: Bot,
) -> IpdDuel:
    """Ensure a duel exists for the given bot code snapshots.

    Duel is directional (A vs B). For fairness, leaderboard will use both A->B and B->A.
    """

    a_hash = code_hash_py(bot_a.code)
    b_hash = code_hash_py(bot_b.code)

    existing = db.scalar(
        select(IpdDuel)
        .where(
            IpdDuel.bot_a_id == bot_a.id,
            IpdDuel.bot_b_id == bot_b.id,
            IpdDuel.bot_a_hash == a_hash,
            IpdDuel.bot_b_hash == b_hash,
        )
        .limit(1)
    )
    if existing is not None:
        return existing

    seed = _stable_seed(a_hash, b_hash)

    result = run_ipd_in_docker(cfg=cfg, bot_a_code=bot_a.code, bot_b_code=bot_b.code, seed=seed)
    if result.error_log:
        # Don't persist a broken duel snapshot
        raise RuntimeError(f"ipd_duel_failed: {result.error_log}")

    duel = IpdDuel(
        bot_a_id=bot_a.id,
        bot_b_id=bot_b.id,
        bot_a_hash=a_hash,
        bot_b_hash=b_hash,
        seed=seed,
        score_a=int(result.cum_a),
        score_b=int(result.cum_b),
    )
    db.add(duel)
    db.commit()
    db.refresh(duel)
    return duel


def compute_ipd_leaderboard(db: Session, *, cfg: DockerRunConfig, limit: int = 50):
    """Leaderboard score = average score vs all other submitted bots.

    For each pair (A,B), we run 2 directional duels (A->B, B->A) and then
    each bot's score is the mean of its directional scores against all opponents.

    Returns rows: {bot_id, bot_name, avg_score, opponents, duels}
    """

    bots = list(db.scalars(select(Bot).where(Bot.env_id == "ipd", Bot.submitted.is_(True)).order_by(Bot.id.asc())))

    # Ensure duels exist (directional) for current code snapshots
    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            a = bots[i]
            b = bots[j]
            ensure_ipd_duel(db=db, cfg=cfg, bot_a=a, bot_b=b)
            ensure_ipd_duel(db=db, cfg=cfg, bot_a=b, bot_b=a)

    # Aggregate: for each bot, average over duels where it's bot_a, using current hashes
    rows = []
    for b in bots:
        b_hash = code_hash_py(b.code)
        q = (
            select(
                func.avg(IpdDuel.score_a).label("avg_score"),
                func.count(IpdDuel.id).label("duels"),
                func.count(func.distinct(IpdDuel.bot_b_id)).label("opponents"),
            )
            .where(IpdDuel.bot_a_id == b.id, IpdDuel.bot_a_hash == b_hash)
        )
        r = db.execute(q).mappings().one()
        rows.append(
            {
                "bot_id": int(b.id),
                "bot_name": str(b.name),
                "avg_score": float(r["avg_score"] or 0.0),
                "duels": int(r["duels"] or 0),
                "opponents": int(r["opponents"] or 0),
            }
        )

    rows.sort(key=lambda x: (-x["avg_score"], -x["opponents"], x["bot_id"]))
    return rows[:limit]
