"""Deterministic, real-Kernel-tick proof that idea 55 (nemesis transfer) and idea 58 (dying wish)
fire together through LifecycleSystem.resolve_lifecycle() (TCK-20260906-CAMPAIGN-SCORECARD-
EVALUATOR-FIELDS, M9 ticket 1, AC2 piece A).

Uses a hand-built AuthoritativeState with the deceased already at max_age_ticks (OLD_AGE death is
fully deterministic -- no combat/AI emergent behavior needed to force it), matching this
codebase's own established "isolated deterministic proof" precedent
(tests/simulation_quality/test_grade_regression.py::
test_information_intent_execution_fires_through_kernel_tick_once, and M7's own
route_new_query_isolated_calibration.py).
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import BlockerState, BlockerKind
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG


def test_nemesis_transfer_and_dying_wish_fire_through_real_kernel_tick():
    deceased = (
        V2EntityBuilder(1)
        .location(0.0, 0.0)
        .lifecycle(active=True, age_ticks=999_999_999, max_age_ticks=1, heir_entity_id=2)
        .strategic(blockers={
            "nemesis_3": BlockerState(id="nemesis_3", kind=BlockerKind.SOCIAL, subject="3", severity=0.8),
        })
        .build()
    )
    heir = (
        V2EntityBuilder(2)
        .location(0.0, 0.0)
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(tick=0, seed=42, entities={1: deceased, 2: heir})

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final_deceased = kernel.state.entities[1]
    final_heir = kernel.state.entities[2]

    assert final_deceased.lifecycle.active is False, "deceased must actually be dead this tick"
    assert final_deceased.lifecycle.death_reason == "OLD_AGE"

    # Idea 55: heir receives a weakened copy of the deceased's nemesis blocker.
    inherited = final_heir.strategic.blockers.get("inherited_nemesis_3")
    assert inherited is not None, "heir must inherit a weakened nemesis blocker"
    assert inherited.severity == 0.8 * 0.5
    assert inherited.subject == "3"
    assert inherited.resolved is False

    # Idea 58: heir receives a dying wish naming the same antagonist idea 55 transferred.
    named_intention = final_heir.cognition.motivation.named_intention
    assert named_intention is not None, "heir must receive a dying wish"
    assert named_intention.source_entity_id == 1
    assert named_intention.status == "PENDING"
    assert "3" in named_intention.text
