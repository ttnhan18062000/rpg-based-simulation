"""TCK-20260902-WORLDCOMPILER-PLACE-WIRING: wires WorldCompiler.compile() to construct
real PlaceState instances from Place-shaped content (idea 66, child 2/5). Covers both
compilation paths documented in docs/world/compiler_contract.md: the Direct path
(WorldSpec -> WorldCompiler.compile()) here, and the Composition path
(WorldModuleSpec -> WorldAssemblyResolver -> WorldSpec, round-tripping through the same
compile() call) in tests/unit/worldassembly/test_resolver.py's sibling test.
"""
import pytest

from src.worldbuilding.schema import WorldSpec, TopologySpec, RegionSpec, PlaceSpec, load_world_spec_from_yaml
from src.worldbuilding.compiler import WorldCompiler
from src.core.state import PlaceKind
from src.engine.checkpoint import CanonicalStateHasher


def _minimal_spec(regions):
    return WorldSpec(
        schema_version="worldspec.v1",
        world_id="test_place_wiring",
        name="Test Place Wiring",
        topology=TopologySpec(width=30, height=30, coordinate_system="grid"),
        regions=regions,
    )


def test_place_shaped_region_compiles_to_real_place_state():
    """A region declaring a Place produces a real PlaceState in AuthoritativeState.places,
    linked to its parent region via the dual-sided membership decision."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="city", position=(5, 5), scale=2.0)],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert "p1" in state.places
    place = state.places["p1"]
    assert place.kind == PlaceKind.CITY
    assert place.region_id == "r1"
    assert place.position == (5.0, 5.0)
    assert place.scale == 2.0
    assert state.regions["r1"].places == ["p1"]


def test_multiple_places_in_one_region():
    """A region can hold zero or many Places, per idea 66's Target Shape."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 20, 20),
            places=[
                PlaceSpec(id="p1", kind="city", position=(5, 5)),
                PlaceSpec(id="p2", kind="ruin", position=(15, 15), hazard_level=3.5),
                PlaceSpec(id="p3", kind="camp", position=(10, 2), maturity=0.4),
            ],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert set(state.places.keys()) == {"p1", "p2", "p3"}
    assert state.regions["r1"].places == ["p1", "p2", "p3"]
    assert state.places["p2"].hazard_level == 3.5
    assert state.places["p3"].maturity == 0.4


def test_non_place_shaped_content_compiles_unchanged():
    """Acceptance Criteria: existing (non-Place-shaped) content still compiles unchanged
    -- no regression to current worlds until they are explicitly migrated (pilot tickets)."""
    spec = _minimal_spec([
        RegionSpec(id="r1", type="town", bounds=(0, 0, 10, 10)),
        RegionSpec(id="r2", type="wilderness", bounds=(11, 0, 20, 10)),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.places == {}
    assert state.regions["r1"].places == []
    assert state.regions["r2"].places == []


def test_place_shaped_and_non_place_shaped_regions_coexist():
    """A world may mix Place-shaped and legacy-flat regions -- confirms the compiler
    doesn't force an all-or-nothing choice within one world."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="lair", position=(5, 5), owner_faction_id="99")],
        ),
        RegionSpec(id="r2", type="town", bounds=(11, 0, 20, 10)),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.regions["r1"].places == ["p1"]
    assert state.regions["r2"].places == []
    assert state.places["p1"].owner_faction_id == 99


def test_place_participates_in_canonical_hash():
    """A Place-shaped world produces a different state_hash than the same world without
    the Place -- coverage from day one, per this ticket's own scope guard."""
    with_place = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="city", position=(5, 5))],
        ),
    ])
    without_place = _minimal_spec([
        RegionSpec(id="r1", type="wilderness", bounds=(0, 0, 10, 10)),
    ])

    state_with, _ = WorldCompiler.compile(with_place, seed=42)
    state_without, _ = WorldCompiler.compile(without_place, seed=42)

    assert (
        CanonicalStateHasher.get_hash(state_with)
        != CanonicalStateHasher.get_hash(state_without)
    )


def test_invalid_place_kind_rejected_at_schema_level():
    """PlaceSpec.kind must be one of the 7 real PlaceKind values -- content authoring
    errors are caught at schema validation, not silently accepted."""
    with pytest.raises(Exception):
        PlaceSpec(id="p1", kind="not_a_real_kind", position=(0, 0))


def test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds():
    """TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT's own acceptance criterion: Stage B
    (hero_guild_routing) compiles correctly with all 4 non-uniform region kinds
    represented as the expected Place.kind values, verified by direct inspection. Uses
    the real, already-resolved content on disk (not a synthetic spec) -- this is a
    regression guard on the actual migrated content, not just the mechanism."""
    resolved_path = "data/worlds/hero_guild_routing/resolved/world.resolved.yaml"
    spec = load_world_spec_from_yaml(resolved_path)

    places_by_region = {r.id: r.places for r in spec.regions}

    # hometown (frontier_village_core): CITY
    hometown_places = places_by_region["hometown"]
    assert len(hometown_places) == 1
    assert hometown_places[0].kind == "CITY"

    # goblin_camp: CAMP
    goblin_places = places_by_region["goblin_camp"]
    assert len(goblin_places) == 1
    assert goblin_places[0].kind == "CAMP"

    # haunted_battlefield (ruins_mystery_quest): RUIN
    ruin_places = places_by_region["haunted_battlefield"]
    assert len(ruin_places) == 1
    assert ruin_places[0].kind == "RUIN"

    # mountain_pass_zone: intentionally zero Places -- pure transit terrain, the "or
    # none at all" case from idea 66's own Target Shape.
    mountain_places = places_by_region["mountain_pass_zone"]
    assert mountain_places == []

    # Confirms this real content actually compiles end-to-end.
    state, report = WorldCompiler.compile(spec, seed=42)
    assert report["place_count"] == 3
    assert set(state.places.keys()) == {"hometown_city", "goblin_camp_place", "haunted_battlefield_ruin"}
