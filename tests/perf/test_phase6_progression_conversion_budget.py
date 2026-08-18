"""
tests/perf/test_phase6_progression_conversion_budget.py

Phase 6 — Performance Budget Gates verification.
"""

import time
import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.domains.progression.phase import ProgressionConversionPhase
from tests.tools.perf_assertions import assert_perf_threshold


@pytest.mark.slow
def test_phase6_progression_conversion_performance_budget():
    # Build 100 entities
    entities = {}
    for i in range(1, 101):
        b = (V2EntityBuilder(i)
             .kind("ACTOR")
             .location(0.0, 0.0)
             .combat(hp=100, atk=10)
             .lifecycle(active=True))
        entities[i] = b.build()

    state = AuthoritativeState(entities=entities, tick=1, seed=1)
    update = StateUpdate()

    # Warmup run
    ProgressionConversionPhase.execute(state, update)

    # Time execution for 100 entities
    t_start = time.perf_counter_ns()
    refined = ProgressionConversionPhase.execute(state, update)
    t_duration_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0

    print(f"\n[PERF] ProgressionConversionPhase execute duration for 100 entities: {t_duration_ms:.3f} ms")

    # Bounded performance budget check: must stay under 5.0ms for 100 entities
    assert_perf_threshold(
        t_duration_ms, 5.0,
        "ProgressionConversionPhase execute duration (100 entities)", op="<",
    )
