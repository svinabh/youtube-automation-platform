from app.analytics.models import NormalizedAnalytics, PerformanceReport, LearningInsight

def extract_insights(performance: PerformanceReport, normalized: NormalizedAnalytics) -> list[LearningInsight]:
    insights = []

    if performance.ctr_performance == "above_average":
        insights.append(
            LearningInsight(
                video_id=performance.video_id,
                insight_type="ctr",
                description="High CTR detected, thumbnail/title combo is effective.",
                confidence_score=0.8
            )
        )
    else:
        insights.append(
            LearningInsight(
                video_id=performance.video_id,
                insight_type="ctr",
                description="Low CTR detected, consider A/B testing different thumbnail styles.",
                confidence_score=0.7
            )
        )

    if performance.engagement_performance == "above_average":
        insights.append(
            LearningInsight(
                video_id=performance.video_id,
                insight_type="engagement",
                description="High engagement detected, content resonates well.",
                confidence_score=0.85
            )
        )
    else:
        insights.append(
            LearningInsight(
                video_id=performance.video_id,
                insight_type="engagement",
                description="Low engagement detected, try adding clearer calls to action.",
                confidence_score=0.75
            )
        )

    return insights
