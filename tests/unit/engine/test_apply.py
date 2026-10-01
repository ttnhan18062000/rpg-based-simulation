"""Source-level architecture guard for TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE (AC5).

`resolve_lifecycle`'s OLD_AGE branch (src/systems/lifecycle_systems/lifecycle.py:193-195) is the
sole declared authority for old-age deactivation. `ApplyPath._compute_entity_changes`'s passive
branch (src/engine/apply.py:94-110) may only deactivate an entity immediately via its own
`new_hp > 0` HP-death gate; it must never again independently flip an already-active entity to
inactive purely because its age has reached `max_age_ticks`. This guard exercises the passive
branch in isolation (no EntityUpdate, so no resolve_lifecycle override in play) via
`ApplyPath.apply_generation`, and fails if the formula regresses to the pre-fix
`active=(new_hp > 0 and new_age < life.max_age_ticks)` shape.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath


def test_passive_branch_does_not_deactivate_an_active_entity_the_tick_its_age_reaches_max():
    max_age_ticks = 5
    entity = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .lifecycle(active=True, age_ticks=max_age_ticks - 1, max_age_ticks=max_age_ticks)
        .build()
    )
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})

    new_state = ApplyPath.apply_generation(state, StateUpdate())

    new_entity = new_state.entities[1]
    assert new_entity.lifecycle.age_ticks == max_age_ticks, (
        "sanity check: age_ticks must have advanced to exactly max_age_ticks this tick"
    )
    assert new_entity.lifecycle.active is True, (
        "the passive branch alone (no resolve_lifecycle EntityUpdate applied) must not deactivate "
        "an already-active entity on the tick its age first reaches max_age_ticks -- old-age "
        "deactivation is resolve_lifecycle's sole authority as of TCK-20260928-NATURAL-AGING-"
        "DEATH-DUAL-WRITER-RACE; a regression back to "
        "`active=(new_hp > 0 and new_age < life.max_age_ticks)` would fail this assertion"
    )


def test_passive_branch_records_hp_death_cause_but_never_deactivates():
    """Updated by TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER: the passive branch
    no longer deactivates on HP loss to zero. resolve_lifecycle is the sole authority for HP-death
    deactivation (as PROG-030 declares for age); the passive branch records the typed cause on the
    fatal tick and leaves `active` untouched."""
    entity = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .biological(hunger=95.0, sleep_debt=98.0)
        .combat(hp=1)
        .lifecycle(active=True, age_ticks=0, max_age_ticks=100_000)
        .build()
    )
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})

    new_state = ApplyPath.apply_generation(state, StateUpdate())

    new_entity = new_state.entities[1]
    assert new_entity.combat.hp == 0
    assert new_entity.lifecycle.active is True
    assert new_entity.lifecycle.passive_death_cause is not None


def test_passive_branch_never_reactivates_an_inactive_entity_younger_than_max_age():
    """`active=(life.active or new_age < max_age)` would be True for any dead entity younger than
    max_age and resurrect every corpse on the next life-due tick; the branch must leave it alone."""
    entity = (
        V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=0)
        .lifecycle(active=False, age_ticks=0, max_age_ticks=100_000)
        .build()
    )
    state = AuthoritativeState(tick=0, seed=42, entities={1: entity})
    new_state = ApplyPath.apply_generation(state, StateUpdate())
    assert new_state.entities[1].lifecycle.active is False
