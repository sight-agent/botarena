"""add code_hash to bot_versions

Revision ID: ab4693bb595c
Revises: 04b0923955ae
Create Date: 2026-02-08 12:30:40.352652

"""

from alembic import op
import sqlalchemy as sa



revision = 'ab4693bb595c'
down_revision = '04b0923955ae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add column nullable first to backfill.
    op.add_column("bot_versions", sa.Column("code_hash", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_bot_versions_code_hash"), "bot_versions", ["code_hash"], unique=False)

    # 2) Backfill using python AST hashing (ignore whitespace/comments).
    import ast
    import hashlib

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, code FROM bot_versions")).fetchall()
    for (vid, code) in rows:
        try:
            tree = ast.parse(code)
            canonical = ast.dump(tree, include_attributes=False)
            ch = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        except Exception:
            # Keep null if unparsable; later saves will reject invalid syntax anyway.
            ch = None
        conn.execute(sa.text("UPDATE bot_versions SET code_hash = :ch WHERE id = :id"), {"ch": ch, "id": vid})

    # 3) Make non-nullable (for valid existing code).
    conn.execute(sa.text("UPDATE bot_versions SET code_hash = '' WHERE code_hash IS NULL"))
    op.alter_column("bot_versions", "code_hash", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bot_versions_code_hash"), table_name="bot_versions")
    op.drop_column("bot_versions", "code_hash")

