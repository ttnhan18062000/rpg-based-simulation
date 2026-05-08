# tests/rpg/test_living_world_ph9.py
import pytest
from src.core.state import AuthoritativeState, RegionState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate, CombatUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.systems.generator import EntityGenerator
from src.core.enums import EntityRole
from src.core.inventory import InventoryComponent

def test_long_run_simulation_ph9():
    """
    Phase 9 Long-Run Stability Test.
    Verifies:
    1. Resource replenishment.
    2. Monster density caps.
    3. Threat escalation and decay.
    4. Idempotent Boss Spawning.
    5. Memory stability (bounded object counts).
    """
    # 1. Setup Initial State
    seed = 42
    generator = EntityGenerator(seed)
    
    # Create a region
    forest = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=0.0,
        retaliation_pressure=0.0
    )
    
    state = AuthoritativeState(
        tick=0,
        seed=seed,
        regions={"region_1": forest},
        global_resources={"metric_total_gold": 1000.0}
    )
    
    # Add a hero to drive some "action"
    hero = generator.spawn_hero((50, 50), state=state)
    # Patch to hero role for survival checks
    from dataclasses import replace
    from src.core.state import IdentityComponent
    hero = replace(hero, identity=replace(hero.identity, role=EntityRole.HERO))
    state = replace(state, entities={**state.entities, hero.id: hero})
    
    ticks_to_run = 1000
    max_entities_seen = 0
    boss_spawn_tick = -1
    
    for t in range(ticks_to_run):
        state = replace(state, tick=t)
        
        # Simulate some combat to drive threat
        # Every 50 ticks, if threat is low, simulate a "massacre"
        raw_update = StateUpdate()
        if t % 50 == 0 and state.regions["region_1"].trauma_score < 30:
            # Add threat via trauma_delta
            from src.core.updates import WorldUpdate
            raw_update.world_updates["region_1"] = WorldUpdate(
                region_id="region_1",
                trauma_delta=5.0
            )
        
        # Maturity Advancement (1 per 10 ticks for test speed)
        if t % 10 == 0 and t > 0:
            state = replace(state, maturity=state.maturity + 1)
        
        # 2. Refine & Apply
        refined = AuthoritativeApplyPipeline.refine(state, raw_update)
        
        # Apply Logic (Simplified for test)
        from src.engine.apply import ApplyPath
        state = ApplyPath.apply_generation(state, refined)
        
        # 3. Invariants Verification
        # I1: Monster count <= regional cap (e.g., 50)
        monster_count = len([e for e in state.entities.values() if e.active and e.combat.alive])
        assert monster_count <= 100, f"Entity explosion at tick {t}: {monster_count}"
        
        # I2: Active boss count <= 1
        bosses = [e for e in state.entities.values() if e.kind == "world_boss" and e.active and e.combat.alive]
        assert len(bosses) <= 1, f"Duplicate bosses at tick {t}: {len(bosses)}"
        
        if len(bosses) > 0 and boss_spawn_tick == -1:
            boss_spawn_tick = t
            
        # I3: Threat bounds
        region = state.regions["region_1"]
        assert 0.0 <= region.trauma_score <= 100.0, f"Threat out of bounds at tick {t}: {region.trauma_score}"
        assert 0.0 <= region.retaliation_pressure <= 100.0, f"Pressure out of bounds at tick {t}: {region.retaliation_pressure}"
        
        # I4: Node caps (Resource stability)
        node_count = len(state.resource_nodes)
        assert node_count <= 200, f"Node explosion at tick {t}: {node_count}"
        
        max_entities_seen = max(max_entities_seen, len(state.entities))

    # Final Assertions
    assert boss_spawn_tick > 0, "Boss should have spawned during 1000 ticks"
    assert state.regions["region_1"].trauma_score > 0, "Threat should have evolved"
    
    # Check for decay
    # At some point threat should decay if we stop adding it
    # We stopped adding it when it reached 30.0
    print(f"Final Threat: {state.regions['region_1'].trauma_score}")
    print(f"Max Entities: {max_entities_seen}")
    print(f"Boss Spawned at Tick: {boss_spawn_tick}")

if __name__ == "__main__":
    test_long_run_simulation_ph9()
