"""drop asnwer votes table

Revision ID: 76d7be5856c2
Revises: 10088a3af848
Create Date: 2025-08-15 22:31:32.952964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76d7be5856c2'
down_revision: Union[str, Sequence[str], None] = '10088a3af848'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
