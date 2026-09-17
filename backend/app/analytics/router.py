import logging
from fastapi import APIRouter, HTTPException, Depends
from app.analytics.models import RawVideoAnalytics, PerformanceReport, LearningInsight
from app.analytics.normalization import calculate_normalized_metrics
from app.analytics.performance import evaluate_performance
from app.analytics.learning import extract_insights
from app.analytics.repository import AnalyticsRepository, get_analytics_repository
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/ingest")
def ingest_analytics(
    raw_data: RawVideoAnalytics,
    repo: AnalyticsRepository = Depends(get_analytics_repository)
) -> Dict[str, Any]:
    logger.info(f"Ingesting analytics for video: {raw_data.video_id}")
    try:
        normalized_data = calculate_normalized_metrics(raw_data)
        logger.debug(f"Normalized data: {normalized_data}")

        performance = evaluate_performance(normalized_data)
        logger.debug(f"Performance report: {performance}")

        insights = extract_insights(performance, normalized_data)
        logger.info(f"Generated {len(insights)} insights for video: {raw_data.video_id}")

        repo.save_performance_report(performance)
        repo.save_insights(insights)

        return {
            "normalized_data": normalized_data,
            "performance": performance,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error processing analytics for video {raw_data.video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error processing analytics")

@router.get("/{video_id}/performance", response_model=PerformanceReport)
def get_performance(
    video_id: str,
    repo: AnalyticsRepository = Depends(get_analytics_repository)
) -> PerformanceReport:
    logger.info(f"Retrieving performance report for video: {video_id}")
    report = repo.get_performance_report(video_id)

    if not report:
        logger.warning(f"Performance report not found for video: {video_id}")
        raise HTTPException(status_code=404, detail="Performance report not found")

    return report
