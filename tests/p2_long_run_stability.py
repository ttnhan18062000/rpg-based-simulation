"""
P2 Long-run stability and invariant tracking.
- RPG-1430: World object bounds and decay
- RPG-0021, RPG-0094: Authoritative state stability
"""
import pytest
from src.core.state import AuthoritativeState, EntityState, CombatComponent, IdentityComponent, InventoryComponent, StrategicComponent, NavigationComponent, BiologicalComponent, LifecycleComponent, AuthoritativeState, AuthoritativeState
from src.core.enums import EntityRole, Faction
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate, ResourceTransferIntent
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.inventory import ItemStack
from src.core.strategic import ProjectState, ProjectStatus, CognitionProfile

def create_authoritative_state():
    return AuthoritativeState(
        tick=0,
        seed=42,
        entities={},
        resource_nodes={},
        ground_items={},
        corpses={},
        regions={}
    )

def setup_simulation():
    state = create_authoritative_state()
    
    # 2 Heroes
    for i in range(2):
        h_id = 100 + i
        hero = EntityState(
            id=h_id,
            kind="HERO",
            position=(10.0, 10.0 + i),
            identity=IdentityComponent(role=EntityRole.HERO, faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=100, max_hp=100, atk=20),
            inventory=InventoryComponent(gold=100),
            strategic=StrategicComponent(profile=CognitionProfile()),
            navigation=NavigationComponent(),
            biological=BiologicalComponent(),
            lifecycle=LifecycleComponent()
        )
        state.entities[h_id] = hero
        
    # 2 Monsters
    for i in range(2):
        m_id = 200 + i
        monster = EntityState(
            id=m_id,
            kind="MONSTER",
            position=(20.0, 20.0 + i),
            identity=IdentityComponent(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=50, max_hp=50, atk=10),
            inventory=InventoryComponent(gold=0),
            strategic=StrategicComponent(),
            navigation=NavigationComponent(),
            biological=BiologicalComponent(),
            lifecycle=LifecycleComponent()
        )
        state.entities[m_id] = monster
        
    return state

def test_long_run_stability():
    """
    RPG-1430: Long-run stability and invariant tracking.
    Runs 2000 ticks and verifies world object bounds.
    """
    state = setup_simulation()
    
    # Track stats
    max_corpses = 0
    max_idempotency_set = 0
    
    for tick in range(2000):
        # Generate some intents to keep things moving
        entity_updates = {}
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            # Simple "Wait" or "Wander" intent
            entity_updates[e_id] = EntityUpdate(
                entity_id=e_id,
                readiness_delta=5.0 # Keep them moving
            )
            
        # Simulate a death occasionally to test corpse decay
        if tick % 500 == 0 and tick > 0:
            target_id = next(iter(state.entities))
            target = state.entities[target_id]
            if target.active:
                from src.core.updates import CombatUpdate
                entity_updates[target_id] = EntityUpdate(
                    entity_id=target_id,
                    combat=CombatUpdate(hp_delta=-999, alive_set=False)
                )

        update = StateUpdate(entity_updates=entity_updates)
        
        # Apply pipeline
        refined_upd = AuthoritativeApplyPipeline.refine(state, update)
        state = ApplyPath.apply_generation(state, refined_upd, next_tick=state.tick + 1)
        
        # Invariant checks
        corpse_count = len(state.corpses)
        max_corpses = max(max_corpses, corpse_count)
        
        # RPG-0045: Corpse decay must happen
        assert corpse_count <= 5, f"Corpse explosion at tick {tick}: {corpse_count}"
        
        # Check strategic project bounds for each entity
        for entity in state.entities.values():
            if entity.active:
                assert len(entity.strategic.projects) <= entity.strategic.profile.max_active_projects, \
                    f"Project bound violated for entity {entity.id}"
                    
        # Check transaction ID set stability
        max_idempotency_set = max(max_idempotency_set, len(state.processed_transaction_ids))
        
    print(f"\nLong-run stability summary:")
    print(f"  Max corpses: {max_corpses}")
    print(f"  Max idempotency set size: {max_idempotency_set}")
    print(f"  Final tick: {state.tick}")
    
    # Verify that the simulation completed
    assert state.tick == 2000
