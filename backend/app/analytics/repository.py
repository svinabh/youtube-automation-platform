from abc import ABC, abstractmethod
from typing import Optional, List
from app.analytics.models import PerformanceReport, LearningInsight

class AnalyticsRepository(ABC):
    @abstractmethod
    def save_performance_report(self, report: PerformanceReport) -> None:
        pass

    @abstractmethod
    def get_performance_report(self, video_id: str) -> Optional[PerformanceReport]:
        pass

    @abstractmethod
    def save_insights(self, insights: List[LearningInsight]) -> None:
        pass

class InMemoryAnalyticsRepository(AnalyticsRepository):
    def __init__(self):
        self._reports = {}
        self._insights = {}

    def save_performance_report(self, report: PerformanceReport) -> None:
        self._reports[report.video_id] = report

    def get_performance_report(self, video_id: str) -> Optional[PerformanceReport]:
        return self._reports.get(video_id)

    def save_insights(self, insights: List[LearningInsight]) -> None:
        if not insights:
            return
        video_id = insights[0].video_id
        self._insights[video_id] = insights

# Singleton instance for dependency injection in the absence of a DB connection pool
_in_memory_repo = InMemoryAnalyticsRepository()

def get_analytics_repository() -> AnalyticsRepository:
    return _in_memory_repo
