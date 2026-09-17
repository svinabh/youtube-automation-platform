import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.analytics.models import RawVideoAnalytics, NormalizedAnalytics, PerformanceReport
from app.analytics.normalization import calculate_normalized_metrics
from app.analytics.performance import evaluate_performance
from app.analytics.learning import extract_insights
from app.analytics.repository import _in_memory_repo

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_repo():
    # Clear the in-memory repository before each test
    _in_memory_repo._reports.clear()
    _in_memory_repo._insights.clear()

def test_normalization_valid_data():
    raw_data = RawVideoAnalytics(
        video_id="vid_123",
        views=1000,
        likes=50,
        comments=10,
        impressions=10000,
        clicks=500,
        watch_time_seconds=60000
    )
    normalized = calculate_normalized_metrics(raw_data)

    assert normalized.video_id == "vid_123"
    assert normalized.ctr == 0.05
    assert normalized.engagement_rate == 0.06
    assert normalized.average_view_duration == 60.0

def test_normalization_zero_division():
    raw_data = RawVideoAnalytics(
        video_id="vid_zero",
        views=0,
        likes=0,
        comments=0,
        impressions=0,
        clicks=0,
        watch_time_seconds=0
    )
    normalized = calculate_normalized_metrics(raw_data)

    assert normalized.ctr == 0.0
    assert normalized.engagement_rate == 0.0
    assert normalized.average_view_duration == 0.0

def test_performance_evaluation():
    normalized_above = NormalizedAnalytics(
        video_id="vid_top", ctr=0.06, engagement_rate=0.05, average_view_duration=100.0
    )
    perf_top = evaluate_performance(normalized_above, baseline_ctr=0.05, baseline_engagement=0.04)
    assert perf_top.ctr_performance == "above_average"
    assert perf_top.engagement_performance == "above_average"
    assert perf_top.is_outperforming is True

    normalized_below = NormalizedAnalytics(
        video_id="vid_bot", ctr=0.04, engagement_rate=0.03, average_view_duration=20.0
    )
    perf_bot = evaluate_performance(normalized_below, baseline_ctr=0.05, baseline_engagement=0.04)
    assert perf_bot.ctr_performance == "below_average"
    assert perf_bot.engagement_performance == "below_average"
    assert perf_bot.is_outperforming is False

def test_learning_insights():
    perf = PerformanceReport(
        video_id="vid_learn",
        ctr_performance="above_average",
        engagement_performance="below_average",
        is_outperforming=False
    )
    norm = NormalizedAnalytics(video_id="vid_learn", ctr=0.06, engagement_rate=0.03, average_view_duration=50.0)

    insights = extract_insights(perf, norm)

    assert len(insights) == 2
    ctr_insight = next(i for i in insights if i.insight_type == "ctr")
    eng_insight = next(i for i in insights if i.insight_type == "engagement")

    assert "High CTR detected" in ctr_insight.description
    assert "Low engagement detected" in eng_insight.description

def test_api_ingest():
    payload = {
        "video_id": "vid_api",
        "views": 2000,
        "likes": 100,
        "comments": 20,
        "impressions": 20000,
        "clicks": 1200,
        "watch_time_seconds": 120000
    }
    response = client.post("/analytics/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "normalized_data" in data
    assert data["normalized_data"]["ctr"] == 0.06

    assert "performance" in data
    assert data["performance"]["ctr_performance"] == "above_average"

    assert "insights" in data
    assert isinstance(data["insights"], list)

def test_api_get_performance():
    # First ingest data so it's stored in the repository
    payload = {
        "video_id": "vid_perf",
        "views": 2000,
        "likes": 100,
        "comments": 20,
        "impressions": 20000,
        "clicks": 1200,
        "watch_time_seconds": 120000
    }
    client.post("/analytics/ingest", json=payload)

    # Now retrieve it
    response = client.get("/analytics/vid_perf/performance")
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "vid_perf"
    assert data["ctr_performance"] == "above_average"

def test_api_get_performance_not_found():
    response = client.get("/analytics/nonexistent/performance")
    assert response.status_code == 404
