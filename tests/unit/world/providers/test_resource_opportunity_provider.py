# Tests for TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP
# Covers: ResourceOpportunityProvider surfaces the new stone_outcrop catalog resource, and the
# defense-in-depth .contains() guard at src/world/providers/resources.py:60 skips (rather than
# crashes on) an unregistered node kind.
from dataclasses import dataclass

from src.core.builder import V2EntityBuilder
from src.core.state import ResourceNodeState
from src.world.providers.resources import ResourceOpportunityProvider


@dataclass
class MockState:
    resource_nodes: dict


def _hero_in_region(region_id: str):
    ent = V2EntityBuilder(1).kind("hero").build()
    object.__setattr__(ent.navigation, "region_id", region_id)
    return ent


def test_stone_outcrop_node_surfaces_as_opportunity_in_frontier_village():
    """Post-fix, stone_outcrop is a real registered resource with
    source_region_tags=("frontier_village",) (data/content/world/resources.yaml). A node of this
    kind must resolve through ResourceRegistry without a KeyError and surface as an opportunity."""
    ent = _hero_in_region("frontier_village")
    node = ResourceNodeState(
        id=1, kind="stone_outcrop", position=(0.0, 0.0),
        yields_item="stone", remaining_charges=10, max_charges=10, required_ticks=10,
    )
    state = MockState(resource_nodes={1: node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, state)

    assert len(opportunities) == 1
    assert opportunities[0].kind == "gather_resource"
    assert opportunities[0].subject == "stone"


def test_unregistered_node_kind_is_skipped_not_crashed():
    """Defense-in-depth guard: an ad hoc/unregistered `kind` (e.g. a stale test fixture or a
    future emission-site regression) must be silently skipped by the .contains() guard, not raise
    KeyError, matching src/town/guild.py and src/engine/intent/action_intent.py's guard pattern."""
    ent = _hero_in_region("frontier_village")
    bad_node = ResourceNodeState(
        id=1, kind="totally_unknown_kind", position=(0.0, 0.0),
        yields_item="mystery", remaining_charges=10, max_charges=10, required_ticks=10,
    )
    state = MockState(resource_nodes={1: bad_node})

    opportunities = ResourceOpportunityProvider.get_opportunities(ent, state)

    assert opportunities == []
