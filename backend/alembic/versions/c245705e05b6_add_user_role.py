"""add_user_role

Revision ID: c245705e05b6
Revises: 142a80df8daf
Create Date: 2026-01-19 01:08:17.899578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c245705e05b6'
down_revision: Union[str, None] = '142a80df8daf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum type
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'COMMON')")
    
    # Adicionar coluna com valor padrão para registros existentes
    op.add_column('users', sa.Column('role', sa.Enum('ADMIN', 'COMMON', name='userrole'), nullable=True))
    
    # Definir todos os usuários existentes como COMMON
    # e usuários superuser como ADMIN
    op.execute("UPDATE users SET role = 'ADMIN' WHERE is_superuser = TRUE")
    op.execute("UPDATE users SET role = 'COMMON' WHERE role IS NULL")
    
    # Tornar a coluna NOT NULL
    op.alter_column('users', 'role', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'role')
    op.execute("DROP TYPE userrole")
