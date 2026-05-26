"""
Unit tests for the Cognition Capture Policy.
"""
import pytest
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.cognition.recorder import CognitionCapturePolicy


class DummyStrategicProfile:
    def __init__(self):
        self.max_leads = 5
        self.max_concerns = 5
        self.interruption_resistance = 1


class DummyStrategicComponent:
    def __init__(self):
        self.directives = {}
        self.projects = {}
        self.blockers = {}
        self.leads = {}
        self.concerns = {}
        self.hypotheses = {}
        self.current_project_id = "proj1"
        self.current_objective_id = "obj1"
        self.primary_overload_source = None
        self.profile = DummyStrategicProfile()


class DummyEntity:
    def __init__(self, entity_id: int):
        self.id = entity_id
        self.strategic = DummyStrategicComponent()


class TestCognitionCapturePolicy:
    """Milestone 59: Cognition capture policy rule assertions."""

    @pytest.fixture(autouse=True)
    def clean_overrides(self):
        yield
        ObservabilityConfig.set_override_mode(None)

    def test_off_mode_records_nothing(self):
        """OFF mode must never capture snapshot under any conditions."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
        policy = CognitionCapturePolicy()
        entity = DummyEntity(1)
        
        # Test anomaly triggers
        assert not policy.should_capture(entity, 1, "ANOMALY_TRIGGERED")
        # Test project changes
        assert not policy.should_capture(entity, 1, "PROJECT_CHANGED")

    def test_light_mode_only_anomalies(self):
        """LIGHT mode captures only anomalies or certification/evidence boundaries."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
        policy = CognitionCapturePolicy()
        entity = DummyEntity(1)
        
        assert policy.should_capture(entity, 1, "ANOMALY_TRIGGERED")
        assert policy.should_capture(entity, 1, "CERTIFICATION_BOUNDARY")
        
        # Should NOT capture normal transitions
        assert not policy.should_capture(entity, 1, "PROJECT_CHANGED")
        assert not policy.should_capture(entity, 1, "BLOCKER_CHANGED")

    def test_debug_mode_captures_all_reasons(self):
        """DEBUG mode captures all valid reasons for the designated target entities."""
        ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)
        
        # By default, in DEBUG mode, all entities or debug selected entities are captured.
        policy = CognitionCapturePolicy(selected_entity_ids={1})
        entity1 = DummyEntity(1)
        entity2 = DummyEntity(2)
        
        assert policy.should_capture(entity1, 1, "PROJECT_CHANGED")
        assert policy.should_capture(entity1, 1, "ANOMALY_TRIGGERED")
        
        # Entity 2 is not in selected set, so it should not capture non-anomalies
        assert not policy.should_capture(entity2, 1, "PROJECT_CHANGED")
        # But should still capture anomalies
        assert policy.should_capture(entity2, 1, "ANOMALY_TRIGGERED")

    def test_state_changes_detection(self):
        """Verify that state changes (blocker, lead, concern, project swaps) are triggered properly."""
        policy = CognitionCapturePolicy()
        
        # Mock previous state tracking
        entity = DummyEntity(1)
        
        # 1. First evaluation: no previous state, so we initialize it
        reasons = policy.detect_state_changes(entity)
        assert not reasons  # First check returns empty since it's baseline
        
        # 2. Project changes
        entity.strategic.current_project_id = "proj2"
        reasons = policy.detect_state_changes(entity)
        assert "PROJECT_CHANGED" in reasons
        
        # 3. Objective changes
        entity.strategic.current_objective_id = "obj2"
        reasons = policy.detect_state_changes(entity)
        assert "OBJECTIVE_CHANGED" in reasons

        # 4. Overload changes
        entity.strategic.primary_overload_source = "some_blocker"
        reasons = policy.detect_state_changes(entity)
        assert "OVERLOAD_CHANGED" in reasons
