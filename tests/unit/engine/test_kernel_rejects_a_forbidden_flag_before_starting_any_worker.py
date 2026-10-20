"""A Kernel that rejects its flags leaves no worker thread and no run folder behind (TCK-20261008-PERF-KERNEL-VALIDATES-FLAGS-AFTER-STARTING-WORKERS).

The constructor used to validate after it had started the event-recorder and trace-writer drain workers, so each rejected construction leaked them.
"""
from __future__ import annotations

import os
import threading

import pytest

from src.config.profiles import PROD_SMALL
from src.config.validator import ConfigValidationError
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.tools.memory_probe import count_drain_workers

FORBIDDEN = ["FORCE_NORMAL", "BYPASS_GOVERNOR", "DISABLE_RESOURCE_CEILINGS"]


def _construct(flags, run_id):
    return Kernel(profile=PROD_SMALL, state=AuthoritativeState(tick=0, seed=1), rng=DeterministicRNG(1), flags=flags, run_id=run_id)


@pytest.mark.parametrize("flag", FORBIDDEN)
def test_a_forbidden_flag_is_rejected_through_the_constructor_with_no_live_worker_and_no_run_folder(flag, tmp_path):
    workers, threads = count_drain_workers(), threading.active_count()
    run_id = f"rejected_{flag.lower()}_{os.getpid()}"
    with pytest.raises(ConfigValidationError):
        _construct({"no_replay": True, flag: True}, run_id)
    assert count_drain_workers() == workers
    assert threading.active_count() == threads
    assert not [p for p in tmp_path.rglob(run_id)], "a rejected construction must not create the run folder"


def test_a_kernel_with_ordinary_flags_still_starts_its_workers_and_shuts_down_clean():
    workers = count_drain_workers()
    kernel = _construct({"no_replay": True}, f"accepted_{os.getpid()}")
    try:
        assert count_drain_workers() > workers
    finally:
        kernel.shutdown()
    assert count_drain_workers() == workers
