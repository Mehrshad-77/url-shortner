"""require password and lowercase usernames

Revision ID: e5b1a7c3d9f2
Revises: c0fe90112cab
Create Date: 2026-10-10 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5b1a7c3d9f2"
down_revision: Union[str, Sequence[str], None] = "c0fe90112cab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fails (and rolls back) if two usernames differ only by case.
    op.execute("UPDATE users SET username = lower(username)")
    # Fails (and rolls back) if any user has no password.
    op.alter_column("users", "hashed_password", existing_type=sa.Text(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "hashed_password", existing_type=sa.Text(), nullable=True)
