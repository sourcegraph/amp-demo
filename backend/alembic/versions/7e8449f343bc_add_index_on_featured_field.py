"""add index on featured field

Revision ID: 7e8449f343bc
Revises: 13088b0b391d
Create Date: 2025-09-18 14:30:59.113944

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7e8449f343bc'
down_revision: Union[str, Sequence[str], None] = '13088b0b391d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Set default values for existing featured column
    op.execute('UPDATE products SET featured = 0 WHERE featured IS NULL')
    # Add index on featured column
    op.create_index(op.f('ix_products_featured'), 'products', ['featured'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_products_featured'), table_name='products')
