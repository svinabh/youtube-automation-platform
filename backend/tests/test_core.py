from app.models import VideoState
from app.state import can_transition
from app.services import VariationGuard,RightsRegistry,DisclosureTagger,BudgetGuard,QuotaManager,AdvertiserPrecheck
def test_state():assert can_transition(VideoState.READY_FOR_REVIEW,VideoState.APPROVED);assert not can_transition(VideoState.READY_FOR_REVIEW,VideoState.UPLOADED)
def test_variation():g=VariationGuard();assert not g.allowed("the quick brown fox jumps over the lazy dog",["the quick brown fox jumps over the lazy dog"])
def test_guards():
 assert RightsRegistry().cleared([{"license":"CC BY","cleared":True}]);assert DisclosureTagger().evaluate(realistic_synthetic=True)["required"]
 assert BudgetGuard(5).allowed(3,2);assert not BudgetGuard(5).allowed(3,3);assert QuotaManager(100).allowed(20,80);assert not AdvertiserPrecheck().evaluate("graphic violence").passed
