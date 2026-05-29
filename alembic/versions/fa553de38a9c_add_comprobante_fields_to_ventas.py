"""add comprobante fields to ventas

Revision ID: fa553de38a9c
Revises: cecbcbb17454
Create Date: 2026-02-14 09:32:52.206526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa553de38a9c'
down_revision: Union[str, Sequence[str], None] = 'cecbcbb17454'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Agrega columnas permitiendo NULL (para no romper data antigua)
    op.add_column("ventas", sa.Column("tipo_comprobante", sa.String(2), nullable=True))
    op.add_column("ventas", sa.Column("serie", sa.String(4), nullable=True))
    op.add_column("ventas", sa.Column("correlativo", sa.Integer(), nullable=True))

    # 2) Backfill para ventas antiguas (las marcas como boleta)
    #    Aquí puedes usar numero como correlativo si ya existía
    op.execute("""
        UPDATE ventas
        SET tipo_comprobante = COALESCE(tipo_comprobante, 'B'),
            serie = COALESCE(serie, 'B001'),
            correlativo = COALESCE(correlativo, numero)
    """)

    # 3) Ahora sí: NOT NULL
    op.alter_column("ventas", "tipo_comprobante", nullable=False)
    op.alter_column("ventas", "serie", nullable=False)
    op.alter_column("ventas", "correlativo", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ventas", "correlativo")
    op.drop_column("ventas", "serie")
    op.drop_column("ventas", "tipo_comprobante")
