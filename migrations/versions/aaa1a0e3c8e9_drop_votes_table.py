"""Drop votes table

Revision ID: aaa1a0e3c8e9
Revises: 993a881f073f
Create Date: 2025-08-15 22:44:58.481368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aaa1a0e3c8e9'
down_revision: Union[str, Sequence[str], None] = '993a881f073f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
