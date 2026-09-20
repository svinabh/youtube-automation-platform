from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from .config import get_settings
from .db import get_db,init_db
from .models import Video,AuditEvent,VideoState
from .services import PolicyEngine,DisclosureTagger,YouTubePublisher
from .state import can_transition
app=FastAPI(title="YouTube Automation Platform",version="1.0.0");settings=get_settings()
@app.on_event("startup")
def startup():init_db()
class VideoCreate(BaseModel):
 topic:str=Field(min_length=3,max_length=300);title:str=Field(min_length=3,max_length=200);description:str="";script:str="";rights_cleared:bool=False
class Approval(BaseModel):approve:bool
def out(v):return {"id":v.id,"topic":v.topic,"title":v.title,"state":v.state,"rights_cleared":v.rights_cleared,"policy_passed":v.policy_passed,"disclosure_required":v.disclosure_required,"approved_by_human":v.approved_by_human}
def move(db,v,target,actor):
 old=VideoState(v.state)
 if not can_transition(old,target):raise HTTPException(409,f"Invalid transition {old}->{target}")
 v.state=target.value;db.add(AuditEvent(video_id=v.id,event="state_transition",actor=actor,detail=f"{old}->{target}"))
@app.get("/health")
def health():return {"status":"ok","kill_switch":settings.global_kill_switch}
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db)):
 vs=db.query(Video).order_by(Video.created_at.desc()).limit(50).all();return {"approval_required":settings.human_approval_required,"kill_switch":settings.global_kill_switch,"pending":[out(v) for v in vs if v.state==VideoState.READY_FOR_REVIEW.value],"recent":[out(v) for v in vs[:20]]}
@app.post("/api/videos")
def create(p:VideoCreate,db:Session=Depends(get_db)):
 v=Video(topic=p.topic,title=p.title,description=p.description,script=p.script,rights_cleared=p.rights_cleared);db.add(v);db.commit();db.refresh(v);return out(v)
@app.post("/api/videos/{vid}/run")
def run(vid:str,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v:raise HTTPException(404,"Video not found")
 if settings.global_kill_switch:raise HTTPException(423,"Global kill switch active")
 if v.state=="IDEA":move(db,v,VideoState.RESEARCHED,"orchestrator")
 if v.state=="RESEARCHED":move(db,v,VideoState.SCRIPTED,"orchestrator")
 if v.state=="SCRIPTED":
  if not v.script:v.script="Research-backed draft for: "+v.topic
  move(db,v,VideoState.GENERATED,"orchestrator")
 if v.state=="GENERATED":move(db,v,VideoState.QC,"qc")
 if v.state=="QC":
  d=DisclosureTagger().evaluate(production_assistance_only=True);v.disclosure_required=d["required"];p=PolicyEngine().evaluate(v.title,v.description,v.script,v.rights_cleared,d);v.policy_passed=p.passed
  if not p.passed:move(db,v,VideoState.REJECTED,"policy")
  else:move(db,v,VideoState.POLICY,"policy")
 if v.state=="POLICY":move(db,v,VideoState.READY_FOR_REVIEW,"orchestrator")
 db.commit();db.refresh(v);return out(v)
@app.post("/api/videos/{vid}/approval")
def approval(vid:str,p:Approval,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v:raise HTTPException(404,"Video not found")
 if v.state!=VideoState.READY_FOR_REVIEW.value:raise HTTPException(409,"Not awaiting approval")
 move(db,v,VideoState.APPROVED if p.approve else VideoState.REJECTED,"founder");v.approved_by_human=p.approve;db.commit();return out(v)
@app.post("/api/videos/{vid}/publish")
async def publish(vid:str,db:Session=Depends(get_db)):
 v=db.get(Video,vid)
 if not v:raise HTTPException(404,"Video not found")
 if settings.global_kill_switch:raise HTTPException(423,"Global kill switch active")
 if v.state!=VideoState.APPROVED.value or not v.rights_cleared or not v.policy_passed:raise HTTPException(409,"Approval, rights, and policy gates are required")
 result=await YouTubePublisher().upload(v.id,v.title,v.description,v.disclosure_required);move(db,v,VideoState.UPLOADED,"publisher");db.commit();return {"video":out(v),"youtube":result}
