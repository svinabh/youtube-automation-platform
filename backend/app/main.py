from fastapi import Depends,FastAPI,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from .config import get_settings
from .db import get_db,init_db
from .media import FFmpegRenderer
from .models import AuditEvent,Video,VideoState
from .services import AIProvider,DisclosureTagger,PolicyEngine,VariationGuard,YouTubePublisher
from .state import can_transition
app=FastAPI(title="YouTube Automation Platform",version="1.1.0");settings=get_settings()
@app.on_event("startup")
def startup(): init_db()
class VideoCreate(BaseModel):
 topic:str=Field(min_length=3,max_length=300);title:str=Field(min_length=3,max_length=200);description:str="";script:str="";rights_cleared:bool=False
class Approval(BaseModel): approve:bool
def out(v): return {"id":v.id,"topic":v.topic,"title":v.title,"state":v.state,"rights_cleared":v.rights_cleared,"policy_passed":v.policy_passed,"disclosure_required":v.disclosure_required,"approved_by_human":v.approved_by_human,"artifact_path":getattr(v,"artifact_path","")}
def move(db,v,target,actor):
 old=VideoState(v.state)
 if not can_transition(old,target): raise HTTPException(409,f"Invalid transition {old}->{target}")
 v.state=target.value;db.add(AuditEvent(video_id=v.id,event="state_transition",actor=actor,detail=f"{old}->{target}"))
async def run_pipeline(video:Video,db:Session):
 if video.state==VideoState.IDEA: move(db,video,VideoState.RESEARCHED,"orchestrator")
 if video.state==VideoState.RESEARCHED: move(db,video,VideoState.SCRIPTED,"orchestrator")
 if video.state==VideoState.SCRIPTED:
  if not video.script:
   prompt="Write an original YouTube script for this topic. Do not invent facts; clearly mark claims needing verification. Topic: "+video.topic
   generated=(await AIProvider.get().generate(prompt)).strip()
   if not generated: move(db,video,VideoState.REJECTED,"ai");db.commit();return
   video.script=generated
  previous=[row[0] for row in db.query(Video.script).filter(Video.id!=video.id,Video.script!="").order_by(Video.created_at.desc()).limit(10).all()]
  if not VariationGuard().allowed(video.script,previous):
   move(db,video,VideoState.REJECTED,"variation_guard");db.commit();return
  move(db,video,VideoState.GENERATED,"orchestrator")
 if video.state==VideoState.GENERATED:
  video.artifact_path=FFmpegRenderer().render(f"{settings.media_root}/{video.id}.mp4")
  move(db,video,VideoState.QC,"renderer")
 if video.state==VideoState.QC:
  disclosure=DisclosureTagger().evaluate(production_assistance_only=True);video.disclosure_required=disclosure["required"]
  policy=PolicyEngine().evaluate(video.title,video.description,video.script,video.rights_cleared,disclosure);video.policy_passed=policy.passed
  move(db,video,VideoState.REJECTED if not policy.passed else VideoState.POLICY,"policy")
 if video.state==VideoState.POLICY: move(db,video,VideoState.READY_FOR_REVIEW,"orchestrator")
 db.commit();db.refresh(video)
@app.get("/health")
def health(): return {"status":"ok","kill_switch":settings.global_kill_switch}
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db)):
 vs=db.query(Video).order_by(Video.created_at.desc()).limit(50).all()
 return {"approval_required":settings.human_approval_required,"kill_switch":settings.global_kill_switch,"pending":[out(v) for v in vs if v.state==VideoState.READY_FOR_REVIEW.value],"recent":[out(v) for v in vs[:20]]}
@app.post("/api/videos")
def create(p:VideoCreate,db:Session=Depends(get_db)):
 v=Video(topic=p.topic,title=p.title,description=p.description,script=p.script,rights_cleared=p.rights_cleared);db.add(v);db.commit();db.refresh(v);return out(v)
@app.post("/api/videos/{vid}/run")
async def run(vid:str,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v: raise HTTPException(404,"Video not found")
 if settings.global_kill_switch: raise HTTPException(423,"Global kill switch active")
 await run_pipeline(v,db);return out(v)
@app.post("/api/videos/{vid}/approval")
def approval(vid:str,p:Approval,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v: raise HTTPException(404,"Video not found")
 if v.state!=VideoState.READY_FOR_REVIEW.value: raise HTTPException(409,"Not awaiting approval")
 move(db,v,VideoState.APPROVED if p.approve else VideoState.REJECTED,"founder");v.approved_by_human=p.approve;db.commit();return out(v)
@app.post("/api/videos/{vid}/publish")
async def publish(vid:str,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v: raise HTTPException(404,"Video not found")
 if settings.global_kill_switch: raise HTTPException(423,"Global kill switch active")
 if v.state!=VideoState.APPROVED.value or not v.rights_cleared or not v.policy_passed or not v.artifact_path: raise HTTPException(409,"Approval, rights, policy, and media gates are required")
 result=await YouTubePublisher().upload(v.artifact_path,v.title,v.description,v.disclosure_required);move(db,v,VideoState.UPLOADED,"publisher");db.commit();return {"video":out(v),"youtube":result}
