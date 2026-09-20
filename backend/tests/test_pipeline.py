import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import run_pipeline
from app.models import Base,Video,VideoState
from app.services import AIProvider

@pytest.fixture
def db():
 engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
 Base.metadata.create_all(engine);session=sessionmaker(bind=engine)()
 try: yield session
 finally: session.close()

@pytest.mark.asyncio
async def test_pipeline_calls_ai_and_replaces_placeholder(monkeypatch,db):
 class FakeProvider:
  async def generate(self,prompt):
   assert "YouTube script" in prompt
   return "REAL AI GENERATED SCRIPT: explain solar energy with three verified claims."
 monkeypatch.setattr(AIProvider,"get",staticmethod(lambda:FakeProvider()))
 video=Video(topic="solar energy",title="Solar Energy Explained",rights_cleared=True,state=VideoState.SCRIPTED.value)
 db.add(video);db.commit()
 await run_pipeline(video,db)
 assert video.script.startswith("REAL AI GENERATED SCRIPT:")
 assert video.script!="Research-backed draft for: "+video.topic
 assert video.artifact_path.endswith(".mp4")

@pytest.mark.asyncio
async def test_pipeline_enforces_variation_before_generated(monkeypatch,db):
 class DuplicateProvider:
  async def generate(self,prompt): return "the quick brown fox jumps over the lazy dog repeatedly"
 monkeypatch.setattr(AIProvider,"get",staticmethod(lambda:DuplicateProvider()))
 old=Video(topic="old",title="Old",script="the quick brown fox jumps over the lazy dog repeatedly",state=VideoState.GENERATED.value,rights_cleared=True)
 candidate=Video(topic="new",title="New",state=VideoState.SCRIPTED.value,rights_cleared=True)
 db.add_all([old,candidate]);db.commit()
 await run_pipeline(candidate,db)
 assert candidate.state==VideoState.REJECTED.value
