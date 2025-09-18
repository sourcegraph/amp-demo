"""Integration tests for FX currency conversion in API endpoints."""
from fastapi.testclient import TestClient
import uuid


def test_get_products_with_currency_conversion(client: TestClient):
    """Test GET /products with currency parameter."""
    # First create a category and product
    category_name = f"Test Category {uuid.uuid4().hex[:8]}"
    response = client.post("/categories", json={"name": category_name})
    assert response.status_code == 200
    category_id = response.json()["id"]
    
    # Create a product with price in USD
    product_data = {
        "title": "Test Product", 
        "description": "Test Description",
        "price": 100.0,
        "category_id": category_id
    }
    response = client.post("/products", json=product_data)
    assert response.status_code == 200
    
    # Test without currency parameter (should return original price)
    response = client.get(f"/products?category_id={category_id}")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["price"] == 100.0
    assert products[0]["currency"] is None
    assert products[0]["original_price"] is None
    
    # Test with USD currency (should return USD price with currency field)
    response = client.get(f"/products?category_id={category_id}&currency=USD")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["price"] == 100.0
    assert products[0]["currency"] == "USD"
    assert products[0]["original_price"] is None
    
    # Test with EUR currency (should return converted price)
    response = client.get(f"/products?category_id={category_id}&currency=EUR")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    # With mock rate of 0.85 EUR/USD, 100 USD should be 85 EUR
    assert products[0]["price"] == 85.0
    assert products[0]["currency"] == "EUR"
    assert products[0]["original_price"] == 100.0


def test_get_single_product_with_currency_conversion(client: TestClient):
    """Test GET /products/{id} with currency parameter."""
    # Create category and product
    category_name = f"Test Category {uuid.uuid4().hex[:8]}"
    response = client.post("/categories", json={"name": category_name})
    category_id = response.json()["id"]
    
    product_data = {
        "title": "Test Product", 
        "description": "Test Description",
        "price": 50.0,
        "category_id": category_id
    }
    response = client.post("/products", json=product_data)
    product_id = response.json()["id"]
    
    # Test with GBP currency
    response = client.get(f"/products/{product_id}?currency=GBP")
    assert response.status_code == 200
    product = response.json()
    # With mock rate of 0.79 GBP/USD, 50 USD should be ~39.5 GBP
    assert product["price"] == 39.5
    assert product["currency"] == "GBP"
    assert product["original_price"] == 50.0


def test_get_category_with_currency_conversion(client: TestClient):
    """Test GET /categories/{id} with currency parameter for products."""
    # Create category and product
    category_name = f"Electronics {uuid.uuid4().hex[:8]}"
    response = client.post("/categories", json={"name": category_name})
    category_id = response.json()["id"]
    
    product_data = {
        "title": "Laptop", 
        "description": "Gaming Laptop",
        "price": 1000.0,
        "category_id": category_id
    }
    response = client.post("/products", json=product_data)
    
    # Test category endpoint with currency conversion
    response = client.get(f"/categories/{category_id}?currency=JPY")
    assert response.status_code == 200
    category = response.json()
    
    assert len(category["products"]) == 1
    product = category["products"][0]
    # With mock rate of 110.0 JPY/USD, 1000 USD should be 110000 JPY
    assert product["price"] == 110000.0
    assert product["currency"] == "JPY"
    assert product["original_price"] == 1000.0


def test_invalid_currency_parameter(client: TestClient):
    """Test that invalid currency codes are rejected."""
    # Create category and product first
    category_name = f"Test Category {uuid.uuid4().hex[:8]}"
    response = client.post("/categories", json={"name": category_name})
    category_id = response.json()["id"]
    
    product_data = {
        "title": "Test Product", 
        "description": "Test Description",
        "price": 100.0,
        "category_id": category_id
    }
    response = client.post("/products", json=product_data)
    
    # Test with invalid currency code
    response = client.get("/products?currency=INVALID")
    assert response.status_code == 422  # Validation error


def test_fx_status_endpoint(client: TestClient):
    """Test the FX status endpoint."""
    response = client.get("/fx/status")
    assert response.status_code == 200
    data = response.json()
    
    # Should have rates available (mock rates)
    assert "status" in data
    assert data["status"] in ["fresh", "stale", "no_rates"]
    
    if data["status"] != "no_rates":
        assert "base" in data
        assert "timestamp" in data
        assert "available_currencies" in data
        assert "rates_count" in data
        assert data["base"] == "USD"
        # Should include the mock currencies
        expected_currencies = ["USD", "GBP", "EUR", "AUD", "MXN", "JPY"]
        for currency in expected_currencies:
            assert currency in data["available_currencies"]


def test_currency_conversion_edge_cases(client: TestClient):
    """Test edge cases for currency conversion."""
    # Create category and product
    category_name = f"Test Category {uuid.uuid4().hex[:8]}"
    response = client.post("/categories", json={"name": category_name})
    category_id = response.json()["id"]
    
    product_data = {
        "title": "Test Product", 
        "description": "Test Description",
        "price": 99.99,  # Price with decimal places
        "category_id": category_id
    }
    response = client.post("/products", json=product_data)
    
    # Test conversion maintains proper decimal precision
    response = client.get("/products?currency=EUR")
    assert response.status_code == 200
    products = response.json()
    
    # Should be rounded to 2 decimal places
    converted_price = products[0]["price"]
    assert round(converted_price, 2) == converted_price
