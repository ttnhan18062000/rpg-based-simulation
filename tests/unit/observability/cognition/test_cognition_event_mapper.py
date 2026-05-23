"""
Unit tests for the CognitionEventMapper mapping.
"""
import pytest
from src.observability.cognition.event_mapper import CognitionEventMapper
from src.observability.cognition.diff_builder import CognitionGraphDiffBuilder
from src.observability.cognition.schema import build_snapshot_record


class TestCognitionEventMapper:
    """Milestone 61: Event mapping unit checks."""

    @pytest.fixture
    def mapper(self):
        return CognitionEventMapper(detour_loop_threshold=2)

    def test_project_changed_emits_event(self, mapper):
        snap_a = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="PROJECT_CHANGED",
            nodes=[], edges=[], current_project_id="proj_old",
        )
        snap_b = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="PROJECT_CHANGED",
            nodes=[], edges=[], current_project_id="proj_new",
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "PROJECT_CHANGED", snap_a, snap_b)
        events = mapper.map_diff_to_events(diff, snap_a, snap_b)

        assert len(events) == 1
        event = events[0]
        assert event.event_type == "StrategicProjectChanged"
        assert event.payload["previous_project_id"] == "proj_old"
        assert event.payload["new_project_id"] == "proj_new"
        assert event.entity_id == 42
        assert "proj_old to proj_new" in event.message

    def test_objective_changed_emits_event(self, mapper):
        snap_a = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="OBJECTIVE_CHANGED",
            nodes=[], edges=[], current_objective_id="obj_old",
        )
        snap_b = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="OBJECTIVE_CHANGED",
            nodes=[], edges=[], current_objective_id="obj_new",
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "OBJECTIVE_CHANGED", snap_a, snap_b)
        events = mapper.map_diff_to_events(diff, snap_a, snap_b)

        assert len(events) == 1
        event = events[0]
        assert event.event_type == "StrategicObjectiveChanged"
        assert event.payload["previous_objective_id"] == "obj_old"
        assert event.payload["new_objective_id"] == "obj_new"

    def test_blocker_added_and_resolved(self, mapper):
        snap_empty = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="BLOCKER_CHANGED",
            nodes=[], edges=[],
        )

        blocker = {
            "node_id": "blocker_01",
            "kind": "blocker",
            "label": "stuck_mud",
            "metadata": {"kind": "environment"},
        }
        snap_blocked = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="BLOCKER_CHANGED",
            nodes=[blocker], edges=[],
        )

        # 1. Test Added blocker
        diff_add = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "BLOCKER_CHANGED", snap_empty, snap_blocked)
        events_add = mapper.map_diff_to_events(diff_add, snap_empty, snap_blocked)

        assert len(events_add) == 1
        assert events_add[0].event_type == "StrategicBlockerAdded"
        assert events_add[0].payload["blocker_id"] == "blocker_01"
        assert events_add[0].payload["blocker_kind"] == "environment"

        # 2. Test Resolved blocker
        diff_resolve = CognitionGraphDiffBuilder.compute_diff("run_1", 3, 42, "BLOCKER_CHANGED", snap_blocked, snap_empty)
        events_resolve = mapper.map_diff_to_events(diff_resolve, snap_blocked, snap_empty)

        assert len(events_resolve) == 1
        assert events_resolve[0].event_type == "StrategicBlockerResolved"
        assert events_resolve[0].payload["blocker_id"] == "blocker_01"

    def test_exhausted_lead_emits_event(self, mapper):
        lead = {"node_id": "lead_01", "kind": "lead", "label": "Search Cave", "metadata": {}}
        snap_lead = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="LEAD_CHANGED",
            nodes=[lead], edges=[],
        )
        snap_empty = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="LEAD_CHANGED",
            nodes=[], edges=[],
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "LEAD_CHANGED", snap_lead, snap_empty)
        events = mapper.map_diff_to_events(diff, snap_lead, snap_empty)

        assert len(events) == 1
        assert events[0].event_type == "StrategicLeadExhausted"
        assert events[0].payload["lead_id"] == "lead_01"

    def test_concern_raised_emits_event(self, mapper):
        concern = {"node_id": "concern_01", "kind": "concern", "label": "Low Health", "metadata": {}}
        snap_empty = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="CONCERN_CHANGED",
            nodes=[], edges=[],
        )
        snap_concern = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="CONCERN_CHANGED",
            nodes=[concern], edges=[],
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "CONCERN_CHANGED", snap_empty, snap_concern)
        events = mapper.map_diff_to_events(diff, snap_empty, snap_concern)

        assert len(events) == 1
        assert events[0].event_type == "StrategicConcernRaised"
        assert events[0].payload["concern_id"] == "concern_01"

    def test_overload_detected_emits_event(self, mapper):
        snap_a = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="OVERLOAD_CHANGED",
            nodes=[], edges=[], overload_source=None,
        )
        snap_b = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="OVERLOAD_CHANGED",
            nodes=[], edges=[], overload_source="too_many_leads",
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "OVERLOAD_CHANGED", snap_a, snap_b)
        events = mapper.map_diff_to_events(diff, snap_a, snap_b)

        assert len(events) == 1
        assert events[0].event_type == "StrategicOverloadDetected"
        assert events[0].payload["overload_source"] == "too_many_leads"

    def test_detour_created_and_loop_suspected(self, mapper):
        # Initial empty state
        snap_empty = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="ANOMALY_TRIGGERED",
            nodes=[], edges=[],
        )

        # State 1: blocker added and detour project created
        blocker = {"node_id": "blocker_99", "kind": "blocker", "label": "No Pickaxe", "metadata": {}}
        detour_proj = {"node_id": "proj_detour_blocker_99_tick_1", "kind": "project", "label": "Detour", "metadata": {}}
        obj = {"node_id": "obj_detour", "kind": "objective", "label": "Forge", "metadata": {}}
        snap_detour1 = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="ANOMALY_TRIGGERED",
            nodes=[blocker, detour_proj, obj],
            edges=[
                {"source_id": "proj_detour_blocker_99_tick_1", "target_id": "obj_detour", "kind": "drives"},
                {"source_id": "blocker_99", "target_id": "obj_detour", "kind": "blocks"},
            ],
        )

        diff1 = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "ANOMALY_TRIGGERED", snap_empty, snap_detour1)
        events1 = mapper.map_diff_to_events(diff1, snap_empty, snap_detour1)

        # Should emit BlockerAdded and DetourCreated
        event_types = [e.event_type for e in events1]
        assert "StrategicBlockerAdded" in event_types
        assert "StrategicDetourCreated" in event_types
        detour_event = next(e for e in events1 if e.event_type == "StrategicDetourCreated")
        assert detour_event.payload["blocker_id"] == "blocker_99"
        assert detour_event.payload["detour_project_id"] == "proj_detour_blocker_99_tick_1"

        # State 2: Second detour project created on same blocker (loop threshold is 2)
        detour_proj_2 = {"node_id": "proj_detour_blocker_99_tick_2", "kind": "project", "label": "Detour Again", "metadata": {}}
        snap_detour2 = build_snapshot_record(
            run_id="run_1", tick=3, entity_id=42, reason="ANOMALY_TRIGGERED",
            nodes=[blocker, detour_proj, detour_proj_2, obj],
            edges=[
                {"source_id": "proj_detour_blocker_99_tick_1", "target_id": "obj_detour", "kind": "drives"},
                {"source_id": "proj_detour_blocker_99_tick_2", "target_id": "obj_detour", "kind": "drives"},
                {"source_id": "blocker_99", "target_id": "obj_detour", "kind": "blocks"},
            ],
        )

        diff2 = CognitionGraphDiffBuilder.compute_diff("run_1", 3, 42, "ANOMALY_TRIGGERED", snap_detour1, snap_detour2)
        events2 = mapper.map_diff_to_events(diff2, snap_detour1, snap_detour2)

        # Should emit DetourCreated AND DetourLoopSuspected!
        event_types_2 = [e.event_type for e in events2]
        assert "StrategicDetourCreated" in event_types_2
        assert "StrategicDetourLoopSuspected" in event_types_2
        loop_event = next(e for e in events2 if e.event_type == "StrategicDetourLoopSuspected")
        assert loop_event.payload["blocker_id"] == "blocker_99"
        assert loop_event.payload["detour_count"] == 2

    def test_metadata_only_change_no_high_severity_event(self, mapper):
        """Verify that minor metadata updates that do not shift strategy emit no high-severity events."""
        snap_a = build_snapshot_record(
            run_id="run_1", tick=1, entity_id=42, reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "p1", "kind": "project", "label": "Mining", "metadata": {"custom": "v1"}}],
            edges=[],
        )
        snap_b = build_snapshot_record(
            run_id="run_1", tick=2, entity_id=42, reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "p1", "kind": "project", "label": "Mining", "metadata": {"custom": "v2"}}],
            edges=[],
        )

        diff = CognitionGraphDiffBuilder.compute_diff("run_1", 2, 42, "ANOMALY_TRIGGERED", snap_a, snap_b)
        events = mapper.map_diff_to_events(diff, snap_a, snap_b)

        # No major project change, blocker add, overload, detour etc. occurred.
        assert not events
