"""A Kernel built in a unit test leaves the real data/runs untouched: the autouse conftest fixture redirects the repository's default base to tmp_path."""
from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

from src.config.profiles import PROD_SMALL
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel

REAL_RUNS = os.path.abspath("data/runs")


def _runs():
    return set(os.listdir(REAL_RUNS)) if os.path.isdir(REAL_RUNS) else set()


def test_a_kernel_on_a_mocked_rng_writes_no_run_folder_into_the_real_data_runs(tmp_path):
    before = _runs()
    kernel = Kernel(profile=PROD_SMALL, state=AuthoritativeState(tick=0, seed=1), rng=MagicMock(), flags={"no_replay": True})
    try:
        assert not os.path.abspath(kernel._artifact_repo.base_dir).startswith(REAL_RUNS)
        assert os.path.isdir(os.path.join(kernel._artifact_repo.base_dir, kernel._run_id))
        assert "Mock" not in kernel._run_id
    finally:
        kernel.shutdown()
    assert _runs() == before


def test_a_kernel_on_a_real_rng_keeps_the_real_default_base(tmp_path):
    from src.platform.rng import DeterministicRNG
    kernel = Kernel(profile=PROD_SMALL, state=AuthoritativeState(tick=0, seed=1), rng=DeterministicRNG(1), flags={"no_replay": True}, run_id=f"keeps_default_base_{os.getpid()}")
    try:
        assert os.path.abspath(kernel._artifact_repo.base_dir) == REAL_RUNS
    finally:
        kernel.shutdown()
        import shutil
        shutil.rmtree(os.path.join(REAL_RUNS, kernel._run_id), ignore_errors=True)


def test_a_repository_that_names_its_own_base_dir_keeps_it(tmp_path):
    from src.observability.reporting.artifact_repository import RunArtifactRepository
    assert RunArtifactRepository(str(tmp_path / "mine")).base_dir == str(tmp_path / "mine")


@pytest.mark.real_data_runs
def test_a_test_that_opts_out_keeps_the_real_default_base():
    from src.observability.reporting.artifact_repository import RunArtifactRepository
    assert RunArtifactRepository().base_dir == REAL_RUNS
