from app.media import FFmpegRenderer
from app.models import Video,VideoState
from app.services import AdvertiserPrecheck,BudgetGuard,DisclosureTagger,QuotaManager,RightsRegistry,VariationGuard
from app.state import can_transition

def test_state():
 assert can_transition(VideoState.READY_FOR_REVIEW,VideoState.APPROVED)
 assert not can_transition(VideoState.READY_FOR_REVIEW,VideoState.UPLOADED)
 assert can_transition(VideoState.APPROVED,VideoState.SIMULATED_UPLOAD)

def test_variation_guard_rejects_duplicate():
 g=VariationGuard();script="the quick brown fox jumps over the lazy dog"
 assert not g.allowed(script,[script])

def test_advertiser_risk_tiers():
 medium=AdvertiserPrecheck().evaluate("documentary about a sensitive event")
 high=AdvertiserPrecheck().evaluate("graphic violence and firearms")
 assert medium.risk_level=="MEDIUM" and medium.passed
 assert high.risk_level=="HIGH" and not high.passed

def test_other_guards():
 assert RightsRegistry().cleared([{"license":"CC BY","cleared":True}])
 assert DisclosureTagger().evaluate(realistic_synthetic=True)["required"]
 assert BudgetGuard(5).allowed(3,2)
 assert not BudgetGuard(5).allowed(3,3)
 assert QuotaManager(100).allowed(20,80)

def test_ffmpeg_extracts_thumbnail_from_uploaded_video(tmp_path):
 source=tmp_path/"uploaded.mp4"
 thumbnail=tmp_path/"thumbnail.jpg"
 import subprocess
 subprocess.run(
  [
   "ffmpeg","-y","-loglevel","error","-f","lavfi","-i",
   "color=c=black:s=320x180:d=1","-c:v","libx264","-pix_fmt","yuv420p",
   str(source),
  ],
  check=True,
 )
 assert FFmpegRenderer().extract_thumbnail(str(source),str(thumbnail))==str(thumbnail)
 assert thumbnail.exists() and thumbnail.stat().st_size>0

def test_video_model_has_media_artifact_field():
 assert "artifact_path" in Video.__table__.columns
 assert "simulated_upload" in Video.__table__.columns
