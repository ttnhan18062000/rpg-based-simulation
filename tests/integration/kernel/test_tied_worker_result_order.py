"""Does the order of tied `WorkerResult`s change the committed state? (TCK-20261004-PERF-M1-TIED-WORKER-RESULT-VERIFICATION)

`Kernel._phase_resolution` sorts results by `(class_priority, -local_priority, entity_id)` and the
sort is stable, so results with an equal key keep their arrival order. This module permutes that
arrival order with a test-only `Kernel` subclass (no edit to `kernel.py`) and compares, per route and
per permutation, five levels:

  1. the ordered validated `WorkerResult` batch (timing fields excluded),
  2. the raw `StateUpdate`,
  3. the refined update (timing fields excluded),
  4. the authoritative state (canonical data),
  5. the proof digest (`CanonicalStateHasher.get_hash`, PERF-D5; never the fingerprint).

Scenarios are non-combat: the combat path has an open nondeterminism ticket that would confound this.
"""
from __future__ import annotations

import dataclasses
import random
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

from src.config.profiles import PROD_SMALL
from src.core.concurrency_law import ConcurrencyLaw
from src.core.protocol_validator import ProtocolValidator, ProtocolViolationError
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate
from src.core.work import WorkClass
from src.core.worker_protocol import WorkerResult
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import ConcurrentExecutionAdapter, LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.worker_manager import WorkerManager
from src.perf.scenarios import (
    build_idle_state, build_movement_state, build_resource_state, build_strategic_state,
)
from src.platform.rng import DeterministicRNG

TICKS = 5
SEED = 42
FLAGS = {"audit_mode": True, "no_frame_pacing": True, "no_replay": True}
DEBT = {"SYS_A": 9, "SYS_B": 7, "SYS_C": 5, "SYS_D": 3}  # four subsystems: four ID-zero DRAIN_DEBT results per tick

def _ready_movers_state() -> AuthoritativeState:
    """Twelve entities that are all ready to act every tick, so many CRITICAL results share class and local priority."""
    entities = {
        i: V2EntityBuilder(i).kind("hero").location(float(3 * i), float((7 * i) % 40)).combat(readiness=100.0)
        .task(work_kind="ENTITY_MOVE").build()
        for i in range(1, 13)
    }
    return AuthoritativeState(tick=0, seed=SEED, entities=entities)


SCENARIOS: Dict[str, Callable[[], Any]] = {
    "ready_movers": _ready_movers_state,
    "idle": lambda: build_idle_state(entity_count=10, seed=SEED),
    "movement": lambda: build_movement_state(entity_count=10, seed=SEED),
    "resource": lambda: build_resource_state(entity_count=10, node_count=3, seed=SEED),
    "strategic": lambda: build_strategic_state(entity_count=10, seed=SEED),
}
ROUTES = ["local", "thread", "process"]
PERMUTATIONS = ["identity", "reverse", "shuffle_1", "shuffle_2"]

_TIMING_RESULT_FIELDS = {"compute_time_ns"}


def _key(r: WorkerResult) -> Tuple[int, int, int]:
    return (r.class_priority, -r.local_priority, r.entity_id)


def _canonical_result(r: WorkerResult) -> Tuple:
    d = {f.name: getattr(r, f.name) for f in dataclasses.fields(r) if f.name not in _TIMING_RESULT_FIELDS}
    return tuple(sorted((k, repr(v)) for k, v in d.items()))


def _permute(results: List[WorkerResult], mode: str, tick: int) -> List[WorkerResult]:
    out = list(results)
    if mode == "reverse":
        out.reverse()
    elif mode.startswith("shuffle_"):
        random.Random(int(mode.split("_")[1]) * 1000 + tick).shuffle(out)
    return out


@dataclasses.dataclass
class TickRecord:
    input_order: Tuple[str, ...]          # work ids, as handed to resolution (after permutation)
    tied_groups: Dict[Tuple, Tuple[str, ...]]  # full key -> work ids in input order, only keys with >= 2 results
    batch: Tuple                          # level 1
    raw_update: Any                       # level 2
    refined_update: Any                   # level 3
    state: Any                            # level 4
    digest: str                           # level 5


class PermutingKernel(Kernel):
    """Test seam: permutes `_final_results` before resolution and records every level."""

    perm_mode = "identity"
    inject: Optional[Callable[[List[WorkerResult]], List[WorkerResult]]] = None
    skip_validation = False

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.records: List[TickRecord] = []
        self._captured: Dict[str, Any] = {}

    def _phase_resolution(self) -> None:
        results = list(self._final_results)
        if self.inject is not None:
            results = self.inject(results)
        results = _permute(results, self.perm_mode, self.state.tick)
        self._final_results = results
        groups: Dict[Tuple, List[str]] = defaultdict(list)
        for r in results:
            groups[_key(r)].append(r.work_id)
        self._captured = {
            "input_order": tuple(r.work_id for r in results),
            "tied_groups": {k: tuple(v) for k, v in groups.items() if len(v) > 1},
        }
        super()._phase_resolution()
        self._captured["batch"] = tuple(_canonical_result(r) for r in self._final_results)  # sorted in place

    def tick_once(self) -> None:
        super().tick_once()
        self.records.append(TickRecord(
            input_order=self._captured["input_order"],
            tied_groups=self._captured["tied_groups"],
            batch=self._captured["batch"],
            raw_update=self._captured.get("raw_update"),
            refined_update=self._captured.get("refined_update"),
            state=CanonicalStateHasher.to_canonical_data(self.state),
            digest=CanonicalStateHasher.get_hash(self.state),
        ))


def _strip_timing(update: Any) -> Any:
    """Drop wall-clock fields from a refined update: `sub_phase_costs` and metric counters named `*_ms`."""
    counters = {k: v for k, v in (update.metric_counters or {}).items() if not k.endswith("_ms")}
    return dataclasses.replace(update, sub_phase_costs={}, metric_counters=counters)


@pytest.fixture
def capture_updates(monkeypatch):
    """Record the raw and refined update the kernel hands to / gets from `AuthoritativeApplyPipeline.refine`."""
    holder: Dict[str, Any] = {"kernel": None}
    original = AuthoritativeApplyPipeline.refine  # a staticmethod: accessing it on the class gives the function

    def refine(state, update, *args, **kwargs):
        refined = original(state, update, *args, **kwargs)
        k = holder["kernel"]
        k._captured["raw_update"] = update
        k._captured["refined_update"] = _strip_timing(refined)
        return refined

    monkeypatch.setattr(AuthoritativeApplyPipeline, "refine", staticmethod(refine))
    return holder


def _make_executor(route: str):
    if route == "local":
        return LocalSequentialExecutor(), None
    manager = WorkerManager(max_workers=2, use_processes=(route == "process"))
    return ConcurrentExecutionAdapter(manager), manager


def run_scenario(
    holder: Dict[str, Any], scenario: str, route: str, perm: str, *, debt: Optional[Dict[str, int]] = DEBT,
    inject: Optional[Callable[[List[WorkerResult]], List[WorkerResult]]] = None, ticks: int = TICKS,
) -> List[TickRecord]:
    state = SCENARIOS[scenario]()
    if debt:
        state = dataclasses.replace(state, work_debt=dict(debt))
    executor, manager = _make_executor(route)
    kernel = PermutingKernel(PROD_SMALL, state, DeterministicRNG(SEED), executor=executor, flags=dict(FLAGS))
    kernel.perm_mode = perm
    kernel.inject = inject
    holder["kernel"] = kernel
    try:
        for _ in range(ticks):
            kernel.tick_once()
        return kernel.records
    finally:
        kernel.shutdown()
        if manager is not None:
            manager.shutdown()


def _key_from_batch(row: Tuple) -> Tuple[int, int, int]:
    d = dict(row)
    return (int(d["class_priority"]), -int(d["local_priority"]), int(d["entity_id"]))


def _normalized_batch(rec: TickRecord) -> Tuple:
    """The batch with the arrival order inside each tied group removed (sorted by full key, then work id)."""
    return tuple(sorted(rec.batch, key=lambda row: (_key_from_batch(row), dict(row)["work_id"])))


def _levels(rec: TickRecord) -> Dict[str, Any]:
    return {"batch": _normalized_batch(rec), "raw_update": rec.raw_update, "refined_update": rec.refined_update,
            "state": rec.state, "digest": rec.digest}


def assert_same_levels(base: List[TickRecord], other: List[TickRecord], label: str) -> None:
    """Level 1 is compared as the same results in the same key order; only the order inside a tie may differ.

    The ordered batch itself is expected to differ inside a tied group (the stable sort keeps arrival
    order). Whether that difference reaches levels 2 to 5 is what this module measures.
    """
    assert len(base) == len(other)
    for tick, (a, b) in enumerate(zip(base, other), start=1):
        la, lb = _levels(a), _levels(b)
        for level in ("batch", "raw_update", "refined_update", "state", "digest"):
            assert la[level] == lb[level], f"{label}: level {level!r} differs at tick {tick}"


def _process_route_available() -> bool:
    try:
        manager = WorkerManager(max_workers=1, use_processes=True)
        manager.shutdown()
        return True
    except Exception:  # pragma: no cover - environment dependent
        return False


PROCESS_OK = _process_route_available()


def _params():
    for scenario in SCENARIOS:
        for route in ROUTES:
            marks = [] if route != "process" or PROCESS_OK else [pytest.mark.skip(reason="process pool unavailable")]
            yield pytest.param(scenario, route, id=f"{scenario}-{route}", marks=marks)


# ---------------------------------------------------------------------------
# A. Permuting arrival order across every route and scenario changes nothing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario, route", list(_params()))
def test_permuted_arrival_order_leaves_all_five_levels_unchanged(capture_updates, scenario, route):
    base = run_scenario(capture_updates, scenario, route, "identity")
    ran_tied = False
    for perm in PERMUTATIONS[1:]:
        other = run_scenario(capture_updates, scenario, route, perm)
        assert_same_levels(base, other, f"{scenario}/{route}/{perm}")
        # The permutation really reordered the tied results (AC2: the input differs, the keys are equal).
        for a, b in zip(base, other):
            for key, ids in a.tied_groups.items():
                if len(ids) > 1 and b.tied_groups[key] != ids:
                    ran_tied = True
                    assert sorted(b.tied_groups[key]) == sorted(ids)
    assert ran_tied, "no permutation reordered a tied group; the experiment would pass vacuously"


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_routes_agree_on_state_and_proof_digest(capture_updates, scenario):
    routes = [r for r in ROUTES if r != "process" or PROCESS_OK]
    runs = {r: run_scenario(capture_updates, scenario, r, "shuffle_1") for r in routes}
    for route in routes[1:]:
        for tick, (a, b) in enumerate(zip(runs["local"], runs[route]), start=1):
            assert a.digest == b.digest, f"{scenario}: {route} digest differs from local at tick {tick}"
            assert a.state == b.state


# ---------------------------------------------------------------------------
# B. Real ties of each kind
# ---------------------------------------------------------------------------

def test_id_zero_system_results_tie_on_the_full_key_and_commute(capture_updates):
    """Kind: ID zero. Four DRAIN_DEBT results (distinct subsystems) share the whole key every tick."""
    base = run_scenario(capture_updates, "idle", "local", "identity")
    first = base[0]
    (key, ids), = first.tied_groups.items()
    assert key == (ConcurrencyLaw.get_class_priority(WorkClass.DEFERRED), 0, 0)
    assert len(ids) == len(DEBT)
    other = run_scenario(capture_updates, "idle", "local", "reverse")
    assert other[0].tied_groups[key] == tuple(reversed(ids))  # the input order differs, the key is equal
    assert base[0].batch != other[0].batch  # the tie order survives the stable sort, so level 1 differs in order only
    assert_same_levels(base, other, "id-zero tie")
    # the drain is real: every subsystem's debt moved, so the comparison saw a non-trivial merge
    assert base[-1].state["work_debt"] != dict(DEBT)


def test_equal_class_and_local_priority_entity_results_are_ordered_by_entity_id(capture_updates):
    """Kind: equal priorities. Entity results share (class, local) but the entity id completes the key."""
    base = run_scenario(capture_updates, "ready_movers", "thread", "identity", debt=None)
    saw_shared_priority = False
    for rec in base:
        keys = [_key_from_batch(row) for row in rec.batch]
        assert len(keys) == len(set(keys)) or all(k[2] == 0 for k, n in _dupes(keys))
        if any(k[:2] == keys[0][:2] for k in keys[1:]):
            saw_shared_priority = True
    assert saw_shared_priority, "no two results shared class and local priority; the case was not exercised"


def _dupes(keys):
    seen: Dict[Tuple, int] = defaultdict(int)
    for k in keys:
        seen[k] += 1
    return [(k, n) for k, n in seen.items() if n > 1]


def _entity_result(entity_id: int, work_id: str) -> WorkerResult:
    return WorkerResult(
        source_packet_id=f"local:1:{work_id}", work_id=work_id, entity_id=entity_id, work_class=WorkClass.CRITICAL,
        update=EntityUpdate(entity_id=entity_id),
    )


def test_same_entity_tie_is_rejected_in_either_order(capture_updates):
    """Kind: same entity. Two results for one entity are a protocol violation, so order never decides state."""
    pair = [_entity_result(7, "w1"), _entity_result(7, "w2")]
    for batch in (pair, list(reversed(pair))):
        with pytest.raises(ProtocolViolationError):
            ProtocolValidator.validate_result_batch(batch, {})

    # Resolution has its own guard if a duplicate ever bypassed the validator.
    def inject(results):
        return results + [_entity_result(7, "dup_a"), _entity_result(7, "dup_b")]

    for perm in ("identity", "reverse"):
        with pytest.raises(ProtocolViolationError):
            run_scenario(capture_updates, "idle", "local", perm, debt=None, inject=inject, ticks=1)


# ---------------------------------------------------------------------------
# C. The bound of the merge rule, and the instrument seeing a divergence
# ---------------------------------------------------------------------------

def _drain(subsystem: str, value: int, work_id: str) -> WorkerResult:
    return WorkerResult(
        source_packet_id=f"local:1:{work_id}", work_id=work_id, entity_id=0,
        work_class=WorkClass.DEFERRED, update=EntityUpdate(entity_id=0),
        class_priority=ConcurrencyLaw.get_class_priority(WorkClass.DEFERRED),
        work_debt_update=value, subsystem_id=subsystem,
    )


def test_validator_rejects_two_system_results_for_one_subsystem():
    """The bound of the merge rule is enforced (TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM).

    Before that ticket the validator accepted this batch, which is why the mutation test below injects
    its divergent pair *after* collection-time validation, directly into resolution: it keeps showing
    that the comparison can see the divergence the validator now makes unreachable.
    """
    for batch in ([_drain("SYS_A", -2, "a1"), _drain("SYS_A", -5, "a2")], [_drain("SYS_A", -5, "a2"), _drain("SYS_A", -2, "a1")]):
        with pytest.raises(ProtocolViolationError, match="SYS_A"):
            ProtocolValidator.validate_result_batch(batch, {})


def test_shipped_constructors_never_emit_two_system_results_for_one_subsystem(capture_updates):
    for route in ("local", "thread"):
        base = run_scenario(capture_updates, "idle", route, "identity")
        for rec in base:
            subsystems = [dict(row)["subsystem_id"] for row in rec.batch if dict(row)["entity_id"] == "0"]
            assert len(subsystems) == len(set(subsystems)), f"{route}: duplicate system result for a subsystem"


def test_mutation_proof_a_noncommutative_tie_makes_the_comparison_fail(capture_updates):
    """The instrument can see a divergence: two same-subsystem drains with different values are last-writer-wins.

    The pair is injected into `_phase_resolution`, below the validator that now rejects it at collection.
    """
    def inject(results):
        return results + [_drain("SYS_A", -1, "inj_a"), _drain("SYS_A", -4, "inj_b")]

    base = run_scenario(capture_updates, "idle", "local", "identity", inject=inject, ticks=2)
    other = run_scenario(capture_updates, "idle", "local", "reverse", inject=inject, ticks=2)
    with pytest.raises(AssertionError, match="differs at tick"):
        assert_same_levels(base, other, "non-commutative tie")
    assert base[0].digest != other[0].digest  # the proof digest itself diverges

    # And the same injection with equal values commutes, so the failure above is caused by the values.
    def inject_equal(results):
        return results + [_drain("SYS_A", -2, "inj_a"), _drain("SYS_A", -2, "inj_b")]

    eq_base = run_scenario(capture_updates, "idle", "local", "identity", inject=inject_equal, ticks=2)
    eq_other = run_scenario(capture_updates, "idle", "local", "reverse", inject=inject_equal, ticks=2)
    assert_same_levels(eq_base, eq_other, "equal-valued duplicate drains")
