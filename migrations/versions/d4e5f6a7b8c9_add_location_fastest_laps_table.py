"""Add location_fastest_laps table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-30 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('location_fastest_laps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('condition', sa.String(length=20), nullable=False),
        sa.Column('racer_id', sa.Integer(), nullable=False),
        sa.Column('best_lap', sa.String(length=20), nullable=False),
        sa.Column('best_lap_seconds', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['racer_id'], ['racers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_location_fastest_laps_location_id', 'location_fastest_laps', ['location_id'], unique=False)


def downgrade():
    op.drop_index('ix_location_fastest_laps_location_id', table_name='location_fastest_laps')
    op.drop_table('location_fastest_laps')
