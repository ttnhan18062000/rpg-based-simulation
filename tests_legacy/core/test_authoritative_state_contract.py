from dataclasses import fields
from src_legacy.core.state import AuthoritativeState, EntityState


def test_authoritative_state_isolation():
    """Ensure core state only contains authoritative fields."""
    state_fields = {f.name for f in fields(AuthoritativeState)}
    
    # Authorized fields
    assert "tick" in state_fields
    assert "seed" in state_fields
    assert "entities" in state_fields
    assert "global_resources" in state_fields
    assert "rng_checkpoint" in state_fields
    
    # Forbidden (Legacy/Observational) fields
    # If these appear, the contract is violated.
    forbidden = {"event_log", "diagnostics", "replay_buffer", "telemetry"}
    assert not (state_fields & forbidden)


def test_entity_state_isolation():
    """Ensure entity state only contains authoritative fields."""
    entity_fields = {f.name for f in fields(EntityState)}
    
    # Authorized
    assert "id" in entity_fields
    assert "kind" in entity_fields
    assert "position" in entity_fields
    assert "active" in entity_fields
    assert "readiness" in entity_fields
    
    # Forbidden
    forbidden = {"last_action_reason", "debug_trace", "visual_cue"}
    assert not (entity_fields & forbidden)
