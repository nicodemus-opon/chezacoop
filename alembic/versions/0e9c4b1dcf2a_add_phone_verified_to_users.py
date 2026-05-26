"""add phone_verified to users

Revision ID: 0e9c4b1dcf2a
Revises: fe109fd69efb
Create Date: 2026-05-26 12:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e9c4b1dcf2a'
down_revision: Union[str, Sequence[str], None] = 'fe109fd69efb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('users', 'phone_verified', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'phone_verified')
