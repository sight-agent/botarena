"""add bot submission flag

Revision ID: 04b0923955ae
Revises: 0002_matches
Create Date: 2026-02-08 12:25:47.602422

"""

from alembic import op
import sqlalchemy as sa



revision = '04b0923955ae'
down_revision = '0002_matches'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bots",
        sa.Column("submitted_env", sa.String(length=50), nullable=True),
    )
    op.create_index(op.f("ix_bots_submitted_env"), "bots", ["submitted_env"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bots_submitted_env"), table_name="bots")
    op.drop_column("bots", "submitted_env")

