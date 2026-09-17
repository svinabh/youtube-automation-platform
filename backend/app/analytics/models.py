from pydantic import BaseModel

class RawVideoAnalytics(BaseModel):
    video_id: str
    views: int
    likes: int
    comments: int
    impressions: int
    clicks: int
    watch_time_seconds: int

class NormalizedAnalytics(BaseModel):
    video_id: str
    ctr: float
    engagement_rate: float
    average_view_duration: float

class PerformanceReport(BaseModel):
    video_id: str
    ctr_performance: str
    engagement_performance: str
    is_outperforming: bool

class LearningInsight(BaseModel):
    video_id: str
    insight_type: str
    description: str
    confidence_score: float
