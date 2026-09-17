import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ApprovalAuditLog(Base):
    __tablename__ = "approval_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., SUBMITTED, APPROVED, REJECTED
    user_id = Column(String, nullable=False) # In a real app, this would be a real user ID
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    video = relationship("Video")
