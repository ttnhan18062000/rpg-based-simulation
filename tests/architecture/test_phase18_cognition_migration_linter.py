import pytest
import dataclasses
from src.core.state import EntityState

def test_no_flat_cognition_fields_in_entity_state():
    # whitelisted fields that are allowed to be flat on EntityState
    whitelist = {
        "id", "kind", "interaction", "identity", "attributes", "inventory",
        "strategic", "social", "biological", "lifecycle", "aptitude", "combat",
        "equipment", "navigation", "task", "stamina", "self_model", "cognition",
        "timeline", "_readonly_cache", "_spatial_grid_cache", "_canonical_cache"
    }
    
    fields = {f.name for f in dataclasses.fields(EntityState)}
    forbidden = fields - whitelist
    assert not forbidden, f"Violation: Forbidden flat cognitive fields found on EntityState: {forbidden}. All new cognitive state must live inside CognitionModel."
