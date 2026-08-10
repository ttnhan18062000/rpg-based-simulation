"""TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK: characterizes
NavigationSystem.get_next_step()'s own single-axis-priority stepping tie-break, and locks in
the real, confirmed, but low-prevalence diagonal mutual-pursuit deadlock it produces when two
entities live-retarget to each other's current position every tick and land on a perfectly
diagonal offset (|dx| == |dy|).

No fix landed for the deadlock itself -- real corpus measurement (3 seeds x up to 8 worlds,
2000 ticks each) found exactly 1 genuinely stuck pair in the entire sample, judged too rare to
justify a stepping-algorithm change (see docs/engine/known_limitations.md Section 1.1). These
tests exist to document and lock in the CURRENT, confirmed-real behavior, so a future change to
get_next_step's own tie-break rule doesn't silently alter this characterized limitation.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.systems.world_systems.navigation import NavigationSystem


def _entity(entity_id: int, pos: tuple[float, float]):
    return (
        V2EntityBuilder(entity_id)
        .kind("monster")
        .location(*pos)
        .combat(alive=True)
        .lifecycle(active=True)
        .build()
    )


def _state(entities: dict):
    return AuthoritativeState(tick=1, seed=42, entities=entities)


def test_get_next_step_moves_x_when_dx_strictly_greater():
    entity = _entity(1, (0.0, 0.0))
    state = _state({1: entity})
    step = NavigationSystem.get_next_step(entity, (3.0, 1.0), state)
    assert step == (1.0, 0.0)


def test_get_next_step_moves_y_when_dy_strictly_greater():
    entity = _entity(1, (0.0, 0.0))
    state = _state({1: entity})
    step = NavigationSystem.get_next_step(entity, (1.0, 3.0), state)
    assert step == (0.0, 1.0)


def test_get_next_step_favors_y_on_exact_diagonal_tie():
    """The specific tie-break rule (`if abs(dx) > abs(dy): X else: Y`) means a perfectly
    diagonal offset (|dx| == |dy|) always resolves to a Y-axis step, never X -- this asymmetry
    is the root mechanism of the mutual-pursuit deadlock characterized below."""
    entity = _entity(1, (0.0, 0.0))
    state = _state({1: entity})
    step = NavigationSystem.get_next_step(entity, (2.0, 2.0), state)
    assert step == (0.0, 1.0)


def test_get_next_step_single_sided_pursuit_of_static_target_converges():
    """Regression guard: a ONE-SIDED pursuer chasing a static (non-reactive) target still
    converges via a staircase path (alternating axes as the tie breaks and re-breaks) -- the
    deadlock requires BOTH sides to be simultaneously, reactively re-targeting each other, not
    merely a diagonal starting offset."""
    entity = _entity(1, (0.0, 0.0))
    state = _state({1: entity})
    target = (3.0, 3.0)
    pos = entity.navigation.position
    for _ in range(10):
        pos = NavigationSystem.get_next_step(entity, target, state)
        entity = _entity(1, pos)
        state = _state({1: entity})
        if pos == target:
            break
    assert pos == target


def test_get_next_step_mutual_diagonal_pursuit_deadlocks():
    """The exact, confirmed-real bug: two entities on a perfectly diagonal offset, each
    live-retargeting to the OTHER's current position every tick (matching
    TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE's own real live-retargeting behavior), never
    converge -- their single-axis steps perpetually cancel each other's progress. Confirmed via
    live corpus trace (dungeon_crawl_seed42_2000t, entities 25/12) to reproduce this exact
    pattern for 990+ real consecutive ticks. This test locks in the CURRENT behavior as a known,
    documented limitation (docs/engine/known_limitations.md Section 1.1) -- it is not a
    "should never deadlock" assertion; a future stepping-algorithm change that resolves this is
    welcome and should update this test, not be blocked by it."""
    pos_a = (57.0, 59.0)
    pos_b = (58.0, 60.0)
    starting_manhattan = abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])

    for _ in range(50):
        entity_a = _entity(1, pos_a)
        entity_b = _entity(2, pos_b)
        state = _state({1: entity_a, 2: entity_b})
        next_a = NavigationSystem.get_next_step(entity_a, pos_b, state)
        next_b = NavigationSystem.get_next_step(entity_b, pos_a, state)
        pos_a, pos_b = next_a, next_b

    ending_manhattan = abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])
    assert ending_manhattan == starting_manhattan
    assert ending_manhattan > 1  # confirms this is a deadlock, not a converged/adjacent pair
