"""create cash_sessions

Revision ID: 75ce753980e1
Revises: 5a885f1050f6
Create Date: 2026-01-25 22:45:59.871711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75ce753980e1'
down_revision: Union[str, Sequence[str], None] = '5a885f1050f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
