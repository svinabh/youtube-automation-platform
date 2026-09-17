from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.video import Video, VideoStatus
from app.models.audit import ApprovalAuditLog

class ApprovalService:
    @staticmethod
    def _create_audit_log(db: Session, video_id: int, action: str, user_id: str, reason: str = None):
        audit_log = ApprovalAuditLog(
            video_id=video_id,
            action=action,
            user_id=user_id,
            reason=reason
        )
        db.add(audit_log)
        db.flush()

    @staticmethod
    def submit_for_approval(db: Session, video_id: int, user_id: str):
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if video.status == VideoStatus.PENDING_APPROVAL:
            return video # Idempotent

        if video.status not in [VideoStatus.DRAFT, VideoStatus.REJECTED]:
            raise HTTPException(status_code=400, detail=f"Cannot submit for approval from status {video.status.name}")

        video.status = VideoStatus.PENDING_APPROVAL
        ApprovalService._create_audit_log(db, video_id, "SUBMITTED", user_id)
        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def approve_video(db: Session, video_id: int, user_id: str, reason: str = None):
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if video.status == VideoStatus.APPROVED:
            return video # Idempotent

        if video.status != VideoStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=400, detail=f"Cannot approve video from status {video.status.name}")

        video.status = VideoStatus.APPROVED
        ApprovalService._create_audit_log(db, video_id, "APPROVED", user_id, reason)
        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def reject_video(db: Session, video_id: int, user_id: str, reason: str):
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if not reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")

        if video.status == VideoStatus.REJECTED:
            return video # Idempotent

        if video.status != VideoStatus.PENDING_APPROVAL:
            raise HTTPException(status_code=400, detail=f"Cannot reject video from status {video.status.name}")

        video.status = VideoStatus.REJECTED
        ApprovalService._create_audit_log(db, video_id, "REJECTED", user_id, reason)
        db.commit()
        db.refresh(video)
        return video
