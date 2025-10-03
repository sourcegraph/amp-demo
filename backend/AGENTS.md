# Backend Agent Guide

## Overview
**Purpose:** FastAPI backend for e-commerce demo with strict TDD practices  
**Stack:** Python 3.13+, FastAPI, SQLModel, SQLite, Alembic, pytest  
**Architecture:** Feature-based structure with dependency injection via FastAPI Depends()

## Essential Commands

**Development:**
- `uv run python main.py` - Start development server (localhost:8001)
- `uv run fastapi dev main.py` - Start with hot-reload
- `uv sync` - Install/update dependencies

**Database:**
- `uv run alembic revision --autogenerate -m "message"` - Create migration
- `uv run alembic upgrade head` - Apply migrations
- `uv run alembic downgrade -1` - Rollback one migration
- `uv run python -m app.seed` - Seed database with sample data

**Testing:**
- `uv run pytest` - Run all tests
- `uv run pytest tests/test_products.py::test_create_product` - Run specific test
- `uv run pytest --cov=app` - Run tests with coverage
- `uv run pytest -v` - Verbose test output

**Quality Checks:**
- `uv run ruff check` - Lint code
- `uv run ruff format` - Format code
- `uv run mypy app/` - Type checking

## Testing Process


### Backend Testing Patterns

**API Testing Example:**
```python
def test_create_product_returns_created_product():
    """Test that POST /products creates and returns product"""
    product_data = get_mock_product_data({
        "name": "Gaming Laptop",
        "price": 999.99,
        "category": "electronics"
    })
    
    response = client.post("/products", json=product_data)
    
    assert response.status_code == 201
    created_product = response.json()
    assert created_product["name"] == "Gaming Laptop"
    assert created_product["id"] is not None
```

**Database Testing with Fixtures:**
```python
@pytest.fixture
def db_session():
    """Provide clean database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_product_repository_creates_product(db_session):
    """Test ProductRepository.create() persists to database"""
    repo = ProductRepository(db_session)
    product_data = get_mock_product_data()
    
    created_product = repo.create(product_data)
    
    assert created_product.id is not None
    db_product = db_session.get(Product, created_product.id)
    assert db_product is not None
```

## Code Style & Architecture

### Type Safety Requirements
- **Type hints:** Required for ALL functions, methods, and variables
- **SQLModel:** For database models and Pydantic validation
- **Strict mypy:** No `Any`, `type: ignore` requires justification

```python
from typing import Optional
from sqlmodel import SQLModel, Field

class ProductBase(SQLModel):
    name: str = Field(max_length=100)
    price: float = Field(gt=0)
    category: str
    description: Optional[str] = None
    in_stock: bool = True

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
```

### FastAPI Patterns

**Dependency Injection:**
```python
from fastapi import Depends
from sqlmodel import Session

def get_session() -> Session:
    with engine.begin() as session:
        yield session

@app.post("/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session)
) -> ProductResponse:
    # implementation
```

**Error Handling:**
```python
from fastapi import HTTPException
from typing import Union

def get_product_or_404(product_id: int, session: Session) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=404, 
            detail=f"Product with id {product_id} not found"
        )
    return product
```

### Test Data Factories

Always use factory functions with overrides:

```python
def get_mock_product_data(overrides: dict = None) -> dict:
    base = {
        "name": "Test Product",
        "price": 29.99,
        "category": "electronics",
        "description": "A test product",
        "in_stock": True
    }
    return base | (overrides or {})

def get_mock_product(overrides: dict = None) -> Product:
    data = get_mock_product_data(overrides)
    return Product(**data)
```

## Directory Structure

```
backend/
├── app/
│   ├── currency.py       # FX rates service, models, schemas
│   ├── models.py         # SQLModel database models (Product, Category, DeliveryOption, FxRates)
│   ├── schemas.py        # Pydantic request/response models
│   ├── crud.py           # Database operations
│   ├── db.py             # Database connection setup
│   ├── main.py           # FastAPI routes and app entry point
│   └── seed.py           # Database seeding script
├── tests/
│   ├── api/
│   │   ├── test_products.py      # Product API tests
│   │   ├── test_currency.py      # Currency/FX rates tests
│   │   ├── test_categories.py    # Category API tests
│   │   ├── test_delivery_options.py # Delivery options tests
│   │   └── test_images.py        # Image handling tests
│   ├── factories.py      # Test data factories
│   └── conftest.py       # Pytest fixtures
├── alembic/
│   └── versions/         # Database migrations
└── main.py               # FastAPI application entry point
```

## Database Guidelines

### Migration Workflow
1. Modify SQLModel models
2. Generate migration: `uv run alembic revision --autogenerate -m "add_product_table"`
3. Review generated migration file
4. Apply: `uv run alembic upgrade head`

### Model Relationships
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    email: str = Field(unique=True)
    
    orders: list["Order"] = Relationship(back_populates="user")

class Order(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    
    user: User = Relationship(back_populates="orders")
```

## API Design Standards

### RESTful Conventions
- `GET /products` - List products
- `POST /products` - Create product
- `GET /products/{id}` - Get specific product
- `PUT /products/{id}` - Update product (full)
- `PATCH /products/{id}` - Partial update
- `DELETE /products/{id}` - Delete product
- `GET /fx/rates` - Get currency exchange rates

### Currency/FX Rates
- **Endpoint:** `GET /fx/rates`
- **Base Currency:** USD (all prices stored in USD)
- **Supported Currencies:** USD, GBP, EUR, AUD, MXN, JPY
- **Caching:** 6-hour TTL with 3-tier caching (memory → DB → fallback)
- **Provider:** frankfurter.app (free, no auth required)
- **Response:** Includes rates, fetched_at, ttl_seconds, stale flag
- **Graceful Degradation:** Serves stale rates when provider unavailable

### Response Format
```python
# Success responses
{"data": {...}, "message": "Product created successfully"}

# Error responses  
{"error": "Product not found", "code": "PRODUCT_NOT_FOUND"}

# List responses with pagination
{
    "data": [...],
    "pagination": {
        "page": 1,
        "size": 20,
        "total": 100,
        "pages": 5
    }
}
```

## Testing Strategy

### Test Categories
- **API Tests:** Test FastAPI endpoints through TestClient
- **Service Tests:** Test business logic in isolation
- **Repository Tests:** Test database operations
- **Integration Tests:** Test full request/response cycle

### Coverage Requirements
- 100% coverage for all business logic
- Every API endpoint must have tests
- Database operations must be tested
- Error cases must be covered

### Mock External Dependencies
```python
from unittest.mock import Mock
import pytest

@pytest.fixture
def mock_email_service():
    return Mock()

def test_order_creation_sends_confirmation_email(mock_email_service):
    # Test that order creation triggers email
    pass
```

## Security Practices

- **Input Validation:** All inputs validated with Pydantic models
- **SQL Injection Prevention:** Use SQLModel, never raw SQL
- **Authentication:** JWT tokens via Authorization header
- **Environment Variables:** All secrets in `.env`, never committed
- **CORS:** Configure properly for frontend origin

## Performance Considerations

- **Database Queries:** Use select/joinload for relationships
- **Pagination:** Always paginate list endpoints
- **Caching:** Consider Redis for frequently accessed data
- **Async Operations:** Use async/await for I/O operations

