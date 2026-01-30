"""add cash_session_id to ventas

Revision ID: 35049f7819fc
Revises: a0678fd19301
Create Date: 2026-01-25 18:20:58.687199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35049f7819fc'
down_revision: Union[str, Sequence[str], None] = 'a0678fd19301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "ventas",
        sa.Column(
            "cash_session_id",
            sa.Integer(),
            sa.ForeignKey("cash_sessions.id", ondelete="SET NULL"),
            nullable=True
        )
    )
    op.create_index(
        "ix_ventas_cash_session_id",
        "ventas",
        ["cash_session_id"]
    )



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_ventas_cash_session_id", table_name="ventas")
    op.drop_column("ventas", "cash_session_id")
