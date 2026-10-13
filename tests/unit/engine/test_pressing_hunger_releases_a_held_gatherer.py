"""A held gather is released to decide when hunger presses and the gatherer carries food it can eat (SURV-06, SURV-07).

TCK-20261012-A-HELD-GATHERER-ON-A-REGROWING-PATCH-IS-NEVER-RELEASED-TO-EAT: a held INTERACT on a node that still has charges runs no brain,
so a grazer on a regrowing patch gathered grass while its hunger climbed. Waking is only a re-decision (the hunger goal then decides EAT).
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ItemStack, TaskComponent
from src.engine.cadence import SystemCadence
from src.engine.policy import GovernorPolicy
from src.engine.scheduler import NEED_WAKE_CADENCE, DeterministicScheduler

BERRIES = "wild_berries"


def _gatherer(eid=1, hunger=80.0, carried=(BERRIES, 2), species="human", action="INTERACT"):
    b = (V2EntityBuilder(eid).kind("hero").location(10.0, 10.0).combat(hp=100, max_hp=100, readiness=100.0, alive=True)
         .lifecycle(active=True).biological(hunger=hunger).properties({"species_id": species}))
    e = b.build()
    items = [ItemStack(*carried)] if carried else []
    return replace(e, inventory=replace(e.inventory, items=items), task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": action, "target_id": 7}))


def _brain_ticks(entity, ticks):
    policy = GovernorPolicy(system_cadence=SystemCadence(strategic_intelligence=10))
    out = []
    for t in ticks:
        items, _ = DeterministicScheduler().select_work(AuthoritativeState(tick=t, seed=1, entities={entity.id: entity}), policy)
        if any(i.owner_id == entity.id and i.work_kind == "ENTITY_BRAIN" for i in items):
            out.append(t)
    return out


def test_a_hungry_gatherer_carrying_edible_food_is_woken_once_per_cadence():
    ticks = _brain_ticks(_gatherer(), range(1, 1 + 3 * NEED_WAKE_CADENCE))
    assert len(ticks) == 3 and all(b - a == NEED_WAKE_CADENCE for a, b in zip(ticks, ticks[1:]))


def test_a_sated_gatherer_keeps_gathering():
    assert _brain_ticks(_gatherer(hunger=10.0), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []


def test_a_hungry_gatherer_with_nothing_edible_carried_keeps_gathering():
    assert _brain_ticks(_gatherer(carried=None), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []
    assert _brain_ticks(_gatherer(carried=("iron_ore", 3)), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []


def test_other_held_actions_are_not_released_by_this_wake():
    assert _brain_ticks(_gatherer(action="ATTACK"), range(1, 1 + 3 * NEED_WAKE_CADENCE)) == []
