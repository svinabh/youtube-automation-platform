from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.video import VideoStatus

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    status: VideoStatus

    model_config = ConfigDict(from_attributes=True)

class ApprovalRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None

class ApprovalResponse(BaseModel):
    video_id: int
    status: VideoStatus
    message: str

class ApprovalAuditLogResponse(BaseModel):
    id: int
    video_id: int
    action: str
    user_id: str
    reason: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
