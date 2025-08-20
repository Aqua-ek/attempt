"""fix unique constraint name for answer_votes

Revision ID: a2c91e52c251
Revises: 888bb656233d
Create Date: 2025-08-15 21:53:47.456308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2c91e52c251'
down_revision: Union[str, Sequence[str], None] = '888bb656233d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
