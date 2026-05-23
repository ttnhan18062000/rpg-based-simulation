"""
Integration tests for Cognition Diff Builder, Event Mapper, and Recorder integration.

Covers:
- Milestone 61: Verification of CognitionGraphDiffRecord writing and SimulationEvent logging.
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
from src.observability.event_recorder import EventRecorder
from src.observability.cognition.recorder import ObservabilityCognitionRecorder


def _make_base_entity(entity_id: int):
    directive = DirectiveState(
        id="d1",
        kind="avenge",
        target="bandit_001",
        priority=DirectivePriority.HIGH,
        salience=0.8,
    )

    project = ProjectState(
        id="p_main",
        kind="crafting",
        status=ProjectStatus.ACTIVE,
        score=50,
        objectives=[],
    )

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(5.0, 5.0)
        .strategic(
            directives={"d1": directive},
            projects={"p_main": project},
            blockers={},
            current_project_id="p_main",
            current_objective_id=None,
        )
        .build()
    )


class TestCognitionDiffEventsIntegration:
    """Milestone 61 Integration checks."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.test_run_id = "test_run_cognition_diff"
        self.test_run_dir = f"data/runs/{self.test_run_id}"
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)
        yield
        if os.path.exists(self.test_run_dir):
            shutil.rmtree(self.test_run_dir)
        ObservabilityConfig.set_override_mode(None)

    def test_recorder_records_snapshots_diffs_and_events(self):
        ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
        
        # 1. Establish baseline tick
        entity = _make_base_entity(1)
        state_1 = AuthoritativeState(tick=1, seed=42, entities={1: entity})
        
        event_recorder = EventRecorder(run_dir=self.test_run_dir, max_events=100)
        recorder = ObservabilityCognitionRecorder(self.test_run_id, self.test_run_dir)

        # Baseline capture
        recorder.record_tick(state_1, 1, events=[], event_recorder=event_recorder)
        
        snap_file = os.path.join(self.test_run_dir, "cognition_graph_snapshots.jsonl")
        diff_file = os.path.join(self.test_run_dir, "cognition_graph_diffs.jsonl")
        events_file = os.path.join(self.test_run_dir, "simulation_events.jsonl")

        assert os.path.exists(snap_file)
        assert os.path.exists(diff_file)
        # Baseline snapshot diff has no previous snapshot, so added_nodes represents all baseline nodes
        with open(diff_file, "r") as f:
            diff_lines = f.readlines()
        assert len(diff_lines) == 1
        first_diff = json.loads(diff_lines[0])
        assert first_diff["entity_id"] == 1
        assert "p_main" in first_diff["added_nodes"]

        # 2. Trigger strategic transitions on tick 2:
        # - Project shift
        # - Blocker added
        # - Objective added/changed
        from dataclasses import replace
        blocker = BlockerState(id="b_mud", kind="environment", subject="mud", severity=0.8)
        objective = ObjectiveState(id="o_clear", kind="gather", target="wood", status=ObjectiveStatus.ACTIVE, blocker_ids=["b_mud"])
        
        # Spawn detour project for blocker to test Detour events
        detour_proj = ProjectState(
            id="proj_detour_b_mud_tick_2",
            kind="detour",
            status=ProjectStatus.ACTIVE,
            score=60,
            objectives=[objective],
            active_objective_id="o_clear",
        )

        new_strat = replace(
            entity.strategic,
            current_project_id="proj_detour_b_mud_tick_2",
            current_objective_id="o_clear",
            blockers={"b_mud": blocker},
            projects={"p_main": entity.strategic.projects["p_main"], "proj_detour_b_mud_tick_2": detour_proj}
        )
        entity_2 = replace(entity, strategic=new_strat)
        state_2 = AuthoritativeState(tick=2, seed=42, entities={1: entity_2})

        # Record next tick
        recorder.record_tick(state_2, 2, events=[], event_recorder=event_recorder)

        # Check diff file
        with open(diff_file, "r") as f:
            diff_lines = f.readlines()
        assert len(diff_lines) == 2
        second_diff = json.loads(diff_lines[1])
        assert second_diff["current_project_changed"] is True
        assert second_diff["current_objective_changed"] is True
        assert "b_mud" in second_diff["added_nodes"]

        # Shutdown event recorder to flush simulation_events.jsonl
        event_recorder.shutdown()

        # Check simulation events file for mapped strategic events
        assert os.path.exists(events_file)
        with open(events_file, "r") as f:
            event_lines = f.readlines()
        
        events = [json.loads(line) for line in event_lines if line.strip()]
        event_types = [ev["event_type"] for ev in events]

        # Verify emitted event types
        assert "StrategicProjectChanged" in event_types
        assert "StrategicObjectiveChanged" in event_types
        assert "StrategicBlockerAdded" in event_types
        assert "StrategicDetourCreated" in event_types

        # Verify event structures and payload preservation
        proj_event = next(ev for ev in events if ev["event_type"] == "StrategicProjectChanged" and ev["payload"].get("previous_project_id") is not None)
        assert proj_event["payload"]["previous_project_id"] == "p_main"
        assert proj_event["payload"]["new_project_id"] == "proj_detour_b_mud_tick_2"
        assert "shifted from p_main to proj_detour_b_mud_tick_2" in proj_event["message"]

        detour_event = next(ev for ev in events if ev["event_type"] == "StrategicDetourCreated")
        assert detour_event["payload"]["blocker_id"] == "b_mud"
        assert detour_event["payload"]["detour_project_id"] == "proj_detour_b_mud_tick_2"
