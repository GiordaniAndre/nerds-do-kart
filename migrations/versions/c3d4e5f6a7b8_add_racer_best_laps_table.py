"""Add racer_best_laps table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-30 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('racer_best_laps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('racer_id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('best_lap', sa.String(length=20), nullable=False),
        sa.Column('best_lap_seconds', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['racer_id'], ['racers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_racer_best_laps_racer_id', 'racer_best_laps', ['racer_id'], unique=False)
    op.create_index('ix_racer_best_laps_location_id', 'racer_best_laps', ['location_id'], unique=False)


def downgrade():
    op.drop_index('ix_racer_best_laps_location_id', table_name='racer_best_laps')
    op.drop_index('ix_racer_best_laps_racer_id', table_name='racer_best_laps')
    op.drop_table('racer_best_laps')
