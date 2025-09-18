"""add_currency_rate_model_and_convert_price_to_decimal

Revision ID: d179d9b4c995
Revises: 13088b0b391d
Create Date: 2025-09-18 11:38:25.391917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd179d9b4c995'
down_revision: Union[str, Sequence[str], None] = '13088b0b391d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create currency_rates table if it doesn't exist
    connection = op.get_bind()
    
    # Check if currency_rates table already exists
    result = connection.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='currency_rates'"
    ))
    currency_table_exists = result.fetchone() is not None
    
    if not currency_table_exists:
        op.create_table('currency_rates',
            sa.Column('code', sa.String(length=3), nullable=False),
            sa.Column('rate_to_usd', sa.Numeric(precision=18, scale=6), nullable=False),
            sa.Column('fetched_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('code')
        )
    
    # Check if products table needs to be migrated (check if price is still FLOAT)
    result = connection.execute(sa.text("PRAGMA table_info(products)"))
    columns = result.fetchall()
    price_column_type = None
    for column in columns:
        if column[1] == 'price':  # column[1] is the column name
            price_column_type = column[2]  # column[2] is the type
            break
    
    # Only migrate if price is still FLOAT/REAL
    if price_column_type and price_column_type.upper() in ('FLOAT', 'REAL'):
        # SQLite doesn't support direct ALTER COLUMN type changes, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy data from old table to new table
        # 3. Drop old table and rename new table
        
        # Create new products table with Decimal price column
        op.create_table('products_new',
            sa.Column('id', sa.Integer(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=False),
            sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('image_data', sa.LargeBinary(), nullable=True),
            sa.Column('image_mime_type', sa.String(), nullable=True),
            sa.Column('image_filename', sa.String(), nullable=True),
            sa.Column('is_saved', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_products_new_category_id'), 'products_new', ['category_id'], unique=False)
        
        # Copy data from old products table to new table, converting price to decimal
        connection.execute(sa.text("""
            INSERT INTO products_new (id, title, description, price, image_data, image_mime_type, 
                                    image_filename, is_saved, created_at, updated_at, category_id)
            SELECT id, title, description, CAST(price AS DECIMAL(10,2)), image_data, image_mime_type,
                   image_filename, is_saved, created_at, updated_at, category_id
            FROM products
        """))
        
        # Drop old products table and rename new table
        op.drop_table('products')
        op.rename_table('products_new', 'products')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop currency_rates table
    op.drop_table('currency_rates')
    
    # Create products table with FLOAT price column (original schema)
    op.create_table('products_old',
        sa.Column('id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('image_data', sa.LargeBinary(), nullable=True),
        sa.Column('image_mime_type', sa.String(), nullable=True),
        sa.Column('image_filename', sa.String(), nullable=True),
        sa.Column('is_saved', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_old_category_id'), 'products_old', ['category_id'], unique=False)
    
    # Copy data from new products table to old table, converting price back to float
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO products_old (id, title, description, price, image_data, image_mime_type, 
                                image_filename, is_saved, created_at, updated_at, category_id)
        SELECT id, title, description, CAST(price AS REAL), image_data, image_mime_type,
               image_filename, is_saved, created_at, updated_at, category_id
        FROM products
    """))
    
    # Drop new products table and rename old table
    op.drop_table('products')
    op.rename_table('products_old', 'products')
