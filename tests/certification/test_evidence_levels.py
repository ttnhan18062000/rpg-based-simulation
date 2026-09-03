"""Tests for EvidenceLevel enum and evidence-capture behaviour.

TCK-20260614-CERT-EVIDENCE-LEVELS

Covers:
  TC-1  EvidenceLevel enum values and str inheritance
  TC-2  SUMMARY level: no state artifact or hash in bundle
  TC-3  SUMMARY level: final_state_summary is None when final_state is None
  TC-4  SUMMARY level: final_state_summary has counts when final_state present
  TC-5  COMPACT level: entity_sample and resource_snapshot added
  TC-6  FULL level: _write_full_evidence() returns the expected relative path
  TC-7  FULL level: canonical state file written at correct path with expected keys
  TC-8  FULL level: to_canonical_data() is used, not asdict()
  TC-9  proofs_bundle.json never contains embedded full state
  TC-10 FULL level: write failure is non-fatal
  TC-11 FULL level: final_state_hash is a valid SHA-256 hex, matches get_hash()
  TC-12 Default (no-arg to_artifact_dict) callers unaffected
  TC-13 recorder.record() accepts evidence_level
  TC-14 state/ subdirectory created by _write_full_evidence()
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import time
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from src.certification.models import (
    ArenaStopCondition,
    CertificationResult,
    EnvironmentCapture,
    EvidenceLevel,
    FailureKind,
    HardwareClass,
    MeasurementPoint,
)
from src.certification.recorder import CertificationRecorder


# ---------------------------------------------------------------------------
# Fake state fixtures
# ---------------------------------------------------------------------------

class _FakeCanonicalObj:
    """Minimal object with to_canonical_dict() for use inside FakeState collections."""
    def __init__(self, **kwargs):
        self._data = kwargs

    def to_canonical_dict(self) -> dict:
        return dict(self._data)


class FakeState:
    """Minimal state object compatible with _final_state_summary() and
    CanonicalStateHasher.to_canonical_data() access patterns."""
    tick = 10
    seed = 42
    # _final_state_summary uses len() on these; to_canonical_data calls .to_canonical_dict()
    entities: dict = {1: _FakeCanonicalObj(hp=100), 2: _FakeCanonicalObj(hp=80), 3: _FakeCanonicalObj(hp=50)}
    resource_nodes: dict = {}
    regions: dict = {}
    places: dict = {}  # Idea 66
    buildings: dict = {}
    corpses: dict = {}
    ground_items: dict = {}

    # Fields required by CanonicalStateHasher.to_canonical_data() for TC-11.
    world_time: float = 0.0
    movement_count: int = 0
    maturity: int = 0
    last_calamity_tick: int = 0
    town_center = (0, 0)
    local_scars: dict = {}
    chests: dict = {}
    groups: dict = {}
    home_storage: dict = {}
    camps: dict = {}
    global_resources: dict = {}
    periodic_due_ticks: dict = {}
    work_debt: dict = {}
    blocked_tiles: list = []
    town_tiles: list = []
    building_tiles: dict = {}
    rng_checkpoint = None


class FakeResourceNode:
    def __init__(self, qty: int):
        self.quantity = qty

    def to_canonical_dict(self) -> dict:
        return {"quantity": self.quantity}


class FakeStateWithResources(FakeState):
    resource_nodes: dict = {f"rn{i}": FakeResourceNode(i * 10) for i in range(7)}


# ---------------------------------------------------------------------------
# Shared factory helpers
# ---------------------------------------------------------------------------

def _make_env() -> EnvironmentCapture:
    return EnvironmentCapture(
        detected_facts={"cpu_count": 4, "ram_gb": 16},
        detected_class=HardwareClass.CLASS_B,
        effective_class=HardwareClass.CLASS_B,
        override_applied=False,
        os_name="linux",
        python_version="3.13",
    )


def _make_measurement() -> MeasurementPoint:
    return MeasurementPoint(
        tick=1,
        mode="NORMAL",
        memory_rss_mb=128.0,
        memory_trend_mb_per_tick=0.1,
        tick_compute_ms=5.0,
        tick_compute_ms_avg=5.0,
        work_debt=0,
        worker_utilization=0.5,
        queue_utilization=0.3,
        replay_pressure=0.0,
        active_workers=2,
        timestamp=time.time(),
    )


def _make_minimal_result(**overrides) -> CertificationResult:
    defaults = dict(
        run_id="test-run-abc123",
        timestamp=1700000000.0,
        commit_sha="abc123def456",
        profile_name="standard_gaming_profile",
        scenario_id="scen-evidence-001",
        seed=42,
        environment=_make_env(),
        measurements=[],
        baseline_hash=None,
        final_hash=None,
        governor_mode_sequence=["NORMAL"],
        conformance_passed=True,
        allowed_failure_observed=False,
        failure_kind=FailureKind.NONE,
        failure_reason=None,
        peak_rss_mb=0.0,
        total_cpu_sec=0.0,
        final_state=None,
    )
    defaults.update(overrides)
    return CertificationResult(**defaults)


def _make_minimal_harness(tmp_path):
    """Create a CertificationHarness without touching HardwareClassifier or git."""
    from src.certification.harness import CertificationHarness

    profile = MagicMock()
    profile.name = "test_profile"
    profile.max_tick_budget_ms = 50.0

    with patch("src.certification.harness.HardwareClassifier.get_detailed_telemetry", return_value={}), \
         patch("src.certification.harness.HardwareClassifier.detect_class", return_value=HardwareClass.CLASS_B), \
         patch("src.certification.harness.CertificationHarness._get_current_sha", return_value="abc123"):
        harness = CertificationHarness(profile, output_dir=str(tmp_path))
    return harness


# ---------------------------------------------------------------------------
# TC-1: EvidenceLevel enum values
# ---------------------------------------------------------------------------

def test_evidence_level_enum_values():
    """TC-1: EvidenceLevel enum has correct string values and is a str subclass."""
    assert EvidenceLevel.SUMMARY.value == "summary"
    assert EvidenceLevel.COMPACT.value == "compact"
    assert EvidenceLevel.FULL.value == "full"
    # str, Enum pattern — must be a str instance
    assert isinstance(EvidenceLevel.SUMMARY, str)
    assert isinstance(EvidenceLevel.COMPACT, str)
    assert isinstance(EvidenceLevel.FULL, str)


# ---------------------------------------------------------------------------
# TC-2: SUMMARY level — no state artifact or hash
# ---------------------------------------------------------------------------

def test_summary_level_has_no_state_artifact():
    """TC-2: SUMMARY level (default) produces final_state_artifact=None, final_state_hash=None."""
    result = _make_minimal_result()
    d = result.to_artifact_dict()  # default = SUMMARY
    assert d["final_state_artifact"] is None
    assert d.get("final_state_hash") is None
    assert d["final_state"] is None


# ---------------------------------------------------------------------------
# TC-3: SUMMARY level — final_state_summary is None when no state
# ---------------------------------------------------------------------------

def test_summary_level_final_state_summary_is_none_when_no_state():
    """TC-3: When final_state=None, final_state_summary is None at SUMMARY level."""
    result = _make_minimal_result(final_state=None)
    d = result.to_artifact_dict(EvidenceLevel.SUMMARY)
    assert d["final_state_summary"] is None


# ---------------------------------------------------------------------------
# TC-4: SUMMARY level — summary has counts when state present; no COMPACT keys
# ---------------------------------------------------------------------------

def test_summary_level_final_state_summary_counts_when_state_present():
    """TC-4: SUMMARY with final_state attached returns compact count dict; no COMPACT extras."""
    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    d = result.to_artifact_dict(EvidenceLevel.SUMMARY)
    s = d["final_state_summary"]
    assert s is not None
    assert s["entity_count"] == 3
    assert s["tick"] == 10
    assert "entity_sample" not in s, "SUMMARY must not include entity_sample"
    assert "resource_snapshot" not in s, "SUMMARY must not include resource_snapshot"


# ---------------------------------------------------------------------------
# TC-5: COMPACT level — entity_sample and resource_snapshot
# ---------------------------------------------------------------------------

def test_compact_level_adds_entity_sample_and_resource_snapshot():
    """TC-5: COMPACT level extends summary with entity_sample and resource_snapshot."""
    fake = FakeStateWithResources()
    result = _make_minimal_result(final_state=fake)
    d = result.to_artifact_dict(EvidenceLevel.COMPACT)
    s = d["final_state_summary"]
    assert s is not None
    assert "entity_sample" in s
    assert len(s["entity_sample"]) <= 5
    assert "resource_snapshot" in s
    assert len(s["resource_snapshot"]) <= 5
    # Top resource node by quantity: rn6 has qty=60 (highest)
    assert s["resource_snapshot"][0] == "rn6"
    # COMPACT still produces no side file — artifact path and hash remain None
    assert d["final_state_artifact"] is None
    assert d.get("final_state_hash") is None


# ---------------------------------------------------------------------------
# TC-6: FULL level — _write_full_evidence returns expected relative path
# ---------------------------------------------------------------------------

def test_full_level_artifact_path_in_dict(tmp_path):
    """TC-6: _write_full_evidence() returns the expected relative path string on success."""
    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)
    write_result = harness._write_full_evidence(result)

    assert write_result is not None
    rel_path, sha256_hex = write_result
    expected_rel = f"state/{result.run_id}.final_state.canonical.json"
    assert rel_path == expected_rel
    # When passed into to_artifact_dict, final_state is still None
    d = result.to_artifact_dict(EvidenceLevel.FULL, final_state_artifact_path=rel_path, final_state_hash=sha256_hex)
    assert d["final_state_artifact"] == expected_rel
    assert d["final_state"] is None


# ---------------------------------------------------------------------------
# TC-7: FULL level — canonical state file written with correct keys
# ---------------------------------------------------------------------------

def test_full_evidence_writes_canonical_state_file(tmp_path):
    """TC-7: _write_full_evidence() writes the canonical state file with expected content."""
    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)
    write_result = harness._write_full_evidence(result)

    assert write_result is not None
    expected_path = tmp_path / "state" / f"{result.run_id}.final_state.canonical.json"
    assert expected_path.exists(), f"Expected state file at {expected_path}"

    data = json.loads(expected_path.read_text())
    assert "tick" in data
    assert "entities" in data
    assert data["tick"] == fake.tick


# ---------------------------------------------------------------------------
# TC-8: FULL level — to_canonical_data() used, not asdict()
# ---------------------------------------------------------------------------

def test_full_evidence_uses_canonical_hasher_not_asdict(tmp_path, monkeypatch):
    """TC-8: FULL evidence write must use to_canonical_data(), not asdict()."""
    import dataclasses as _dc

    def forbidden_asdict(obj, *args, **kwargs):
        raise AssertionError("asdict() must not be called during FULL evidence write")

    monkeypatch.setattr(_dc, "asdict", forbidden_asdict, raising=False)
    # Also patch in the harness module namespace in case it was imported locally
    monkeypatch.setattr("src.certification.harness.asdict", forbidden_asdict, raising=False)

    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)
    # Must NOT raise AssertionError
    write_result = harness._write_full_evidence(result)

    expected_path = tmp_path / "state" / f"{result.run_id}.final_state.canonical.json"
    assert expected_path.exists()
    assert write_result is not None


# ---------------------------------------------------------------------------
# TC-9: proofs_bundle.json never contains embedded full state
# ---------------------------------------------------------------------------

def test_proof_index_never_contains_full_state(tmp_path):
    """TC-9: Even with FULL evidence level, proofs_bundle.json never embeds state data."""
    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    recorder = CertificationRecorder(str(tmp_path))
    recorder.record(result, EvidenceLevel.FULL)

    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists()
    bundle = json.loads(bundle_path.read_text())
    key = f"{result.profile_name}:{result.scenario_id}"
    entry = bundle[key]

    assert entry["final_state"] is None, "final_state must always be None in bundle entry"
    # final_state_artifact is either None or a path string — never embedded content
    if entry.get("final_state_artifact") is not None:
        assert isinstance(entry["final_state_artifact"], str)
    # No entity structure embedded at top level of the entry
    assert "entities" not in entry


# ---------------------------------------------------------------------------
# TC-10: FULL level — write failure is non-fatal
# ---------------------------------------------------------------------------

def test_full_evidence_write_failure_is_nonfatal(tmp_path, monkeypatch):
    """TC-10: OSError during write_text is caught; _write_full_evidence returns None, not raises."""
    def raise_on_write(self, *args, **kwargs):
        raise OSError("Simulated disk failure")

    monkeypatch.setattr(Path, "write_text", raise_on_write)

    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)

    # Must NOT raise — returns None on failure
    write_result = harness._write_full_evidence(result)
    assert write_result is None


# ---------------------------------------------------------------------------
# TC-11: FULL level — final_state_hash matches CanonicalStateHasher.get_hash()
# ---------------------------------------------------------------------------

def test_full_evidence_final_state_hash_in_artifact(tmp_path):
    """TC-11: final_state_hash from _write_full_evidence matches CanonicalStateHasher.get_hash()."""
    from src.engine.checkpoint import CanonicalStateHasher

    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)
    write_result = harness._write_full_evidence(result)

    assert write_result is not None
    _rel_path, sha256_hex = write_result

    # Must be 64-character SHA-256 hex string
    assert len(sha256_hex) == 64
    assert all(c in "0123456789abcdef" for c in sha256_hex)

    # Must match what CanonicalStateHasher.get_hash() produces
    expected_hash = CanonicalStateHasher.get_hash(fake)
    assert sha256_hex == expected_hash, (
        f"final_state_hash mismatch: got {sha256_hex!r}, expected {expected_hash!r}"
    )


# ---------------------------------------------------------------------------
# TC-12: Default (no-arg to_artifact_dict) callers unaffected
# ---------------------------------------------------------------------------

def test_existing_callers_not_broken_by_evidence_level_default():
    """TC-12: Existing no-arg callers of to_artifact_dict() still receive valid output."""
    result = _make_minimal_result()
    d = result.to_artifact_dict()  # no evidence_level arg
    assert d["schema_version"] == "certification_result.v1"
    assert d["final_state"] is None
    assert d["final_state_artifact"] is None
    assert "conformance_passed" in d
    assert "failure_kind" in d
    assert "run_id" in d
    assert "profile_name" in d


# ---------------------------------------------------------------------------
# TC-13: recorder.record() accepts evidence_level
# ---------------------------------------------------------------------------

def test_recorder_record_accepts_evidence_level(tmp_path):
    """TC-13: CertificationRecorder.record() accepts evidence_level kwarg without error."""
    result = _make_minimal_result()
    recorder = CertificationRecorder(str(tmp_path))

    path1 = recorder.record(result, EvidenceLevel.SUMMARY)
    assert path1.endswith("proofs_bundle.json")

    path2 = recorder.record(result, EvidenceLevel.FULL)
    assert path2.endswith("proofs_bundle.json")

    # Both should produce a valid bundle
    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists()
    bundle = json.loads(bundle_path.read_text())
    key = f"{result.profile_name}:{result.scenario_id}"
    assert key in bundle


# ---------------------------------------------------------------------------
# TC-14: state/ subdirectory created by _write_full_evidence()
# ---------------------------------------------------------------------------

def test_state_dir_created_on_full_evidence(tmp_path):
    """TC-14: _write_full_evidence() creates state/ subdirectory under output_dir."""
    fake = FakeState()
    result = _make_minimal_result(final_state=fake)
    harness = _make_minimal_harness(tmp_path)
    harness._write_full_evidence(result)

    state_dir = tmp_path / "state"
    assert state_dir.is_dir(), f"state/ directory must be created at {state_dir}"
