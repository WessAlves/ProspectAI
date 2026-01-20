"""add user profile fields

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar tipo de pessoa
    op.execute("CREATE TYPE persontype AS ENUM ('individual', 'company')")
    
    # Perfil completo
    op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('person_type', sa.Enum('individual', 'company', name='persontype'), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    
    # Campos para Pessoa Física
    op.add_column('users', sa.Column('cpf', sa.String(14), nullable=True))
    op.add_column('users', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))
    
    # Campos para Pessoa Jurídica
    op.add_column('users', sa.Column('cnpj', sa.String(18), nullable=True))
    op.add_column('users', sa.Column('company_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('trade_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('state_registration', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('municipal_registration', sa.String(50), nullable=True))
    
    # Endereço
    op.add_column('users', sa.Column('address_street', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('address_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('address_complement', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_neighborhood', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_city', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_state', sa.String(2), nullable=True))
    op.add_column('users', sa.Column('address_zip_code', sa.String(10), nullable=True))
    
    # Dados de pagamento
    op.add_column('users', sa.Column('payment_method_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('card_last_four', sa.String(4), nullable=True))
    op.add_column('users', sa.Column('card_brand', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('card_exp_month', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('card_exp_year', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('billing_name', sa.String(255), nullable=True))
    
    # Índices únicos
    op.create_unique_constraint('uq_users_cpf', 'users', ['cpf'])
    op.create_unique_constraint('uq_users_cnpj', 'users', ['cnpj'])


def downgrade() -> None:
    # Remover índices únicos
    op.drop_constraint('uq_users_cnpj', 'users', type_='unique')
    op.drop_constraint('uq_users_cpf', 'users', type_='unique')
    
    # Remover colunas de pagamento
    op.drop_column('users', 'billing_name')
    op.drop_column('users', 'card_exp_year')
    op.drop_column('users', 'card_exp_month')
    op.drop_column('users', 'card_brand')
    op.drop_column('users', 'card_last_four')
    op.drop_column('users', 'payment_method_id')
    
    # Remover colunas de endereço
    op.drop_column('users', 'address_zip_code')
    op.drop_column('users', 'address_state')
    op.drop_column('users', 'address_city')
    op.drop_column('users', 'address_neighborhood')
    op.drop_column('users', 'address_complement')
    op.drop_column('users', 'address_number')
    op.drop_column('users', 'address_street')
    
    # Remover colunas de Pessoa Jurídica
    op.drop_column('users', 'municipal_registration')
    op.drop_column('users', 'state_registration')
    op.drop_column('users', 'trade_name')
    op.drop_column('users', 'company_name')
    op.drop_column('users', 'cnpj')
    
    # Remover colunas de Pessoa Física
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'birth_date')
    op.drop_column('users', 'cpf')
    
    # Remover colunas de perfil
    op.drop_column('users', 'phone')
    op.drop_column('users', 'person_type')
    op.drop_column('users', 'profile_completed')
    
    # Remover tipo enum
    op.execute("DROP TYPE persontype")
