from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.video import VideoResponse, ApprovalRequest, ApprovalResponse, VideoCreate
from app.services.qc_service import ApprovalService
from app.models.video import Video

router = APIRouter()

# For testing purposes only to create a video
@router.post("/", response_model=VideoResponse)
def create_video(video: VideoCreate, db: Session = Depends(get_db)):
    db_video = Video(title=video.title, description=video.description)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

@router.post("/{video_id}/submit-approval", response_model=ApprovalResponse)
def submit_for_approval(video_id: int, request: ApprovalRequest, db: Session = Depends(get_db)):
    video = ApprovalService.submit_for_approval(db, video_id, request.user_id)
    return ApprovalResponse(video_id=video.id, status=video.status, message="Successfully submitted for approval")

@router.post("/{video_id}/approve", response_model=ApprovalResponse)
def approve_video(video_id: int, request: ApprovalRequest, db: Session = Depends(get_db)):
    video = ApprovalService.approve_video(db, video_id, request.user_id, request.reason)
    return ApprovalResponse(video_id=video.id, status=video.status, message="Video approved successfully")

@router.post("/{video_id}/reject", response_model=ApprovalResponse)
def reject_video(video_id: int, request: ApprovalRequest, db: Session = Depends(get_db)):
    video = ApprovalService.reject_video(db, video_id, request.user_id, request.reason)
    return ApprovalResponse(video_id=video.id, status=video.status, message="Video rejected")

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
