from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import LargeBinary, Column
from typing import Optional, List
from datetime import datetime


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    products: List["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int = Field(primary_key=True)  # Keep existing JSON IDs
    title: str
    description: str
    price: float

    # BLOB storage for images with explicit LargeBinary column
    image_data: Optional[bytes] = Field(
        default=None, sa_column=Column("image_data", LargeBinary)
    )
    image_mime_type: Optional[str] = Field(default=None)  # e.g., "image/jpeg"
    image_filename: Optional[str] = Field(default=None)  # Original filename
    is_saved: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    category_id: int = Field(foreign_key="categories.id", index=True)
    category: Optional[Category] = Relationship(back_populates="products")
