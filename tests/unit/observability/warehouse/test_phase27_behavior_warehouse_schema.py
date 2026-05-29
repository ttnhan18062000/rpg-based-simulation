import os
import json
import pytest
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.warehouse.adapters import LocalWarehouseAdapter

def test_behavior_warehouse_schema_queries(tmp_path):
    # Setup test workspace run dir
    run_id = "run_warehouse_test"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock behavior events
    events = [
        {"tick": 10, "event_id": "e1", "entity_id": "hero1", "category": "combat", "family": "strike", "action": "hit", "subject_type": "monster", "subject_id": "m1", "success": True, "metadata": {}},
        {"tick": 15, "event_id": "e2", "entity_id": "hero1", "category": "quest", "family": "story", "action": "accept", "subject_type": "npc", "subject_id": "n1", "success": True, "metadata": {}}
    ]
    with open(run_dir / "behavior_events.jsonl", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
            
    # Write mock behavior episodes
    episodes = [
        {"episode_id": "ep1", "entity_id": "hero1", "category": "combat", "start_tick": 5, "end_tick": 15, "duration_ticks": 10, "outcome": "SUCCESS", "event_count": 2, "events": []}
    ]
    with open(run_dir / "behavior_episodes.jsonl", "w") as f:
        for ep in episodes:
            f.write(json.dumps(ep) + "\n")

    # Write mock entity scorecards
    scorecards = [
        {"entity_id": "hero1", "total_events": 10, "category_counts": {}, "family_counts": {}, "episode_counts": {}, "episode_outcomes": {}, "total_failures": 1, "total_adaptations": 1, "failure_loop_count": 0, "adaptation_proof_count": 0, "suspicion_score": 0.0, "verdict": "STABLE"}
    ]
    with open(run_dir / "entity_behavior_scorecards.jsonl", "w") as f:
        for sc in scorecards:
            f.write(json.dumps(sc) + "\n")

    # Write mock run scorecard
    run_sc = {"total_events": 100, "total_episodes": 5, "total_failures": 2, "total_adaptations": 3, "entity_count": 1, "verdict_distribution": {}, "category_counts": {}, "family_counts": {}}
    with open(run_dir / "run_behavior_scorecard.json", "w") as f:
        json.dump(run_sc, f)

    # Initialize repository and adapter
    repo = RunArtifactRepository(base_dir=str(tmp_path))
    adapter = LocalWarehouseAdapter(run_repo=repo)

    # Query and assert behavior events
    bev_events = adapter.query_behavior_events({"run_id": run_id})
    assert len(bev_events) == 2
    assert bev_events[0].entity_id == "hero1"
    assert bev_events[0].category == "combat"

    # Query behavior episodes
    bev_episodes = adapter.query_behavior_episodes({"run_id": run_id})
    assert len(bev_episodes) == 1
    assert bev_episodes[0].outcome == "SUCCESS"

    # Query entity scorecards
    entity_scs = adapter.query_entity_behavior_scorecards({"run_id": run_id})
    assert len(entity_scs) == 1
    assert entity_scs[0].verdict == "STABLE"

    # Query run scorecard
    r_sc = adapter.query_run_behavior_scorecards({"run_id": run_id})
    assert len(r_sc) == 1
    assert r_sc[0].total_events == 100
