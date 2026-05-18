# Compliance IDs: PERF-015
import pytest
from unittest.mock import MagicMock
from src.core.updates import EntityUpdate, CombatUpdate, NavigationUpdate, AttributeUpdate, IdentityUpdate, WoundUpdate
from src.core.state import EntityState, CombatComponent, NavigationComponent, AttributeComponent, IdentityComponent
from src.engine.patches import (
    extract_patches, CombatPatch, NavigationPatch, AttributePatch, IdentityPatch, WoundPatch, KindPatch
)

def test_patch_noop_detection():
    # Test KindPatch
    kp_noop = KindPatch(entity_id=1, kind_set=None)
    assert kp_noop.is_noop() is True
    kp_active = KindPatch(entity_id=1, kind_set="Goblin")
    assert kp_active.is_noop() is False

    # Test CombatPatch
    cp_noop = CombatPatch(entity_id=1, combat=None, readiness_delta=0.0)
    assert cp_noop.is_noop() is True
    cp_active = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-10), readiness_delta=0.0)
    assert cp_active.is_noop() is False

def test_patch_merging():
    cp1 = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-10, atk_delta=2), readiness_delta=10.0)
    cp2 = CombatPatch(entity_id=1, combat=CombatUpdate(hp_delta=-5, def_delta=1), readiness_delta=-5.0)
    
    merged = cp1.merge(cp2)
    assert merged.combat.hp_delta == -15
    assert merged.combat.atk_delta == 2
    assert merged.combat.def_delta == 1
    assert merged.readiness_delta == 5.0

def test_order_sensitivity():
    # Verify extract_patches maintains correct dependency order
    update = EntityUpdate(
        entity_id=1,
        kind_set="Orc",
        attributes=AttributeUpdate(strength_delta=5),
        combat=CombatUpdate(hp_delta=-15),
        identity=IdentityUpdate(role_set="Warrior")
    )
    patches = extract_patches(1, update)
    patch_types = [type(p) for p in patches]
    
    # Kind and Identity must come before Combat and Attributes
    assert KindPatch in patch_types
    assert IdentityPatch in patch_types
    assert CombatPatch in patch_types
    assert AttributePatch in patch_types
    
    kind_idx = patch_types.index(KindPatch)
    id_idx = patch_types.index(IdentityPatch)
    com_idx = patch_types.index(CombatPatch)
    att_idx = patch_types.index(AttributePatch)
    
    # Kind and Identity precede Combat
    assert kind_idx < com_idx
    assert id_idx < com_idx
