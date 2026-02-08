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
    # Idempotent: previous failed attempts might have created the columns.
    op.execute("ALTER TABLE ipd_duels ADD COLUMN IF NOT EXISTS exec_ms_a INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE ipd_duels ADD COLUMN IF NOT EXISTS exec_ms_b INTEGER NOT NULL DEFAULT 0")


def downgrade() -> None:
    op.execute("ALTER TABLE ipd_duels DROP COLUMN IF EXISTS exec_ms_b")
    op.execute("ALTER TABLE ipd_duels DROP COLUMN IF EXISTS exec_ms_a")

