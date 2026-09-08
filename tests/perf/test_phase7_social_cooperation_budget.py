"""
tests/perf/test_phase7_social_cooperation_budget.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Performance and Strategic Budget Tests.
"""

import statistics
import time
import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase
from src.domains.combat_engagement.phase import build_combat_risk_belief
from tests.tools.perf_assertions import assert_perf_threshold


@pytest.mark.slow
def test_cooperation_phase_performance_budget_100_entities():
    # Build 100 entities, half with help needs
    entities = {}
    for i in range(1, 101):
        b = (V2EntityBuilder(i)
             .kind("HERO")
             .location(float(i % 10), float(i // 10))
             .combat(hp=100, max_hp=100)
             .lifecycle(active=True))
             
        ent = b.build()
        if i <= 50:
            # Active objective & high risk
            obj = ObjectiveState(id=f"obj_{i}", kind=ObjectiveKind.DEFEAT_ENEMY)
            proj = ProjectState(id=f"proj_{i}", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id=f"obj_{i}")
            # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: real BeliefEntry (0.6 -> HIGH)
            ent.strategic.beliefs["combat_risk"] = build_combat_risk_belief(
                death_risk=0.6, current_tick=1
            )
            ent.strategic.projects[f"proj_{i}"] = proj
            object.__setattr__(ent.strategic, "current_project_id", f"proj_{i}")
            object.__setattr__(ent.strategic, "current_objective_id", f"obj_{i}")
            
            # Trust mapping for i+1
            ent.social.trust_history[i + 1 if i < 100 else 1] = 0.8
        entities[i] = ent
        
    state = AuthoritativeState(entities=entities, tick=1, seed=123)
    update = StateUpdate()
    
    # Measure execution speed with warm-up to amortize imports and JIT
    for _ in range(5):
        CooperationPhase.execute(state, update)
        
    iterations = 20
    durations_ms = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        refined = CooperationPhase.execute(state, update)
        durations_ms.append((time.perf_counter_ns() - t0) / 1e6)

    # Median rather than mean: a single VM-scheduler-induced spike among 20
    # samples must not fail the whole run (observed in practice — see
    # TCK-20260712-SIMQ-COOPERATION-SOCIAL-STALE-TESTS).
    median_duration = statistics.median(durations_ms)

    print(f"\n[PERF] Phase 7 median execution speed for 100 entities: {median_duration:.2f}ms "
          f"(samples: {[round(d, 2) for d in durations_ms]})")

    # Must stay strictly inside agreed budget of < 25.0ms for 100+ entities.
    assert_perf_threshold(
        median_duration, 25.0,
        f"CooperationPhase median duration across {iterations} samples "
        f"({[round(d, 2) for d in durations_ms]})", op="<",
    )
    assert refined.metric_counters["cooperation_evaluations"] == 50
