"""TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES: a default run id is a name only, and no two runs can share a directory.

Two same-seed Kernels built in one second used to get the same `run_<second>_<seeded suffix>` and write into one directory (events doubled).
"""
from __future__ import annotations

import os
import shutil
from unittest import mock

import pytest

from src.config.profiles import PROD_SMALL
from src.engine import run_identity
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.run_identity import default_run_id
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
RUNS = os.path.abspath("data/runs")


def _kernel(run_id=None):
    return Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=compile_world(WORLD_ID), rng=DeterministicRNG(DEFAULT_SEED),
                  flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor(), run_id=run_id)


@pytest.fixture
def made():
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)  # run directories exist only when observability is on
    ids = []
    yield ids
    ObservabilityConfig.set_override_mode(None)
    for run_id in ids:
        shutil.rmtree(os.path.join(RUNS, run_id), ignore_errors=True)


def test_two_same_seed_kernels_in_one_second_get_different_ids_and_directories(made):
    with mock.patch.object(run_identity.time, "time", return_value=1_800_000_000.0):
        a, b = _kernel(), _kernel()
    try:
        made.extend([a._run_id, b._run_id])
        assert a._run_id != b._run_id
        assert os.path.isdir(os.path.join(RUNS, a._run_id)) and os.path.isdir(os.path.join(RUNS, b._run_id))
    finally:
        a.shutdown(); b.shutdown()


def test_a_default_id_never_reuses_an_existing_directory(made):
    taken = "run_1800000000_1234_1_deadbeef"
    os.makedirs(os.path.join(RUNS, taken), exist_ok=True)
    marker = os.path.join(RUNS, taken, "keep.txt")
    open(marker, "w").write("another run's file")
    made.append(taken)
    ids = iter([taken, "run_1800000000_1234_1_cafef00d"])
    with mock.patch.object(run_identity, "default_run_id", side_effect=lambda suffix: next(ids)):
        k = _kernel()
    try:
        made.append(k._run_id)
        assert k._run_id == "run_1800000000_1234_1_cafef00d"
        assert os.path.exists(marker), "the existing run's directory must not be touched"
    finally:
        k.shutdown()


def test_an_explicit_run_id_is_unchanged(made):
    k = _kernel(run_id="run_explicit_h6_test")
    made.append("run_explicit_h6_test")
    try:
        assert k._run_id == "run_explicit_h6_test"
    finally:
        k.shutdown()


def test_default_id_carries_pid_and_a_nonce_that_is_not_seeded():
    one, two = default_run_id(4321), default_run_id(4321)
    assert one != two and f"_{os.getpid()}_" in one


def test_the_id_is_naming_only_same_seed_runs_end_with_the_same_state_hash(made):
    from src.engine.checkpoint import CanonicalHashScheduler
    hashes = []
    for _ in range(2):
        k = _kernel()
        made.append(k._run_id)
        try:
            for _t in range(5):
                k.tick_once()
            hashes.append(CanonicalHashScheduler(k._state.tick).compute_digest(k._state, k._state.tick).require_value())
        finally:
            k.shutdown()
    assert hashes[0] == hashes[1]
