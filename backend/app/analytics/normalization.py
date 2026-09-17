from app.analytics.models import RawVideoAnalytics, NormalizedAnalytics

def calculate_normalized_metrics(raw_data: RawVideoAnalytics) -> NormalizedAnalytics:
    ctr = (raw_data.clicks / raw_data.impressions) if raw_data.impressions > 0 else 0.0
    engagement_rate = ((raw_data.likes + raw_data.comments) / raw_data.views) if raw_data.views > 0 else 0.0
    average_view_duration = (raw_data.watch_time_seconds / raw_data.views) if raw_data.views > 0 else 0.0

    return NormalizedAnalytics(
        video_id=raw_data.video_id,
        ctr=ctr,
        engagement_rate=engagement_rate,
        average_view_duration=average_view_duration
    )
