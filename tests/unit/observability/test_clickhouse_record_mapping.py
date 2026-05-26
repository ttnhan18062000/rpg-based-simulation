import pytest
import json
import os
from unittest.mock import MagicMock, patch

from src.observability.warehouse.clickhouse import ClickHouseWarehouseAdapter, calculate_checksum
from src.observability.warehouse.models import RunRecord, EventRecord, AnomalyRecord
from src.observability.config import ObservabilityConfig
from src.observability.reporting.artifact_repository import RunArtifactRepository


@pytest.fixture
def mock_clickhouse_connect():
    with patch("src.observability.warehouse.clickhouse.clickhouse_connect") as mock_conn:
        mock_client = MagicMock()
        mock_conn.get_client.return_value = mock_client
        yield mock_conn, mock_client


def test_clickhouse_adapter_initialization(mock_clickhouse_connect):
    mock_conn, mock_client = mock_clickhouse_connect
    
    with patch.object(ObservabilityConfig, "get_clickhouse_host", return_value="127.0.0.99"), \
         patch.object(ObservabilityConfig, "get_clickhouse_port", return_value=9999), \
         patch.object(ObservabilityConfig, "get_clickhouse_database", return_value="test_db"):
        
        adapter = ClickHouseWarehouseAdapter()
        
        assert adapter.host == "127.0.0.99"
        assert adapter.port == 9999
        assert adapter.database == "test_db"
        assert adapter.client is mock_client
        mock_conn.get_client.assert_called_once_with(
            host="127.0.0.99",
            port=9999,
            username="default",
            password="",
            database="test_db",
            secure=False
        )


def test_clickhouse_adapter_health_success(mock_clickhouse_connect):
    _, mock_client = mock_clickhouse_connect
    mock_client.ping.return_value = None
    
    adapter = ClickHouseWarehouseAdapter()
    health = adapter.health()
    
    assert health.connected is True
    assert health.latency_ms >= 0.0
    assert health.error is None
    mock_client.ping.assert_called_once()


def test_clickhouse_adapter_health_failure(mock_clickhouse_connect):
    _, mock_client = mock_clickhouse_connect
    mock_client.ping.side_effect = Exception("Connection refused")
    
    adapter = ClickHouseWarehouseAdapter()
    health = adapter.health()
    
    assert health.connected is False
    assert "Connection refused" in health.error


def test_clickhouse_adapter_init_schema(mock_clickhouse_connect):
    _, mock_client = mock_clickhouse_connect
    
    adapter = ClickHouseWarehouseAdapter()
    adapter.init_schema()
    
    # Verify CREATE TABLE commands are run
    assert mock_client.command.call_count >= 6
    calls = [c[0][0] for c in mock_client.command.call_args_list]
    assert any("CREATE TABLE IF NOT EXISTS runs" in query for query in calls)
    assert any("CREATE TABLE IF NOT EXISTS simulation_events" in query for query in calls)


def test_clickhouse_adapter_query_runs(mock_clickhouse_connect):
    _, mock_client = mock_clickhouse_connect
    
    mock_result = MagicMock()
    mock_result.named_results.return_value = [
        {
            "run_id": "run_test_1",
            "scenario_name": "combat",
            "scenario_type": "standard",
            "seed": 123,
            "status": "COMPLETED",
            "ticks_completed": 100,
            "health_score": 95.5,
            "started_at": "2026-05-20T10:00:00Z",
            "ended_at": "2026-05-20T10:05:00Z",
            "schema_version": "observability_artifact_v1",
            "manifest_json": "{}"
        }
    ]
    mock_client.query.return_value = mock_result
    
    adapter = ClickHouseWarehouseAdapter()
    runs = adapter.query_runs({"scenario_name": "combat", "limit": 5})
    
    assert len(runs) == 1
    assert runs[0].run_id == "run_test_1"
    assert runs[0].health_score == 95.5
    
    mock_client.query.assert_called_once()
    query_str = mock_client.query.call_args[0][0]
    params = mock_client.query.call_args[0][1]
    assert "SELECT * FROM runs" in query_str
    assert "scenario_name = %(scenario_name)s" in query_str
    assert params["scenario_name"] == "combat"
    assert params["limit"] == 5


def test_clickhouse_adapter_query_events(mock_clickhouse_connect):
    _, mock_client = mock_clickhouse_connect
    
    mock_result = MagicMock()
    mock_result.named_results.return_value = [
        {
            "run_id": "run_test_1",
            "tick": 12,
            "event_type": "move",
            "event_category": "movement",
            "severity": "INFO",
            "entity_id": "hero_1",
            "region_id": None,
            "quest_id": None,
            "faction_id": None,
            "message": "Hero moved",
            "payload_json": "{}",
            "created_at": "2026-05-20T10:00:12Z"
        }
    ]
    mock_client.query.return_value = mock_result
    
    adapter = ClickHouseWarehouseAdapter()
    events = adapter.query_events({"run_id": "run_test_1", "limit": 10})
    
    assert len(events) == 1
    assert events[0].event_type == "move"
    assert events[0].entity_id == "hero_1"
    
    mock_client.query.assert_called_once()
    query_str = mock_client.query.call_args[0][0]
    params = mock_client.query.call_args[0][1]
    assert "SELECT * FROM simulation_events" in query_str
    assert params["run_id"] == "run_test_1"


def test_clickhouse_adapter_ingest_run_dry_run(mock_clickhouse_connect, tmp_path):
    _, mock_client = mock_clickhouse_connect
    
    # Construct manifest
    manifest_data = {
        "run_id": "run_test_dry",
        "scenario_name": "combat",
        "scenario_type": "standard",
        "seed": 42,
        "status": "COMPLETED",
        "ticks_completed": 10,
        "health_score": 100.0,
        "started_at": "2026-05-20T12:00:00Z",
        "artifact_schema_version": "observability_artifact_v1"
    }
    
    # Mock resolve_path to point to a temporary test directory
    run_dir = tmp_path / "run_test_dry"
    run_dir.mkdir()
    
    manifest_file = run_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f)
        
    events_file = run_dir / "events.jsonl"
    with open(events_file, "w") as f:
        f.write(json.dumps({"tick": 1, "event_type": "spawn", "message": "Hero spawned", "timestamp": "2026-05-20T12:00:01Z"}) + "\n")
        
    with patch.object(RunArtifactRepository, "resolve_path") as mock_resolve:
        def resolve_side_effect(run_id, file_type):
            if file_type == "manifest":
                return str(manifest_file)
            elif file_type == "events":
                return str(events_file)
            return str(run_dir / f"{file_type}.json")
        mock_resolve.side_effect = resolve_side_effect
        
        adapter = ClickHouseWarehouseAdapter()
        res = adapter.ingest_run("run_test_dry", dry_run=True)
        
        assert res.status == "DRY_RUN"
        assert res.records_ingested["runs"] == 1
        assert res.records_ingested["events"] == 1
        assert not res.errors
        
        # In a dry run, no db insert/query operations are made
        mock_client.query.assert_not_called()
        mock_client.insert.assert_not_called()
