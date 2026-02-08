"""ipd duels store exec time

Revision ID: 0fdf135e783a
Revises: 61bd7a670a46
Create Date: 2026-02-08 12:51:04.235115

"""

from alembic import op
import sqlalchemy as sa



revision = '0fdf135e783a'
down_revision = '61bd7a670a46'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ipd_duels", sa.Column("exec_ms_a", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ipd_duels", sa.Column("exec_ms_b", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("ipd_duels", "exec_ms_b")
    op.drop_column("ipd_duels", "exec_ms_a")

