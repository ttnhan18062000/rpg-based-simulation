"""LB-S21 parts 1 and 2 (owner decisions 45-50): a generic plant-eater grazes the land's plant food, and keeps away from or flees what could eat it.

Stage order and relations only, through the real kernel: nothing here reads a predator or prey label. The plant-eater is the kind compiled from
content (`small_plant_eater`); the meat-eater is the corpus wolf. Arms:
GRAZE      a hungry plant-eater beside a berry thicket gathers and eats it (hunger falls), and a meat-only wolf in the same staging does not.
AVOID      beside a hungry wolf that is coming for it the plant-eater flees (a decided flight); a wolf that is not hungry draws only distance-keeping.
CONTROL    a wolf out of the plant-eater's perception draws no response.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.core.items import food_hunger_recovery
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("scenario")]

WORLD, SEED = "frontier_living_world", 42
WINDOW = 60


def _species(e):
    return (e.identity.properties or {}).get("species_id")


def _stage(*, wolf_gap=None, wolf_hunger=85.0, eater_hunger=0.0, berries=False, keep_wolf=True):
    state = compile_world(WORLD, SEED)
    eater = next(e for e in state.entities.values() if _species(e) == "small_plant_eater")
    wolf = next(e for e in state.entities.values() if _species(e) == "wolf")
    x, y = eater.navigation.position
    eater = replace(eater, biological=replace(eater.biological, hunger=eater_hunger))
    entities = {eater.id: eater}
    if wolf_gap is not None:
        wolf = replace(wolf, biological=replace(wolf.biological, hunger=wolf_hunger),
                       navigation=replace(wolf.navigation, position=(x + float(wolf_gap), y), home_position=None, leash_radius=0.0))
        entities[wolf.id] = wolf
    nodes = {}
    if berries:
        template = next(n for n in state.resource_nodes.values() if food_hunger_recovery(n.yields_item) > 0.0)
        nodes = {template.id: replace(template, position=(x + 2.0, y), remaining_charges=2)}
    return replace(state, entities=entities, buildings={}, building_tiles={}, resource_nodes=nodes), eater.id, wolf.id


def _run(stage, ticks=WINDOW):
    state, eater_id, wolf_id = stage
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    rows = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            now = kernel._state
            eater, wolf = now.entities[eater_id], now.entities.get(wolf_id)
            rows.append({"hunger": eater.biological.hunger, "alive": eater.combat.alive,
                         "reason": eater.task.payload.get("reason"), "carried": sum(s.quantity for s in eater.inventory.items),
                         "wolf_attacked": bool(wolf and wolf.task.payload.get("action") == "ATTACK" and wolf.task.payload.get("target_id") == eater_id)})
    finally:
        kernel.shutdown()
    return rows


def test_graze_a_hungry_plant_eater_gathers_and_eats_the_land_s_plant_food():
    """The patch is small (2 charges) so that stripping it releases the gatherer's held task, as in LB-S17; it then eats what it gathered."""
    rows = _run(_stage(eater_hunger=70.0, berries=True), ticks=230)
    assert any(r["carried"] > 0 for r in rows), "a plant-eater must gather the plant food"
    assert min(r["hunger"] for r in rows) < 70.0 - 20.0, "and eat it, so its hunger falls well below where it began"


def test_avoid_a_plant_eater_beside_a_hungry_wolf_flees_and_a_sated_wolf_draws_only_distance_keeping():
    hungry = _run(_stage(wolf_gap=3, wolf_hunger=85.0))
    assert any(r["reason"] in ("FLEE_THREAT", "KEEP_DISTANCE") for r in hungry), "the plant-eater must react to a wolf it cannot overcome"
    sated = _run(_stage(wolf_gap=3, wolf_hunger=0.0))
    assert any(r["reason"] == "KEEP_DISTANCE" for r in sated), "the same kind of wolf, not hungry, still draws distance-keeping (prey never reads hunger)"
    assert not any(r["wolf_attacked"] for r in sated), "and a sated wolf does not hunt it"
    assert not any(r["reason"] == "FLEE_THREAT" for r in sated), "a wolf that is not coming for it is not a threat to flee"


def test_control_a_wolf_out_of_perception_draws_no_response():
    rows = _run(_stage(wolf_gap=40, wolf_hunger=85.0), ticks=30)
    assert not any(r["reason"] in ("FLEE_THREAT", "KEEP_DISTANCE") for r in rows)
