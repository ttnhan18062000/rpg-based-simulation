from dataclasses import fields
from src.core.state import AuthoritativeState, EntityState


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
    
    # Authorized (V2 Components)
    assert "id" in entity_fields
    assert "kind" in entity_fields
    assert "navigation" in entity_fields
    assert "lifecycle" in entity_fields
    assert "combat" in entity_fields
    
    # Forbidden (Legacy/Observational)
    forbidden = {"last_action_reason", "debug_trace", "visual_cue"}
    assert not (entity_fields & forbidden)


def test_mutation_tripwire_during_decision():
    """
    RPG-AUTH-009: Mutation tripwire during decision.
    Verify that any attempt to mutate entities during the decision phase raises a ReadOnlyError.
    """
    from src.core.state import AuthoritativeState, EntityState, ReadOnlyError, InventoryComponent, ItemStack
    import pytest
    from dataclasses import FrozenInstanceError
    
    from src.core.builder import V2EntityBuilder
    # Setup state with an entity that has mutable-looking fields
    e1 = (V2EntityBuilder(1)
          .kind("ACTOR")
          .location(0, 0)
          .replace_inventory(InventoryComponent(items=[ItemStack("gold_coin", 10)]))
          .identity(properties={"can_mutate": True})
          .build())
    state = AuthoritativeState(tick=1, seed=1, entities={1: e1})
    
    # Obtain the readonly view used by workers
    view = state.readonly_view()
    view_entity = view.entities[1]
    
    # 1. Test top-level dataclass mutation (should raise FrozenInstanceError/AttributeError)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        view_entity.navigation = None
        
    # 2. Test dict mutation (properties)
    # MappingProxyType raises TypeError, not ReadOnlyError.
    with pytest.raises((ReadOnlyError, TypeError)):
        view_entity.properties["new_key"] = "forbidden"

    # 3. Test nested list mutation (inventory items)
    with pytest.raises((ReadOnlyError, TypeError, AttributeError)):
        view_entity.inventory.items.append(ItemStack("stolen_gold", 999))

    # 4. Test equipment mutation
    from src.core.state import EquipSlot
    with pytest.raises((ReadOnlyError, TypeError)):
        view_entity.equipment.slots[EquipSlot.HEAD] = "forbidden_helmet"


def test_deep_freeze_behavior():
    """
    RPG-AUTH-023, RPG-AUTH-024: Deep freeze recursion and idempotency.
    """
    from src.core.immutability import deep_freeze
    from src.core.state import ReadOnlyDict, ReadOnlyError
    import pytest
    
    # 1. Recursion
    data = {"a": [1, 2, {"b": 3}]}
    frozen = deep_freeze(data)
    assert isinstance(frozen, ReadOnlyDict)
    assert isinstance(frozen["a"], tuple)
    assert isinstance(frozen["a"][2], ReadOnlyDict)
    
    # Verify mutation prevention
    with pytest.raises(ReadOnlyError):
        frozen["new"] = 1
    
    # 2. Idempotency
    frozen2 = deep_freeze(frozen)
    assert frozen2 is frozen # Should return the same object if already frozen
