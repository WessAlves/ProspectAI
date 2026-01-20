"""add_prospecting_fields_to_campaign

Revision ID: d26048876920
Revises: bf9238ce8c91
Create Date: 2026-01-19 00:28:42.584839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd26048876920'
down_revision: Union[str, None] = 'bf9238ce8c91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar o tipo ENUM primeiro
    prospectingsource = postgresql.ENUM(
        'GOOGLE', 'GOOGLE_MAPS', 'INSTAGRAM', 'LINKEDIN', 'ALL',
        name='prospectingsource',
        create_type=True
    )
    prospectingsource.create(op.get_bind(), checkfirst=True)
    
    # Adicionar novas colunas
    op.add_column('campaigns', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('campaigns', sa.Column(
        'prospecting_source', 
        sa.Enum('GOOGLE', 'GOOGLE_MAPS', 'INSTAGRAM', 'LINKEDIN', 'ALL', name='prospectingsource'),
        nullable=True,  # Temporariamente nullable para dados existentes
        server_default='GOOGLE_MAPS'
    ))
    op.add_column('campaigns', sa.Column('niche', sa.String(length=255), nullable=True))
    op.add_column('campaigns', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('campaigns', sa.Column('hashtags', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('campaigns', sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True))
    
    # Atualizar registros existentes e remover nullable
    op.execute("UPDATE campaigns SET prospecting_source = 'GOOGLE_MAPS' WHERE prospecting_source IS NULL")
    op.alter_column('campaigns', 'prospecting_source', nullable=False)


def downgrade() -> None:
    op.drop_column('campaigns', 'keywords')
    op.drop_column('campaigns', 'hashtags')
    op.drop_column('campaigns', 'location')
    op.drop_column('campaigns', 'niche')
    op.drop_column('campaigns', 'prospecting_source')
    op.drop_column('campaigns', 'description')
    
    # Remover o tipo ENUM
    sa.Enum(name='prospectingsource').drop(op.get_bind(), checkfirst=True)
