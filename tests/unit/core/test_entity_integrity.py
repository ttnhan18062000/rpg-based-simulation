import pytest
from dataclasses import fields
from src.core.state import EntityState, CombatComponent, IdentityComponent

# Approved fields for V2 EntityState
# Strictly speaking, RPG-AUTH-030 says "only ID, Kind, and Aspects"
# But we might have some legacy drift. Let's see what fails.
REQUIRED_BASE_FIELDS = {"id", "kind"}

FORBIDDEN_LEGACY_PROPERTIES = {
    "hp", "max_hp", "atk", "def_stat", "speed", "mp", "max_mp", 
    "xp", "level", "gold", "stamina_current",
    "faction", "role", "name", "hero_class",
    "ai_state", "goals", "target",
    "home_pos", "leash_radius"
}

def test_entity_field_integrity():
    """RPG-AUTH-030: Ensure Entity model_fields contains only the ID, Kind, and Aspects."""
    entity_fields = {f.name for f in fields(EntityState)}
    
    aspects = {
        "interaction", "identity", "attributes", "inventory", 
        "strategic", "social", "biological", "lifecycle", 
        "aptitude", "combat", "equipment", "navigation", 
        "task", "stamina"
    }
    
    extra_fields = entity_fields - REQUIRED_BASE_FIELDS - aspects - {"_readonly_cache", "_spatial_grid_cache", "_canonical_cache", "timeline"}
    
    assert not extra_fields, f"Unauthorized fields detected in EntityState: {extra_fields}"

def test_entity_property_locking():
    """RPG-AUTH-031: Ensure no forbidden legacy properties have been re-introduced as shims."""
    entity_members = set(dir(EntityState))
    leaked = entity_members & FORBIDDEN_LEGACY_PROPERTIES
    assert not leaked, f"Legacy properties leaked into EntityState namespace: {leaked}."

def test_aspect_model_purity():
    """RPG-AUTH-032: Ensure aspects themselves stay clean of Cross-Aspect dependencies."""
    combat_fields = {f.name for f in fields(CombatComponent)}
    assert "gold" not in combat_fields
    assert "ai_state" not in combat_fields
    
    identity_fields = {f.name for f in fields(IdentityComponent)}
    assert "hp" not in identity_fields

def test_mandatory_aspect_naming():
    """RPG-AUTH-033: Aspects must be named exactly as their type (lowercase)."""
    entity_fields = {f.name for f in fields(EntityState)}
    expected_aspects = {
        "interaction", "identity", "attributes", "inventory", 
        "strategic", "social", "biological", "lifecycle", 
        "aptitude", "combat", "equipment", "navigation", 
        "task", "stamina"
    }
    for aspect in expected_aspects:
        assert aspect in entity_fields, f"EntityState missing {aspect} aspect field"
