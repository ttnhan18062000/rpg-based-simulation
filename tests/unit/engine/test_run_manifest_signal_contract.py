"""A run's manifest records how its governor inputs were produced (PERF-D1; TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY, step 3)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest

RUN_IDS = ("sc_manifest_canonical", "sc_manifest_live", "sc_manifest_audit")


def _profile(contract: str) -> RuntimeProfile:
    return RuntimeProfile(
        name="TEST", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=100, max_replay_buffer_kb=64, max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0, signal_contract=contract,
    )


@pytest.fixture(autouse=True)
def _remove_own_run_dirs():
    # Stay in the repo cwd (see test_kernel_provenance_manifest_load): Kernel's content warmup loads data/content relatively.
    yield
    for run_id in RUN_IDS:
        shutil.rmtree(Path("data/runs") / run_id, ignore_errors=True)


def _kernel(monkeypatch, run_id: str, contract: str, flags=None) -> Kernel:
    monkeypatch.setattr(ObservabilityConfig, "get_mode", classmethod(lambda cls: ObservabilityMode.LIGHT))
    return Kernel(state=AuthoritativeState(tick=0, seed=42), profile=_profile(contract), rng=MagicMock(),
                  flags={"no_replay": True, **(flags or {})}, run_id=run_id, world_id="w")


def test_a_canonical_run_records_its_contract_and_work_model(monkeypatch):
    kernel = _kernel(monkeypatch, "sc_manifest_canonical", "canonical")
    try:
        expected = {"signal_contract": "CANONICAL", "effective_source": "canonical",
                    "work_model": "WORK_MODEL_V1", "work_model_status": "PROVISIONAL"}
        assert kernel._artifact_repo.read_manifest("sc_manifest_canonical").signal_contract == expected
        assert kernel._replay._manifest["signal_contract"] == expected
    finally:
        kernel.shutdown()


def test_a_live_run_and_an_audit_run_say_so(monkeypatch):
    live = _kernel(monkeypatch, "sc_manifest_live", "live")
    audit = _kernel(monkeypatch, "sc_manifest_audit", "canonical", flags={"audit_mode": True})
    try:
        assert live._artifact_repo.read_manifest("sc_manifest_live").signal_contract["effective_source"] == "live"
        recorded = audit._artifact_repo.read_manifest("sc_manifest_audit").signal_contract
        assert (recorded["signal_contract"], recorded["effective_source"]) == ("CANONICAL", "audit_zeroed")
    finally:
        live.shutdown()
        audit.shutdown()


def test_a_manifest_written_before_the_field_existed_still_loads(tmp_path):
    repo = RunArtifactRepository(base_dir=str(tmp_path))
    repo.create_run("old_run", RunManifest(run_id="old_run", scenario_name="s", scenario_type="t", seed=1,
                                           observability_mode="LIGHT", started_at="2026-01-01T00:00:00Z", ticks_requested=10))
    path = Path(repo.resolve_path("old_run", "manifest"))
    data = json.loads(path.read_text())
    del data["signal_contract"]  # what a manifest from before this field looks like
    path.write_text(json.dumps(data))
    assert repo.read_manifest("old_run").signal_contract is None
    assert repo.update_manifest("old_run", status="RUNNING").status == "RUNNING"
