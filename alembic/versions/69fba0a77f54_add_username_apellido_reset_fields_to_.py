"""add username apellido reset fields to super_admins

Revision ID: 69fba0a77f54
Revises: 147cb71ee801
Create Date: 2026-01-16 17:05:27.468102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69fba0a77f54'
down_revision: Union[str, Sequence[str], None] = '147cb71ee801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade schema."""
    # 1) agregar columnas nuevas (nullable al inicio para no romper)
    op.add_column("super_admins", sa.Column("apellido", sa.String(length=120), nullable=True))
    op.add_column("super_admins", sa.Column("username", sa.String(length=80), nullable=True))
    op.add_column("super_admins", sa.Column("reset_token", sa.String(length=255), nullable=True))
    op.add_column("super_admins", sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True))

    # 2) poblar username para registros existentes (usa nombre -> minúsculas)
    op.execute("""
        UPDATE super_admins
        SET username = lower(nombre)
        WHERE username IS NULL;
    """)

    # 3) crear índice + unique
    op.create_index("ix_super_admins_username", "super_admins", ["username"])
    op.create_unique_constraint("uq_super_admins_username", "super_admins", ["username"])

    # 4) ahora sí, hacerlo NOT NULL
    op.alter_column("super_admins", "username", existing_type=sa.String(length=80), nullable=False)
    


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_super_admins_username", "super_admins", type_="unique")
    op.drop_index("ix_super_admins_username", table_name="super_admins")

    op.drop_column("super_admins", "reset_token_expires_at")
    op.drop_column("super_admins", "reset_token")
    op.drop_column("super_admins", "username")
    op.drop_column("super_admins", "apellido")
    
