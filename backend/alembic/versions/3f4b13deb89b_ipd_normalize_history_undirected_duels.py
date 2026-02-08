"""ipd: normalize history; undirected duels

Revision ID: 3f4b13deb89b
Revises: 0fdf135e783a
Create Date: 2026-02-08 12:59:21.683354

"""

from alembic import op
import sqlalchemy as sa



revision = '3f4b13deb89b'
down_revision = '0fdf135e783a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop and recreate ipd_duels with undirected pairs (bot1<bot2).
    op.drop_table("ipd_duels")

    op.create_table(
        "ipd_duels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bot1_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot2_id", sa.Integer(), sa.ForeignKey("bots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("bot1_hash", sa.String(length=64), nullable=False),
        sa.Column("bot2_hash", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("score1", sa.Integer(), nullable=False),
        sa.Column("score2", sa.Integer(), nullable=False),
        sa.Column("exec_ms_1", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exec_ms_2", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("bot1_id < bot2_id", name="ck_ipd_duels_bot_order"),
        sa.UniqueConstraint("bot1_id", "bot2_id", "bot1_hash", "bot2_hash", name="uq_ipd_duels_pair_hash"),
    )
    op.create_index(op.f("ix_ipd_duels_bot1_id"), "ipd_duels", ["bot1_id"], unique=False)
    op.create_index(op.f("ix_ipd_duels_bot2_id"), "ipd_duels", ["bot2_id"], unique=False)


def downgrade() -> None:
    raise RuntimeError("Irreversible MVP change")

