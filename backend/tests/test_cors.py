from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_cors_allowed_origin():
    """
    Test that an allowed origin successfully receives the appropriate CORS headers.
    """
    # Assuming http://localhost:3000 is allowed
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_cors_disallowed_origin():
    """
    Test that a disallowed origin does not receive the access-control-allow-origin header.
    """
    headers = {
        "Origin": "http://evil-origin.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
