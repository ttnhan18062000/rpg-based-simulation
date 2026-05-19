import os
import json
import pytest
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.metric_recorder import MetricWindowRecord
from src.observability.anomaly.pipeline import AnalysisPipeline, AnalysisInputLoader
from src.observability.anomaly.rules_engine import RuleEngine

def test_pipeline_rule_engine_integration(tmp_path):
    repo = RunArtifactRepository(base_dir=str(tmp_path))
    run_id = "run_integration_rules"

    # Create run directory
    run_dir = os.path.join(str(tmp_path), run_id)
    os.makedirs(run_dir, exist_ok=True)

    # 1. Create Manifest
    manifest = RunManifest(
        run_id=run_id,
        status="COMPLETED",
        ticks_completed=200,
        scenario_name="test_scenario",
        scenario_type="resource_economy",
        seed=42,
        observability_mode="LIGHT",
        started_at="2026-05-19T00:00:00Z",
        ticks_requested=200
    )
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        f.write(manifest.model_dump_json(indent=2))

    # 2. Create Events (Quest started event that is stalled)
    events_data = [
        {
            "tick": 10, "event_type": "quest_event", "event_category": "quest", "entity_id": 99,
            "severity": "WARNING", "message": "Quest started", "source_system": "quest_system",
            "payload": {"quest_id": "STALL_Q", "status": "started"}
        },
    ]
    with open(os.path.join(run_dir, "simulation_events.jsonl"), "w", encoding="utf-8") as f:
        for ev in events_data:
            f.write(json.dumps(ev) + "\n")

    # 3. Create Metric Windows (ResourceProductionZero positive scenario)
    windows_data = [
        {
            "run_id": run_id,
            "window_start_tick": 0,
            "window_end_tick": 100,
            "ticks_observed": 100,
            "alive_entities_avg": 2.0,
            "active_entities_avg": 2.0,
            "gold_total_avg": 0.0,
            "tick_compute_ms_avg": 1.0,
            "tick_compute_ms_p95": 2.0,
            "memory_rss_bytes_avg": 1024.0,
            "memory_rss_bytes_max": 2048.0,
            "hard_law_violation_count": 0,
            "event_count": 5,
            "anomaly_candidate_count": 0,
            "governor_mode_dominant": "NORMAL"
        },
        {
            "run_id": run_id,
            "window_start_tick": 100,
            "window_end_tick": 200,
            "ticks_observed": 100,
            "alive_entities_avg": 2.0,
            "active_entities_avg": 2.0,
            "gold_total_avg": 0.0,
            "tick_compute_ms_avg": 1.0,
            "tick_compute_ms_p95": 2.0,
            "memory_rss_bytes_avg": 1024.0,
            "memory_rss_bytes_max": 2048.0,
            "hard_law_violation_count": 0,
            "event_count": 5,
            "anomaly_candidate_count": 0,
            "governor_mode_dominant": "NORMAL"
        }
    ]
    with open(os.path.join(run_dir, "metric_windows.jsonl"), "w", encoding="utf-8") as f:
        for w in windows_data:
            f.write(json.dumps(w) + "\n")

    # 4. Create config directory with custom thresholds if needed
    os.makedirs(os.path.join("config", "observability"), exist_ok=True)
    config_file_path = os.path.join("config", "observability", "rules_core.json")
    
    # Save a temporary config override that disables ResourceProductionZero for verification
    config_override = {
        "ResourceProductionZero": {
            "enabled": False,
            "thresholds": {"window_threshold": 2},
            "scenario_types": ["resource_economy"]
        },
        "QuestStalledBasic": {
            "enabled": True,
            "thresholds": {"tick_threshold": 50}
        }
    }
    with open(config_file_path, "w", encoding="utf-8") as f:
        json.dump(config_override, f, indent=2)

    try:
        pipeline = AnalysisPipeline(repo=repo)
        result = pipeline.run(run_id)

        # Assertions
        assert result.status == "COMPLETED"
        assert result.anomaly_count > 0

        # Load output anomalies.json to verify contents
        anomalies_json_path = repo.resolve_path(run_id, "anomalies")
        assert os.path.exists(anomalies_json_path)
        with open(anomalies_json_path, "r", encoding="utf-8") as f:
            saved_anomalies = json.load(f)

        assert len(saved_anomalies) > 0
        # ResourceProductionZero was disabled in rules_core.json, so it shouldn't produce anomalies
        assert not any(a["rule_name"] == "ResourceProductionZero" for a in saved_anomalies)
        # QuestStalledBasic should be present
        assert any(a["rule_name"] == "QuestStalledBasic" for a in saved_anomalies)

        # Manifest must be ANALYZED
        updated_manifest = repo.read_manifest(run_id)
        assert updated_manifest.status == "ANALYZED"

    finally:
        # Cleanup config file override
        if os.path.exists(config_file_path):
            os.remove(config_file_path)
