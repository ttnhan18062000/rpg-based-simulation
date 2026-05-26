from __future__ import annotations
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from src.api.routes.search import (
    search_runs,
    search_events,
    search_anomalies,
    get_entity_timeline,
    get_metric_trend
)
from src.observability.warehouse.models import (
    RunRecord,
    EventRecord,
    AnomalyRecord,
    MetricWindowRecord
)

@pytest.fixture
def mock_warehouse():
    with patch("src.api.routes.search.get_warehouse_adapter") as mock_get:
        adapter = MagicMock()
        mock_get.return_value = adapter
        yield adapter


@pytest.mark.anyio
async def test_api_search_runs(mock_warehouse):
    # Mock return value
    mock_runs = [
        RunRecord(
            run_id="run-123",
            scenario_name="test_scenario",
            scenario_type="combat",
            seed=42,
            status="COMPLETED",
            ticks_completed=100,
            health_score=95.5,
            started_at="2026-05-20T10:00:00Z",
            ended_at="2026-05-20T10:05:00Z",
            manifest_json="{}"
        )
    ]
    mock_warehouse.query_runs.return_value = mock_runs

    # Invoke directly
    results = await search_runs(
        scenario_name="test_scenario",
        status="COMPLETED",
        sort="health_score_desc",
        limit=10,
        offset=0
    )

    assert len(results) == 1
    assert results[0]["run_id"] == "run-123"
    assert results[0]["health_score"] == 95.5

    # Check mock call args
    mock_warehouse.query_runs.assert_called_once_with({
        "scenario_name": "test_scenario",
        "status": "COMPLETED",
        "sort": "health_score_desc",
        "limit": 10,
        "offset": 0
    })


@pytest.mark.anyio
async def test_api_search_events(mock_warehouse):
    mock_events = [
        EventRecord(
            run_id="run-123",
            tick=5,
            event_type="move",
            event_category="movement",
            severity="INFO",
            entity_id="hero1",
            message="hero moved",
            created_at="2026-05-20T10:00:05Z",
            payload_json="{}"
        )
    ]
    mock_warehouse.query_events.return_value = mock_events

    # Invoke directly
    results = await search_events(
        run_id="run-123",
        entity_id="hero1",
        tick_start=0,
        tick_end=10,
        severity="INFO",
        limit=5,
        offset=0
    )

    assert len(results) == 1
    assert results[0]["run_id"] == "run-123"
    assert results[0]["tick"] == 5

    # Check tick validation tick_start > tick_end raises HTTPException 400
    with pytest.raises(HTTPException) as exc:
        await search_events(
            run_id="run-123",
            tick_start=20,
            tick_end=10
        )
    assert exc.value.status_code == 400
    assert "tick_start cannot be greater than tick_end" in exc.value.detail


@pytest.mark.anyio
async def test_api_search_anomalies(mock_warehouse):
    mock_anomalies = [
        AnomalyRecord(
            run_id="run-123",
            rule_id="NavigationStuckLive",
            severity="WARNING",
            domain="movement",
            tick_start=10,
            tick_end=15,
            affected_entity_count=1,
            message="stuck actor",
            evidence_json="{}"
        )
    ]
    mock_warehouse.query_anomalies.return_value = mock_anomalies

    results = await search_anomalies(
        run_id="run-123",
        rule_id="NavigationStuckLive",
        limit=10,
        offset=0
    )
    assert len(results) == 1
    assert results[0]["rule_id"] == "NavigationStuckLive"


@pytest.mark.anyio
async def test_api_entity_timeline(mock_warehouse):
    # Mock events returned
    mock_events = [
        EventRecord(
            run_id="run-123",
            tick=5,
            event_type="move",
            event_category="movement",
            severity="INFO",
            entity_id="hero1",
            message="hero moved",
            created_at="2026-05-20T10:00:05Z",
            payload_json="{}"
        )
    ]
    mock_warehouse.query_events.return_value = mock_events

    # Mock anomalies returned (will be filtered by the route for matching entity ID)
    mock_anomalies = [
        AnomalyRecord(
            run_id="run-123",
            rule_id="NavigationStuckLive",
            severity="WARNING",
            domain="movement",
            tick_start=10,
            tick_end=15,
            affected_entity_count=1,
            message="hero1 is stuck in corner",
            evidence_json='{"entity_id": "hero1"}'
        ),
        AnomalyRecord(
            run_id="run-123",
            rule_id="NavigationStuckLive",
            severity="WARNING",
            domain="movement",
            tick_start=20,
            tick_end=25,
            affected_entity_count=1,
            message="hero2 is stuck in corner",
            evidence_json='{"entity_id": "hero2"}'
        )
    ]
    mock_warehouse.query_anomalies.return_value = mock_anomalies

    results = await get_entity_timeline(
        run_id="run-123",
        entity_id="hero1"
    )
    
    # Combined, sorted timeline should have 1 event and 1 matching anomaly
    assert len(results) == 2
    assert results[0]["type"] == "event"
    assert results[0]["tick"] == 5
    assert results[1]["type"] == "anomaly"
    assert results[1]["tick"] == 10
    assert results[1]["details"]["entity_id"] == "hero1"


@pytest.mark.anyio
async def test_api_metric_trend(mock_warehouse):
    mock_trends = [
        MetricWindowRecord(
            run_id="run-123",
            window_start_tick=0,
            window_end_tick=10,
            tick_compute_ms_avg=5.5,
            tick_compute_ms_p95=8.0,
            memory_rss_bytes_avg=102400.0,
            memory_rss_bytes_max=204800.0,
            alive_entities_avg=10.0,
            gold_total_avg=500.0,
            event_count=100,
            hard_law_violation_count=0,
            metrics_json="{}"
        )
    ]
    mock_warehouse.query_metric_windows.return_value = mock_trends

    results = await get_metric_trend(
        run_id="run-123",
        limit=10,
        offset=0
    )
    assert len(results) == 1
    assert results[0]["window_start_tick"] == 0
    assert results[0]["tick_compute_ms_avg"] == 5.5


@pytest.mark.anyio
async def test_api_security_sanitization(mock_warehouse):
    # Path traversal patterns should raise HTTPException with 400 status code
    with pytest.raises(HTTPException) as exc:
        await search_events(run_id="../../etc/passwd")
    assert exc.value.status_code == 400
    assert "Invalid identifier security warning" in exc.value.detail
