"""drop votes table

Revision ID: 10088a3af848
Revises: 23b2cd1ea05f
Create Date: 2025-08-15 22:27:29.449170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10088a3af848'
down_revision: Union[str, Sequence[str], None] = '23b2cd1ea05f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
