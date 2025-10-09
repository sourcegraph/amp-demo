from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_validation_error_returns_rfc7807_response():
    response = client.post("/categories", json={"invalid": "data"})
    
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/problem+json"
    
    body = response.json()
    assert body["type"].startswith("https://docs.lineasupply.com/errors/")
    assert body["title"] == "Validation Error"
    assert body["status"] == 400
    assert body["code"] == "VALIDATION.INVALID_FIELDS"
    assert "request_id" in body
    assert "trace_id" in body
    assert "details" in body
    assert "fields" in body["details"]


def test_not_found_error_returns_rfc7807_response():
    response = client.get("/products/999999")
    
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/problem+json"
    
    body = response.json()
    assert body["status"] == 404
    assert body["code"] == "RESOURCE.NOT_FOUND"
    assert "request_id" in body
    assert "trace_id" in body


def test_duplicate_category_returns_409_conflict():
    client.post("/categories", json={"name": "Test Category"})
    
    response = client.post("/categories", json={"name": "Test Category"})
    
    assert response.status_code == 409
    assert response.headers["Content-Type"] == "application/problem+json"
    
    body = response.json()
    assert body["status"] == 409
    assert body["code"] == "CONFLICT.DUPLICATE"
    assert "request_id" in body


def test_trace_headers_propagation():
    incoming_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    
    response = client.get("/health", headers={"traceparent": incoming_traceparent})
    
    assert "X-Request-ID" in response.headers
    assert "traceparent" in response.headers
    
    outgoing_traceparent = response.headers["traceparent"]
    parts = outgoing_traceparent.split("-")
    assert len(parts) == 4
    assert parts[0] == "00"
    assert len(parts[1]) == 32
    assert len(parts[2]) == 16
    assert parts[3] == "01"


def test_trace_headers_generated_when_missing():
    response = client.get("/health")
    
    assert "X-Request-ID" in response.headers
    assert "traceparent" in response.headers
    
    request_id = response.headers["X-Request-ID"]
    traceparent = response.headers["traceparent"]
    
    assert len(request_id) == 32
    parts = traceparent.split("-")
    assert len(parts) == 4
    assert parts[1] == request_id


def test_cors_headers_expose_trace_context():
    response = client.get("/health")
    
    assert "Access-Control-Expose-Headers" in response.headers
    exposed = response.headers["Access-Control-Expose-Headers"]
    assert "X-Request-ID" in exposed
    assert "traceparent" in exposed
