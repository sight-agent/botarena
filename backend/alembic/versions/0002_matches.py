"""matches + match_steps

Revision ID: 0002_matches
Revises: 0001_init
Create Date: 2026-02-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_matches"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("env_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "bot_version_id",
            sa.Integer(),
            sa.ForeignKey("bot_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("opponent_name", sa.String(length=100), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_log", sa.Text(), nullable=True),
    )
    op.create_index(op.f("ix_matches_env_id"), "matches", ["env_id"], unique=False)
    op.create_index(op.f("ix_matches_user_id"), "matches", ["user_id"], unique=False)
    op.create_index(op.f("ix_matches_bot_id"), "matches", ["bot_id"], unique=False)
    op.create_index(op.f("ix_matches_bot_version_id"), "matches", ["bot_version_id"], unique=False)
    op.create_index(op.f("ix_matches_status"), "matches", ["status"], unique=False)

    json_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")
    op.create_table(
        "match_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("match_id", sa.Integer(), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("obs_a", json_type, nullable=False),
        sa.Column("act_a", sa.String(length=1), nullable=False),
        sa.Column("obs_b", json_type, nullable=False),
        sa.Column("act_b", sa.String(length=1), nullable=False),
        sa.Column("reward_a", sa.Integer(), nullable=False),
        sa.Column("reward_b", sa.Integer(), nullable=False),
        sa.Column("cum_a", sa.Integer(), nullable=False),
        sa.Column("cum_b", sa.Integer(), nullable=False),
        sa.UniqueConstraint("match_id", "round", name="uq_match_steps_match_id_round"),
    )
    op.create_index(op.f("ix_match_steps_match_id"), "match_steps", ["match_id"], unique=False)


def downgrade() -> None:
    op.drop_table("match_steps")
    op.drop_table("matches")

