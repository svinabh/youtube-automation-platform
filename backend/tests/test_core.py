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

def test_ffmpeg_produces_real_mp4(tmp_path):
 output=tmp_path/"artifact.mp4"
 assert FFmpegRenderer().render(str(output))==str(output)
 assert output.exists() and output.stat().st_size>1024
 assert output.read_bytes()[4:8]==b"ftyp"

def test_video_model_has_media_artifact_field():
 assert "artifact_path" in Video.__table__.columns
 assert "simulated_upload" in Video.__table__.columns
