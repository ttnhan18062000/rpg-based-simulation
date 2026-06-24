"""
tests/perf/test_phase7_social_cooperation_budget.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Performance and Strategic Budget Tests.
"""

import time
import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase


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
            ent.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}
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
        
    t_start = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        refined = CooperationPhase.execute(state, update)
    t_duration = ((time.perf_counter() - t_start) * 1000.0) / iterations # Average ms per execute
    
    print(f"\n[PERF] Phase 7 average execution speed for 100 entities: {t_duration:.2f}ms")
    
    # Must stay strictly inside agreed budget of < 25.0ms for 100+ entities after averaging JIT/interpreter cost on VM
    assert t_duration < 25.0
    assert refined.metric_counters["cooperation_evaluations"] == 50
