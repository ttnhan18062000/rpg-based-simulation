"""The proof digest contract (TCK-20261004-PERF-M1-HASH-POLICY-CHECKPOINT-SLICE, PERF-D5).

Covers three things the PERF-D5 policy relies on:
  1. the flat hash values did not change when the scheme was named (byte-identity);
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
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG

# `get_hash` of the fixed fixture below, computed with `src/engine/checkpoint.py` as it was on
# origin/main (9793aee08) before this ticket. It must never change without a new scheme version.
FIXTURE_DIGEST_ON_MAIN = "ec75b10657b6e6f2129670f3968fed91d6b1f54b3bda4780ca6b27f496f505f5"


def _fixed_state() -> AuthoritativeState:
    entities = {
        1: V2EntityBuilder(1).kind("hero").location(3.0, 4.0).combat(readiness=100.0).build(),
        2: V2EntityBuilder(2).kind("villager").location(7.0, 1.0).build(),
    }
    return AuthoritativeState(tick=3, seed=42, entities=entities, work_debt={"B": 2, "A": 1})


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

def test_flat_hash_of_fixed_fixture_is_unchanged_from_main():
    assert CanonicalStateHasher.get_hash(_fixed_state()) == FIXTURE_DIGEST_ON_MAIN


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
