import os
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest
from src.observability.reporting.retention import RetentionPolicy, RetentionManager

def test_behavior_artifact_paths_resolve():
    repo = RunArtifactRepository(base_dir="/tmp/test_runs")
    
    # Check all required keys resolve
    keys = [
        "behavior_events",
        "behavior_timelines",
        "behavior_episodes",
        "behavior_metric_windows",
        "entity_behavior_scorecards",
        "run_behavior_scorecard",
        "behavior_findings",
        "behavior_insights",
        "cohort_behavior_report",
        "run_behavior_comparison"
    ]
    for key in keys:
        path = repo.resolve_path("run_123", key)
        assert path.endswith(f"{key}.json" if not key.endswith("s") and not "window" in key and not "finding" in key else f"{key}.jsonl" if "timeline" not in key and "insight" not in key and "report" not in key and "comparison" not in key and "scorecard" not in key else f"{key}.json" if "scorecard" in key and not key.startswith("entity") else f"{key}.jsonl" if "scorecard" in key else f"{key}.json")

def test_old_run_without_behavior_artifacts_still_loads():
    # Verify retention policy handles old runs
    policy = RetentionPolicy()
    manifest = RunManifest(
        run_id="old_run_1",
        scenario_name="test",
        scenario_type="test",
        seed=42,
        observability_mode="standard",
        started_at="2026-05-29T12:00:00Z",
        ticks_requested=100,
        ticks_completed=100,
        status="COMPLETED"
    )
    category, reason, days = policy.classify_run(manifest, "/tmp/non_existent_dir")
    assert category == "recent_run"
    assert days == 7
