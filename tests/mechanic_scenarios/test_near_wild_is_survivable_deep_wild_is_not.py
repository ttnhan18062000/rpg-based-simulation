"""SPC-S16 (docs/world_rules/scenarios/space-environment-batch-04.md): the near wild is survivable, the deep wild is not.

Rules invoked: ENV-08 (decision 30: settled land and the near edge of the wild are survivable for the people who live beside them,
lethal ambient danger belongs to deep or cursed land), ENV-02 (endurance unchanged), SURV-06 with decision 29 (wild food in wild
land outside settlements).

A `town_council` worker (it endures no NATURAL_TERRAIN hazard) at full HP walks a FORCED route (a staged move task, then a staged
move home), so the scenario measures the land and not the decision. No hostiles, calamity 0. The arms differ only in the destination:
the MAIN arm goes to the wild-food node in `near_forest`, across the second town (`trading_hometown`), and home; the CONTROL arm goes
into `deep_forest`. The world is `frontier_extended`, which compiles the home town, the second town, `near_forest` with a thicket,
and `deep_forest`. Everything is read from authoritative state, per tick, through the real kernel.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Tuple

import pytest

from src.config.profiles import PROD_SMALL
from src.core.enums import EntityRole
from src.core.items import food_hunger_recovery
from src.core.state import AuthoritativeState, TaskComponent
from src.engine.kernel import Kernel
from src.engine.legality import LegalityServiceV2
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("environment"), pytest.mark.level("scenario")]

WORLD = "frontier_extended"
SEED = 42
HOME = (35.0, 25.0)  # inside hometown
DEEP_FOREST_TILE = (2.0, 71.0)  # inside deep_forest, outside every other region's box
WINDOW = 400
STAGED_HUNGER = 40.0  # low enough that starvation does not act inside the window
FOOD_KIND = "berry_thicket"


@dataclass
class Walk:
    ticks: List[Tuple[int, int, str, int]] = field(default_factory=list)  # (tick, hp, region id, carried)
    died_in: str | None = None
    death_reason: str | None = None
    reached_node: bool = False
    returned_home: bool = False


def _region_id(state: AuthoritativeState, position) -> str | None:
    region = LegalityServiceV2.get_region_for_position(position, state)
    return region.id if region else None


def _carried(entity) -> int:
    return sum(s.quantity for s in entity.inventory.items if food_hunger_recovery(s.item_id) > 0.0)


def _move_to(entity, destination):
    return replace(entity, navigation=replace(entity.navigation, target=destination),
                   task=TaskComponent(work_kind="ENTITY_MOVE", payload={"reason": "STAGED_ROUTE", "target_position": destination}))


def _walk(destination_kind: str) -> Walk:
    state = compile_world(WORLD, SEED)
    node = next(n for n in state.resource_nodes.values()
                if n.kind == FOOD_KIND and _region_id(state, n.position) == "near_forest")
    destination = node.position if destination_kind == "near_forest" else DEEP_FOREST_TILE
    worker = next(e for e in state.entities.values()
                  if e.identity.role == EntityRole.WORKER and (e.identity.properties or {}).get("species_id") == "human")
    assert (worker.identity.properties or {}).get("faction_id") == "town_council"
    worker = replace(worker, biological=replace(worker.biological, hunger=STAGED_HUNGER),
                     inventory=replace(worker.inventory, gold=0, items=[]),
                     navigation=replace(worker.navigation, position=HOME), combat=replace(worker.combat, hp=worker.combat.max_hp))
    worker = _move_to(worker, destination)
    staged = replace(state, entities={worker.id: worker},
                     regions={i: replace(r, calamity_intensity=0.0) for i, r in state.regions.items()})
    walk = Walk()
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=staged, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True})
    try:
        for _ in range(WINDOW):
            kernel.tick_once()
            now = kernel._state
            entity = now.entities[worker.id]
            region = _region_id(now, entity.navigation.position)
            walk.ticks.append((now.tick, entity.combat.hp, region, _carried(entity)))
            if not entity.combat.alive:
                walk.died_in, walk.death_reason = region, str(entity.lifecycle.death_reason)
                break
            if destination_kind == "near_forest":
                if not walk.reached_node and _carried(entity) >= 1:
                    walk.reached_node = True  # it gathered at the node: turn it round
                    kernel._state = replace(now, entities={**now.entities, worker.id: _move_to(entity, HOME)})
                elif walk.reached_node and entity.navigation.position == HOME:
                    walk.returned_home = True
                    break
    finally:
        kernel.shutdown()
    return walk


@pytest.fixture(scope="module")
def main_arm() -> Walk:
    return _walk("near_forest")


@pytest.fixture(scope="module")
def control_arm() -> Walk:
    return _walk("deep_forest")


def test_main_arm_the_worker_crosses_the_second_town_gathers_in_the_near_forest_and_walks_home_alive(main_arm):
    regions = {row[2] for row in main_arm.ticks}
    assert {"hometown", "trading_hometown", "near_forest"} <= regions  # the route really crossed the second town into the near forest
    assert main_arm.reached_node and main_arm.ticks[-1][3] >= 1  # it gathered and still carries it
    assert main_arm.returned_home and main_arm.died_in is None


def test_main_arm_no_health_is_lost_to_the_land_on_any_tick(main_arm):
    hps = [row[1] for row in main_arm.ticks]
    assert hps[0] == hps[-1] == max(hps)  # full HP throughout: hazard_damage is 0 in the towns and in the near forest


def test_control_arm_the_same_walk_into_the_deep_forest_kills_the_worker_inside_it(control_arm):
    assert control_arm.died_in == "deep_forest" and control_arm.death_reason == "HAZARD"
    assert control_arm.ticks[-1][1] == 0
    inside_before = [row[1] for row in control_arm.ticks if row[2] != "deep_forest"]
    assert inside_before and all(hp == inside_before[0] for hp in inside_before)  # the loss starts only inside deep_forest


def test_no_settled_region_carries_a_standing_ambient_hazard_at_compile():
    from pathlib import Path
    settled_kinds = {"TOWN", "SETTLEMENT"}
    for resolved in sorted(Path("data/worlds").glob("*/resolved")):
        for region in compile_world(resolved.parent.name, SEED).regions.values():
            if region.kind in settled_kinds or region.id == "survivor_outpost":
                assert region.hazard_level == 0.0, (resolved.parent.name, region.id, region.hazard_level)
