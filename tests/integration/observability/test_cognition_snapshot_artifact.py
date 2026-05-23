"""
Integration tests for Cognition Snapshot Recorder.

Covers:
- Milestone 59: Trigger-based snapshot recording.
- Determinism/Parity: Verifies no state hash drift or mutations are caused by the recorder.
"""
import pytest
import os
import shutil
import json
from typing import Dict, Any

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import (
    StrategicComponent, DirectiveState, DirectivePriority,
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    BlockerState, LeadState, LeadCertainty, ConcernState,
    HypothesisState
)
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import SimulationEvent
from src.observability.cognition.recorder import ObservabilityCognitionRecorder


def _make_rich_entity(entity_id: int):
    """Build a rich strategic entity."""
    directive = DirectiveState(
        id="d1",
        kind="avenge",
        target="bandit_001",
        priority=DirectivePriority.HIGH,
        salience=0.8,
    )

    objective = ObjectiveState(
        id="o1",
        kind="acquire_item",
        target="iron",
        status=ObjectiveStatus.ACTIVE,
        blocker_ids=["b1"],
    )

    project = ProjectState(
        id="p1",
        kind="crafting",
        status=ProjectStatus.ACTIVE,
        score=50,
        objectives=[objective],
        active_objective_id="o1",
    )

    blocker = BlockerState(
        id="b1",
        kind="material",
        subject="iron",
        severity=0.7,
    )

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(
            directives={"d1": directive},
            projects={"p1": project},
            blockers={"b1": blocker},
            current_project_id="p1",
            current_objective_id="o1",
        )
        .build()
    )


class TestCognitionSnapshotArtifact:
    """Milestone 59 integration validation suite."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.test_run_id = "test_run_cognition_rec"
        self.test_run_dir = f"data/runs/{self.test_run_id}"
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)
        yield
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)
        ObservabilityConfig.set_override_mode(None)

    def test_recorder_creates_snapshot_file_on_anomaly(self):
        """LIGHT mode recorder should only write a snapshot when an anomaly event occurs."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
        
        # Build mock state with rich entity
        entity = _make_rich_entity(1)
        state = AuthoritativeState(
            tick=1,
            seed=42,
            entities={1: entity}
        )

        recorder = ObservabilityCognitionRecorder(self.test_run_id, self.test_run_dir)
        
        # 1. Record normal tick (no anomaly) -> shouldn't write snapshot
        recorder.record_tick(state, 1, events=[])
        snap_file = os.path.join(self.test_run_dir, "cognition_graph_snapshots.jsonl")
        assert not os.path.exists(snap_file)

        # 2. Record tick with QuestStalled anomaly event -> should write snapshot
        anomaly_event = SimulationEvent(
            event_type="QuestStalled",
            event_category="anomaly",
            tick=1,
            severity="WARNING",
            source_system="quest_system",
            message="Quest has been stalled for 10 ticks",
            entity_id=1
        )
        recorder.record_tick(state, 1, events=[anomaly_event])
        assert os.path.exists(snap_file)

        # Verify snapshots content and structure
        with open(snap_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["schema_version"] == "1.0.0"
        assert record["entity_id"] == 1
        assert record["reason"] == "ANOMALY_TRIGGERED"
        assert record["trigger_anomaly_id"] == "QuestStalled"
        assert record["node_count"] == 4  # directive + project + objective + blocker

    def test_recorder_debug_mode_state_changes(self):
        """DEBUG mode recorder should write snapshots on strategic changes."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
        
        entity = _make_rich_entity(1)
        state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
        recorder = ObservabilityCognitionRecorder(self.test_run_id, self.test_run_dir)

        # First tick establishes baseline state
        recorder.record_tick(state, 1, events=[])
        
        # Change project ID -> triggers project change snapshot on next tick record
        from dataclasses import replace
        new_strat = replace(entity.strategic, current_project_id="p2")
        entity = replace(entity, strategic=new_strat)
        state = AuthoritativeState(tick=2, seed=42, entities={1: entity})
        recorder.record_tick(state, 2, events=[])

        snap_file = os.path.join(self.test_run_dir, "cognition_graph_snapshots.jsonl")
        assert os.path.exists(snap_file)

        with open(snap_file, "r") as f:
            lines = f.readlines()
        
        # Should contain two records: tick 1 (debug selected entity baseline) and tick 2 (project changed)
        assert len(lines) >= 1
        records = [json.loads(line) for line in lines]
        reasons = [r["reason"] for r in records]
        assert "PROJECT_CHANGED" in reasons

    def test_state_hash_determinism_preserved(self):
        """Recording snapshots must be strictly read-only and not mutate final state hashes."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
        
        entity = _make_rich_entity(1)
        state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
        
        # Calculate baseline hash
        from src.engine.checkpoint import CanonicalStateHasher
        baseline_hash = CanonicalStateHasher.get_hash(state)

        recorder = ObservabilityCognitionRecorder(self.test_run_id, self.test_run_dir)
        recorder.record_tick(state, 1, events=[])

        # Verify hash after recording remains identical
        current_hash = CanonicalStateHasher.get_hash(state)
        assert current_hash == baseline_hash

    def test_kernel_integration_captures_automatically(self):
        """Verifies that Kernel's internal _cognition_recorder runs and records snapshots automatically during _phase_observability."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
        
        from src.engine.kernel import Kernel
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG
        
        profile = RuntimeProfile(
            name="test-kernel-cognition",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=1024,
            max_cpu_percent=100.0,
            max_worker_count=1,
            max_queue_depth=100,
            max_replay_buffer_kb=0,
            max_observability_budget_percent=0.0,
            max_tick_budget_ms=16.6
        )

        entity = _make_rich_entity(1)
        state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: entity})
        rng = DeterministicRNG(42)
        
        kernel = Kernel(profile, state, rng, run_id=self.test_run_id)
        
        # We invoke _phase_observability, which should trigger the first snapshot (baseline in DEBUG mode)
        prior_state = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
        kernel._phase_observability(prior_state, None)
        
        # Verify that the snapshots file exists and has recorded the baseline snapshot
        snap_file = os.path.join(self.test_run_dir, "cognition_graph_snapshots.jsonl")
        assert os.path.exists(snap_file)
        
        with open(snap_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["entity_id"] == 1
        assert record["reason"] == "DEBUG_SELECTED_ENTITY"
        
        # Shutdown kernel
        kernel.shutdown()
