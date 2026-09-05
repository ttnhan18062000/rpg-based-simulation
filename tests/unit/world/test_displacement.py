"""
Idea 65 ("Named Refugee Threads") + idea 59 ("Home, Exile & Return") — M6
Political Identity epic. DisplacementService relocates living entities out of
a calamity-struck region into their lowest-calamity_intensity neighbor,
carrying home_region_id forward (set once, never overwritten).

Ticket: TCK-20260905-HOME-EXILE-REFUGEE-THREADS
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, RegionState
from src.engine.apply import ApplyPath
from src.systems.world_systems.routine import RoutineService
from src.world.displacement import DisplacementService

THRESHOLD = DisplacementService.DISPLACEMENT_THRESHOLD

# Struck region "A" adjacent to a safer "B" (gap=0<=50) and a far, ignorable "C" (gap=100>50).
_R_A = RegionState(id="A", name="A", bounds=(0, 0, 100, 100), calamity_intensity=THRESHOLD)
_R_B = RegionState(id="B", name="B", bounds=(100, 0, 200, 100), calamity_intensity=0.2)
_R_C = RegionState(id="C", name="C", bounds=(200, 0, 300, 100), calamity_intensity=0.0)


def _entity(entity_id: int, pos: tuple[float, float], home_region_id: str | None = None):
    builder = (V2EntityBuilder(entity_id)
        .kind("villager")
        .location(*pos)
        .identity(faction=Faction.TOWN_COUNCIL)
        .combat(hp=10))
    if home_region_id is not None:
        builder = builder.strategic(home_region_id=home_region_id)
    return builder.build()


def test_noop_when_no_region_crosses_threshold():
    state = AuthoritativeState(tick=1, seed=1, regions={"A": replace(_R_A, calamity_intensity=0.1), "B": _R_B})
    update = DisplacementService.compute_displacement(state)
    assert update.is_noop()


def test_living_entity_in_struck_region_relocated_to_safest_neighbor():
    villager = _entity(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B, "C": _R_C},
                                entities={1: villager})
    update = DisplacementService.compute_displacement(state)
    assert 1 in update.entity_updates
    assert update.entity_updates[1].new_position == _R_B.center


def test_home_region_id_set_to_struck_region_when_previously_unset():
    villager = _entity(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B}, entities={1: villager})
    update = DisplacementService.compute_displacement(state)
    assert update.entity_updates[1].strategic.home_region_id_set == "A"


def test_home_region_id_preserved_when_already_set():
    # A boss-shaped entity whose home is region "C" (far away), currently physically in "A" when
    # it gets struck -- their real home must NOT be overwritten to "A".
    displaced_native = _entity(1, pos=(5.0, 5.0), home_region_id="C")
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B, "C": _R_C},
                                entities={1: displaced_native})
    update = DisplacementService.compute_displacement(state)
    assert update.entity_updates[1].strategic is None


def test_dead_entity_not_displaced():
    corpse = _entity(1, pos=(5.0, 5.0))
    corpse = replace(corpse, combat=replace(corpse.combat, alive=False))
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B}, entities={1: corpse})
    update = DisplacementService.compute_displacement(state)
    assert update.is_noop()


def test_no_safe_neighbor_means_no_displacement():
    isolated = RegionState(id="Z", name="Z", bounds=(1000, 1000, 1100, 1100), calamity_intensity=THRESHOLD)
    villager = _entity(1, pos=(1050.0, 1050.0))
    state = AuthoritativeState(tick=1, seed=1, regions={"Z": isolated}, entities={1: villager})
    update = DisplacementService.compute_displacement(state)
    assert update.is_noop()


def test_compute_displacement_is_deterministic_across_repeated_calls():
    villagers = {i: _entity(i, pos=(5.0, 5.0)) for i in (3, 1, 2)}
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B}, entities=villagers)
    first = DisplacementService.compute_displacement(state)
    second = DisplacementService.compute_displacement(state)
    assert list(first.entity_updates.keys()) == list(second.entity_updates.keys()) == [1, 2, 3]


def test_only_reads_calamity_intensity_never_writes_it():
    villager = _entity(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B}, entities={1: villager})
    update = DisplacementService.compute_displacement(state)
    assert update.world_updates == {}


def test_displaced_entity_return_home_concern_points_at_original_home_not_new_location():
    """End-to-end: a villager with no home_region_id, struck out of region A into safer region
    B by DisplacementService, applied through the real authoritative apply-path (ApplyPath), has
    home_region_id="A" durably set on the post-apply entity -- and RoutineService's pre-existing
    "return home" concern (idea 59's already-wired consumer) correctly targets that original home
    region, not the entity's new physical location in B, once the entity later wanders away from
    B while idle."""
    villager = _entity(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=1, seed=1, regions={"A": _R_A, "B": _R_B}, entities={1: villager})

    displacement_update = DisplacementService.compute_displacement(state)
    next_state = ApplyPath.apply_partial(state, displacement_update)

    displaced = next_state.entities[1]
    assert displaced.strategic.home_region_id == "A"
    assert displaced.navigation.position == _R_B.center

    # Now idle and away from home (still in B, not A) -- RoutineService must ask them to return
    # to "A", their original home, never to "B" (where the write physically relocated them).
    concerns = RoutineService.evaluate_anchored_behavior(displaced, next_state)
    assert any(c.id == "concern_return_home" for c in concerns)
