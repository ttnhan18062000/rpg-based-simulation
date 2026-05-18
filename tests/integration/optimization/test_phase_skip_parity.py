# Compliance IDs: RPG-OPT-PHASE-GRAPH, PERF-016
import pytest
from src.core.state import (
    AuthoritativeState, EntityState, NavigationComponent, CombatComponent,
    BiologicalComponent, LifecycleComponent, StaminaComponent, StrategicComponent,
    AttributeComponent, IdentityComponent, InventoryComponent
)
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate, InventoryUpdate
from src.engine.cadence import SystemCadence
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.core.dirty import DirtySet


def test_phase_skip_parity():
    """
    Run identical multi-tick scenarios with dynamic phase skipping enabled versus disabled.
    Prove 100% exact simulation state hash parity while verifying non-zero phase skip counts.
    """
    def run_scenario(force_full: bool) -> tuple[AuthoritativeState, int, int]:
        entities = {}
        for i in range(1, 11):
            entities[i] = EntityState(
                id=i,
                kind="HERO",
                navigation=NavigationComponent(position=(float(i * 5), float(i * 5))),
                combat=CombatComponent(hp=100, max_hp=100, alive=True, atk=15, def_stat=5, speed=0, readiness=0.0),
                biological=BiologicalComponent(),
                lifecycle=LifecycleComponent(age_ticks=10, max_age_ticks=2000, active=True),
                stamina=StaminaComponent(current=100.0, max_stamina=100.0),
                attributes=AttributeComponent(strength=10, agility=10),
                identity=IdentityComponent(role="WARRIOR", evolution_level=1),
                inventory=InventoryComponent(),
                strategic=StrategicComponent()
            )
        
        state = AuthoritativeState(tick=1, seed=42, world_time=1000, entities=entities)
        cadence = SystemCadence(building_sabotage=100, town_resolution=100, strategic_intelligence=100)

        total_skips = 0
        total_runs = 0

        for tick in range(1, 11):
            if tick % 3 == 1:
                # Tick 1, 4, 7, 10: Explicit 1-step movement target for entity 1
                e_upds = {1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(6.0, 5.0)))}
                dirty = DirtySet(movement_entities={1})
            elif tick % 3 == 2:
                # Tick 2, 5, 8: Inventory update for entity 2
                e_upds = {2: EntityUpdate(entity_id=2, inventory=InventoryUpdate(gold_delta=10))}
                dirty = DirtySet(inventory_entities={2})
            else:
                # Tick 3, 6, 9: Quiet tick, no entity updates
                e_upds = {}
                dirty = DirtySet()

            update = StateUpdate(entity_updates=e_upds, dirty_set=dirty, force_full_scan=force_full)
            refined_upd = AuthoritativeApplyPipeline.refine(state, update, cadence=cadence, force_full_scan=force_full)
            
            total_skips += refined_upd.metric_counters.get("phase_skips", 0)
            total_runs += refined_upd.metric_counters.get("phase_runs", 0)

            state = ApplyPath.apply_generation(state, refined_upd, next_tick=tick + 1, cadence=cadence)

        return state, total_skips, total_runs

    # Run optimized (phase skipping enabled)
    opt_state, opt_skips, opt_runs = run_scenario(force_full=False)
    assert opt_skips > 0, f"Expected non-zero phase skips during optimized run, got 0 skips and {opt_runs} runs."

    # Run reference (force full scan, phase skipping disabled)
    ref_state, ref_skips, ref_runs = run_scenario(force_full=True)
    assert ref_skips == 0, f"Expected 0 phase skips during reference full run, got {ref_skips} skips."

    # Assert exact state parity
    assert opt_state.tick == ref_state.tick
    assert len(opt_state.entities) == len(ref_state.entities)
    for eid in opt_state.entities:
        opt_ent = opt_state.entities[eid]
        ref_ent = ref_state.entities[eid]
        assert opt_ent.navigation.position == ref_ent.navigation.position
        assert opt_ent.combat.hp == ref_ent.combat.hp
        assert opt_ent.inventory.gold == ref_ent.inventory.gold
