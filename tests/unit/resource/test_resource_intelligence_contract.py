import pytest
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, InventoryComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, InventoryUpdate
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile
from src.platform.rng import DeterministicRNG
from src.core.strategic import StrategicComponent

@pytest.fixture
def base_state():
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(gold=10, items=[ItemStack("wood", 1)])
        .identity(known_recipes=("craft_steel_sword",), craft_target="craft_steel_sword")
        .build())
    
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity}
    )

@pytest.fixture
def kernel(base_state):
    from src.config.profiles import RuntimeProfile, HardwareClass
    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=100,
        max_cpu_percent=100,
        max_worker_count=0,
        max_queue_depth=10,
        max_replay_buffer_kb=100,
        max_observability_budget_percent=10,
        max_tick_budget_ms=100
    )
    rng = DeterministicRNG(base_seed=42)
    k = Kernel(profile, base_state, rng)
    yield k
    k.shutdown()

def test_law_of_necessity_blocker_generation(kernel):
    """Verify that crafting failures produce correct blockers."""
    # Propose a no-op (representing being at the blacksmith but failing)
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1)
        }
    )
    
    # Run one tick
    # In V2, we simulate being at a building by placing the entity on a building tile or 
    # relying on the system to resolve if the goal is active.
    # Current BlacksmithSystem resolves if craft_target is set and entity is in town.
    kernel._state = replace(kernel._state, town_tiles={(0,0)}, building_tiles={(0,0): "blacksmith"})
    
    # We call resolution directly for speed in contract test
    from src.engine.blacksmith import BlacksmithSystem
    refined_upd = BlacksmithSystem.enforce(kernel._state, update)
    
    # Assert blockers were added to the update
    assert 1 in refined_upd.entity_updates
    strat_up = refined_upd.entity_updates[1].strategic
    assert strat_up is not None
    blockers = {b.subject: b for b in strat_up.blockers_add_or_update}
    
    assert "iron_ore" in blockers
    assert "gold" in blockers
    assert blockers["iron_ore"].kind == "material"
    assert blockers["gold"].kind == "material"

def test_law_of_discovery_blocker_resolution(kernel):
    """Verify that material acquisition resolves active blockers."""
    # 1. Manually inject a blocker into state
    from src.core.strategic import BlockerState
    blocker = BlockerState(id="blocker_mat_iron_ore", kind="material", subject="iron_ore")
    
    ent = kernel._state.entities[1]
    kernel._state = replace(kernel._state, entities={
        1: replace(ent, strategic=StrategicComponent(blockers={"blocker_mat_iron_ore": blocker}))
    })
    
    # 2. Propose adding iron_ore
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 1)])
            )
        }
    )
    
    # 3. Use Kernel's resolution phase (which calls StrategicIntelligenceSystem.resolve_blockers)
    from src.systems.strategic import StrategicIntelligenceSystem
    refined_upd = StrategicIntelligenceSystem.resolve_blockers(kernel._state, update)
    
    # Assert blocker removal was added to the update
    assert 1 in refined_upd.entity_updates
    strat_up = refined_upd.entity_updates[1].strategic
    assert strat_up is not None
    assert "blocker_mat_iron_ore" in strat_up.blockers_remove

def test_blocker_persistence_through_apply(kernel):
    """Verify that blockers survive the apply cycle."""
    from src.core.strategic import BlockerState
    blocker = BlockerState(id="blocker_gold", kind="material", subject="gold")
    
    # Correct way to create StrategicUpdate in test
    from src.core.updates import StrategicUpdate
    strat_up = StrategicUpdate(blockers_add_or_update=[blocker])
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, strategic=strat_up)
        }
    )
    
    from src.engine.apply import ApplyPath
    next_state = ApplyPath.apply_generation(kernel._state, update, 2, 100)
    
    assert "blocker_gold" in next_state.entities[1].strategic.blockers
    assert next_state.entities[1].strategic.blockers["blocker_gold"].subject == "gold"
