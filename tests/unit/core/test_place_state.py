"""TCK-20260902-PLACE-SCHEMA-MIGRATION: PlaceState/PlaceKind schema and RegionState.places
membership. Schema-only ticket (idea 66) -- no WorldCompiler wiring or content migration yet,
see docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md.
"""
from dataclasses import replace as dataclass_replace

from src.core.state import (
    AuthoritativeState, BuildingState, CombatComponent, EntityState,
    PlaceKind, PlaceState, RegionState,
)
from src.core.builder import V2EntityBuilder
from src.engine.checkpoint import CanonicalStateHasher


def test_place_state_construction_minimal():
    """A PlaceState can be constructed with only the required fields; all optional
    fields default sensibly per kind (per the Target Shape's per-kind optionality)."""
    place = PlaceState(place_id="p1", region_id="r1", kind=PlaceKind.CITY, position=(5.0, 5.0))
    assert place.place_id == "p1"
    assert place.region_id == "r1"
    assert place.kind == PlaceKind.CITY
    assert place.footprint is None
    assert place.owner_faction_id is None
    assert place.scale is None
    assert place.maturity is None
    assert place.occupant_entity_id is None
    assert place.hazard_level is None
    assert place.building_ids == set()
    assert place.entity_ids == set()
    assert place.prior_kind is None
    assert place.transformed_tick is None


def test_place_state_all_kinds_constructible():
    """All 7 PlaceKind values (CITY | CAMP | NEST | LAIR | RUIN | DUNGEON | LANDMARK) per
    the Target Shape construct without error."""
    for kind in PlaceKind:
        place = PlaceState(place_id=f"p_{kind.value}", region_id="r1", kind=kind, position=(0.0, 0.0))
        assert place.kind == kind


def test_place_state_transformation_trail():
    """prior_kind/transformed_tick (2026-09-02 direction-alignment audit extension) --
    a City destroyed into a Ruin carries legible trace of what it used to be."""
    ruin = PlaceState(
        place_id="p1", region_id="r1", kind=PlaceKind.RUIN, position=(0.0, 0.0),
        prior_kind=PlaceKind.CITY, transformed_tick=500,
    )
    assert ruin.prior_kind == PlaceKind.CITY
    assert ruin.transformed_tick == 500


def test_region_state_places_membership_list():
    """RegionState.places holds ordered place_id references -- the forward half of the
    dual-sided membership decision. A Region can hold zero or many Places."""
    empty_region = RegionState(id="r1", name="Wilderness", bounds=(0, 0, 10, 10))
    assert empty_region.places == []

    multi_place_region = RegionState(
        id="r2", name="Frontier", bounds=(0, 0, 20, 20), places=["p1", "p2", "p3"],
    )
    assert multi_place_region.places == ["p1", "p2", "p3"]


def test_place_id_back_reference_on_navigation_and_building():
    """The back-reference half of the dual-sided membership decision: entities get a
    cached place_id on NavigationComponent (mirroring region_id), buildings get one on
    BuildingState (new -- no prior region containment field existed for buildings)."""
    entity = V2EntityBuilder(1).build()
    assert entity.navigation.place_id is None
    entity_in_place = dataclass_replace(entity, navigation=dataclass_replace(entity.navigation, place_id="p1"))
    assert entity_in_place.navigation.place_id == "p1"

    building = BuildingState(id=1, kind="SHOP", position=(1.0, 1.0))
    assert building.place_id is None
    building_in_place = dataclass_replace(building, place_id="p1")
    assert building_in_place.place_id == "p1"


def test_place_state_participates_in_canonical_hash():
    """A PlaceState's presence in AuthoritativeState.places changes
    CanonicalStateHasher.get_hash() output -- coverage from day one, per this ticket's own
    scope guard against repeating the Social/Knowledge canonical-hash gap pattern."""
    place = PlaceState(place_id="p1", region_id="r1", kind=PlaceKind.CITY, position=(5.0, 5.0))
    region = RegionState(id="r1", name="Test Region", bounds=(0, 0, 10, 10), places=["p1"])

    state_with_place = AuthoritativeState(tick=0, seed=1, regions={"r1": region}, places={"p1": place})
    state_without_place = AuthoritativeState(tick=0, seed=1, regions={"r1": region}, places={})

    assert (
        CanonicalStateHasher.get_hash(state_with_place)
        != CanonicalStateHasher.get_hash(state_without_place)
    )


def test_place_state_field_divergence_participates_in_canonical_hash():
    """Each PlaceState field independently changes to_canonical_dict() output when it
    diverges -- confirms no field was silently left uncovered."""
    base = PlaceState(place_id="p1", region_id="r1", kind=PlaceKind.CITY, position=(0.0, 0.0))
    base_dict = base.to_canonical_dict()

    variants = {
        "kind": dataclass_replace(base, kind=PlaceKind.RUIN),
        "position": dataclass_replace(base, position=(9.0, 9.0)),
        "footprint": dataclass_replace(base, footprint=(0, 0, 5, 5)),
        "owner_faction_id": dataclass_replace(base, owner_faction_id=42),
        "scale": dataclass_replace(base, scale=3.0),
        "maturity": dataclass_replace(base, maturity=0.8),
        "occupant_entity_id": dataclass_replace(base, occupant_entity_id=7),
        "hazard_level": dataclass_replace(base, hazard_level=0.5),
        "building_ids": dataclass_replace(base, building_ids={1, 2}),
        "entity_ids": dataclass_replace(base, entity_ids={3, 4}),
        "prior_kind": dataclass_replace(base, prior_kind=PlaceKind.CAMP),
        "transformed_tick": dataclass_replace(base, transformed_tick=100),
    }

    for field_name, changed in variants.items():
        assert base_dict != changed.to_canonical_dict(), (
            f"'{field_name}' divergence did not change to_canonical_dict() output"
        )


def test_region_state_places_participates_in_canonical_hash():
    """RegionState.places itself (the forward-list half) is covered by
    RegionState.to_canonical_dict() -- not just the Place objects it references."""
    empty = RegionState(id="r1", name="Test", bounds=(0, 0, 10, 10))
    with_place = RegionState(id="r1", name="Test", bounds=(0, 0, 10, 10), places=["p1"])

    assert empty.to_canonical_dict() != with_place.to_canonical_dict()


def test_navigation_place_id_participates_in_canonical_hash_end_to_end():
    """place_id specifically gets explicit canonical-dict coverage even though
    NavigationComponent's own region_id (and most other fields) are NOT covered -- a
    separate, pre-existing gap (TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP) this new
    field must not silently inherit."""
    entity = EntityState(id=1, kind="hero", combat=CombatComponent(hp=100, max_hp=100, alive=True))
    assert entity.navigation.place_id is None

    with_place = dataclass_replace(entity, navigation=dataclass_replace(entity.navigation, place_id="p1"))

    state_base = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: entity})
    state_with_place = AuthoritativeState(tick=1, seed=1, world_time=0, entities={1: with_place})

    assert (
        CanonicalStateHasher.get_hash(state_base)
        != CanonicalStateHasher.get_hash(state_with_place)
    )
