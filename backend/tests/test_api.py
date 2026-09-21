from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import get_settings
from app.db import get_db
from app.main import app
from app.models import AuditEvent,Base,Video,VideoState
from app.services import ReviewSuggestionEngine, YouTubePublisher

TEST_KEY = "test-founder-key"
get_settings().founder_api_key = TEST_KEY
AUTH = {"Authorization": f"Bearer {TEST_KEY}"}
BAD_AUTH = {"Authorization": "Bearer wrong-key"}

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
  video=make_approved_video(db);response=TestClient(app).post(f"/api/videos/{video.id}/publish",headers=AUTH)
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
  video=make_approved_video(db);response=TestClient(app).post(f"/api/videos/{video.id}/publish",headers=AUTH)
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
  response=TestClient(app).post(f"/api/videos/{video.id}/media",headers=AUTH,files={"file":("clip.txt",b"not-video","text/plain")})
  assert response.status_code==415
  db.refresh(video);assert video.state==VideoState.BRIEF_READY.value
 finally:
  app.dependency_overrides.clear();db.close()

def test_media_upload_stores_finished_mp4_durably_and_transitions(tmp_path,monkeypatch):
 db=make_db();app.dependency_overrides[get_db]=override_db(db)
 monkeypatch.setattr(get_settings(),"media_root",str(tmp_path))
 try:
  video=make_brief_video(db)
  response=TestClient(app).post(f"/api/videos/{video.id}/media",headers=AUTH,files={"file":("clip.mp4",b"finished-video-placeholder","video/mp4")})
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
  response=TestClient(app).post(f"/api/videos/{video.id}/media",headers=AUTH,files={"file":("clip.mp4",b"x","video/mp4")})
  assert response.status_code==409
 finally:
  app.dependency_overrides.clear();db.close()


def make_ready_for_review_video(db, suggestion=False):
    video = Video(
        topic="synthetic media",
        title="Synthetic Media Explained",
        description="",
        script="A verified script.",
        brief='{"scenes":[{"visual":"AI-generated visuals of a city"}],"target_duration_seconds":30,"aspect_ratio":"9:16","voice_and_pacing_notes":"clear"}'
        if suggestion
        else '{"scenes":[{"visual":"Original camera footage"}],"target_duration_seconds":30,"aspect_ratio":"9:16","voice_and_pacing_notes":"clear"}',
        state=VideoState.READY_FOR_REVIEW.value,
        rights_cleared=True,
        policy_passed=True,
        artifact_path="",
        disclosure_suggestion=suggestion,
        disclosure_suggestion_reason="brief/script mentions AI-generated visuals" if suggestion else "No known synthetic-content signal found in the script/brief text.",
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def test_review_suggestion_engine_detects_positive_and_negative_signals():
    engine = ReviewSuggestionEngine()
    positive, positive_reason = engine.suggest("The video uses AI-generated visuals and a voice clone.")
    negative, negative_reason = engine.suggest("The video uses original camera footage and a human-recorded voice.")
    assert positive is True
    assert "AI-generated visuals" in positive_reason
    assert negative is False
    assert "No known synthetic-content signal" in negative_reason


def test_review_endpoint_rejects_without_watched_confirmation():
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        video = make_ready_for_review_video(db, suggestion=True)
        response = TestClient(app).post(
            f"/api/videos/{video.id}/review",
            headers=AUTH,
            json={"watched_confirmed": False, "disclosure_answer": True},
        )
        assert response.status_code == 400
        db.refresh(video)
        assert video.human_watched_confirmed is False
        assert video.human_disclosure_answer is None
        assert video.disclosure_required is False
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_approval_is_blocked_until_human_review_is_submitted():
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        video = make_ready_for_review_video(db, suggestion=True)
        response = TestClient(app).post(
            f"/api/videos/{video.id}/approval",
            headers=AUTH,
            json={"approve": True},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Review required before approval"
        db.refresh(video)
        assert video.state == VideoState.READY_FOR_REVIEW.value
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_human_disclosure_answer_overrides_system_suggestion():
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        video = make_ready_for_review_video(db, suggestion=True)
        response = TestClient(app).post(
            f"/api/videos/{video.id}/review",
            headers=AUTH,
            json={"watched_confirmed": True, "disclosure_answer": False},
        )
        assert response.status_code == 200
        db.refresh(video)
        assert video.human_watched_confirmed is True
        assert video.human_disclosure_answer is False
        assert video.disclosure_required is False
        assert video.disclosure_suggestion is True
        assert video.disclosure_suggestion != video.disclosure_required
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_approval_succeeds_after_explicit_human_review():
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        video = make_ready_for_review_video(db, suggestion=True)
        review = TestClient(app).post(
            f"/api/videos/{video.id}/review",
            headers=AUTH,
            json={"watched_confirmed": True, "disclosure_answer": True},
        )
        assert review.status_code == 200
        approval_response = TestClient(app).post(
            f"/api/videos/{video.id}/approval",
            headers=AUTH,
            json={"approve": True},
        )
        assert approval_response.status_code == 200
        db.refresh(video)
        assert video.state == VideoState.APPROVED.value
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_uploaded_media_is_streamed_by_review_endpoint(tmp_path):
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        media = tmp_path / "video.mp4"
        media.write_bytes(b"fake-mp4-for-stream-test")
        video = make_ready_for_review_video(db)
        video.artifact_path = str(media)
        db.commit()
        response = TestClient(app).get(f"/api/videos/{video.id}/media",headers=AUTH)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("video/mp4")
        assert response.content == b"fake-mp4-for-stream-test"
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_write_endpoint_requires_founder_auth():
    db = make_db()
    app.dependency_overrides[get_db] = override_db(db)
    try:
        response = TestClient(app).post("/api/videos", json={"topic": "solar energy", "title": "Solar Energy Explained"}, headers=BAD_AUTH)
        assert response.status_code == 401
        response = TestClient(app).post("/api/videos", json={"topic": "solar energy", "title": "Solar Energy Explained"})
        assert response.status_code == 401
        response = TestClient(app).post("/api/videos", json={"topic": "solar energy", "title": "Solar Energy Explained"}, headers=AUTH)
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_dashboard_requires_founder_auth():
    client = TestClient(app)
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/dashboard", headers=BAD_AUTH).status_code == 401
    assert client.get("/api/dashboard", headers=AUTH).status_code == 200


def test_health_remains_public():
    assert TestClient(app).get("/health").status_code == 200
