"""LB-S17 (docs/world_rules/scenarios/life-body-batch-05.md): a broke worker forages wild land and eats what it carries.

Rules invoked: SURV-06 and Decision 29 (wild food belongs to the land, by biome, outside settlements), SURV-07 with Decision 27
(a need with no open way pulls toward the step that opens one), RES-05 (regrowth by a declared process), Bible 03 (conservation).

Two arms of the same staging differ only in whether the wild region holds wild food: the MAIN arm is the compiled forest (HIGH
fertility, `near_forest`), the CONTROL arm is the same world with the food the biome table places there removed, as a NONE biome
(`old_mine`) places none. The control shows the food in the main arm came from the land through foraging, not from a free meal.

The land is not staged: since ENV-08 (decision 30) the second town and the near forest carry no ambient hazard, so the walk out is survivable
and the forage loop is what the scenario sees (SPC-S16 covers the land itself).

Everything is read from authoritative state, per tick, through the real kernel; no log line is parsed.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Tuple

import pytest

from src.config.profiles import PROD_SMALL
from src.core.enums import EntityRole
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("economy"), pytest.mark.level("scenario")]

WORLD = "frontier_living_world"
SEED = 42
WINDOW = 460  # the walk out (~100 ticks), the gathering, the eating, and one regrowth interval of the stripped node
FOOD_KIND = "berry_thicket"
STARTING_HUNGER = 70.0  # past the point where Decision 27's pull applies
STAGED_CHARGES = 2  # a small patch, so that stripping it fits the window
INN_EAT_PRICE = 5  # service_prices.EAT_PRICE_GOLD


@dataclass
class Trace:
    worker_id: int
    ticks: List[Tuple[int, float, int, int, Tuple[int, ...]]] = field(default_factory=list)  # (tick, hunger, gold, carried, node charges)
    events: set = field(default_factory=set)
    final: AuthoritativeState | None = None


def _carried(entity) -> int:
    return sum(s.quantity for s in entity.inventory.items if food_hunger_recovery(s.item_id) > 0.0)


def _stage(state: AuthoritativeState, *, wild_food: bool) -> Tuple[AuthoritativeState, int]:
    worker = next(e for e in state.entities.values()
                  if e.identity.role == EntityRole.WORKER and (e.identity.properties or {}).get("species_id") == "human")
    worker = replace(worker, biological=replace(worker.biological, hunger=STARTING_HUNGER),
                     inventory=replace(worker.inventory, gold=0, items=[]),
                     navigation=replace(worker.navigation, position=(38.0, 30.0)))  # inside the settlement, beside the inn
    nodes = {i: n for i, n in state.resource_nodes.items() if n.kind != FOOD_KIND}
    if wild_food:
        nodes.update({i: replace(n, remaining_charges=STAGED_CHARGES) for i, n in state.resource_nodes.items() if n.kind == FOOD_KIND})
    return replace(state, entities={worker.id: worker}, resource_nodes=nodes), worker.id


def _run(*, wild_food: bool) -> Trace:
    state, worker_id = _stage(compile_world(WORLD, SEED), wild_food=wild_food)
    trace = Trace(worker_id)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True})
    try:
        for _ in range(WINDOW):
            kernel.tick_once()
            now = kernel._state
            worker = now.entities[worker_id]
            food = sorted(n.remaining_charges for n in now.resource_nodes.values() if food_hunger_recovery(n.yields_item) > 0.0)
            trace.ticks.append((now.tick, worker.biological.hunger, worker.inventory.gold, _carried(worker), tuple(food)))
            trace.events.update((e.category, e.subject) for e in now.recent_world_events)
        trace.final = kernel._state
    finally:
        kernel.shutdown()
    return trace


@pytest.fixture(scope="module")
def main_arm() -> Trace:
    return _run(wild_food=True)


@pytest.fixture(scope="module")
def control_arm() -> Trace:
    return _run(wild_food=False)


def _gathered(trace: Trace) -> int:
    return sum(max(0, b[3] - a[3]) for a, b in zip(trace.ticks, trace.ticks[1:]))


def _eaten(trace: Trace) -> int:
    return sum(max(0, a[3] - b[3]) for a, b in zip(trace.ticks, trace.ticks[1:]))


def test_main_arm_the_worker_gathers_and_the_node_charges_fall_by_what_it_carries(main_arm):
    assert _gathered(main_arm) >= 1
    # Conservation (Bible 03): the item enters only by gathering. Between regrowth the node's loss equals the worker's gain.
    for (_, _, _, car_a, ch_a), (_, _, _, car_b, ch_b) in zip(main_arm.ticks, main_arm.ticks[1:]):
        if car_b > car_a:
            assert sum(ch_b) == sum(ch_a) - (car_b - car_a)


def test_main_arm_the_worker_eats_from_what_it_carries_and_pays_nothing(main_arm):
    eaten = [(a, b) for a, b in zip(main_arm.ticks, main_arm.ticks[1:]) if b[3] < a[3]]
    assert eaten, "the worker never ate what it carried"
    for before, after in eaten:
        assert before[3] - after[3] == 1  # one carried item per meal
        assert after[1] < before[1] - 5  # hunger falls
        assert after[2] == before[2] == 0  # gold unchanged, so no inn meal was bought
    assert all(row[2] == 0 for row in main_arm.ticks)
    assert _gathered(main_arm) - _eaten(main_arm) == main_arm.ticks[-1][3]  # held = gathered - eaten, nothing created or lost


def test_main_arm_the_stripped_patch_is_depleted_and_then_recovers(main_arm):
    charges = [sum(row[4]) for row in main_arm.ticks]
    depleted_at = next((i for i, c in enumerate(charges) if c == 0), None)
    assert depleted_at is not None, "the patch was never stripped to 0"
    assert any(c > 0 for c in charges[depleted_at:]), "the stripped patch never grew back"
    assert any(category == WorldEventCategory.RESOURCE_RECOVERED for category, _ in main_arm.events)


def test_main_arm_no_wild_food_node_stands_inside_the_settlement(main_arm):
    state = main_arm.final
    hometown = state.regions["hometown"].bounds
    for node in state.resource_nodes.values():
        if food_hunger_recovery(node.yields_item) > 0.0:
            x, y = node.position
            assert not (hometown[0] <= x <= hometown[2] and hometown[1] <= y <= hometown[3])


def test_control_arm_there_is_no_wild_food_no_gather_and_no_meal_without_payment(control_arm):
    assert _gathered(control_arm) == 0 and all(row[3] == 0 for row in control_arm.ticks)
    assert all(row[4] == () for row in control_arm.ticks)  # the land holds no wild food
    assert all(row[2] == 0 for row in control_arm.ticks)  # nothing was paid
    hungers = [row[1] for row in control_arm.ticks]
    assert all(b >= a for a, b in zip(hungers, hungers[1:]))  # no meal ever lowered it
    assert hungers[-1] > hungers[0]  # hunger keeps rising inside the window
