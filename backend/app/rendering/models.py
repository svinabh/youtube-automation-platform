from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class MediaType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"

class Resolution(BaseModel):
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)

class MediaElement(BaseModel):
    id: str
    media_type: MediaType
    file_path: str
    duration: float = Field(..., gt=0)
    start_time: float = Field(0.0, ge=0)
    volume: Optional[float] = Field(None, ge=0, le=1.0) # For audio/video

class Scene(BaseModel):
    id: str
    elements: List[MediaElement]
    duration: float = Field(..., gt=0)

class Timeline(BaseModel):
    id: str
    resolution: Resolution
    scenes: List[Scene]
    global_audio_tracks: List[MediaElement] = Field(default_factory=list)
    output_path: str

    @property
    def total_duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)
