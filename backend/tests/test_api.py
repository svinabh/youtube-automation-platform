from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import AuditEvent,Base,Video,VideoState
from app.services import YouTubePublisher

def make_db():
 engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
 Base.metadata.create_all(engine)
 return sessionmaker(bind=engine)()

def override_db(db):
 def _override():
  try: yield db
  finally: pass
 return _override

def make_approved_video(db):
 video=Video(topic="solar energy",title="Solar Energy Explained",description="",script="A verified script.",state=VideoState.APPROVED.value,artifact_path="/tmp/artifact.mp4",rights_cleared=True,policy_passed=True)
 db.add(video);db.commit();db.refresh(video)
 return video

def make_brief_video(db):
 video=Video(topic="solar energy",title="Solar Energy Explained",description="",script="A verified script.",brief='{"scenes":[],"target_duration_seconds":30,"aspect_ratio":"9:16","voice_and_pacing_notes":"calm"}',state=VideoState.BRIEF_READY.value,rights_cleared=True)
 db.add(video);db.commit();db.refresh(video)
 return video

def test_health():
 assert TestClient(app).get("/health").json()["status"]=="ok"

def test_publish_disabled_never_marks_uploaded_and_records_simulation():
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 try:
  video=make_approved_video(db);response=TestClient(app).post(f"/api/videos/{video.id}/publish")
  assert response.status_code==200
  db.refresh(video)
  assert video.state==VideoState.SIMULATED_UPLOAD.value
  assert video.state!=VideoState.UPLOADED.value
  assert video.simulated_upload is True
  event=db.query(AuditEvent).filter_by(video_id=video.id,event="simulated_publish").one()
  assert "no real YouTube upload occurred" in event.detail
 finally:
  app.dependency_overrides.clear();db.close()

def test_real_published_status_is_required_for_uploaded_state(monkeypatch):
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 class RealPublisher:
  async def upload(self,path,title,description,disclosure): return {"status":"PUBLISHED","video_id":"yt-real-123"}
 monkeypatch.setattr("app.main.YouTubePublisher",RealPublisher)
 try:
  video=make_approved_video(db);response=TestClient(app).post(f"/api/videos/{video.id}/publish")
  assert response.status_code==200
  db.refresh(video);assert video.state==VideoState.UPLOADED.value;assert video.simulated_upload is False
  event=db.query(AuditEvent).filter_by(video_id=video.id,event="real_publish").one()
  assert "real YouTube publish completed" in event.detail
 finally:
  app.dependency_overrides.clear();db.close()

def test_cors_allows_whitelisted_origin_and_rejects_non_whitelisted_origin():
 client=TestClient(app)
 allowed=client.options("/health",headers={"Origin":"http://localhost:3000","Access-Control-Request-Method":"GET"})
 assert allowed.status_code==200
 assert allowed.headers["access-control-allow-origin"]=="http://localhost:3000"
 blocked=client.options("/health",headers={"Origin":"http://evil.example","Access-Control-Request-Method":"GET"})
 assert blocked.status_code==400
 assert "access-control-allow-origin" not in blocked.headers

def test_media_upload_requires_mp4_and_starts_at_brief_ready(tmp_path,monkeypatch):
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 monkeypatch.setattr(get_settings(),"media_root",str(tmp_path))
 try:
  video=make_brief_video(db)
  response=TestClient(app).post(f"/api/videos/{video.id}/media",files={"file":("clip.txt",b"not-video","text/plain")})
  assert response.status_code==415
  db.refresh(video);assert video.state==VideoState.BRIEF_READY.value
 finally:
  app.dependency_overrides.clear();db.close()

def test_media_upload_stores_finished_mp4_durably_and_transitions(tmp_path,monkeypatch):
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 monkeypatch.setattr(get_settings(),"media_root",str(tmp_path))
 try:
  video=make_brief_video(db)
  response=TestClient(app).post(f"/api/videos/{video.id}/media",files={"file":("clip.mp4",b"finished-video-placeholder","video/mp4")})
  assert response.status_code==200
  db.refresh(video)
  assert video.state==VideoState.MEDIA_RECEIVED.value
  assert video.artifact_path and Path(video.artifact_path).exists()
  assert Path(video.artifact_path).read_bytes()==b"finished-video-placeholder"
  assert video.thumbnail_path==""  # invalid fixture; thumbnail extraction is optional/non-blocking
 finally:
  app.dependency_overrides.clear();db.close()

def test_media_upload_rejects_wrong_state(tmp_path,monkeypatch):
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 monkeypatch.setattr(get_settings(),"media_root",str(tmp_path))
 try:
  video=make_approved_video(db)
  response=TestClient(app).post(f"/api/videos/{video.id}/media",files={"file":("clip.mp4",b"x","video/mp4")})
  assert response.status_code==409
 finally:
  app.dependency_overrides.clear();db.close()
