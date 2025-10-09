import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from tests.factories import create_test_category, create_test_product

def test_get_categories(client: TestClient):
    """Test getting all categories"""
    response = client.get("/categories")
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) > 0
    
    # Check category structure
    category = categories[0]
    required_fields = ["id", "name", "created_at", "updated_at"]
    for field in required_fields:
        assert field in category

def test_get_single_category(client: TestClient):
    """Test getting a single category by ID"""
    # Get all categories first
    categories_response = client.get("/categories")
    categories = categories_response.json()
    assert len(categories) > 0
    
    category_id = categories[0]["id"]
    
    # Get single category
    response = client.get(f"/categories/{category_id}")
    assert response.status_code == 200
    category = response.json()
    assert category["id"] == category_id
    assert "products" in category  # Should include products

def test_get_nonexistent_category(client: TestClient):
    """Test getting a category that doesn't exist"""
    response = client.get("/categories/99999")
    assert response.status_code == 404

def test_create_category(client: TestClient):
    """Test creating a new category"""
    category_data = {
        "name": "Test Category"
    }
    
    response = client.post("/categories", json=category_data)
    assert response.status_code == 200
    created_category = response.json()
    assert created_category["name"] == category_data["name"]
    assert "id" in created_category
    assert "created_at" in created_category

def test_create_duplicate_category(client: TestClient):
    """Test creating a category with duplicate name"""
    # Get existing category
    categories_response = client.get("/categories")
    existing_category = categories_response.json()[0]
    
    category_data = {
        "name": existing_category["name"]  # Duplicate name
    }
    
    response = client.post("/categories", json=category_data)
    # This should fail due to unique constraint
    assert response.status_code == 409

def test_category_with_products(client: TestClient):
    """Test that category endpoint includes its products"""
    # Get categories
    categories_response = client.get("/categories")
    categories = categories_response.json()
    
    # Find a category that should have products
    for category in categories:
        category_response = client.get(f"/categories/{category['id']}")
        category_detail = category_response.json()
        
        if len(category_detail.get("products", [])) > 0:
            # Verify product structure in category response
            product = category_detail["products"][0]
            required_fields = ["id", "title", "description", "price"]
            for field in required_fields:
                assert field in product
            break
    else:
        pytest.skip("No categories with products found for testing")


def test_create_category_duplicate_name(client: TestClient):
    """Test creating category with duplicate name returns 400"""
    category_data = {"name": "Electronics"}
    
    # First creation should succeed
    response1 = client.post("/categories", json=category_data)
    assert response1.status_code == 200
    
    # Duplicate should fail
    response2 = client.post("/categories", json=category_data)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"].lower()


def test_create_category_empty_name(client: TestClient):
    """Test creating category with empty/whitespace name fails"""
    test_cases = [
        {"name": ""},
        {"name": "   "},
        {"name": None}
    ]
    
    for category_data in test_cases:
        response = client.post("/categories", json=category_data)
        assert response.status_code == 400  # Validation error


def test_get_category_with_products_includes_image_urls(client: TestClient, session: Session):
    """Test that category endpoint includes image URLs for products"""
    category = create_test_category(session)
    product = create_test_product(session, category.id, with_image=True)
    
    response = client.get(f"/categories/{category.id}")
    assert response.status_code == 200
    
    category_data = response.json()
    assert len(category_data["products"]) == 1
    assert category_data["products"][0]["image_url"] == f"/products/{product.id}/image"
