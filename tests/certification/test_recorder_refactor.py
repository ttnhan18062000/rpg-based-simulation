"""
Tests for CertificationRecorder refactor (TCK-20260614-CERT-RECORDER-REFACTOR).

Verifies that record() consumes result.to_artifact_dict() directly instead of
the json.loads(result.to_json()) string roundtrip, while preserving all
proofs_bundle.json contract obligations.
"""
from __future__ import annotations

import json
import time
import pytest
from pathlib import Path

from src.certification.recorder import CertificationRecorder
from src.certification.models import (
    CertificationResult,
    EnvironmentCapture,
    HardwareClass,
    MeasurementPoint,
    FailureKind,
)


# ---------------------------------------------------------------------------
# PoisonState: test-local sentinel to assert final_state is never traversed
# ---------------------------------------------------------------------------

class PoisonState:
    """Sentinel that raises on deep traversal (__dict__, vars, dataclasses.asdict).

    Allows safe getattr() access (which _final_state_summary() uses legitimately)
    but raises RuntimeError if anyone calls vars() or accesses __dict__ for
    bulk serialization — the pattern that causes memory amplification.
    """

    # Provide the attributes _final_state_summary() reads via getattr so the
    # safe summary path works without error.
    entities: dict = {}
    resource_nodes: dict = {}
    regions: dict = {}
    buildings: dict = {}
    corpses: dict = {}
    ground_items: dict = {}
    tick: int = 0
    seed: int = 0

    @property
    def __dict__(self):  # type: ignore[override]
        raise RuntimeError(
            "PoisonState.__dict__ accessed — bulk serialization (asdict/vars) "
            "must never be called on final_state"
        )


# ---------------------------------------------------------------------------
# Shared fixture factory
# ---------------------------------------------------------------------------

def _make_minimal_result(**overrides) -> CertificationResult:
    """Construct a valid CertificationResult with all required fields.

    Pass keyword overrides to parametrize specific fields.
    Does NOT include PoisonState by default.
    """
    env = overrides.pop(
        "environment",
        EnvironmentCapture(
            detected_facts={"cpu_count": 4, "ram_gb": 16},
            detected_class=HardwareClass.CLASS_B,
            effective_class=HardwareClass.CLASS_B,
            override_applied=False,
        ),
    )
    measurements = overrides.pop(
        "measurements",
        [
            MeasurementPoint(
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
        ],
    )
    defaults = dict(
        run_id="run-001",
        timestamp=time.time(),
        commit_sha="abc123def456",
        profile_name="standard_gaming_profile",
        scenario_id="scen-001",
        seed=42,
        environment=env,
        measurements=measurements,
        baseline_hash="hash-baseline",
        final_hash="hash-final",
        governor_mode_sequence=["NORMAL"],
        conformance_passed=True,
        allowed_failure_observed=False,
        failure_kind=FailureKind.NONE,
        failure_reason=None,
        peak_rss_mb=256.0,
        total_cpu_sec=12.5,
        final_state=None,
    )
    defaults.update(overrides)
    return CertificationResult(**defaults)


# ---------------------------------------------------------------------------
# Test 1: record() must NOT call to_json() at any point
# ---------------------------------------------------------------------------

def test_recorder_does_not_call_to_json_roundtrip(tmp_path):
    """Monkeypatching to_json to raise proves record() never invokes it."""
    result = _make_minimal_result()

    def _poison_to_json():
        raise RuntimeError("to_json() must not be called by recorder.record()")

    result.to_json = _poison_to_json  # type: ignore[method-assign]

    recorder = CertificationRecorder(output_dir=str(tmp_path))
    # Should succeed — to_artifact_dict() is called directly, not via to_json()
    bundle_path = recorder.record(result)
    assert Path(bundle_path).exists()


# ---------------------------------------------------------------------------
# Test 2: proofs_bundle.json is written and contains the expected run key
# ---------------------------------------------------------------------------

def test_recorder_still_writes_proofs_bundle(tmp_path):
    """After record(), proofs_bundle.json must exist and contain the run key."""
    result = _make_minimal_result()
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    recorder.record(result)

    bundle_path = tmp_path / "proofs_bundle.json"
    assert bundle_path.exists(), "proofs_bundle.json must be written"

    with open(bundle_path) as f:
        bundle = json.load(f)

    expected_key = f"{result.profile_name}:{result.scenario_id}"
    assert expected_key in bundle, f"Bundle must contain key '{expected_key}'"
    assert isinstance(bundle[expected_key], dict)


# ---------------------------------------------------------------------------
# Test 3: Bundle entry must not contain live final_state data
# ---------------------------------------------------------------------------

def test_bundle_entry_does_not_contain_final_state(tmp_path):
    """PoisonState as final_state: record() must succeed and entry["final_state"] must be None."""
    result = _make_minimal_result(final_state=PoisonState())
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    # Must not raise — PoisonState attributes are never accessed
    recorder.record(result)

    bundle_path = tmp_path / "proofs_bundle.json"
    with open(bundle_path) as f:
        bundle = json.load(f)

    key = f"{result.profile_name}:{result.scenario_id}"
    entry = bundle[key]
    assert entry.get("final_state") is None, (
        "Bundle entry final_state must be None — live state must not be serialized"
    )


# ---------------------------------------------------------------------------
# Test 4: Bundle entry must contain all required scoped metadata
# ---------------------------------------------------------------------------

def test_bundle_entry_has_required_scoped_metadata(tmp_path):
    """Entry must contain profile_name, scenario_id, detected_hardware_class,
    effective_hardware_class at top-level and in environment dict."""
    result = _make_minimal_result()
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    recorder.record(result)

    bundle_path = tmp_path / "proofs_bundle.json"
    with open(bundle_path) as f:
        bundle = json.load(f)

    key = f"{result.profile_name}:{result.scenario_id}"
    entry = bundle[key]

    # Top-level required fields
    assert "profile_name" in entry, "entry must have profile_name"
    assert "scenario_id" in entry, "entry must have scenario_id"
    assert "commit_sha" in entry, "entry must have commit_sha"

    # Environment sub-dict required fields
    env = entry.get("environment", {})
    assert "detected_hardware_class" in env, "environment must have detected_hardware_class"
    assert "effective_hardware_class" in env, "environment must have effective_hardware_class"
    assert env["effective_hardware_class"] == "class_b"
    assert env["detected_hardware_class"] == "class_b"


# ---------------------------------------------------------------------------
# Test 5: Two sequential record() calls accumulate distinct keys in bundle
# ---------------------------------------------------------------------------

def test_two_records_accumulate_in_bundle(tmp_path):
    """Calling record() twice with different scenario_ids produces two keys in the bundle."""
    result_a = _make_minimal_result(scenario_id="scen-001")
    result_b = _make_minimal_result(scenario_id="scen-002")

    recorder = CertificationRecorder(output_dir=str(tmp_path))
    recorder.record(result_a)
    recorder.record(result_b)

    bundle_path = tmp_path / "proofs_bundle.json"
    with open(bundle_path) as f:
        bundle = json.load(f)

    key_a = f"{result_a.profile_name}:{result_a.scenario_id}"
    key_b = f"{result_b.profile_name}:{result_b.scenario_id}"
    assert key_a in bundle, f"Bundle must contain key '{key_a}'"
    assert key_b in bundle, f"Bundle must contain key '{key_b}'"
    assert len(bundle) == 2


# ---------------------------------------------------------------------------
# Test 6: Guard rejects result with environment=None
# ---------------------------------------------------------------------------

def test_guard_rejects_missing_environment(tmp_path):
    """record() must raise ValueError when environment is None."""
    # to_artifact_dict() raises ValueError when environment is None
    result = _make_minimal_result()
    # Force environment to None bypassing frozen dataclass (CertificationResult is not frozen)
    result.environment = None  # type: ignore[assignment]

    recorder = CertificationRecorder(output_dir=str(tmp_path))
    with pytest.raises((ValueError, AttributeError)):
        recorder.record(result)


# ---------------------------------------------------------------------------
# Test 7: release_report.md is written after record()
# ---------------------------------------------------------------------------

def test_release_report_md_written(tmp_path):
    """After record(), release_report.md must exist in output_dir."""
    result = _make_minimal_result()
    recorder = CertificationRecorder(output_dir=str(tmp_path))
    recorder.record(result)

    report_path = tmp_path / "release_report.md"
    assert report_path.exists(), "release_report.md must be written by recorder.record()"

    content = report_path.read_text()
    assert result.scenario_id in content, "release_report.md must contain scenario_id"
    assert result.profile_name in content, "release_report.md must contain profile_name"
