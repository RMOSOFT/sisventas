"""baseline

Revision ID: 218dfdd3ca24
Revises: f47527ec80cc
Create Date: 2026-01-16 12:49:37.781032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '218dfdd3ca24'
down_revision: Union[str, Sequence[str], None] = 'f47527ec80cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
