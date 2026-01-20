"""Add lead packages table

Revision ID: g2h3i4j5k6l7
Revises: f1g2h3i4j5k6
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g2h3i4j5k6l7'
down_revision = 'f1g2h3i4j5k6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create package_type enum
    package_type_enum = postgresql.ENUM(
        'leads_500', 'leads_1000', 'leads_1500',
        name='packagetype',
        create_type=False
    )
    package_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create payment_status enum
    payment_status_enum = postgresql.ENUM(
        'pending', 'paid', 'failed', 'refunded',
        name='paymentstatus',
        create_type=False
    )
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create lead_packages table with UUID for user_id
    op.create_table(
        'lead_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('package_type', postgresql.ENUM('leads_500', 'leads_1000', 'leads_1500', name='packagetype', create_type=False), nullable=False),
        sa.Column('leads_purchased', sa.Integer(), nullable=False),
        sa.Column('leads_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('price_paid', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_status', postgresql.ENUM('pending', 'paid', 'failed', 'refunded', name='paymentstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('purchase_month', sa.String(length=7), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_lead_packages_user_id', 'lead_packages', ['user_id'], unique=False)
    op.create_index('ix_lead_packages_user_month', 'lead_packages', ['user_id', 'purchase_month'], unique=False)
    op.create_index('ix_lead_packages_payment_status', 'lead_packages', ['payment_status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lead_packages_payment_status', table_name='lead_packages')
    op.drop_index('ix_lead_packages_user_month', table_name='lead_packages')
    op.drop_index('ix_lead_packages_user_id', table_name='lead_packages')
    
    # Drop table
    op.drop_table('lead_packages')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS packagetype')
