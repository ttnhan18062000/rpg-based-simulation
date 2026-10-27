"""Same-seed parity of the v3 proof digest over a state whose carried-state fields are populated
(TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS).

The metropolis scenario populates at most `recent_world_events`, and only after a few hundred ticks (no current scenario fills the other five), so the long-run parity check cannot show that
`item_instances`, `quest_registry`, `factions`, `clans` and `information_providers` hash deterministically. This test seeds the five, and an event window, on top of a real
metropolis state before the kernel starts and runs the real Kernel twice with the same seed.

What it covers and what it does not: the entries are SEEDED AT START and CARRIED FORWARD by `ApplyPath.apply_generation` every tick, while real systems tick
over real entities. The CREATION or MUTATION of those entries during a run is NOT exercised, because no current scenario reaches it
(`ENABLE_WORLD_EMERGENCE` is off by default; no compiled world seeds clans, information providers or item instances).
"""
from __future__ import annotations

import dataclasses
from typing import Tuple

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.models.inventory import AcquiredMethod, ItemInstance
from src.core.models.quests import QuestOpportunity
from src.core.state import AuthoritativeState, ClanState, FactionState
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.checkpoint import PROOF_DIGEST_SCHEME, CanonicalStateHasher
from src.engine.kernel import Kernel
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG

SEED = 303
TICKS = 30
ENTITIES = 60
SEEDED_FIELDS = ("item_instances", "recent_world_events", "quest_registry", "factions", "clans", "information_providers")


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="proof_digest_populated_parity", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0,
        max_worker_count=0, max_queue_depth=500, max_replay_buffer_kb=4096,
        max_observability_budget_percent=10.0, max_tick_budget_ms=50.0,
    )


def _seeded(state: AuthoritativeState) -> AuthoritativeState:
    """`state` plus one entry in each of the five fields no scenario populates, and the event window (empty after a short run), naming real entity ids; the values mirror the proof-digest contract fixture."""
    first, second = sorted(state.entities)[:2]
    return dataclasses.replace(
        state,
        item_instances={7: ItemInstance(7, "iron_sword", [str(first), str(second)], 1, AcquiredMethod.CRAFTED)},
        recent_world_events=[
            WorldEvent(WorldEventCategory.ENTITY_DEATH, 0, region_id="r1", subject=str(second), severity=2.0, payload={"b": 1.0, "a": 2.0}),
            WorldEvent(WorldEventCategory.RESOURCE_DEPLETED, 0, region_id="r2"),
        ],
        quest_registry={"q1": QuestOpportunity("q1", "resource_crisis", "iron low", ("fetch:iron_ore:3",), {"gold": 5, "xp": 2}, "f_seeded", 30, str(first))},
        factions={**state.factions, "f_seeded": FactionState("f_seeded", territory=("r1",), resources={"iron": 3}, military_strength=2.5)},
        clans={"c1": ClanState("c1", name="Ash", member_entity_ids=(second, first), founded_tick=1)},
        information_providers={second: InformationProviderState(second, InformationProviderArchetype.MERCHANT, 0.5, ("material_source",), 3, 1)},
    )


def _run(seed_the_five: bool) -> Tuple[str, AuthoritativeState]:
    state = SCENARIO_BUILDERS["metropolis"](entity_count=ENTITIES, seed=SEED)
    if seed_the_five:
        state = _seeded(state)
    kernel = Kernel(_profile(), state, DeterministicRNG(SEED), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True})
    try:
        for _ in range(TICKS):
            kernel.tick_once()
        final_state = kernel.state
    finally:
        digest = kernel.shutdown().final_hash
    return digest, final_state


def test_populated_carried_state_hashes_the_same_across_two_same_seed_runs():
    hash1, state1 = _run(True)
    hash2, state2 = _run(True)

    assert hash1 == hash2
    # Positive control: the digest was taken over populated fields, so equal hashes are not equal-because-empty.
    for state in (state1, state2):
        empty = [f for f in SEEDED_FIELDS if not getattr(state, f)]
        assert not empty, f"carried fields empty at the end of the run: {empty}"


def test_the_digest_is_sensitive_to_the_seeded_run():
    """Coarse check: a seeded run and an unseeded run hash differently. It cannot name a field the hasher drops, so the per-field test below does."""
    seeded_hash, _ = _run(True)
    unseeded_hash, _ = _run(False)
    assert seeded_hash != unseeded_hash


@pytest.fixture(scope="module")
def seeded_final_state() -> AuthoritativeState:
    return _run(True)[1]


@pytest.mark.parametrize("field", SEEDED_FIELDS)
def test_the_digest_covers_each_seeded_field(seeded_final_state: AuthoritativeState, field: str):
    """Emptying one field of the final state of one seeded run moves the digest, so the hasher does not silently drop it.

    Uses `CanonicalStateHasher.get_hash`, the entry point `Kernel.shutdown`'s digest ends in (`CanonicalHashScheduler.compute_digest`). No re-ticking.
    """
    value = getattr(seeded_final_state, field)
    assert value, f"{field} is empty in the final state"
    blanked = dataclasses.replace(seeded_final_state, **{field: type(value)()})
    assert CanonicalStateHasher.get_hash(seeded_final_state) != CanonicalStateHasher.get_hash(blanked)


def test_the_digest_scheme_is_v3():
    assert PROOF_DIGEST_SCHEME == "flat-sha256-v3"
