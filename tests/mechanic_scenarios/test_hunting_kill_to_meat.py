"""LB-S20 (owner decisions 44, 46, 47): a hungry meat-eater hunts a creature it can eat and believes it can overcome, the kill leaves meat
on the carcass, and the meat-eater eats it where it lies, so its hunger falls. Nothing names a predator or a prey: the hunt is derived
from declared properties (diet, edibility, power band) and the subject's KNOW-04 belief about the other kind.

Four arms of the same staging (a lone meat-eater and one other creature, no building, no food node, through the real kernel; an arm judges the meat-eater's own attacks, because a free creature wanders on its own):
MAIN       hungry meat-eater + a creature of a kind it believes it can overcome: the creature dies, a carcass with meat appears, the meat is
           eaten at the carcass and hunger falls by what that meat gives.
CONTROL    the same, but the meat-eater is not hungry: nothing is hunted.
DERIVATION the same hungry meat-eater beside a creature of a kind it believes more dangerous: it does not attack, and no flag is read.
DIET       a hungry meat-eater beside berries and no creature: it forages nothing and its hunger does not fall.
Observables are authoritative state per tick (stage order and relations), not log lines; the wolf's own stats decide the fight, so the prey is
staged weak enough that the fight is not the thing under test.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.engine.behavior_consumers import get_kind_properties

from src.config.profiles import PROD_SMALL
from src.core.items import food_hunger_recovery
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("scenario")]

WORLD, SEED = "frontier_living_world", 42
HUNGRY, FED = 85.0, 0.0
WINDOW = 80
PLAIN_RADIUS = 20  # tiles of plain around the pair


def _species(entity):
    return (entity.identity.properties or {}).get("species_id")


def _stage(*, hunger, prey_species="goblin", with_prey=True, berries=False):
    state = compile_world(WORLD, SEED)
    wolf = next(e for e in state.entities.values() if _species(e) == "wolf")
    prey = next(e for e in state.entities.values() if _species(e) == "goblin")
    x, y = wolf.navigation.position
    wolf = replace(wolf, biological=replace(wolf.biological, hunger=hunger))
    prey = replace(prey, navigation=replace(prey.navigation, position=(x + 4.0, y), target=None),
                   combat=replace(prey.combat, hp=5, max_hp=5),
                   identity=replace(prey.identity, properties={**prey.identity.properties, "species_id": prey_species}))
    entities = {wolf.id: wolf, **({prey.id: prey} if with_prey else {})}
    nodes = {}
    if berries:
        template = next(n for n in state.resource_nodes.values() if food_hunger_recovery(n.yields_item) > 0.0)
        nodes = {template.id: replace(template, position=(x + 2.0, y), remaining_charges=4)}
    # Staged on plain so the test is about hunting, not terrain time (D75); terrain slowing is covered in test_terrain_cost_is_time.py.
    terrain = {**state.terrain, **{(int(x) + dx, int(y) + dy): "plain" for dx in range(-PLAIN_RADIUS, PLAIN_RADIUS + 1)
                                   for dy in range(-PLAIN_RADIUS, PLAIN_RADIUS + 1)}}
    return replace(state, entities=entities, buildings={}, building_tiles={}, resource_nodes=nodes, terrain=terrain), wolf.id, prey.id


def _run(stage, ticks=WINDOW):
    state, wolf_id, prey_id = stage
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True}, executor=LocalSequentialExecutor(), governor=PinnedNormalGovernor())
    rows = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            now = kernel._state
            wolf, prey = now.entities[wolf_id], now.entities.get(prey_id)
            rows.append({"tick": now.tick, "attacked": wolf.task.payload.get("action") == "ATTACK" and wolf.task.payload.get("target_id") == prey_id, "hunger": wolf.biological.hunger, "prey_alive": prey.combat.alive if prey else None,
                         "carried": sum(s.quantity for s in wolf.inventory.items),
                         "corpses": {c.id: tuple((s.item_id, s.quantity) for s in c.items) for c in now.corpses.values()}})
    finally:
        kernel.shutdown()
    return rows, prey_id


def test_main_a_hungry_meat_eater_kills_leaves_meat_and_eats_it_at_the_carcass():
    rows, prey_id = _run(_stage(hunger=HUNGRY))
    killed = next(i for i, r in enumerate(rows) if r["prey_alive"] is False)
    carcass_id = 1000000 + prey_id
    declared = get_kind_properties("goblin")[1].meat_yield  # what the prey's body declares, not a figure in the test
    assert ("raw_meat", declared) in rows[killed]["corpses"][carcass_id], "the kill must leave the meat its body declares"
    eaten = next(i for i, r in enumerate(rows) if i >= killed and "raw_meat" not in dict(r["corpses"].get(carcass_id, ())))
    assert eaten > killed, "the meat leaves the carcass only after the kill, by being eaten"
    before = max(r["hunger"] for r in rows[killed:eaten])
    assert min(r["hunger"] for r in rows[eaten:]) <= before - food_hunger_recovery("raw_meat") + 2.0, "eating the meat must lower hunger by what it gives"


def test_a_kill_leads_to_the_meal_at_the_same_hunger_the_hunt_starts_at():
    """One gate for the hunt and the meal: a meat-eater at a moderate hunger that kills eats that same carcass within a bounded number of ticks."""
    rows, prey_id = _run(_stage(hunger=60.0), ticks=120)
    killed = next(i for i, r in enumerate(rows) if r["prey_alive"] is False)
    carcass_id = 1000000 + prey_id
    eaten = next((i for i, r in enumerate(rows) if i >= killed and "raw_meat" not in dict(r["corpses"].get(carcass_id, ()))), None)
    assert eaten is not None and eaten - killed <= 40, "a kill must be eaten soon after, at the hunger it was hunted at"


def test_control_a_fed_meat_eater_hunts_nothing():
    rows, _ = _run(_stage(hunger=FED))
    assert not any(r["attacked"] for r in rows), "a meat-eater that is not hungry does not go after the creature"


def test_derivation_a_hungry_meat_eater_does_not_hunt_a_kind_it_believes_more_dangerous():
    rows, _ = _run(_stage(hunger=HUNGRY, prey_species="orc"))
    assert not any(r["attacked"] for r in rows), "no creature of a kind believed more dangerous is hunted, and no label is read"


def test_diet_a_meat_only_kind_forages_no_berries_while_hungry():
    rows, _ = _run(_stage(hunger=HUNGRY, with_prey=False, berries=True))
    assert all(r["carried"] == 0 for r in rows), "a meat-only diet must not gather berries"
    assert rows[-1]["hunger"] > rows[0]["hunger"] - 1.0, "and no berry meal lowers its hunger"
