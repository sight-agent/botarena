"""refactor bots: single code per bot; drop versions

Revision ID: 2001c1a261aa
Revises: ab4693bb595c
Create Date: 2026-02-08 12:34:06.626436

"""

from alembic import op
import sqlalchemy as sa



revision = '2001c1a261aa'
down_revision = 'ab4693bb595c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- bots: add env_id + code + submitted ---
    op.add_column("bots", sa.Column("env_id", sa.String(length=50), nullable=True))
    op.add_column("bots", sa.Column("code", sa.Text(), nullable=True))
    op.add_column(
        "bots",
        sa.Column("submitted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    # Backfill env_id (MVP: only IPD exists)
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE bots SET env_id = 'ipd' WHERE env_id IS NULL"))

    # Backfill code from active version
    # If no active_version_id, take max(version_num) as fallback.
    conn.execute(
        sa.text(
            """
            UPDATE bots b
            SET code = v.code
            FROM bot_versions v
            WHERE v.id = b.active_version_id
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE bots b
            SET code = v.code
            FROM bot_versions v
            WHERE b.code IS NULL
              AND v.bot_id = b.id
              AND v.version_num = (SELECT max(v2.version_num) FROM bot_versions v2 WHERE v2.bot_id = b.id)
            """
        )
    )
    # Ensure non-null code
    conn.execute(sa.text("UPDATE bots SET code = 'def act(observation, state):\n    return \"C\", state\n' WHERE code IS NULL"))

    # Backfill submitted from previous submitted_env
    conn.execute(sa.text("UPDATE bots SET submitted = true WHERE submitted_env = 'ipd'"))

    # Tighten nullability
    op.alter_column("bots", "env_id", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("bots", "code", existing_type=sa.Text(), nullable=False)

    # Enforce new global uniqueness (env_id, name): rename duplicates automatically.
    # Keep the smallest id as-is; for the others, append "-<id>".
    dup_rows = conn.execute(
        sa.text(
            """
            SELECT env_id, name, array_agg(id ORDER BY id) AS ids
            FROM bots
            GROUP BY env_id, name
            HAVING count(*) > 1
            """
        )
    ).fetchall()
    for env_id, name, ids in dup_rows:
        # ids is a Python list thanks to psycopg2 array adaptation
        for bid in ids[1:]:
            conn.execute(
                sa.text("UPDATE bots SET name = :new_name WHERE id = :id"),
                {"new_name": f"{name}-{bid}", "id": bid},
            )

    # Drop old unique constraint and create new one (env_id,name)
    op.drop_constraint("uq_bots_user_id_name", "bots", type_="unique")
    op.create_unique_constraint("uq_bots_env_id_name", "bots", ["env_id", "name"])

    # --- matches: remove bot_version_id, store bot_code_hash (optional) ---
    op.add_column("matches", sa.Column("bot_code_hash", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_matches_bot_code_hash"), "matches", ["bot_code_hash"], unique=False)

    # Backfill bot_code_hash from bot_versions.code_hash
    conn.execute(
        sa.text(
            """
            UPDATE matches m
            SET bot_code_hash = v.code_hash
            FROM bot_versions v
            WHERE v.id = m.bot_version_id
            """
        )
    )
    conn.execute(sa.text("UPDATE matches SET bot_code_hash = '' WHERE bot_code_hash IS NULL"))
    op.alter_column("matches", "bot_code_hash", existing_type=sa.String(length=64), nullable=False)

    # Drop FK + column bot_version_id
    op.drop_index(op.f("ix_matches_bot_version_id"), table_name="matches")
    op.drop_constraint("matches_bot_version_id_fkey", "matches", type_="foreignkey")
    op.drop_column("matches", "bot_version_id")

    # --- cleanup bots: drop active_version_id + submitted_env ---
    op.drop_column("bots", "active_version_id")
    op.drop_index(op.f("ix_bots_submitted_env"), table_name="bots")
    op.drop_column("bots", "submitted_env")

    # --- drop bot_versions table ---
    op.drop_index(op.f("ix_bot_versions_code_hash"), table_name="bot_versions")
    op.drop_constraint("uq_bot_versions_bot_id_version_num", "bot_versions", type_="unique")
    op.drop_index(op.f("ix_bot_versions_bot_id"), table_name="bot_versions")
    op.drop_table("bot_versions")


def downgrade() -> None:
    raise RuntimeError("Irreversible MVP refactor")

