"""add prospect contact fields

Revision ID: e5f6g7h8i9j0
Revises: c3d4e5f6g7h8
Create Date: 2026-01-19 12:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar novos campos de contato para leads manuais
    op.add_column('prospects', sa.Column('email', sa.String(255), nullable=True))
    op.add_column('prospects', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('prospects', sa.Column('company', sa.String(255), nullable=True))
    op.add_column('prospects', sa.Column('position', sa.String(255), nullable=True))
    
    # Tornar campaign_id nullable para leads sem campanha
    op.alter_column('prospects', 'campaign_id', nullable=True)
    
    # Atualizar enum de plataforma para incluir manual e import
    # Nota: Em PostgreSQL, enums precisam ser alterados manualmente
    op.execute("ALTER TYPE prospectplatform ADD VALUE IF NOT EXISTS 'manual'")
    op.execute("ALTER TYPE prospectplatform ADD VALUE IF NOT EXISTS 'import'")


def downgrade() -> None:
    op.drop_column('prospects', 'position')
    op.drop_column('prospects', 'company')
    op.drop_column('prospects', 'phone')
    op.drop_column('prospects', 'email')
    op.alter_column('prospects', 'campaign_id', nullable=False)
