"""Add google_maps to ProspectPlatform enum and rejected to ProspectStatus

Revision ID: f1g2h3i4j5k6
Revises: e5f6g7h8i9j0
Create Date: 2026-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1g2h3i4j5k6'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar 'google_maps' ao enum ProspectPlatform
    op.execute("ALTER TYPE prospectplatform ADD VALUE IF NOT EXISTS 'google_maps'")
    
    # Adicionar 'rejected' ao enum ProspectStatus
    op.execute("ALTER TYPE prospectstatus ADD VALUE IF NOT EXISTS 'rejected'")


def downgrade() -> None:
    # Nota: PostgreSQL não permite remover valores de enum facilmente
    # Esta operação não é reversível sem recriar a tabela
    pass
