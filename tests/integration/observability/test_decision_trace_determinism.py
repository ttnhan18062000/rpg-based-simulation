"""
tests/integration/observability/test_decision_trace_determinism.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260702-OBSISO-TRACE-ASYNC — AC #4 (determinism) end-to-end proof.

Runs the same seeded scenario twice through a real Kernel (init -> tick loop ->
shutdown()), each into its own run directory, and asserts the two resulting
decision_trace.jsonl files are identical in per-tick entry order.

Determinism caveat (see plan.md Step 8): strict FIFO ordering is only
guaranteed for items actually pushed onto DecisionTraceWriter's private
BoundedObservabilityQueue. _DecisionTraceQueueItem.severity is hardcoded to
"INFO", so on overflow (queue depth reaches max_size) new entries are
silently dropped, not evicted-and-reordered — a genuine, scheduling-dependent
non-determinism source. This test proves the invariant, not scale-dependent
luck: it asserts dropped_count == 0 on both writers' queues after the run, so
byte-identical output is a proven property of this scenario/tick-count
combination, not an accident of small scale. If a future change to this
test's scenario size or tick count removes that headroom, this assertion
will fail loudly rather than the test silently becoming flaky.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, CombatComponent, BiologicalComponent, PersonalityComponent, ResourceNodeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityConfig, ObservabilityMode

SEED = 42
TICKS = 15
RUN_IDS = (
    "test_decision_trace_determinism_run_a",
    "test_decision_trace_determinism_run_b",
)


def _build_state() -> AuthoritativeState:
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=2))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    p = PersonalityComponent(greed=0.5, bravery=0.5, sociability=0.5, industry=0.5)
    b.identity(evolution_level=1, personality=p, class_id="warrior")
    b.location(0.0, 0.0)
    b.lifecycle(active=True)
    hero = b.build()
    object.__setattr__(hero.navigation, "region_id", "old_mine")  # matches resource node below

    node = ResourceNodeState(
        id=201, kind="node_iron", position=(1.0, 1.0), yields_item="iron_ore",
        remaining_charges=50, max_charges=50, required_ticks=10,
    )

    state = AuthoritativeState(
        tick=1, seed=SEED, world_time=100, entities={hero.id: hero},
        groups={}, regions={}, resource_nodes={node.id: node}, buildings={},
        chests={}, ground_items={}, corpses={}, camps={}, local_scars={},
        global_resources={}, town_tiles=set(), building_tiles={}, terrain={},
        home_storage={}, town_center=(0, 0), periodic_due_ticks={}, work_debt={},
        movement_count=0, maturity=0, last_calamity_tick=0,
        blocked_tiles=set(), town_entity_ids=set(),
    )
    flags = dict(state.feature_flags)
    flags["ENABLE_ADVENTURE_ROUTING"] = 1.0
    return replace(state, feature_flags=flags)


def _build_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="decision-trace-determinism",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )


def _run(run_id: str) -> tuple[list[str], int]:
    """Run TICKS ticks under run_id; return (decision_trace.jsonl lines, dropped_count)."""
    kernel = Kernel(profile=_build_profile(), state=_build_state(), rng=DeterministicRNG(SEED), run_id=run_id)
    dropped_count = 0
    try:
        for _ in range(TICKS):
            kernel.tick_once()
        dropped_count = kernel._decision_trace_writer._queue.dropped_count
        trace_path = kernel._decision_trace_writer._path
    finally:
        kernel.shutdown()

    if not os.path.exists(trace_path):
        return [], dropped_count
    with open(trace_path, "r", encoding="utf-8") as f:
        return f.readlines(), dropped_count


@pytest.fixture(autouse=True)
def _cleanup_run_dirs():
    yield
    for run_id in RUN_IDS:
        run_dir = os.path.join("data", "runs", run_id)
        if os.path.exists(run_dir):
            shutil.rmtree(run_dir, ignore_errors=True)


def test_decision_trace_identical_across_two_seeded_runs():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    try:
        lines_a, dropped_a = _run(RUN_IDS[0])
        lines_b, dropped_b = _run(RUN_IDS[1])
    finally:
        ObservabilityConfig.set_override_mode(None)

    assert lines_a, "decision_trace.jsonl must be non-empty for this scenario to prove anything"
    assert lines_a == lines_b, (
        "decision_trace.jsonl content and ordering must be identical across two same-seed runs"
    )

    # Proof that the async drain worker never dropped an entry — the determinism
    # guarantee above holds because occupancy stayed under max_size, not by luck.
    assert dropped_a == 0, f"Run A's decision-trace queue dropped {dropped_a} entries"
    assert dropped_b == 0, f"Run B's decision-trace queue dropped {dropped_b} entries"
