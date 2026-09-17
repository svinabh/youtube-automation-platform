import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.video import VideoStatus
from app.models.audit import ApprovalAuditLog

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_qc.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_full_approval_workflow():
    # 1. Create a video
    response = client.post("/videos/", json={"title": "Test Video", "description": "A test video for QC"})
    assert response.status_code == 200
    video_id = response.json()["id"]
    assert response.json()["status"] == VideoStatus.DRAFT.value

    # 2. Cannot approve from DRAFT
    response = client.post(f"/videos/{video_id}/approve", json={"user_id": "reviewer1", "reason": "LGTM"})
    assert response.status_code == 400
    assert "Cannot approve video" in response.json()["detail"]

    # 3. Submit for approval
    response = client.post(f"/videos/{video_id}/submit-approval", json={"user_id": "creator1"})
    assert response.status_code == 200
    assert response.json()["status"] == VideoStatus.PENDING_APPROVAL.value

    # Check audit log
    db = TestingSessionLocal()
    logs = db.query(ApprovalAuditLog).filter(ApprovalAuditLog.video_id == video_id).all()
    assert len(logs) == 1
    assert logs[0].action == "SUBMITTED"
    assert logs[0].user_id == "creator1"
    db.close()

    # 4. Approve video
    response = client.post(f"/videos/{video_id}/approve", json={"user_id": "reviewer1", "reason": "LGTM"})
    assert response.status_code == 200
    assert response.json()["status"] == VideoStatus.APPROVED.value

    # Check audit log
    db = TestingSessionLocal()
    logs = db.query(ApprovalAuditLog).filter(ApprovalAuditLog.video_id == video_id).order_by(ApprovalAuditLog.id).all()
    assert len(logs) == 2
    assert logs[1].action == "APPROVED"
    assert logs[1].user_id == "reviewer1"
    assert logs[1].reason == "LGTM"
    db.close()

def test_rejection_workflow():
    # 1. Create a video
    response = client.post("/videos/", json={"title": "Bad Video", "description": "This should be rejected"})
    video_id = response.json()["id"]

    # 2. Submit for approval
    client.post(f"/videos/{video_id}/submit-approval", json={"user_id": "creator1"})

    # 3. Reject without reason should fail
    response = client.post(f"/videos/{video_id}/reject", json={"user_id": "reviewer1", "reason": ""})
    assert response.status_code == 400
    assert "reason is required" in response.json()["detail"]

    # 4. Reject video properly
    response = client.post(f"/videos/{video_id}/reject", json={"user_id": "reviewer1", "reason": "Violates policy"})
    assert response.status_code == 200
    assert response.json()["status"] == VideoStatus.REJECTED.value

    # 5. Resubmit from REJECTED should work
    response = client.post(f"/videos/{video_id}/submit-approval", json={"user_id": "creator1"})
    assert response.status_code == 200
    assert response.json()["status"] == VideoStatus.PENDING_APPROVAL.value

def test_idempotency():
    # Create video
    response = client.post("/videos/", json={"title": "Idempotency Test"})
    video_id = response.json()["id"]

    # Submit twice
    client.post(f"/videos/{video_id}/submit-approval", json={"user_id": "creator1"})
    response = client.post(f"/videos/{video_id}/submit-approval", json={"user_id": "creator1"})
    assert response.status_code == 200 # Should succeed
    assert response.json()["status"] == VideoStatus.PENDING_APPROVAL.value

    # Verify only 1 audit log
    db = TestingSessionLocal()
    logs = db.query(ApprovalAuditLog).filter(ApprovalAuditLog.video_id == video_id).all()
    assert len(logs) == 1
    db.close()

    # Approve twice
    client.post(f"/videos/{video_id}/approve", json={"user_id": "reviewer1"})
    response = client.post(f"/videos/{video_id}/approve", json={"user_id": "reviewer1"})
    assert response.status_code == 200

    # Verify only 2 audit logs (1 for submit, 1 for approve)
    db = TestingSessionLocal()
    logs = db.query(ApprovalAuditLog).filter(ApprovalAuditLog.video_id == video_id).all()
    assert len(logs) == 2
    db.close()

def test_not_found():
    response = client.post("/videos/999/approve", json={"user_id": "reviewer1"})
    assert response.status_code == 404
