"""Add condition to racer_best_laps

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-01-30 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('racer_best_laps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('condition', sa.String(length=20), nullable=True, server_default='dry'))


def downgrade():
    with op.batch_alter_table('racer_best_laps', schema=None) as batch_op:
        batch_op.drop_column('condition')
