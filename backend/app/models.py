from datetime import datetime,timezone
from enum import StrEnum
from uuid import uuid4
from sqlalchemy import Boolean,DateTime,Integer,String,Text
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
class Base(DeclarativeBase):pass
class VideoState(StrEnum):
 IDEA="IDEA";RESEARCHED="RESEARCHED";SCRIPTED="SCRIPTED";GENERATED="GENERATED";QC="QC";POLICY="POLICY";READY_FOR_REVIEW="READY_FOR_REVIEW";APPROVED="APPROVED";REJECTED="REJECTED";UPLOADED="UPLOADED";FAILED="FAILED"
class Video(Base):
 __tablename__="videos"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid4()))
 title:Mapped[str]=mapped_column(String(200));topic:Mapped[str]=mapped_column(String(300));description:Mapped[str]=mapped_column(Text,default="");script:Mapped[str]=mapped_column(Text,default="")
 state:Mapped[str]=mapped_column(String(32),default=VideoState.IDEA.value);rights_cleared:Mapped[bool]=mapped_column(Boolean,default=False);policy_passed:Mapped[bool]=mapped_column(Boolean,default=False);disclosure_required:Mapped[bool]=mapped_column(Boolean,default=False);approved_by_human:Mapped[bool]=mapped_column(Boolean,default=False)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[int]=mapped_column(Integer,primary_key=True);video_id:Mapped[str]=mapped_column(String(36));event:Mapped[str]=mapped_column(String(100));actor:Mapped[str]=mapped_column(String(100));detail:Mapped[str]=mapped_column(Text,default="");created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
