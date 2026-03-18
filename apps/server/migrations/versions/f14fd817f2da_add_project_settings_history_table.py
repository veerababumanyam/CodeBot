"""add_project_settings_history_table

Revision ID: f14fd817f2da
Revises: ea394e8a966d
Create Date: 2026-03-18 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f14fd817f2da'
down_revision: Union[str, Sequence[str], None] = 'ea394e8a966d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create project_settings_history table."""
    op.create_table(
        'project_settings_history',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('settings_snapshot', sa.JSON(), nullable=False),
        sa.Column('changed_by', sa.Uuid(), nullable=True),
        sa.Column('change_source', sa.String(length=50), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_project_settings_history_project_id'),
        'project_settings_history',
        ['project_id'],
        unique=False,
    )


def downgrade() -> None:
    """Drop project_settings_history table."""
    op.drop_index(
        op.f('ix_project_settings_history_project_id'),
        table_name='project_settings_history',
    )
    op.drop_table('project_settings_history')
