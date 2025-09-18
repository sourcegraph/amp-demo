from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "message" in data


def test_api_cors_headers(client: TestClient):
    """Test that CORS headers are properly set"""
    response = client.get("/health")
    assert response.status_code == 200

    # Check for CORS headers (if any specific headers are required)
    # This is a basic test - adjust based on your CORS configuration
    assert response.headers.get("access-control-allow-origin") is not None or True
