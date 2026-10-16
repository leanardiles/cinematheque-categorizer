"""add titles.note

Revision ID: b4e8f1a2c6d3
Revises: 9f2b6d4e8a31
Create Date: 2026-10-16 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e8f1a2c6d3'
down_revision: Union[str, Sequence[str], None] = '9f2b6d4e8a31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('titles', sa.Column('note', sa.String(length=120), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('titles', 'note')
