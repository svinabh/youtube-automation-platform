import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import get_db
from app.main import app
from app.models import AuditEvent,Base,Video,VideoState
from app.services import YouTubePublisher

@pytest.fixture
def db():
 engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
 Base.metadata.create_all(engine)
 session=sessionmaker(bind=engine)()
 try: yield session
 finally: session.close()

@pytest.fixture
def client(db):
 app.dependency_overrides[get_db]=lambda: db
 try: yield TestClient(app)
 finally: app.dependency_overrides.clear()

def approved_video(db):
 video=Video(
  topic="solar energy",title="Solar Energy Explained",description="",
  script="A safe verified script.",state=VideoState.APPROVED.value,
  artifact_path="/tmp/test.mp4",rights_cleared=True,policy_passed=True,
 )
 db.add(video);db.commit();db.refresh(video)
 return video

def test_health():
 assert TestClient(app).get("/health").json()["status"]=="ok"

def test_cors_allows_configured_origin():
 response=TestClient(app).get("/health",headers={"Origin":"http://localhost:3000"})
 assert response.headers["access-control-allow-origin"]=="http://localhost:3000"

def test_cors_rejects_non_whitelisted_origin():
 response=TestClient(app).get("/health",headers={"Origin":"http://evil.example"})
 assert "access-control-allow-origin" not in response.headers

@pytest.mark.asyncio
async def test_publish_simulation_never_marks_uploaded(client,db):
 video=approved_video(db)
 response=client.post(f"/api/videos/{video.id}/publish")
 assert response.status_code==200
 payload=response.json()
 assert payload["youtube"]["status"]=="SIMULATED"
 assert payload["video"]["state"]==VideoState.SIMULATED_UPLOAD.value
 assert payload["video"]["state"]!=VideoState.UPLOADED.value
 assert payload["video"]["simulated_upload"] is True
 event=db.query(AuditEvent).filter(AuditEvent.video_id==video.id,AuditEvent.event=="simulated_publish").one()
 assert "no YouTube upload occurred" in event.detail

@pytest.mark.asyncio
async def test_publish_marks_uploaded_only_for_real_published(monkeypatch,client,db):
 async def fake_upload(self,path,title,description,disclosure):
  return {"status":"PUBLISHED","video_id":"real123"}
 monkeypatch.setattr(YouTubePublisher,"upload",fake_upload)
 video=approved_video(db)
 response=client.post(f"/api/videos/{video.id}/publish")
 assert response.status_code==200
 payload=response.json()
 assert payload["youtube"]["status"]=="PUBLISHED"
 assert payload["video"]["state"]==VideoState.UPLOADED.value
 assert payload["video"]["simulated_upload"] is False
 event=db.query(AuditEvent).filter(AuditEvent.video_id==video.id,AuditEvent.event=="real_publish").one()
 assert "real YouTube publish completed" in event.detail
