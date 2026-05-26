import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.core.strategic import ProjectState, ProjectKind, ProjectStatus, ObjectiveState, ObjectiveKind, ObjectiveStatus
from src.observability.cognition.recorder import ObservabilityCognitionRecorder
from src.observability.config import ObservabilityConfig, ObservabilityMode

class MockEventRecorder:
    def __init__(self):
        self.recorded_events = []
    def record(self, event):
        self.recorded_events.append(event)

def test_cognition_causal_trace_enrichment():
    """Verify that StrategicProjectChanged contains enriched causal trace fields."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
    
    try:
        # 1. Setup entities with active strategic projects
        obj = ObjectiveState(
            id="obj_collect",
            kind=ObjectiveKind.REACH_LOCATION,
            target_position=(10.0, 20.0),
            status=ObjectiveStatus.ACTIVE
        )
        proj = ProjectState(
            id="proj_harvest",
            kind=ProjectKind.EXPLORATION,
            status=ProjectStatus.ACTIVE,
            objectives=[obj],
            active_objective_id="obj_collect",
            score=72.5
        )
        
        ent = (V2EntityBuilder(1)
            .kind("HERO")
            .strategic(projects={"proj_harvest": proj}, current_project_id="proj_harvest")
            .task(work_kind="ENTITY_ACT")
            .build())
            
        region = RegionState(id="forest", name="Deep Forest", bounds=(0, 0, 50, 50))
        state = AuthoritativeState(tick=100, seed=42, entities={1: ent}, regions={"forest": region})
        
        recorder = ObservabilityCognitionRecorder(run_id="test_run", run_dir="tmp/test_run")
        event_rec = MockEventRecorder()
        
        # Trigger a tick record. The capture policy will capture PROJECT_CHANGED since it baseline-initializes first tick.
        # To trigger PROJECT_CHANGED, let's record first tick as baseline, then shift project and record second tick!
        recorder.record_tick(state, tick=100, events=[], event_recorder=event_rec)
        
        # Shift project on entity
        obj_new = ObjectiveState(
            id="obj_new",
            kind=ObjectiveKind.REACH_LOCATION,
            target_position=(30.0, 40.0),
            status=ObjectiveStatus.ACTIVE
        )
        proj_new = ProjectState(
            id="proj_new",
            kind=ProjectKind.COMBAT,
            status=ProjectStatus.ACTIVE,
            objectives=[obj_new],
            active_objective_id="obj_new",
            score=95.0
        )
        
        ent_new = (V2EntityBuilder(1)
            .kind("HERO")
            .strategic(projects={"proj_new": proj_new}, current_project_id="proj_new")
            .task(work_kind="ENTITY_MOVE")
            .build())
            
        state_new = AuthoritativeState(tick=101, seed=42, entities={1: ent_new}, regions={"forest": region})
        
        # Record tick 101 to capture project shift
        recorder.record_tick(state_new, tick=101, events=[], event_recorder=event_rec)
        
        # Verify StrategicProjectChanged was created with enriched trace fields
        strategic_events = [e for e in event_rec.recorded_events if e.event_type == "StrategicProjectChanged"]
        assert len(strategic_events) > 1
        
        evt = strategic_events[1]
        assert evt.previous_project_id == "proj_harvest"
        assert evt.new_project_id == "proj_new"
        assert evt.source_goal_score == 95.0
        assert evt.resulting_action == "ENTITY_MOVE"
        assert evt.target_pos == [30.0, 40.0]
        assert "95.0" in evt.message
        assert "ENTITY_MOVE" in evt.message
    finally:
        ObservabilityConfig.set_override_mode(None)
