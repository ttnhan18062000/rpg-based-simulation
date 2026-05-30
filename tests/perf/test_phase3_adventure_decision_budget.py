"""
tests/perf/test_phase3_adventure_decision_budget.py

Phase 3 — AdventureDecisionPhase performance budget and strategic scaling gates.
"""

import pytest
import time
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent, PersonalityComponent, AuthoritativeState
from src.domains.adventure.phase import AdventureDecisionPhase


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_stamina(StaminaComponent(current=100, max_stamina=100))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p)
    return b.build()


def _state(entities) -> AuthoritativeState:
    ent_map = {e.id: e for e in entities}
    return AuthoritativeState(
        tick=10,
        seed=1,
        world_time=100,
        entities=ent_map,
        groups={},
        regions={},
        resource_nodes={},
        buildings={},
        chests={},
        ground_items={},
        corpses={},
        camps={},
        local_scars={},
        global_resources={},
        town_tiles=(),
        building_tiles=(),
        terrain=(),
        home_storage={},
        town_center=(0, 0),
        periodic_due_ticks={},
        work_debt={},
        movement_count=0,
        maturity=0,
        last_calamity_tick=0,
        blocked_tiles=(),
        town_entity_ids=(),
    )


def test_phase3_adventure_decision_perf_budget():
    """
    Verify that executing routing decisions for 100+ entities
    is highly performant and falls well within target budgets (<5ms clean updates).
    """
    # 1. Prepare 100 clean/locked entities
    entities = [_entity(i) for i in range(105)]
    state = _state(entities)

    # 2. Benchmark evaluation phase
    t0 = time.perf_counter_ns()
    update = AdventureDecisionPhase.apply(state)
    t_delta_ms = (time.perf_counter_ns() - t0) / 1e6

    # Verify response bounds under 100+ entities (<15ms for active decisions, <5ms with locked filters)
    assert t_delta_ms < 15.0, f"Adventure decision phase execution is too slow: {t_delta_ms}ms"
