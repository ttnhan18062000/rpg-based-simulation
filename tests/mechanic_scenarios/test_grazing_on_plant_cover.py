"""LB-S22 (owner row 59, grazing): wild land carries plant cover that a grazing diet eats and a person's diet does not.

Through the real kernel on the compiled world; nothing reads a kind name, only diet and food class. Arms:
COMPILE   every region whose biome declares cover has its patches, a number set by the cover kind's density over the region's bounds.
GRAZE     a hungry plant-eater beside a patch (and no berries) gathers and eats it; a hungry person in the same staging takes none of it.
BARE      a patch eaten to zero stays bare for its declared wait, and when the wait ends it gains no charges: the ecology regrowth resumes from zero.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldassembly.cover import patch_count
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("world"), pytest.mark.level("scenario")]

WORLD, SEED = "frontier_living_world", 42
GRASS = "grass_cover"


def _species(e):
    return (e.identity.properties or {}).get("species_id")


def _patches(state):
    return [n for n in state.resource_nodes.values() if n.yields_item == GRASS]


def test_compile_every_cover_region_has_its_patches_with_the_declared_charges_and_regrowth():
    state = compile_world(WORLD, SEED)
    patches = _patches(state)
    assert patches, "a world with a near_forest region must carry cover"
    assert all(n.regrowth_mode == "regrow" and n.respawn_cooldown > 0 and n.regen_rate_per_tick > 0 for n in patches)
    assert all(n.remaining_charges == n.max_charges for n in patches)
    forest = next(r for r in state.regions.values() if r.id.endswith("near_forest"))
    assert len(patches) == patch_count(forest.bounds, 4), "one patch count per region, from the cover kind's density over the region's bounds"


def _stage(species, *, hunger, charges=2, wait=None, regen=None):
    state = compile_world(WORLD, SEED)
    subject = next(e for e in state.entities.values() if _species(e) == species)
    x, y = subject.navigation.position
    subject = replace(subject, biological=replace(subject.biological, hunger=hunger),
                      navigation=replace(subject.navigation, home_position=None, leash_radius=0.0))
    template = _patches(state)[0]
    patch = replace(template, position=(x + 2.0, y), remaining_charges=charges, max_charges=max(charges, template.max_charges))
    if wait is not None:
        patch = replace(patch, respawn_cooldown=wait)
    if regen is not None:
        patch = replace(patch, regen_rate_per_tick=regen)  # staged so a held gatherer's patch empties (LB-S17: a gatherer on a regrowing node is not released)
    return replace(state, entities={subject.id: subject}, buildings={}, building_tiles={}, resource_nodes={patch.id: patch}), subject.id, patch.id


def _run(stage, ticks):
    state, subject_id, patch_id = stage
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    rows = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            now = kernel._state
            who, patch = now.entities[subject_id], now.resource_nodes[patch_id]
            rows.append({"tick": now.tick, "hunger": who.biological.hunger,
                         "carried_grass": sum(s.quantity for s in who.inventory.items if s.item_id == GRASS),
                         "charges": patch.remaining_charges, "cooldown": patch.cooldown_remaining})
    finally:
        kernel.shutdown()
    return rows


def test_graze_a_hungry_plant_eater_eats_the_cover_and_a_person_takes_none_of_it():
    grazer = _run(_stage("small_plant_eater", hunger=70.0, regen=0), ticks=260)
    assert min(r["charges"] for r in grazer) < 2, "the grazer must take from the patch"
    assert min(r["hunger"] for r in grazer) < 70.0 - 15.0, "and eat it"
    person = _run(_stage("human", hunger=70.0, regen=0), ticks=120)
    assert all(r["charges"] == 2 for r in person), "a person's diet does not take plant cover"
    assert all(r["carried_grass"] == 0 for r in person)


def test_bare_a_patch_eaten_to_zero_waits_bare_then_regrows_from_zero_never_refills():
    wait = 40
    rows = _run(_stage("small_plant_eater", hunger=70.0, charges=1, wait=wait, regen=1), ticks=330)
    emptied = next(i for i, r in enumerate(rows) if r["charges"] == 0 and r["cooldown"] > 0)
    assert rows[emptied]["cooldown"] >= wait - 2, "emptying the patch starts the declared bare wait"
    ended = next(i for i, r in enumerate(rows) if i > emptied and r["cooldown"] == 0)
    assert rows[ended]["charges"] == 0, "the wait ends with nothing added: regrowth resumes from zero, it does not refill"
    regrown = [r["charges"] for r in rows[ended:]]
    assert max(regrown) > 0 and max(regrown) < 20, "and the ecology regrowth then adds charges a step at a time"
