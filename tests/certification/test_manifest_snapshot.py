"""Tests for manifest_snapshot.json writing (TCK-20260614-CERT-MANIFEST-SNAPSHOT).

Covers:
  TC-1  manifest_snapshot.json written alongside proof bundle when manifest present
  TC-2  missing manifest path does not raise — run succeeds, snapshot absent
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.certification.harness import CertificationHarness
from src.certification.models import (
    CertificationResult,
    EnvironmentCapture,
    EvidenceLevel,
    FailureKind,
    HardwareClass,
    MeasurementPoint,
)
from src.config.profiles import RuntimeProfile, HardwareClass as ProfileHardwareClass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="test_profile",
        hardware_class=ProfileHardwareClass.CLASS_B,
        max_worker_count=1,
        max_ram_mb=512,
        max_cpu_percent=70.0,
        max_queue_depth=2000,
        max_replay_buffer_kb=16384,
        max_observability_budget_percent=2.0,
        max_tick_budget_ms=100.0,
    )


def _make_minimal_result() -> CertificationResult:
    env = EnvironmentCapture(
        detected_facts={"cpu_count": 4, "ram_gb": 16},
        detected_class=HardwareClass.CLASS_B,
        effective_class=HardwareClass.CLASS_B,
        override_applied=False,
    )
    measurements = [
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
    ]
    return CertificationResult(
        run_id="run-manifest-test",
        timestamp=time.time(),
        commit_sha="abc123",
        profile_name="test_profile",
        scenario_id="scen-manifest",
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
        total_cpu_sec=10.0,
        final_state=None,
    )


# ---------------------------------------------------------------------------
# TC-1: manifest_snapshot.json written alongside proof bundle when manifest present
# ---------------------------------------------------------------------------

def test_manifest_snapshot_written_alongside_proof_bundle(tmp_path):
    manifest_content = {"version": "1.0", "engine": "rpg-sim", "milestone": "ME"}
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_content))

    output_dir = tmp_path / "proof"
    output_dir.mkdir()

    harness = CertificationHarness(
        profile=_make_profile(),
        output_dir=str(output_dir),
        manifest_path=manifest_file,
    )

    result = _make_minimal_result()

    with patch.object(harness._recorder, "record"):
        harness._persist_proof_bundle(result, EvidenceLevel.SUMMARY)

    snapshot = output_dir / "manifest_snapshot.json"
    assert snapshot.exists(), "manifest_snapshot.json must be written to output_dir"
    written = json.loads(snapshot.read_text())
    assert written == manifest_content, "snapshot must match source manifest verbatim"


# ---------------------------------------------------------------------------
# TC-2: missing manifest path does not raise — run succeeds, snapshot absent
# ---------------------------------------------------------------------------

def test_missing_manifest_path_does_not_fail_run(tmp_path):
    nonexistent = tmp_path / "no_such_manifest.json"

    output_dir = tmp_path / "proof"
    output_dir.mkdir()

    harness = CertificationHarness(
        profile=_make_profile(),
        output_dir=str(output_dir),
        manifest_path=nonexistent,
    )

    result = _make_minimal_result()

    with patch.object(harness._recorder, "record"):
        # Must not raise
        harness._persist_proof_bundle(result, EvidenceLevel.SUMMARY)

    snapshot = output_dir / "manifest_snapshot.json"
    assert not snapshot.exists(), "snapshot must not be written when manifest file is missing"
