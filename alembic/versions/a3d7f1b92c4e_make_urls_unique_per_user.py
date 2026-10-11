"""make urls unique per user

Revision ID: a3d7f1b92c4e
Revises: e5b1a7c3d9f2
Create Date: 2026-10-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3d7f1b92c4e'
down_revision: Union[str, Sequence[str], None] = 'e5b1a7c3d9f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The old rule (one row per URL, across all users) was stricter than the new
    # one, so existing data always satisfies the new index.
    op.drop_constraint('urls_original_url_key', 'urls', type_='unique')
    op.create_index(
        'uq_urls_user_id_original_url',
        'urls',
        ['user_id', 'original_url'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Fails if two users have saved the same URL since the upgrade.
    op.drop_index('uq_urls_user_id_original_url', table_name='urls')
    op.create_unique_constraint('urls_original_url_key', 'urls', ['original_url'])
