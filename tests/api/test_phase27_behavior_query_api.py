from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.routes.behavior import (
    get_behavior_events,
    get_entity_behavior_timeline,
    get_entity_behavior_episodes,
    get_run_behavior_scorecard,
    get_run_behavior_insights,
    get_run_cohorts,
    compare_run_behavior
)
from src.observability.warehouse.models import (
    BehaviorEventRecord,
    BehaviorEpisodeRecord,
    RunBehaviorScorecardRecord,
    BehaviorInsightRecord,
    CohortBehaviorReportRecord,
    RunBehaviorComparisonRecord
)

@pytest.fixture
def mock_adapter():
    with patch("src.api.routes.behavior.adapter") as m:
        yield m

@pytest.mark.anyio
async def test_get_behavior_events_success(mock_adapter):
    mock_adapter.query_behavior_events.return_value = [
        BehaviorEventRecord(
            run_id="run_123",
            tick=10,
            event_id="e1",
            entity_id="hero1",
            category="combat",
            family="melee",
            action="attack",
            subject_type="monster",
            success=True,
            metadata_json="{}"
        )
    ]

    res = await get_behavior_events(run_id="run_123", entity_id="hero1", category="combat", limit=50, offset=0)
    assert len(res) == 1
    assert res[0]["event_id"] == "e1"
    mock_adapter.query_behavior_events.assert_called_once_with({
        "run_id": "run_123",
        "entity_id": "hero1",
        "category": "combat",
        "limit": 50,
        "offset": 0
    })

@pytest.mark.anyio
async def test_get_entity_behavior_timeline_success(mock_adapter):
    mock_adapter.query_behavior_events.return_value = []
    res = await get_entity_behavior_timeline(run_id="run_123", entity_id="hero1", limit=50, offset=0)
    assert res == []

@pytest.mark.anyio
async def test_get_entity_behavior_episodes_success(mock_adapter):
    mock_adapter.query_behavior_episodes.return_value = [
        BehaviorEpisodeRecord(
            run_id="run_123",
            episode_id="ep1",
            entity_id="hero1",
            category="combat",
            start_tick=5,
            end_tick=15,
            duration_ticks=10,
            outcome="SUCCESS",
            event_count=5,
            events_json="[]"
        )
    ]
    res = await get_entity_behavior_episodes(run_id="run_123", entity_id="hero1", category=None, limit=50, offset=0)
    assert len(res) == 1
    assert res[0]["episode_id"] == "ep1"

@pytest.mark.anyio
async def test_get_run_behavior_scorecard_empty(mock_adapter):
    mock_adapter.query_run_behavior_scorecards.return_value = []
    res = await get_run_behavior_scorecard(run_id="run_123")
    assert res == {}

@pytest.mark.anyio
async def test_get_run_behavior_scorecard_success(mock_adapter):
    mock_adapter.query_run_behavior_scorecards.return_value = [
        RunBehaviorScorecardRecord(
            run_id="run_123",
            total_events=100,
            total_episodes=5,
            total_failures=2,
            total_adaptations=3,
            entity_count=2,
            verdict_distribution_json="{}",
            category_counts_json="{}",
            family_counts_json="{}"
        )
    ]
    res = await get_run_behavior_scorecard(run_id="run_123")
    assert res["total_events"] == 100

@pytest.mark.anyio
async def test_get_run_behavior_insights(mock_adapter):
    mock_adapter.query_behavior_insights.return_value = [
        BehaviorInsightRecord(
            run_id="run_123",
            insight_id="in1",
            insight_type="repeated_failures",
            title="Repeated Failure Loop detected",
            evidence_json="{}",
            recommendation="none",
            severity="WARNING"
        )
    ]
    res = await get_run_behavior_insights(run_id="run_123")
    assert len(res) == 1
    assert res[0]["insight_id"] == "in1"

@pytest.mark.anyio
async def test_get_run_cohorts(mock_adapter):
    mock_adapter.query_cohort_behavior_reports.return_value = [
        CohortBehaviorReportRecord(
            run_id="run_123",
            cohort_name="STABLE",
            entities_json="[]",
            metrics_json="{}"
        )
    ]
    res = await get_run_cohorts(run_id="run_123")
    assert len(res) == 1
    assert res[0]["cohort_name"] == "STABLE"

@pytest.mark.anyio
async def test_compare_run_behavior(mock_adapter):
    mock_adapter.query_run_behavior_comparisons.return_value = [
        RunBehaviorComparisonRecord(
            run_id="run_123",
            baseline_run_id="run_base",
            episode_success_rate_delta=0.2,
            consecutive_failures_delta=-1.0,
            event_volume_delta=5.0,
            verdict="IMPROVED",
            reason="More success"
        )
    ]
    res = await compare_run_behavior(run_id="run_123", baseline_run_id="run_base")
    assert res["verdict"] == "IMPROVED"
    assert res["baseline_run_id"] == "run_base"
