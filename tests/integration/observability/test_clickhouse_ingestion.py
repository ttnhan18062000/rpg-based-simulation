import os
import json
import pytest

from src.observability.warehouse.clickhouse import ClickHouseWarehouseAdapter
from src.observability.warehouse.registry import WarehouseSchemaRegistry
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.observability.sweeper import RunSetManifest
from src.observability.config import ObservabilityConfig

# 1. Establish live ClickHouse availability check
clickhouse_available = False
try:
    import clickhouse_connect
    # Attempt ping
    client = clickhouse_connect.get_client(host="127.0.0.1", port=8123, password="clickhouse")
    client.ping()
    clickhouse_available = True
    client.close()
except Exception:
    clickhouse_available = False

pytestmark = pytest.mark.skipif(
    not clickhouse_available,
    reason="Local ClickHouse server is not running or unreachable on 127.0.0.1:8123."
)


@pytest.fixture
def clickhouse_env():
    """Configures environment to point to our test ClickHouse container instance."""
    import os
    from unittest.mock import patch
    with patch.dict(os.environ, {
        "SIM_WAREHOUSE_BACKEND": "clickhouse",
        "SIM_WAREHOUSE_CLICKHOUSE_HOST": "127.0.0.1",
        "SIM_WAREHOUSE_CLICKHOUSE_PORT": "8123",
        "SIM_WAREHOUSE_CLICKHOUSE_DATABASE": "test_ingestion_db",
        "SIM_WAREHOUSE_CLICKHOUSE_USERNAME": "default",
        "SIM_WAREHOUSE_CLICKHOUSE_PASSWORD": "clickhouse",
        "SIM_WAREHOUSE_CLICKHOUSE_SECURE": "False",
        "SIM_WAREHOUSE_CLICKHOUSE_BATCH_SIZE": "100"
    }):
        yield


def test_live_clickhouse_ingestion_flow(clickhouse_env, tmp_path):
    """
    Verifies full ClickHouse warehouse life-cycle:
    Schema DDL initialization -> Run Ingestion -> Idempotency Checksum Skip -> Force Overwrite -> Queries.
    """
    # 1. Setup run directories and files
    run_id = "test_run_clickhouse_123"
    base_dir = tmp_path / "runs"
    run_repo = RunArtifactRepository(base_dir=str(base_dir))
    
    manifest = RunManifest(
        run_id=run_id,
        scenario_name="arena_combat",
        scenario_type="combat",
        seed=999,
        observability_mode="LIGHT",
        started_at="2026-05-20T11:00:00Z",
        ticks_requested=5,
        ticks_completed=5,
        status="COMPLETED"
    )
    run_repo.create_run(run_id, manifest)
    
    # Write events JSONL
    events_path = run_repo.resolve_path(run_id, "events")
    with open(events_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "tick": 1,
            "event_type": "move",
            "event_category": "movement",
            "severity": "INFO",
            "entity_id": "hero_solo",
            "message": "Hero walked east",
            "payload": {"x": 10.0}
        }) + "\n")
        f.write(json.dumps({
            "tick": 2,
            "event_type": "combat_strike",
            "event_category": "combat",
            "severity": "CRITICAL",
            "entity_id": "hero_solo",
            "message": "Hero hit goblin for 40 damage",
            "payload": {"damage": 40.0}
        }) + "\n")

    # Write anomalies list JSON
    anomalies_path = run_repo.resolve_path(run_id, "anomalies")
    with open(anomalies_path, "w", encoding="utf-8") as f:
        json.dump([
            {
                "rule_id": "rule_gold_leak",
                "severity": "WARNING",
                "domain": "economy",
                "tick_start": 1,
                "tick_end": 2,
                "affected_entity_count": 0,
                "message": "Abnormal gold balance",
                "evidence": {}
            }
        ], f)
        
    # Write violations JSONL
    violations_path = run_repo.resolve_path(run_id, "violations")
    with open(violations_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "tick": 2,
            "violation_type": "SovereigntyViolation",
            "severity": "CRITICAL",
            "actor_id": "hero_solo",
            "message": "Sovereignty rule breached",
            "evidence": {}
        }) + "\n")
        
    # Write metrics JSONL
    metrics_path = os.path.join(run_repo.base_dir, run_id, "metric_windows.jsonl")
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "window_start_tick": 0,
            "window_end_tick": 4,
            "tick_compute_ms_avg": 12.5,
            "tick_compute_ms_p95": 14.8,
            "memory_rss_bytes_avg": 500000.0,
            "memory_rss_bytes_max": 510000.0,
            "alive_entities_avg": 2.0,
            "gold_total_avg": 100.0,
            "event_count": 2,
            "hard_law_violation_count": 1,
            "metrics": {}
        }) + "\n")

    # 2. Initialize schema
    adapter = ClickHouseWarehouseAdapter(run_repo=run_repo)
    assert adapter.health().connected is True
    
    # Drops DB to start fresh using a temporary connection
    temp_client = clickhouse_connect.get_client(host="127.0.0.1", port=8123, password="clickhouse", database="default")
    temp_client.command("DROP DATABASE IF EXISTS test_ingestion_db")
    temp_client.close()
    
    adapter.init_schema()

    # 3. Perform Live Ingestion
    res = adapter.ingest_run(run_id, dry_run=False)
    assert res.errors == []
    assert res.status == "COMPLETED"
    assert res.records_ingested["runs"] == 1
    assert res.records_ingested["events"] == 2
    assert res.records_ingested["anomalies"] == 1
    assert res.records_ingested["violations"] == 1
    assert res.records_ingested["metrics"] == 1

    # 4. Perform Duplicate Ingestion (Idempotency) -> Should skip!
    res_skipped = adapter.ingest_run(run_id, dry_run=False)
    assert res_skipped.status == "SKIPPED"
    assert res_skipped.records_ingested["runs"] == 0
    assert res_skipped.records_ingested["events"] == 0

    # 5. Modify manifest slightly (e.g. status) to trigger different checksum without force -> Should fail!
    with open(run_repo.resolve_path(run_id, "manifest"), "r") as f:
        manifest_dict = json.load(f)
    manifest_dict["status"] = "FAILED"
    with open(run_repo.resolve_path(run_id, "manifest"), "w") as f:
        json.dump(manifest_dict, f)
        
    with pytest.raises(ValueError) as exc:
        adapter.ingest_run(run_id, dry_run=False)
    assert "force=True" in str(exc.value)

    # 6. Re-run with force=True -> Should overwrite successfully!
    res_forced = adapter.ingest_run(run_id, dry_run=False, force=True)
    assert res_forced.status == "COMPLETED"
    assert res_forced.records_ingested["runs"] == 1

    # 7. Query Runs & Verification
    runs = adapter.query_runs({"scenario_name": "arena_combat"})
    assert len(runs) == 1
    assert runs[0].run_id == run_id
    assert runs[0].status == "FAILED"

    # 8. Query Events by Entity ID
    events = adapter.query_events({"entity_id": "hero_solo"})
    assert len(events) == 2
    assert events[0].event_type == "move"
    assert events[1].event_type == "combat_strike"
    assert events[1].severity == "CRITICAL"

    # Clean up database
    adapter.close()
    temp_client = clickhouse_connect.get_client(host="127.0.0.1", port=8123, password="clickhouse", database="default")
    temp_client.command("DROP DATABASE IF EXISTS test_ingestion_db")
    temp_client.close()
