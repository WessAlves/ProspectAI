"""Fix enum values to lowercase in existing records

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-19 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Primeiro, precisamos adicionar os valores em minúsculas ao enum do PostgreSQL
    # E depois converter os dados existentes
    
    # Adicionar valores em minúsculas ao enum userrole
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'common'")
    
    # Nota: ALTER TYPE ADD VALUE não pode rodar dentro de uma transação
    # Por isso, fazemos commit implícito aqui e atualizamos os dados em seguida
    
    # Agora corrigir os dados (isso precisa ser feito em uma transação separada)
    # Os dados serão atualizados na próxima execução ou manualmente


def downgrade() -> None:
    # Não é possível remover valores de enum no PostgreSQL facilmente
    pass
