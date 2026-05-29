"""add session_id to access_requests

Revision ID: a615e4a398fe
Revises: 5caecbf57059
Create Date: 2026-01-20 21:58:00.096948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a615e4a398fe'
down_revision: Union[str, Sequence[str], None] = '5caecbf57059'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("access_requests", sa.Column("session_id", sa.String(length=64), nullable=True))

    # opcional: índice para búsqueda rápida
    op.create_index(
        "ix_access_requests_session_id",
        "access_requests",
        ["session_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_access_requests_session_id", table_name="access_requests")
    op.drop_column("access_requests", "session_id")
