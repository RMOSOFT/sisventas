"""create stock_movements

Revision ID: f872f6200ac3
Revises: 7f8409eac63c
Create Date: 2026-01-25 07:46:53.398589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f872f6200ac3'
down_revision: Union[str, Sequence[str], None] = '7f8409eac63c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
