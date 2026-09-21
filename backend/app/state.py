from .models import VideoState
ALLOWED={VideoState.IDEA:{VideoState.RESEARCHED},VideoState.RESEARCHED:{VideoState.SCRIPTED},
VideoState.SCRIPTED:{VideoState.GENERATED,VideoState.REJECTED},VideoState.GENERATED:{VideoState.QC,VideoState.REJECTED},
VideoState.QC:{VideoState.POLICY,VideoState.REJECTED},VideoState.POLICY:{VideoState.READY_FOR_REVIEW},
VideoState.READY_FOR_REVIEW:{VideoState.APPROVED,VideoState.REJECTED},VideoState.APPROVED:{VideoState.UPLOADED,VideoState.SIMULATED_UPLOAD},
VideoState.REJECTED:set(),VideoState.UPLOADED:set(),VideoState.SIMULATED_UPLOAD:set(),VideoState.FAILED:set()}
def can_transition(old,new): return new in ALLOWED.get(old,set())
