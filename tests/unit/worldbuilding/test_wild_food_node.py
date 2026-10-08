"""TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL (SURV-06, Decision 29): wild food is part of the land.

A forest region declares a food node, town land declares none (it holds owned food), the need path counts the node, a harvest
conserves items and charges (Bible 03 section 1 and 3), and a stripped node regrows through the ecology process (RES-05)."""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache

import pytest

from src.core.conservation import ResourceTransactionResolver
from src.core.items import food_hunger_recovery
from src.core.models.inventory import ItemStack
from src.core.update_models.resources import ResourceTransferIntent
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine import behavior_consumers
from src.engine.legality import LegalityServiceV2
from src.engine.need_paths import need_path_report
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.updates import StateUpdate
from src.world.ecology import ResourceEcologyService
from src.worldbuilding.compiler import RESOURCE_PLACEMENT_ATTEMPTS, WorldCompiler, _draw_tile_owned_by
from src.worldbuilding.repository import WorldRepository
from tests.helpers.entities import make_entity

pytestmark = [pytest.mark.domain("economy"), pytest.mark.level("unit")]

FOOD_KIND = "berry_thicket"
WILD_WORLD = "frontier_living_world"
HIGH_FERTILITY_CHARGES = 10  # wood_node's default_charges: the kind the near_forest ecology already lists


@lru_cache(maxsize=None)
def _state(world: str, seed: int = 42):
    spec, ctx = WorldRepository("data/worlds").load_world_with_context(world)
    state, _ = WorldCompiler.compile(spec, seed, context=ctx)
    return state


def _food_nodes(state):
    return [n for n in state.resource_nodes.values() if food_hunger_recovery(n.yields_item) > 0.0]


def test_a_forest_region_compiles_exactly_one_food_node_with_the_high_fertility_charges():
    state = _state(WILD_WORLD)
    nodes = _food_nodes(state)
    assert [n.kind for n in nodes] == [FOOD_KIND]
    assert nodes[0].max_charges == nodes[0].remaining_charges == HIGH_FERTILITY_CHARGES
    x_min, y_min, x_max, y_max = state.regions["near_forest"].bounds
    assert x_min <= nodes[0].position[0] <= x_max and y_min <= nodes[0].position[1] <= y_max


@pytest.mark.parametrize("seed", [42, 43, 44])
def test_the_food_node_count_does_not_depend_on_the_seed(seed):
    assert len(_food_nodes(_state(WILD_WORLD, seed))) == 1


@pytest.mark.parametrize("world", ["crowded_frontier", "urban_political"])
def test_a_world_with_no_wild_land_declares_no_food_node(world):
    assert _food_nodes(_state(world)) == []


def test_no_food_node_is_declared_in_the_home_town_region():
    for world in (WILD_WORLD, "crowded_frontier", "urban_political"):
        state = _state(world)
        x_min, y_min, x_max, y_max = state.regions["hometown"].bounds
        assert not [n for n in _food_nodes(state) if x_min <= n.position[0] <= x_max and y_min <= n.position[1] <= y_max]


def test_the_need_path_report_counts_the_wild_food_node():
    behavior_consumers._auto_init()
    rows = need_path_report(_state(WILD_WORLD), behavior_consumers._catalog)
    assert rows and all(row["food_nodes_in_world"] == 1 for row in rows)
    assert any(row["hunger_path"] is True for row in rows)
    rows_without = need_path_report(_state("crowded_frontier"), behavior_consumers._catalog)
    assert all(row["food_nodes_in_world"] == 0 for row in rows_without)


def test_gathering_the_node_conserves_items_and_charges():
    state = _state(WILD_WORLD)
    node = _food_nodes(state)[0]
    actor = make_entity(1)
    intent = ResourceTransferIntent(source_id=node.id, source_kind="NODE", items_add=[ItemStack(node.yields_item, 1)], transfer_kind="HARVEST")
    result = ResourceTransactionResolver.resolve(replace(state, entities={actor.id: actor}), actor, intent)
    assert result.accepted
    assert result.node_update.charges_delta == -1  # one charge spent ...
    assert result.inventory_update.items_add == [ItemStack(node.yields_item, 1)]  # ... for exactly one item gained


def test_a_stripped_node_regrows_and_reports_recovery_through_the_ecology_process():
    state = _state(WILD_WORLD)
    node = _food_nodes(state)[0]
    stripped = replace(state, tick=ResourceEcologyService.ECOLOGY_INTERVAL,
                       resource_nodes={**state.resource_nodes, node.id: replace(node, remaining_charges=0, cooldown_remaining=0)})
    refined = AuthoritativeApplyPipeline.refine(stripped, StateUpdate())
    assert refined.node_updates[node.id].charges_delta == 1
    assert [e.subject for e in refined.world_events_add if e.category == WorldEventCategory.RESOURCE_RECOVERED] == [str(node.id)]


WORLDS_WITH_RESOLVED_SPEC = sorted(p.parent.name for p in __import__("pathlib").Path("data/worlds").glob("*/resolved"))
SETTLEMENT_KINDS = {"TOWN"}


@pytest.mark.parametrize("world", WORLDS_WITH_RESOLVED_SPEC)
@pytest.mark.parametrize("seed", [42, 43, 44])
def test_no_food_node_stands_on_a_tile_a_settlement_region_owns(world, seed):
    state = _state(world, seed)
    for node in _food_nodes(state):
        owner = LegalityServiceV2.get_region_for_position(node.position, state)
        assert owner is not None and owner.kind not in SETTLEMENT_KINDS, (world, seed, node.position, owner and owner.id)
        assert owner.id == "near_forest"


@pytest.mark.parametrize("world", ["frontier_living_world", "wilderness_survival", "sandbox_world"])
def test_the_placement_rule_changes_only_the_food_node(world):
    """A kind without the placement field keeps its exact draws: everything but the food node compiles the same with the rule off."""
    def compiled(rule_on):
        spec, ctx = WorldRepository("data/worlds").load_world_with_context(world)
        if not rule_on:
            for profile in ctx.resources.values():
                profile.placement = None
        state, _ = WorldCompiler.compile(spec, 42, context=ctx)
        return replace(state, resource_nodes={i: n for i, n in state.resource_nodes.items() if n.kind != FOOD_KIND})
    assert repr(compiled(True)) == repr(compiled(False))


def test_the_compiled_positions_are_the_same_on_a_second_compile():
    first = [(n.position, n.id) for n in _food_nodes(_state(WILD_WORLD, 45))]
    spec, ctx = WorldRepository("data/worlds").load_world_with_context(WILD_WORLD)
    state, _ = WorldCompiler.compile(spec, 45, context=ctx)
    assert first == [(n.position, n.id) for n in _food_nodes(state)]


class _Region:
    def __init__(self, region_id, bounds):
        self.id, self.bounds = region_id, bounds


class _Rng:
    def __init__(self):
        self.calls = 0

    def get_int(self, domain, tick, entity_id, lo, hi, sub_id=0):
        self.calls += 1
        return lo + (sub_id % (hi - lo + 1))


def test_an_owned_first_draw_costs_no_extra_draw():
    rng = _Rng()
    assert _draw_tile_owned_by(rng, 1, [_Region("wild", (0, 0, 9, 9))], "wild", (3, 4), (0, 0, 9, 9)) == (3, 4)
    assert rng.calls == 0


def test_a_region_that_owns_no_tile_is_given_up_after_the_bounded_draws_and_places_nothing():
    rng = _Rng()
    ordered = [_Region("town", (0, 0, 9, 9)), _Region("wild", (0, 0, 9, 9))]  # the town owns every tile of the wild box
    assert _draw_tile_owned_by(rng, 1, ordered, "wild", (3, 4), (0, 0, 9, 9)) is None
    assert rng.calls == 2 * (RESOURCE_PLACEMENT_ATTEMPTS - 1)
