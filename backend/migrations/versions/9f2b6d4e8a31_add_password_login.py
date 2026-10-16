"""add password login: users.password_hash, login_failures, login_locked_until

Revision ID: 9f2b6d4e8a31
Revises: 7c3e1a9b5d20
Create Date: 2026-10-16 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f2b6d4e8a31'
down_revision: Union[str, Sequence[str], None] = '7c3e1a9b5d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_hash', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('login_failures', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('login_locked_until', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'login_locked_until')
    op.drop_column('users', 'login_failures')
    op.drop_column('users', 'password_hash')
