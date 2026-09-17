from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """
    Test the /api/v1/health endpoint to ensure it returns HTTP 200
    and a deterministic JSON response.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "youtube-automation-platform"
