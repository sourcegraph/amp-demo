from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .fx import CurrencyCode

class CurrencyRateBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, description="Currency code like EUR, GBP")
    rate_to_usd: Decimal = Field(..., gt=0, decimal_places=6, description="Exchange rate to USD")
    
class CurrencyRateCreate(CurrencyRateBase):
    pass

class CurrencyRateRead(CurrencyRateBase):
    fetched_at: datetime

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1)

    @field_validator('name')
    def name_must_not_be_empty_or_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ProductBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    is_saved: bool = False

    @field_validator('title', 'description')
    def strings_must_not_be_empty_or_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

class ProductCreate(ProductBase):
    category_id: int

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, decimal_places=2)
    is_saved: Optional[bool] = None
    category_id: Optional[int] = None

class ProductRead(BaseModel):
    id: int
    title: str
    description: str
    price: float  # Always returned as float for JSON compatibility
    is_saved: bool
    category_id: int
    image_url: Optional[str] = None  # Generated URL for frontend
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryRead] = None
    # Currency conversion fields
    currency: Optional[CurrencyCode] = None  # Currency of the returned price
    original_price: Optional[float] = None  # Original price in USD

class ProductReadWithCategory(ProductRead):
    category: CategoryRead

class CategoryReadWithProducts(CategoryRead):
    products: List[ProductRead] = []
