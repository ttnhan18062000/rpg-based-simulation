import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for Architectural Integrity (AOA Pillar 1 & 2).

These tests ensure that the core Entity model and AI handlers stay strictly compositional
and do not re-introduce legacy "flat" properties that violate Aspect-Oriented boundaries.
"""

import pytest
from src.core.entities.entity import Entity

# Approved shims (AOA Phase 1-5 stabilization)
# These are the only allowed top-level properties on Entity that are not aspects
APPROVED_SHIMS = {
    "id", "kind",                            # Core Pydantic fields
    "pos", "alive", "stats",                  # Legacy compatibility shims
    "inventory", "progression", "identity",   # Aspect Accessors
    "spatial", "combat", "mind", "interaction" # Aspect Accessors
}

# Strictly forbidden legacy properties (should ALWAYS be accessed via aspects)
FORBIDDEN_LEGACY_PROPERTIES = {
    "hp", "max_hp", "atk", "def", "spd", "mp", "max_mp", # Move to .combat
    "xp", "level", "gold", "stamina",                   # Move to .progression
    "faction", "role", "name", "hero_class",            # Move to .identity
    "ai_state", "goals", "target",                      # Move to .mind
    "home_pos", "leash_radius"                          # Move to .spatial
}

def test_entity_field_integrity():
    """Ensure Entity model_fields contains only the ID, Kind, and Aspects."""
    fields = set(Entity.model_fields.keys())
    
    # Required base fields
    assert "id" in fields
    assert "kind" in fields
    
    # Allowed aspects
    aspects = {"inventory", "progression", "identity", "spatial", "combat", "mind", "interaction"}
    for aspect in aspects:
        assert aspect in fields, f"Missing mandatory aspect field: {aspect}"
        
    # Check for unauthorized fields
    extra_fields = fields - aspects - {"id", "kind", "next_act_at"}
    assert not extra_fields, f"Unauthorized fields detected in Entity model: {extra_fields}"

def test_entity_property_locking():
    """Ensure no forbidden legacy properties have been re-introduced as shims."""
    # We check dir(Entity) which includes properties, methods, and fields
    entity_members = set(dir(Entity))
    
    leaked = entity_members & FORBIDDEN_LEGACY_PROPERTIES
    assert not leaked, f"Legacy properties leaked into Entity namespace: {leaked}. Use aspect paths instead!"

def test_aspect_model_purity():
    """Ensure aspects themselves stay clean of Cross-Aspect dependencies."""
    # This is a soft check for now, ensuring for example that CombatAspect 
    # doesn't start holding 'gold' or 'ai_state'.
    from src.core.aspects.combat import CombatAspect
    combat_fields = set(CombatAspect.model_fields.keys())
    assert "gold" not in combat_fields
    assert "ai_state" not in combat_fields
    
    from src.core.aspects.progression import ProgressionAspect
    prog_fields = set(ProgressionAspect.model_fields.keys())
    assert "hp" not in prog_fields
    assert "max_hp" not in prog_fields

@pytest.mark.parametrize("aspect_name", [
    "inventory", "progression", "identity", "spatial", "combat", "mind", "interaction"
])
def test_mandatory_aspect_naming(aspect_name):
    """Aspects must be named exactly as their type (lowercase)."""
    assert aspect_name in Entity.model_fields, f"Entity missing {aspect_name} aspect field"
