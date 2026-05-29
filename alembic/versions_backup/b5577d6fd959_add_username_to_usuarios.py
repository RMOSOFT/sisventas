"""add username to usuarios

Revision ID: b5577d6fd959
Revises: 92b2d54d37b4
Create Date: 2026-01-17 17:40:07.730572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5577d6fd959'
down_revision: Union[str, Sequence[str], None] = '92b2d54d37b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) agregar columna como NULLABLE primero (para no romper data)
    op.add_column("usuarios", sa.Column("username", sa.String(length=60), nullable=True))

    # 2) backfill: generar username para los existentes (seguro y único)
    #    ejemplo: user_1, user_2, ...
    op.execute("UPDATE usuarios SET username = 'user_' || id WHERE username IS NULL")

    # 3) ahora sí: hacerlo NOT NULL
    op.alter_column("usuarios", "username", nullable=False)

    # 4) crear unique constraints por empresa
    op.create_unique_constraint("uq_usuario_empresa_username", "usuarios", ["empresa_id", "username"])
    #op.create_unique_constraint("uq_usuario_empresa_email", "usuarios", ["empresa_id", "email"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_usuario_empresa_email", "usuarios", type_="unique")
    op.drop_constraint("uq_usuario_empresa_username", "usuarios", type_="unique")
    op.drop_column("usuarios", "username")
