import json
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

def cleared_asset():
 return [{"source":"creator-upload","license":"CC BY 4.0","cleared":True}]

def brief_json():
 return json.dumps({
  "scenes":[{"scene_number":1,"duration_seconds":8,"visual":"Solar panels at sunrise","tone":"clear","narration_focus":"verified solar-energy fact"}],
  "target_duration_seconds":8,
  "aspect_ratio":"9:16",
  "voice_and_pacing_notes":"Calm, concise pacing."
 })

class FakeProvider:
 async def generate(self,prompt):
  if "production-ready video brief" in prompt:
   return brief_json()
  return "REAL AI GENERATED SCRIPT: explain solar energy with verified claims."

@pytest.mark.asyncio
async def test_pipeline_rejects_assets_without_license(monkeypatch,db):
 class ExplodingProvider:
  async def generate(self,prompt):
   raise AssertionError("AI must not run before the rights gate")
 monkeypatch.setattr(AIProvider,"get",staticmethod(lambda:ExplodingProvider()))
 video=Video(topic="solar energy",title="Solar Energy Explained",assets=[{"source":"unknown","cleared":True}],state=VideoState.SCRIPTED.value)
 db.add(video);db.commit()
 await run_pipeline(video,db)
 assert video.rights_cleared is False
 assert video.state==VideoState.REJECTED.value

@pytest.mark.asyncio
async def test_pipeline_generates_real_structured_brief(monkeypatch,db):
 monkeypatch.setattr(AIProvider,"get",staticmethod(lambda:FakeProvider()))
 video=Video(topic="solar energy",title="Solar Energy Explained",assets=cleared_asset(),state=VideoState.SCRIPTED.value)
 db.add(video);db.commit()
 await run_pipeline(video,db)
 assert video.rights_cleared is True
 assert video.state==VideoState.BRIEF_READY.value
 assert video.brief and "Solar panels at sunrise" in video.brief
 parsed=json.loads(video.brief)
 assert parsed["aspect_ratio"]=="9:16"
 assert "REAL AI GENERATED SCRIPT:" in video.script

@pytest.mark.asyncio
async def test_pipeline_enforces_variation_before_brief(monkeypatch,db):
 class DuplicateProvider:
  async def generate(self,prompt):
   return "the quick brown fox jumps over the lazy dog repeatedly"
 monkeypatch.setattr(AIProvider,"get",staticmethod(lambda:DuplicateProvider()))
 old=Video(topic="old",title="Old",script="the quick brown fox jumps over the lazy dog repeatedly",state=VideoState.GENERATED.value,assets=cleared_asset())
 candidate=Video(topic="new",title="New",state=VideoState.SCRIPTED.value,assets=cleared_asset())
 db.add_all([old,candidate]);db.commit()
 await run_pipeline(candidate,db)
 assert candidate.state==VideoState.REJECTED.value


@pytest.mark.asyncio
async def test_qc_wires_disclosure_suggestion_without_setting_final_value(db):
    positive = Video(
        topic="synthetic media",
        title="AI Visuals",
        script="Use synthetic visuals for the explainer.",
        brief='{"scenes":[{"visual":"AI-generated visuals of a city"}]}',
        state=VideoState.MEDIA_RECEIVED.value,
        assets=cleared_asset(),
        rights_cleared=True,
    )
    negative = Video(
        topic="nature",
        title="Nature Walk",
        script="Use original camera footage.",
        brief='{"scenes":[{"visual":"original camera footage"}]}',
        state=VideoState.MEDIA_RECEIVED.value,
        assets=cleared_asset(),
        rights_cleared=True,
    )
    db.add_all([positive, negative])
    db.commit()

    await run_pipeline(positive, db)
    await run_pipeline(negative, db)

    assert positive.state == VideoState.READY_FOR_REVIEW.value
    assert positive.disclosure_suggestion is True
    assert "AI-generated visuals" in positive.disclosure_suggestion_reason
    assert positive.disclosure_required is False

    assert negative.state == VideoState.READY_FOR_REVIEW.value
    assert negative.disclosure_suggestion is False
    assert negative.disclosure_required is False
