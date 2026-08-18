"""
tests/perf/test_phase2_self_model_budget.py

Phase 2 — Bottom-up self-model update budget and dirty-check performance verification.
"""

import pytest
import time
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent, BiologicalComponent
from src.cognition.self_model_phase import SelfModelUpdatePhase
from tests.tools.perf_assertions import assert_perf_threshold


def _entity(e_id):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_stamina(StaminaComponent(current=100, max_stamina=100))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    return b.build()


@pytest.mark.slow
def test_phase2_self_model_perf_budget_and_dirty_check():
    """
    Verify that updating 100 entities is well within performance budgets,
    and that the dirty-check skip provides at least 5x speedup for clean entities.
    """
    # 1. Prepare 100 entities
    entities = [_entity(i) for i in range(100)]

    # 2. Benchmark Warm Update (Tick 0 -> Tick 1, all must run)
    t0 = time.perf_counter_ns()
    updated_entities = []
    for ent in entities:
        # Run first update
        bundle = SelfModelUpdatePhase.run(ent, tick=1)
        # Store updated state
        ent_updated = V2EntityBuilder(ent.id).replace_self_model(bundle).replace_combat(ent.combat).replace_stamina(ent.stamina).replace_biological(ent.biological).identity(evolution_level=ent.identity.evolution_level).build()
        updated_entities.append(ent_updated)
    t_warm_ms = (time.perf_counter_ns() - t0) / 1e6

    # Warm budget check: 100 entities warm update should easily complete in under 50ms
    assert_perf_threshold(t_warm_ms, 50.0, "Warm self-model update (100 entities)", op="<")

    # 3. Benchmark Clean Update (Tick 1 -> Tick 2, dirty-check skips needing update)
    t1 = time.perf_counter_ns()
    for ent in updated_entities:
        # Run second update (with no changes)
        SelfModelUpdatePhase.run(ent, tick=2)
    t_clean_ms = (time.perf_counter_ns() - t1) / 1e6

    # Clean budget check: 100 clean entities should skip and complete in under 5ms
    assert_perf_threshold(t_clean_ms, 5.0, "Clean (dirty-check-skip) self-model update (100 entities)", op="<")

    # Dirty-check ratio validation: clean run must be significantly faster (at least 5x)
    ratio = t_warm_ms / max(0.01, t_clean_ms)
    assert_perf_threshold(
        ratio, 5.0,
        f"Dirty-check speedup ratio (warm={t_warm_ms}ms, clean={t_clean_ms}ms)", op=">=",
    )
