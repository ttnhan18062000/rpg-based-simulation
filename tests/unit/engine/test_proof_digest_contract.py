"""The proof digest contract (TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE, PERF-D5).

Covers three things the PERF-D5 policy relies on:
  1. the flat hash is pinned under its scheme; v2 differs from v1 only by the two state keys that were removed
     (`TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE`), and the current scheme (v3) differs from v2 only by seven carried-state fields
     (`TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS`);
  2. the certification harness's digest (now taken through the scheduler) equals `get_hash`
     (until PERF-M1-T03b replaces the copy with a call);
  3. no cached canonical dict is stale: the only path by which a stale value can reach the flat hash.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.certification.harness import CertificationHarness
from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.models.inventory import AcquiredMethod, ItemInstance
from src.core.models.quests import QuestOpportunity
from src.core.state import AuthoritativeState, ClanState, FactionState
from src.domains.information.providers import InformationProviderArchetype, InformationProviderState
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory
from src.engine.checkpoint import PROOF_DIGEST_SCHEME, CanonicalStateHasher
from src.engine.kernel import Kernel
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG

# v1 (`flat-sha256-v1`) `get_hash` of the fixture below *as it was*, with `work_debt={"B": 2, "A": 1}` in the state, computed with
# `src/engine/checkpoint.py` as it was on origin/main (9793aee08). Kept only as history: v1 digests are never compared with v2 ones, and the
# engine no longer computes v1. `test_v2_is_v1_without_the_two_removed_keys` rebuilds the v1 form to prove it still ties to this value.
FIXTURE_DIGEST_V1_ON_MAIN = "13ed76f7fa7f7ba5fc324a20a1bb999295048507fb7630ec1f394fdd81b6fc5f"
# v2 (`flat-sha256-v2`) `get_hash` of the same fixture without the removed fields. It must never change without a new scheme version.
FIXTURE_DIGEST_V2 = "41b03d22dc75548914f32c96aab57ab6d520842b818245d46c491cdcf7a382b7"
# v3 (`flat-sha256-v3`) `get_hash` of `_carried_state()`: the v2 fixture plus non-empty values for the seven carried-state fields. It must never change without a new scheme version.
FIXTURE_DIGEST_V3 = "37679334c2e549023f515e742db36c97d6d028d9f3778b85f6661a59625a619a"
V3_ADDED_KEYS = ("item_instances", "recent_world_events", "quest_registry", "factions", "clans", "information_providers")
REMOVED_KEYS = ("periodic_due_ticks", "work_debt")


def _fixed_state() -> AuthoritativeState:
    entities = {
        1: V2EntityBuilder(1).kind("hero").location(3.0, 4.0).combat(readiness=100.0).build(),
        2: V2EntityBuilder(2).kind("villager").location(7.0, 1.0).build(),
    }
    return AuthoritativeState(tick=3, seed=42, entities=entities)


def _carried_state() -> AuthoritativeState:
    """`_fixed_state()` plus a non-empty value for each of the seven carried-state fields (six state fields and `CombatComponent.last_hit_tick`)."""
    base = _fixed_state()
    hero = base.entities[1]
    entities = {**base.entities, 1: dataclasses.replace(hero, combat=dataclasses.replace(hero.combat, last_hit_tick=2))}
    return dataclasses.replace(
        base,
        entities=entities,
        item_instances={7: ItemInstance(7, "iron_sword", ["hero", "villager"], 1, AcquiredMethod.CRAFTED)},
        recent_world_events=[
            WorldEvent(WorldEventCategory.ENTITY_DEATH, 2, region_id="r1", subject="2", severity=2.0, payload={"b": 1.0, "a": 2.0}),
            WorldEvent(WorldEventCategory.RESOURCE_DEPLETED, 3, region_id="r2"),
        ],
        quest_registry={"q1": QuestOpportunity("q1", "resource_crisis", "iron low", ("fetch:iron_ore:3",), {"gold": 5, "xp": 2}, "f1", 30, "e1")},
        factions={"f1": FactionState("f1", territory=("r1",), resources={"iron": 3}, military_strength=2.5)},
        clans={"c1": ClanState("c1", name="Ash", member_entity_ids=(2, 1), founded_tick=1)},
        information_providers={2: InformationProviderState(2, InformationProviderArchetype.MERCHANT, 0.5, ("material_source",), 3, 1)},
    )


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="proof_digest_test", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0,
        max_worker_count=0, max_queue_depth=500, max_replay_buffer_kb=4096,
        max_observability_budget_percent=10.0, max_tick_budget_ms=50.0,
    )


def _evolved_state(scenario: str, ticks: int = 8) -> AuthoritativeState:
    """A real state after some ticks of a non-combat scenario (the combat path has an open nondeterminism ticket)."""
    extra = {"node_count": 3} if scenario == "resource" else {}
    state = SCENARIO_BUILDERS[scenario](entity_count=6, seed=11, **extra)
    kernel = Kernel(_profile(), state, DeterministicRNG(11), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True})
    try:
        for _ in range(ticks):
            kernel.tick_once()
        return kernel.state
    finally:
        kernel.shutdown()


# ---------------------------------------------------------------------------
# 1. Byte-identity of the flat hash
# ---------------------------------------------------------------------------

def test_flat_hash_of_carried_fixture_is_pinned_under_v3():
    assert PROOF_DIGEST_SCHEME == "flat-sha256-v3"
    assert CanonicalStateHasher.get_hash(_carried_state()) == FIXTURE_DIGEST_V3


def _v2_form(state: AuthoritativeState) -> Dict[str, Any]:
    """The v2 canonical data of a state: v3 data minus the six added keys and the entities' `last_hit_tick`."""
    data = CanonicalStateHasher.to_canonical_data(state)
    assert set(V3_ADDED_KEYS) <= set(data)
    for key in V3_ADDED_KEYS:
        del data[key]
    for entity in data["entities"].values():
        entity["combat"] = {k: v for k, v in entity["combat"].items() if k != "last_hit_tick"}
    return data


def _digest_of(data: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_v3_is_v2_plus_the_seven_carried_state_fields():
    """Migration proof: take away the seven fields and the v2 digest is reproduced exactly, for the empty fixture and for the carried one
    (whose v2 form is the same state), so nothing else in the canonical JSON changed."""
    assert _digest_of(_v2_form(_fixed_state())) == FIXTURE_DIGEST_V2
    assert _digest_of(_v2_form(_carried_state())) == FIXTURE_DIGEST_V2
    assert CanonicalStateHasher.get_hash(_carried_state()) != FIXTURE_DIGEST_V2


def _vary(state: AuthoritativeState, field_name: str) -> AuthoritativeState:
    """The carried state with exactly one of the seven fields changed."""
    if field_name == "last_hit_tick":
        hero = state.entities[1]
        return dataclasses.replace(state, entities={**state.entities, 1: dataclasses.replace(hero, combat=dataclasses.replace(hero.combat, last_hit_tick=3))})
    if field_name == "item_instances":
        return dataclasses.replace(state, item_instances={7: dataclasses.replace(state.item_instances[7], owner_history=["hero"])})
    if field_name == "recent_world_events":
        return dataclasses.replace(state, recent_world_events=list(reversed(state.recent_world_events)))
    if field_name == "quest_registry":
        return dataclasses.replace(state, quest_registry={"q1": dataclasses.replace(state.quest_registry["q1"], expiry_ticks=31)})
    if field_name == "factions":
        return dataclasses.replace(state, factions={"f1": dataclasses.replace(state.factions["f1"], military_strength=2.6)})
    if field_name == "clans":
        return dataclasses.replace(state, clans={"c1": dataclasses.replace(state.clans["c1"], clan_reputation=0.9)})
    if field_name == "information_providers":
        return dataclasses.replace(state, information_providers={2: dataclasses.replace(state.information_providers[2], knowledge_age=4)})
    raise AssertionError(field_name)


@pytest.mark.parametrize("field_name", [*V3_ADDED_KEYS, "last_hit_tick"])
def test_each_carried_state_field_alone_changes_the_v3_digest(field_name: str):
    """Positive control: the digest sees a divergence in that one field (the seven fields were invisible under v2)."""
    base = _carried_state()
    assert CanonicalStateHasher.get_hash(_vary(base, field_name)) != CanonicalStateHasher.get_hash(base)


def test_v2_is_v1_without_the_two_removed_keys():
    """Migration proof: put the two keys back (with the old fixture's debt) and the v1 digest on main is reproduced exactly, so nothing
    else in the canonical JSON changed. The v2 digest of the same state is a different value, as the scheme bump says."""
    data = _v2_form(_fixed_state())
    assert not set(REMOVED_KEYS) & set(data)
    v1_form = {**data, "periodic_due_ticks": {}, "work_debt": {"A": 1, "B": 2}}
    v1_digest = _digest_of(v1_form)
    assert v1_digest == FIXTURE_DIGEST_V1_ON_MAIN
    assert _digest_of(data) != v1_digest


def test_the_authoritative_state_has_no_removed_fields():
    assert not set(REMOVED_KEYS) & set(AuthoritativeState.__dataclass_fields__)



# ---------------------------------------------------------------------------
# 2. The harness's digest equals get_hash
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario", ["movement", "resource"])
def test_certification_harness_digest_equals_get_hash(tmp_path: Path, scenario: str):
    """`CertificationHarness._write_full_evidence` takes its digest through the scheduler (PERF-M1-T03b)."""
    state = _evolved_state(scenario)
    harness = CertificationHarness.__new__(CertificationHarness)  # only `_output_dir` is read
    harness._output_dir = tmp_path
    written = harness._write_full_evidence(SimpleNamespace(final_state=state, run_id="run_x"))

    assert written is not None
    _, harness_digest = written
    assert harness_digest == CanonicalStateHasher.get_hash(state)


# ---------------------------------------------------------------------------
# 3. Audit of cached canonical dicts
# ---------------------------------------------------------------------------

def _cached_objects(root: Any) -> List[Any]:
    """Every object reachable from *root* that holds a populated `_canonical_cache`."""
    found: List[Any] = []
    seen: set = set()

    def walk(obj: Any) -> None:
        if obj is None or isinstance(obj, (str, bytes, int, float, bool)) or id(obj) in seen:
            return
        seen.add(id(obj))
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(k)
                walk(v)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            for v in obj:
                walk(v)
        elif dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            if getattr(obj, "_canonical_cache", None) is not None:
                found.append(obj)
            for f in dataclasses.fields(obj):
                if f.name != "_canonical_cache":
                    walk(getattr(obj, f.name, None))

    walk(root)
    return found


def audit_cached_canonical_dicts(state: AuthoritativeState) -> List[str]:
    """Recompute every cached canonical dict from scratch and return a description of each mismatch.

    All caches are cleared first, so a stale cache of a child cannot hide inside its parent's recompute.
    The original caches are restored afterwards.
    """
    holders = _cached_objects(state)
    saved = [(h, h._canonical_cache) for h in holders]
    mismatches: List[str] = []
    try:
        for h, _ in saved:
            object.__setattr__(h, "_canonical_cache", None)
        for h, cached in saved:
            fresh = h.to_canonical_dict()
            if json.dumps(fresh, sort_keys=True, default=str) != json.dumps(cached, sort_keys=True, default=str):
                mismatches.append(f"{type(h).__name__}: cached canonical dict differs from a fresh recompute")
    finally:
        for h, cached in saved:
            object.__setattr__(h, "_canonical_cache", cached)
    return mismatches


@pytest.mark.parametrize("scenario", ["movement", "resource"])
def test_no_cached_canonical_dict_is_stale_after_a_real_run(scenario: str):
    state = _evolved_state(scenario)
    CanonicalStateHasher.get_hash(state)  # populate the caches the way a run does
    assert _cached_objects(state), "the audit found no cached canonical dicts; it would pass vacuously"
    assert audit_cached_canonical_dicts(state) == []


def test_audit_detects_a_cached_dict_mutated_in_place():
    """Guards the guard: this is the failure the audit exists to catch."""
    state = _evolved_state("movement")
    CanonicalStateHasher.get_hash(state)
    victim = _cached_objects(state)[0]
    victim._canonical_cache["__poisoned__"] = 1  # in-place mutation of the cached dict

    mismatches = audit_cached_canonical_dicts(state)
    assert any(type(victim).__name__ in m for m in mismatches)
