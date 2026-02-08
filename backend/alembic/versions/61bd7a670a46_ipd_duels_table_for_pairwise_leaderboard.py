"""ipd duels table for pairwise leaderboard

Revision ID: 61bd7a670a46
Revises: 2001c1a261aa
Create Date: 2026-02-08 12:47:35.330433

"""

from alembic import op
import sqlalchemy as sa



revision = '61bd7a670a46'
down_revision = '2001c1a261aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ipd_duels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot_a_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot_b_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot_a_hash", sa.String(length=64), nullable=False),
        sa.Column("bot_b_hash", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("score_a", sa.Integer(), nullable=False),
        sa.Column("score_b", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("bot_a_id", "bot_b_id", "bot_a_hash", "bot_b_hash", name="uq_ipd_duels_pair_hash"),
    )
    op.create_index(op.f("ix_ipd_duels_bot_a_id"), "ipd_duels", ["bot_a_id"], unique=False)
    op.create_index(op.f("ix_ipd_duels_bot_b_id"), "ipd_duels", ["bot_b_id"], unique=False)


def downgrade() -> None:
    op.drop_table("ipd_duels")

