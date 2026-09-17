from app.analytics.models import NormalizedAnalytics, PerformanceReport

def evaluate_performance(
    normalized_data: NormalizedAnalytics,
    baseline_ctr: float = 0.05,
    baseline_engagement: float = 0.04
) -> PerformanceReport:

    ctr_perf = "above_average" if normalized_data.ctr > baseline_ctr else "below_average"
    engagement_perf = "above_average" if normalized_data.engagement_rate > baseline_engagement else "below_average"

    is_outperforming = (ctr_perf == "above_average" and engagement_perf == "above_average")

    return PerformanceReport(
        video_id=normalized_data.video_id,
        ctr_performance=ctr_perf,
        engagement_performance=engagement_perf,
        is_outperforming=is_outperforming
    )
