import json
import logging

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityConfig, ObservabilityMode
from unittest.mock import MagicMock


def _profile():
    return RuntimeProfile(
        name="TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=50.0, max_worker_count=1,
        max_queue_depth=100, max_work_debt=100, max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0, max_tick_budget_ms=10.0,
    )


def _make_kernel(tmp_path, monkeypatch, run_id, provenance_path):
    monkeypatch.chdir(tmp_path)  # RunArtifactRepository writes to ./data/runs
    monkeypatch.setattr(ObservabilityConfig, "get_mode", classmethod(lambda cls: ObservabilityMode.LIGHT))
    return Kernel(
        state=AuthoritativeState(tick=0, seed=42), profile=_profile(), rng=MagicMock(),
        flags={"no_replay": True}, run_id=run_id, world_id="w",
        provenance_manifest_path=str(provenance_path),
    )


def test_run_manifest_takes_fingerprints_from_provenance_manifest(tmp_path, monkeypatch):
    """The provenance manifest must actually be loaded: a missing `json` import made
    `json.load` raise NameError, which a bare `except Exception: pass` hid on every lab run."""
    prov = tmp_path / "provenance_manifest.json"
    prov.write_text(json.dumps({
        "catalog_fingerprint": "cat-fp-from-provenance",
        "module_fingerprints": {"module_a": "fp-a"},
    }))

    kernel = _make_kernel(tmp_path, monkeypatch, "prov_load_ok", prov)
    try:
        manifest = kernel._artifact_repo.read_manifest("prov_load_ok")
        assert manifest.catalog_fingerprint == "cat-fp-from-provenance"
        assert manifest.module_fingerprints == {"module_a": "fp-a"}
    finally:
        kernel.shutdown()


def test_corrupt_provenance_manifest_is_logged_not_swallowed(tmp_path, monkeypatch, caplog):
    prov = tmp_path / "provenance_manifest.json"
    prov.write_text("{not json")

    with caplog.at_level(logging.WARNING, logger="src.engine.kernel"):
        kernel = _make_kernel(tmp_path, monkeypatch, "prov_load_bad", prov)
    try:
        assert any("Could not load provenance manifest" in r.getMessage() for r in caplog.records)
        assert kernel._artifact_repo.read_manifest("prov_load_bad").module_fingerprints is None
    finally:
        kernel.shutdown()
