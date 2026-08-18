"""Integration test: §9 Traceability Design drill-down path, steps 1-3
(TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST).

Proves QualityReport -> pillar worst_events[:5] -> ScoreRecord.event_id
resolves to a real entry in the same run's simulation_events.jsonl.
"""
from __future__ import annotations

import dataclasses
import json
import os
import shutil
import time
from unittest.mock import MagicMock

import pytest

from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.kernel import Kernel
from src.observability.events import SimulationEvent

RUN_ID = "simq-traceability-test"


def _make_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_tick_budget_ms=500,
        max_cpu_percent=50.0,
        max_worker_count=0,
        max_queue_depth=64,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=5.0,
    )


@pytest.fixture()
def minimal_kernel(monkeypatch):
    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(_make_profile(), state, rng, run_id=RUN_ID, flags={"no_replay": True})
    yield kernel
    kernel.shutdown()
    filepath = kernel._event_recorder.filepath
    if filepath is not None:
        run_dir = os.path.dirname(filepath)
        if os.path.isdir(run_dir):
            shutil.rmtree(run_dir)


def _inject_combat_hard_law_violation(kernel) -> None:
    kernel._event_recorder.record(SimulationEvent(
        event_type="combat_hard_law_violation",
        event_category="combat",
        tick=1,
        severity="ERROR",
        source_system="test",
        message="hard law violated in combat pipeline (test injection)",
        entity_id=1,
    ))
    time.sleep(0.15)


def test_worst_event_id_resolves_in_simulation_events_jsonl(minimal_kernel):
    _inject_combat_hard_law_violation(minimal_kernel)

    report = minimal_kernel._quality_hub.get_quality_report()
    assert report.pillars["COMBAT"].worst_events, (
        "COMBAT pillar has no worst_events after injecting a combat_hard_law_violation event — "
        "expected an unconditional -30.0 weight (config/simulation_quality/scoring_weights.yaml:38)"
    )
    worst_event_id = report.pillars["COMBAT"].worst_events[0].event_id

    filepath = minimal_kernel._event_recorder.filepath
    with open(filepath, "r", encoding="utf-8") as f:
        event_ids = {json.loads(line)["event_id"] for line in f if line.strip()}

    assert worst_event_id in event_ids, (
        f"worst_events[0].event_id={worst_event_id!r} not found in {filepath} "
        f"(event_ids present: {event_ids!r})"
    )


def test_worst_event_id_matches_originating_envelope_exactly(minimal_kernel):
    _inject_combat_hard_law_violation(minimal_kernel)

    report = minimal_kernel._quality_hub.get_quality_report()
    assert report.pillars["COMBAT"].worst_events, (
        "COMBAT pillar has no worst_events after injecting a combat_hard_law_violation event — "
        "expected an unconditional -30.0 weight (config/simulation_quality/scoring_weights.yaml:38)"
    )
    worst_event_id = report.pillars["COMBAT"].worst_events[0].event_id

    filepath = minimal_kernel._event_recorder.filepath
    with open(filepath, "r", encoding="utf-8") as f:
        matches = [json.loads(line) for line in f if line.strip() and json.loads(line)["event_id"] == worst_event_id]

    assert len(matches) == 1, (
        f"expected exactly one simulation_events.jsonl line for event_id={worst_event_id!r}, "
        f"found {len(matches)} in {filepath}"
    )
    envelope = matches[0]
    assert envelope["event_type"] == "combat_hard_law_violation"
    assert envelope["tick"] == 1
    assert envelope["entity_id"] == 1


def test_run_directory_cleaned_up_after_test():
    state = AuthoritativeState(tick=0, seed=42)
    rng = MagicMock()
    kernel = Kernel(_make_profile(), state, rng, run_id=RUN_ID, flags={"no_replay": True})
    filepath = kernel._event_recorder.filepath
    kernel.shutdown()
    run_dir = os.path.dirname(filepath)
    shutil.rmtree(run_dir)

    assert not os.path.isdir(run_dir), (
        f"expected {run_dir!r} to be removed after shutil.rmtree() in test teardown"
    )


# ── spawn_occupancy_violation (TCK-20260716-PLACELEGAL-SIMQ-SIGNAL) ─────────


def _inject_spawn_occupancy_violation(kernel) -> None:
    kernel._event_recorder.record(SimulationEvent(
        event_type="InvariantViolation",
        event_category="hard_law",
        tick=0,
        severity="ERROR",
        source_system="hard_law_monitor",
        message="spawn placement violates occupancy/terrain legality (test injection)",
        entity_id=6,
        payload={
            "law_id": "LAW-SPAWN-OCCUPANCY",
            "object_kind": "entity",
            "tile": [1, 1],
            "colliding_object_kind": "entity",
            "colliding_object_id": 2,
        },
    ))
    time.sleep(0.15)


def test_spawn_occupancy_violation_reaches_world_pillar_via_minimal_kernel(minimal_kernel):
    """Injection-pattern test: proves the dispatcher (_translate_invariant) + WorldDynamicsScorer
    path end-to-end, independent of whether Kernel._run_initial_placement_check() actually emits
    the event in production (that real-wiring path is covered separately below)."""
    _inject_spawn_occupancy_violation(minimal_kernel)

    report = minimal_kernel._quality_hub.get_quality_report()
    assert report.pillars["WORLD"].worst_events, (
        "WORLD pillar has no worst_events after injecting a LAW-SPAWN-OCCUPANCY InvariantViolation — "
        "expected a -30.0 weight (config/simulation_quality/scoring_weights.yaml, WORLD: spawn_occupancy_violation)"
    )
    worst_event_id = report.pillars["WORLD"].worst_events[0].event_id

    filepath = minimal_kernel._event_recorder.filepath
    with open(filepath, "r", encoding="utf-8") as f:
        event_ids = {json.loads(line)["event_id"] for line in f if line.strip()}

    assert worst_event_id in event_ids, (
        f"worst_events[0].event_id={worst_event_id!r} not found in {filepath} "
        f"(event_ids present: {event_ids!r})"
    )


def test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction(monkeypatch):
    """Real-wiring test: constructs a Kernel against a forced entity-tile collision, proving
    Kernel._run_initial_placement_check() actually emits the InvariantViolation SimulationEvent
    that _translate_invariant()/WorldDynamicsScorer then route into the WORLD pillar — not merely
    reachable via a hand-built envelope or a manually-injected event.

    The collision itself is forced post-compile (dataclasses.replace onto a real compiled
    world's state, immutably, before Kernel construction) rather than relying on a naturally
    occurring one: the specific seed=42 `unit_information_density` entity-6/entity-14 collision
    this test originally used as its fixture was fixed by
    `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (see
    `src/worldbuilding/compiler.py`'s `_resolve_entity_spawn_tile()`), so it no longer occurs
    naturally. This test's own purpose is to verify the EVENT-ROUTING mechanism, not to prove a
    live placement bug (that's covered by `tests/engine/test_hard_law_monitor.py`'s own
    `test_check_initial_placement_full_population_scan_unit`, which already forces a synthetic
    collision on a minimal hand-built `AuthoritativeState` for the same reason) — forcing the
    collision here still exercises the full real Kernel construction + routing pipeline
    end-to-end, only the precondition (two entities occupying the same starting tile) is now
    deliberately constructed rather than an accident of the old buggy RNG.

    Regression source: tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler

    monkeypatch.setenv("QUALITY_FEED_MODE", "inprocess")
    monkeypatch.delenv("QUALITY_SCORING_DISABLED", raising=False)

    repo = WorldRepository("data/worlds")
    spec = repo.load_world("unit_information_density")
    state, _ = WorldCompiler.compile(spec, seed=42)

    entity_6 = state.entities[6]
    entity_14 = state.entities[14]
    entity_14_collided = dataclasses.replace(
        entity_14,
        navigation=dataclasses.replace(entity_14.navigation, position=entity_6.navigation.position),
    )
    state = dataclasses.replace(state, entities={**state.entities, 14: entity_14_collided})

    rng = MagicMock()
    run_id = "simq-traceability-real-wiring-test"
    kernel = Kernel(_make_profile(), state, rng, run_id=run_id, flags={"no_replay": True})
    try:
        time.sleep(0.15)
        report = kernel._quality_hub.get_quality_report()
        assert report.pillars["WORLD"].worst_events, (
            "WORLD pillar has no worst_events after constructing a real Kernel against the "
            "seed=42 unit_information_density collision — expected "
            "Kernel._run_initial_placement_check() to emit an InvariantViolation SimulationEvent "
            "(law_id=LAW-SPAWN-OCCUPANCY) that routes to spawn_occupancy_violation"
        )
        worst_event_id = report.pillars["WORLD"].worst_events[0].event_id

        filepath = kernel._event_recorder.filepath
        with open(filepath, "r", encoding="utf-8") as f:
            event_ids = {json.loads(line)["event_id"] for line in f if line.strip()}

        assert worst_event_id in event_ids, (
            f"worst_events[0].event_id={worst_event_id!r} not found in {filepath} "
            f"(event_ids present: {event_ids!r})"
        )
    finally:
        kernel.shutdown()
        filepath = kernel._event_recorder.filepath
        if filepath is not None:
            run_dir = os.path.dirname(filepath)
            if os.path.isdir(run_dir):
                shutil.rmtree(run_dir)
