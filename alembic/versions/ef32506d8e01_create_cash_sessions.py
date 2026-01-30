"""create cash_sessions

Revision ID: ef32506d8e01
Revises: f872f6200ac3
Create Date: 2026-01-25 17:43:15.508185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef32506d8e01'
down_revision: Union[str, Sequence[str], None] = 'f872f6200ac3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
