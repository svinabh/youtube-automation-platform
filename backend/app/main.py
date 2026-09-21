from pathlib import Path
from fastapi import Depends,FastAPI,File,HTTPException,UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from .config import get_settings
from .db import get_db,init_db
from .media import FFmpegRenderer
from .models import AuditEvent,Video,VideoState
from .services import AIProvider,PolicyEngine,RightsRegistry,ReviewSuggestionEngine,VariationGuard,VideoBriefGenerator,YouTubePublisher
from .state import can_transition
app=FastAPI(title="YouTube Automation Platform",version="1.2.0");settings=get_settings()
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.on_event("startup")
def startup(): init_db()

class VideoCreate(BaseModel):
    topic:str=Field(min_length=3,max_length=300);title:str=Field(min_length=3,max_length=200);description:str="";script:str="";assets:list[dict]=Field(default_factory=list)
class Approval(BaseModel):
    approve: bool


class HumanReview(BaseModel):
    watched_confirmed: bool
    disclosure_answer: bool

def out(v): return {"id":v.id,"topic":v.topic,"title":v.title,"state":v.state,"assets":v.assets,"rights_cleared":v.rights_cleared,"policy_passed":v.policy_passed,"disclosure_required":v.disclosure_required,"disclosure_suggestion":v.disclosure_suggestion,"disclosure_suggestion_reason":v.disclosure_suggestion_reason,"advertiser_risk_level":v.advertiser_risk_level,"human_watched_confirmed":v.human_watched_confirmed,"human_disclosure_answer":v.human_disclosure_answer,"approved_by_human":v.approved_by_human,"artifact_path":getattr(v,"artifact_path",""),"thumbnail_path":getattr(v,"thumbnail_path",""),"brief":getattr(v,"brief",""),"simulated_upload":v.simulated_upload}

def move(db,v,target,actor):
    old=VideoState(v.state)
    if not can_transition(old,target): raise HTTPException(409,f"Invalid transition {old}->{target}")
    v.state=target.value;db.add(AuditEvent(video_id=v.id,event="state_transition",actor=actor,detail=f"{old}->{target}"))

async def run_pipeline(video:Video,db:Session):
    if video.state==VideoState.IDEA: move(db,video,VideoState.RESEARCHED,"orchestrator")
    if video.state==VideoState.RESEARCHED: move(db,video,VideoState.SCRIPTED,"orchestrator")
    if video.state==VideoState.SCRIPTED:
        video.rights_cleared=RightsRegistry().cleared(video.assets or [])
        if not video.rights_cleared:
            move(db,video,VideoState.REJECTED,"rights_registry");db.commit();return
        if not video.script:
            prompt="Write an original YouTube script for this topic. Do not invent facts; clearly mark claims needing verification. Topic: "+video.topic
            generated=(await AIProvider.get().generate(prompt)).strip()
            if not generated: move(db,video,VideoState.REJECTED,"ai");db.commit();return
            video.script=generated
        previous=[row[0] for row in db.query(Video.script).filter(Video.id!=video.id,Video.script!="").order_by(Video.created_at.desc()).limit(10).all()]
        if not VariationGuard().allowed(video.script,previous):
            move(db,video,VideoState.REJECTED,"variation_guard");db.commit();return
        video.brief=await VideoBriefGenerator().generate(video.script,video.title,video.topic)
        move(db,video,VideoState.BRIEF_READY,"brief_generator")
    if video.state==VideoState.MEDIA_RECEIVED:
        # External video ingestion replaces the former internal GENERATED/FFmpeg synthesis step.
        move(db,video,VideoState.QC,"orchestrator")
    if video.state==VideoState.QC:
        suggestion_text=f"{video.title}\n{video.topic}\n{video.script}\n{video.brief}"
        video.disclosure_suggestion,video.disclosure_suggestion_reason=ReviewSuggestionEngine().suggest(suggestion_text)
        policy=PolicyEngine().evaluate(video.title,video.description,video.script,video.rights_cleared,{"required":video.disclosure_suggestion})
        video.policy_passed=policy.passed
        video.advertiser_risk_level=policy.risk_level
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
    v=Video(topic=p.topic,title=p.title,description=p.description,script=p.script,assets=p.assets,rights_cleared=False);db.add(v);db.commit();db.refresh(v);return out(v)

@app.post("/api/videos/{vid}/run")
async def run(vid:str,db:Session=Depends(get_db)):
    v=db.get(Video,vid)
    if not v: raise HTTPException(404,"Video not found")
    if settings.global_kill_switch: raise HTTPException(423,"Global kill switch active")
    await run_pipeline(v,db);return out(v)

@app.post("/api/videos/{vid}/media")
async def receive_media(vid:str,file:UploadFile=File(...),db:Session=Depends(get_db)):
    v=db.get(Video,vid)
    if not v: raise HTTPException(404,"Video not found")
    if v.state!=VideoState.BRIEF_READY.value: raise HTTPException(409,"Video brief must be ready before media upload")
    if Path(file.filename or "").suffix.lower()!=".mp4" or file.content_type!="video/mp4":
        raise HTTPException(415,"Only MP4 video uploads are accepted")
    max_bytes=settings.max_media_upload_mb*1024*1024
    target_dir=Path(settings.media_root)/"uploads";target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/f"{v.id}.mp4";written=0
    try:
        with target.open("wb") as output:
            while chunk:=await file.read(1024*1024):
                written+=len(chunk)
                if written>max_bytes: raise HTTPException(413,"Media file exceeds configured size limit")
                output.write(chunk)
    except HTTPException:
        target.unlink(missing_ok=True);raise
    try:
        thumb=FFmpegRenderer().extract_thumbnail(str(target),str(target_dir/f"{v.id}.jpg"))
        v.thumbnail_path=thumb
    except Exception:
        v.thumbnail_path=""
    v.artifact_path=str(target)
    move(db,v,VideoState.MEDIA_RECEIVED,"media_ingestion")
    db.commit();db.refresh(v)
    return out(v)

@app.get("/api/videos/{vid}/media")
def stream_media(vid: str, db: Session = Depends(get_db)):
    v = db.get(Video, vid)
    if not v:
        raise HTTPException(404, "Video not found")
    if not v.artifact_path or not Path(v.artifact_path).is_file():
        raise HTTPException(404, "Video file is not available")
    return FileResponse(
        v.artifact_path,
        media_type="video/mp4",
        filename=f"{v.id}.mp4",
        content_disposition_type="inline",
    )


@app.post("/api/videos/{vid}/review")
def review(vid: str, p: HumanReview, db: Session = Depends(get_db)):
    v = db.get(Video, vid)
    if not v:
        raise HTTPException(404, "Video not found")
    if v.state != VideoState.READY_FOR_REVIEW.value:
        raise HTTPException(409, "Video is not ready for human review")
    if not p.watched_confirmed:
        raise HTTPException(400, "You must confirm that you watched the full video before review")
    v.human_watched_confirmed = True
    v.human_disclosure_answer = p.disclosure_answer
    v.disclosure_required = p.disclosure_answer
    db.add(
        AuditEvent(
            video_id=v.id,
            event="human_review",
            actor="founder",
            detail=f"watched_confirmed=true; disclosure_answer={p.disclosure_answer}",
        )
    )
    db.commit()
    db.refresh(v)
    return out(v)


@app.post("/api/videos/{vid}/approval")
def approval(vid:str,p:Approval,db:Session=Depends(get_db)):
    v=db.get(Video,vid)
    if not v: raise HTTPException(404,"Video not found")
    if v.state!=VideoState.READY_FOR_REVIEW.value: raise HTTPException(409,"Not awaiting approval")
    if not v.human_watched_confirmed or v.human_disclosure_answer is None:
        raise HTTPException(409,"Review required before approval")
    move(db,v,VideoState.APPROVED if p.approve else VideoState.REJECTED,"founder");v.approved_by_human=p.approve;db.commit();return out(v)

@app.post("/api/videos/{vid}/publish")
async def publish(vid:str,db:Session=Depends(get_db)):
    v=db.get(Video,vid)
    if not v: raise HTTPException(404,"Video not found")
    if settings.global_kill_switch: raise HTTPException(423,"Global kill switch active")
    if v.state!=VideoState.APPROVED.value or not v.rights_cleared or not v.policy_passed or not v.artifact_path: raise HTTPException(409,"Approval, rights, policy, and media gates are required")
    result=await YouTubePublisher().upload(v.artifact_path,v.title,v.description,v.disclosure_required)
    status=result.get("status")
    if status=="PUBLISHED":
        v.simulated_upload=False;move(db,v,VideoState.UPLOADED,"publisher");db.add(AuditEvent(video_id=v.id,event="real_publish",actor="publisher",detail="real YouTube publish completed"))
    elif status=="SIMULATED":
        v.simulated_upload=True;move(db,v,VideoState.SIMULATED_UPLOAD,"publisher");db.add(AuditEvent(video_id=v.id,event="simulated_publish",actor="publisher",detail="publish simulation; no real YouTube upload occurred"))
    else: raise HTTPException(502,"Publisher returned an unknown success status")
    db.commit();return {"video":out(v),"youtube":result}
