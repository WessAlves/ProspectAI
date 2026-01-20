"""Update plan_tier enum to new values

Revision ID: a1b2c3d4e5f6
Revises: c245705e05b6
Create Date: 2026-01-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c245705e05b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar novos valores ao enum existente
    # No PostgreSQL, precisamos alterar o tipo enum
    
    # 1. Adicionar os novos valores 'starter' e 'scale' ao enum
    op.execute("ALTER TYPE plantier ADD VALUE IF NOT EXISTS 'starter'")
    op.execute("ALTER TYPE plantier ADD VALUE IF NOT EXISTS 'scale'")
    
    # Nota: Se houvesse registros com 'enterprise', precisaríamos migrar
    # Mas como o enum original só tem free, pro, enterprise e o banco
    # pode não ter enterprise ainda, não fazemos update


def downgrade() -> None:
    # Reverter 'scale' para 'pro' (se necessário)
    op.execute("UPDATE users SET plan_tier = 'pro' WHERE plan_tier = 'scale'")
    op.execute("UPDATE users SET plan_tier = 'free' WHERE plan_tier = 'starter'")
    
    # Nota: Não é possível remover valores de um enum no PostgreSQL facilmente
    # A solução completa seria recriar o tipo enum, mas isso é complexo
