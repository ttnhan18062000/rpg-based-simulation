"""
Phase 22 — BehaviorWorker post-run JSONL integration tests.

Tests verify:
- Worker can process a simulation_events.jsonl file post-run.
- Worker produces correct BehaviorEvents from JSONL input.
- Worker writes behavior_events.jsonl artifact correctly.
- Worker handles missing/corrupt JSONL gracefully (no crash).
- Worker failure does not affect simulation engine (isolation test).
"""
from __future__ import annotations

import json
import time
import threading
from pathlib import Path

import pytest

from src.observability.behavior.normalizer import BehaviorEventNormalizer
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.behavior.worker import BehaviorWorker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_events_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _make_movement_event_dict(tick: int = 1, entity_id: int = 1) -> dict:
    return {
        "event_id": f"evt_move_{tick}_{entity_id}",
        "event_type": "movement",
        "event_category": "movement",
        "tick": tick,
        "severity": "INFO",
        "source_system": "locomotion_system",
        "message": f"Entity {entity_id} moved",
        "entity_id": entity_id,
        "run_id": "run_test",
        "start_pos": [0.0, 0.0],
        "end_pos": [1.0, 1.0],
        "payload": {},
    }


def _make_combat_event_dict(tick: int = 2, entity_id: int = 2) -> dict:
    return {
        "event_id": f"evt_combat_{tick}_{entity_id}",
        "event_type": "combat_damage",
        "event_category": "combat",
        "tick": tick,
        "severity": "INFO",
        "source_system": "combat_system",
        "message": f"Entity {entity_id} took damage",
        "entity_id": entity_id,
        "run_id": "run_test",
        "damage": 10,
        "is_lethal": False,
        "payload": {"is_lethal": False, "attacker_id": 99},
    }


def _make_quest_event_dict(status: str = "progress", tick: int = 3, entity_id: int = 1) -> dict:
    return {
        "event_id": f"evt_quest_{tick}_{entity_id}",
        "event_type": "quest_event",
        "event_category": "quest",
        "tick": tick,
        "severity": "INFO",
        "source_system": "quest_system",
        "message": f"Entity {entity_id} quest {status}",
        "entity_id": entity_id,
        "run_id": "run_test",
        "quest_id": "q_001",
        "status": status,
        "progress_delta": 0.1,
        "payload": {"status": status},
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBehaviorWorkerFromJsonl:

    def test_behavior_worker_can_process_jsonl_post_run(self, tmp_path):
        """Worker must process a JSONL file and produce BehaviorEvents."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        _write_events_jsonl(jsonl_path, [
            _make_movement_event_dict(tick=1, entity_id=1),
            _make_combat_event_dict(tick=2, entity_id=2),
            _make_quest_event_dict(status="progress", tick=3, entity_id=1),
        ])

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)
        results = worker.process_jsonl(jsonl_path)

        assert len(results) == 3
        categories = {be.behavior_category for be in results}
        assert "movement" in categories
        assert "combat" in categories
        assert "quest" in categories

    def test_worker_writes_behavior_events_jsonl(self, tmp_path):
        """Worker must write behavior_events.jsonl artifact."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        output_path = tmp_path / "behavior_events.jsonl"
        _write_events_jsonl(jsonl_path, [
            _make_movement_event_dict(),
            _make_combat_event_dict(),
        ])

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)
        results = worker.process_jsonl(jsonl_path, output_path=output_path)

        # Output file must exist
        assert output_path.exists()
        lines = output_path.read_text().strip().split("\n")
        assert len(lines) == 2

        # Each line must be valid JSON with expected fields
        for line in lines:
            data = json.loads(line)
            assert "behavior_category" in data
            assert "behavior_family" in data
            assert "tick" in data
            assert "run_id" in data

    def test_worker_handles_missing_jsonl_gracefully(self, tmp_path):
        """Worker must not crash when JSONL file does not exist."""
        missing_path = tmp_path / "nonexistent.jsonl"
        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)

        # Should not raise
        results = worker.process_jsonl(missing_path)
        assert results == ()
        # Worker health should remain HEALTHY (file not found is not a crash)
        # (it logs a warning but doesn't set DEGRADED)

    def test_worker_skips_corrupt_lines(self, tmp_path):
        """Corrupt JSONL lines must be skipped; valid lines still processed."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        with open(jsonl_path, "w") as f:
            f.write(json.dumps(_make_movement_event_dict(tick=1)) + "\n")
            f.write("not valid json !!!\n")  # corrupt line
            f.write(json.dumps(_make_combat_event_dict(tick=2)) + "\n")

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)
        results = worker.process_jsonl(jsonl_path)

        # Should process valid lines; corrupt line is skipped
        assert len(results) == 2

    def test_worker_source_event_ids_are_linked(self, tmp_path):
        """Produced BehaviorEvents must link the source raw event ID."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        event = _make_movement_event_dict(tick=5, entity_id=3)
        event["event_id"] = "evt_link_test"
        _write_events_jsonl(jsonl_path, [event])

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)
        results = worker.process_jsonl(jsonl_path)

        assert len(results) == 1
        assert "evt_link_test" in results[0].source_event_ids

    def test_worker_output_fn_called_for_each_behavior_event(self, tmp_path):
        """Output callback must be invoked for each produced BehaviorEvent."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        _write_events_jsonl(jsonl_path, [
            _make_movement_event_dict(tick=1),
            _make_quest_event_dict(status="started", tick=2),
        ])

        collected = []
        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx, output_fn=collected.append)
        worker.process_jsonl(jsonl_path)

        assert len(collected) == 2

    def test_worker_failure_does_not_affect_engine(self, tmp_path):
        """
        Simulates a failing output_fn to verify worker degrades gracefully.
        The caller (engine proxy) must not raise.
        """
        jsonl_path = tmp_path / "simulation_events.jsonl"
        _write_events_jsonl(jsonl_path, [_make_movement_event_dict()])

        def _failing_output(be):
            raise RuntimeError("Downstream service down")

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx, output_fn=_failing_output)

        # Must not propagate the exception
        results = worker.process_jsonl(jsonl_path)

        # Health degrades but no exception escapes
        assert worker.health_status == "DEGRADED"

    def test_worker_health_tracks_processed_count(self, tmp_path):
        """Worker health must track how many events were processed."""
        jsonl_path = tmp_path / "simulation_events.jsonl"
        _write_events_jsonl(jsonl_path, [
            _make_movement_event_dict(tick=1),
            _make_combat_event_dict(tick=2),
        ])

        ctx = BehaviorNormalizationContext.minimal("run_test")
        worker = BehaviorWorker(context=ctx)
        worker.process_jsonl(jsonl_path)

        assert worker.health.processed_count >= 2
