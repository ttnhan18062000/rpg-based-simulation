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


def test_lair_kind_place_compiles_via_worldcompiler():
    """Synthetic fixture (not real corpus content, per TCK-20260904-LAIR-ENTITY-ANCHOR's
    Option-A/content decision -- see stored_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/plan.md)
    proving a LAIR-kind PlaceSpec compiles to a real PlaceState with occupant_entity_id
    defaulting to None (unwritten in that ticket -- Option A keys Lair occupancy off
    entity-side identity.properties, not this field)."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="lair", position=(5, 5))],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    place = state.places["p1"]
    assert place.kind == PlaceKind.LAIR
    assert place.occupant_entity_id is None


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


# TCK-20260904-CAMPSTATE-PLACE-BRIDGE: WorldCompiler.compile() now builds a companion
# CampState alongside a PlaceState(kind=CAMP/NEST) whenever content sets the new,
# opt-in PlaceSpec.creature_kind field. Inert for all content that doesn't set it
# (including hero_guild_routing's real goblin_camp_place, above) -- see plan.md's
# Gameplay-Activation Risk Decision.

def test_camp_kind_place_compiles_to_companion_campstate():
    """A CAMP-kind PlaceSpec with creature_kind set produces both a PlaceState and a
    linked CampState, keyed by the same place_id."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="camp", position=(5, 5), creature_kind="goblin")],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert "p1" in state.places
    assert state.places["p1"].kind == PlaceKind.CAMP
    assert "p1" in state.camps
    camp = state.camps["p1"]
    assert camp.kind == "goblin"
    assert camp.position == (5.0, 5.0)


def test_nest_kind_place_compiles_to_companion_campstate():
    """A NEST-kind PlaceSpec with a Nest-classified race carries through end-to-end,
    preserving CampService.NEST_RACE_KINDS membership."""
    from src.world.camp import CampService

    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="nest", position=(5, 5), creature_kind="wolf")],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.places["p1"].kind == PlaceKind.NEST
    assert state.camps["p1"].kind in CampService.NEST_RACE_KINDS


def test_non_camp_nest_place_kinds_do_not_construct_campstate():
    """The Camp bridge is strictly scoped to CAMP/NEST kinds -- CITY/RUIN/DUNGEON/
    LANDMARK/LAIR never produce a CampState entry."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 20, 20),
            places=[
                PlaceSpec(id="p1", kind="city", position=(1, 1)),
                PlaceSpec(id="p2", kind="ruin", position=(2, 2)),
                PlaceSpec(id="p3", kind="dungeon", position=(3, 3)),
                PlaceSpec(id="p4", kind="landmark", position=(4, 4)),
                PlaceSpec(id="p5", kind="lair", position=(5, 5)),
            ],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.camps == {}


def test_non_place_shaped_content_compiles_unchanged_with_camp_bridge():
    """Extends test_non_place_shaped_content_compiles_unchanged: a region with no
    places at all still compiles with camps == {} alongside places == {}."""
    spec = _minimal_spec([
        RegionSpec(id="r1", type="town", bounds=(0, 0, 10, 10)),
        RegionSpec(id="r2", type="wilderness", bounds=(11, 0, 20, 10)),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.places == {}
    assert state.camps == {}


def test_campstate_place_linkage_round_trips_via_place_id():
    """Given a place_id, both state.places[place_id] and state.camps[place_id] resolve
    and share the same key -- the linkage scheme this ticket's plan.md chose."""
    spec = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="camp", position=(5, 5), creature_kind="orc")],
        ),
    ])

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.places["p1"].place_id == "p1"
    assert state.camps["p1"].id == "p1"


def test_invalid_creature_race_rejected_at_schema_level():
    """PlaceSpec.creature_kind must be one of the Camp+Nest race set -- content
    authoring errors are caught at schema validation, not silently accepted."""
    with pytest.raises(Exception):
        PlaceSpec(id="p1", kind="camp", position=(0, 0), creature_kind="dragon")


def test_creature_kind_field_is_none_for_non_camp_nest_place_kinds():
    """The new field stays Optional/unset for non-Camp/Nest PlaceSpecs, confirming it
    doesn't become an accidental required field breaking existing content."""
    place = PlaceSpec(id="p1", kind="city", position=(0, 0))
    assert place.creature_kind is None

    spec = _minimal_spec([
        RegionSpec(id="r1", type="wilderness", bounds=(0, 0, 10, 10), places=[place]),
    ])
    state, _ = WorldCompiler.compile(spec, seed=42)
    assert state.camps == {}


def test_campstate_place_bridge_participates_in_canonical_hash():
    """A CAMP-kind Place with creature_kind set produces a different state_hash than the
    same world without it -- mirrors test_place_participates_in_canonical_hash."""
    with_camp = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="camp", position=(5, 5), creature_kind="goblin")],
        ),
    ])
    without_camp = _minimal_spec([
        RegionSpec(
            id="r1", type="wilderness", bounds=(0, 0, 10, 10),
            places=[PlaceSpec(id="p1", kind="camp", position=(5, 5))],
        ),
    ])

    state_with, _ = WorldCompiler.compile(with_camp, seed=42)
    state_without, _ = WorldCompiler.compile(without_camp, seed=42)

    assert (
        CanonicalStateHasher.get_hash(state_with)
        != CanonicalStateHasher.get_hash(state_without)
    )
