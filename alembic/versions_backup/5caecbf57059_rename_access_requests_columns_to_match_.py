"""rename access_requests columns to match model

Revision ID: 5caecbf57059
Revises: fda6e4a87e8d
Create Date: 2026-01-20 12:12:03.079463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5caecbf57059'
down_revision: Union[str, Sequence[str], None] = 'fda6e4a87e8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Renombrar columnas a lo que espera el modelo
    op.alter_column("access_requests", "requested_by_user_id", new_column_name="user_id")
    op.alter_column("access_requests", "modulo", new_column_name="recurso")
    op.alter_column("access_requests", "estado", new_column_name="status")
    op.alter_column("access_requests", "resolved_by_user_id", new_column_name="approved_by")

    # 2) Asegurar longitudes (opcional pero pro)
    op.alter_column("access_requests", "recurso", type_=sa.String(length=60), existing_type=sa.String())
    op.alter_column("access_requests", "status", type_=sa.String(length=20), existing_type=sa.String())

    # 3) Crear FKs (si no existen)
    op.create_foreign_key(
        "fk_access_requests_user_id_usuarios",
        "access_requests", "usuarios",
        ["user_id"], ["id"],
        ondelete="CASCADE"
    )

    op.create_foreign_key(
        "fk_access_requests_approved_by_usuarios",
        "access_requests", "usuarios",
        ["approved_by"], ["id"],
        ondelete="SET NULL"
    )

    # 4) Índices (si quieres pro / rápido)
    op.execute("CREATE INDEX IF NOT EXISTS ix_access_requests_user_id ON access_requests (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_access_requests_empresa_id ON access_requests (empresa_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_access_requests_status ON access_requests (status)")


def downgrade() -> None:
    """Downgrade schema."""
    # bajar índices
    op.drop_index("ix_access_requests_status", table_name="access_requests")
    op.drop_index("ix_access_requests_empresa_id", table_name="access_requests")
    op.drop_index("ix_access_requests_user_id", table_name="access_requests")

    # bajar FKs
    op.drop_constraint("fk_access_requests_approved_by_usuarios", "access_requests", type_="foreignkey")
    op.drop_constraint("fk_access_requests_user_id_usuarios", "access_requests", type_="foreignkey")

    # renombrar de vuelta
    op.alter_column("access_requests", "approved_by", new_column_name="resolved_by_user_id")
    op.alter_column("access_requests", "status", new_column_name="estado")
    op.alter_column("access_requests", "recurso", new_column_name="modulo")
    op.alter_column("access_requests", "user_id", new_column_name="requested_by_user_id")
