"""
Tests for ArtifactBudgetRegistry (TCK-20260614-ARTIFACT-BUDGET-REG).

INFRA-193 compliance.  Pure unit tests — no Kernel, WorldCompiler, or
ScenarioLabOrchestrator imports.

All tests use the autouse reset_registry fixture to avoid singleton pollution
between test cases.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.certification.artifact_budget import (
    ArtifactBudget,
    ArtifactBudgetRegistry,
    ArtifactBudgetViolationError,
    BudgetCheckResult,
    get_default_registry,
    reset_default_registry,
)
from src.certification.recorder import CertificationRecorder
from src.certification.models import (
    CertificationResult,
    EnvironmentCapture,
    HardwareClass,
    MeasurementPoint,
    FailureKind,
)


# ---------------------------------------------------------------------------
# Autouse fixture: reset singleton before/after every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_registry():
    reset_default_registry()
    yield
    reset_default_registry()


# ---------------------------------------------------------------------------
# Helper: build a minimal valid CertificationResult
# ---------------------------------------------------------------------------


def _make_minimal_result(**overrides) -> CertificationResult:
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
# Core registry tests
# ---------------------------------------------------------------------------


def test_registry_allows_within_budget():
    """1 MB estimated vs 2 MB max → allowed=True, action="allow"."""
    registry = ArtifactBudgetRegistry()
    registry.register(
        ArtifactBudget(
            artifact_type="test_artifact",
            max_size_mb=2.0,
            fail_on_budget_violation=False,
        )
    )
    one_mb_bytes = 1 * 1024 * 1024
    result = registry.check("test_artifact", one_mb_bytes)
    assert result.allowed is True
    assert result.action == "allow"


def test_registry_rejects_over_budget():
    """
    3 MB vs 2 MB max:
      - fail_on_budget_violation=False → allowed=True, action="warn"
      - fail_on_budget_violation=True  → allowed=False, action="reject"
    """
    three_mb_bytes = 3 * 1024 * 1024

    # warn-only (fail_on=False)
    registry_warn = ArtifactBudgetRegistry()
    registry_warn.register(
        ArtifactBudget(
            artifact_type="test_artifact",
            max_size_mb=2.0,
            fail_on_budget_violation=False,
        )
    )
    result_warn = registry_warn.check("test_artifact", three_mb_bytes)
    assert result_warn.allowed is True
    assert result_warn.action == "warn"

    # reject (fail_on=True)
    registry_reject = ArtifactBudgetRegistry()
    registry_reject.register(
        ArtifactBudget(
            artifact_type="test_artifact",
            max_size_mb=2.0,
            fail_on_budget_violation=True,
        )
    )
    result_reject = registry_reject.check("test_artifact", three_mb_bytes)
    assert result_reject.allowed is False
    assert result_reject.action == "reject"


def test_registry_warns_on_soft_limit():
    """
    Budget: soft=1.0 MB, max=2.0 MB.
    Estimate 1.6 MB → action="warn" (soft exceeded, hard not exceeded).
    """
    registry = ArtifactBudgetRegistry()
    registry.register(
        ArtifactBudget(
            artifact_type="test_artifact",
            max_size_mb=2.0,
            soft_limit_mb=1.0,
            fail_on_budget_violation=False,
        )
    )
    one_point_six_mb = int(1.6 * 1024 * 1024)
    result = registry.check("test_artifact", one_point_six_mb)
    assert result.allowed is True
    assert result.action == "warn"
    assert result.reason is not None
    assert "soft limit" in result.reason


def test_no_budget_registered_allows():
    """Unregistered artifact type → allowed=True, action="allow"."""
    registry = ArtifactBudgetRegistry()
    result = registry.check("completely_unknown_type", 999_999_999)
    assert result.allowed is True
    assert result.action == "allow"
    assert result.reason is None


def test_registry_get_returns_none_for_unknown():
    """registry.get() must return None for an unregistered type."""
    registry = ArtifactBudgetRegistry()
    assert registry.get("unknown") is None


def test_registry_overwrite_replaces_budget():
    """Registering the same type twice: second registration wins."""
    registry = ArtifactBudgetRegistry()
    registry.register(ArtifactBudget(artifact_type="my_type", max_size_mb=1.0))
    registry.register(ArtifactBudget(artifact_type="my_type", max_size_mb=50.0))

    budget = registry.get("my_type")
    assert budget is not None
    assert budget.max_size_mb == 50.0


def test_get_default_registry_returns_singleton():
    """Two consecutive calls to get_default_registry() return the same object."""
    reg_a = get_default_registry()
    reg_b = get_default_registry()
    assert reg_a is reg_b


def test_reset_default_registry_reregisters_defaults():
    """After reset, get_default_registry() returns a fresh registry with defaults."""
    # Pollute the singleton with a custom budget
    get_default_registry().register(
        ArtifactBudget(artifact_type="certification_result", max_size_mb=999.0)
    )
    # Reset wipes the singleton
    reset_default_registry()
    # Next call re-initializes with defaults
    fresh = get_default_registry()
    cert_budget = fresh.get("certification_result")
    assert cert_budget is not None
    assert cert_budget.max_size_mb == 2.0  # default value, not 999.0


def test_singleton_reset_between_tests():
    """
    Registering a custom type, then resetting, leaves the registry clean
    (custom type absent, defaults present).
    """
    reg = get_default_registry()
    reg.register(ArtifactBudget(artifact_type="custom_ephemeral", max_size_mb=0.1))
    assert reg.get("custom_ephemeral") is not None

    reset_default_registry()
    fresh = get_default_registry()
    assert fresh.get("custom_ephemeral") is None  # ephemeral type is gone
    assert fresh.get("replay_chunk") is not None   # defaults are back


def test_default_budgets_registered():
    """Default registry must have non-None budgets for known artifact types."""
    reg = get_default_registry()
    assert reg.get("certification_result") is not None
    assert reg.get("replay_chunk") is not None
    assert reg.get("behavior_report") is not None
    assert reg.get("proof_index") is not None

    # Spot-check key values
    cert = reg.get("certification_result")
    assert cert.max_size_mb == 2.0
    assert cert.allow_full_state is False
    assert cert.fail_on_budget_violation is False

    replay = reg.get("replay_chunk")
    assert replay.max_size_mb == 10.0
    assert replay.fail_on_budget_violation is False


def test_budget_check_result_fields():
    """BudgetCheckResult must expose allowed, action, and reason."""
    r = BudgetCheckResult(allowed=True, action="allow", reason=None)
    assert hasattr(r, "allowed")
    assert hasattr(r, "action")
    assert hasattr(r, "reason")
    assert r.allowed is True
    assert r.action == "allow"
    assert r.reason is None

    r2 = BudgetCheckResult(allowed=False, action="reject", reason="too big")
    assert r2.allowed is False
    assert r2.reason == "too big"


# ---------------------------------------------------------------------------
# CertificationRecorder integration
# ---------------------------------------------------------------------------


def test_recorder_consults_budget_before_write(tmp_path):
    """
    Recorder must call registry.check("certification_result", <int>) before
    writing proofs_bundle.json.

    Sub-case A (warn): check() returns action="warn" → file IS written.
    Sub-case B (reject): check() returns action="reject" → ArtifactBudgetViolationError
                          raised and proofs_bundle.json is NOT written.
    """
    result = _make_minimal_result()

    # --- Sub-case A: warn path (write proceeds) ---
    mock_reg_warn = MagicMock(spec=ArtifactBudgetRegistry)
    mock_reg_warn.check.return_value = BudgetCheckResult(
        allowed=True, action="warn", reason="test warn"
    )

    recorder_warn = CertificationRecorder(
        output_dir=str(tmp_path / "warn"),
        registry=mock_reg_warn,
    )
    recorder_warn.record(result)

    mock_reg_warn.check.assert_called_once()
    call_args = mock_reg_warn.check.call_args
    assert call_args[0][0] == "certification_result"   # first positional arg
    assert isinstance(call_args[0][1], int)             # second arg is int bytes

    bundle_warn = tmp_path / "warn" / "proofs_bundle.json"
    assert bundle_warn.exists(), "proofs_bundle.json must be written on warn path (INFRA-060)"

    # --- Sub-case B: reject path (write blocked) ---
    mock_reg_reject = MagicMock(spec=ArtifactBudgetRegistry)
    mock_reg_reject.check.return_value = BudgetCheckResult(
        allowed=False, action="reject", reason="test reject"
    )

    recorder_reject = CertificationRecorder(
        output_dir=str(tmp_path / "reject"),
        registry=mock_reg_reject,
    )
    with pytest.raises(ArtifactBudgetViolationError):
        recorder_reject.record(result)

    bundle_reject = tmp_path / "reject" / "proofs_bundle.json"
    assert not bundle_reject.exists(), (
        "proofs_bundle.json must NOT exist after budget reject (INFRA-060)"
    )


# ---------------------------------------------------------------------------
# ReplayManager wire test
# ---------------------------------------------------------------------------


def test_replay_manager_wire(tmp_path):
    """
    _rotate_chunk() must call get_default_registry().check("replay_chunk", <int>).

    We patch get_default_registry at the replay_manager module level and verify
    that check() is invoked with the correct artifact_type.
    """
    from src.engine.replay_manager import ReplayManager

    mock_registry = MagicMock(spec=ArtifactBudgetRegistry)
    mock_registry.check.return_value = BudgetCheckResult(
        allowed=True, action="allow", reason=None
    )

    with patch(
        "src.engine.replay_manager.get_default_registry",
        return_value=mock_registry,
    ):
        manager = ReplayManager(
            run_dir=tmp_path,
            profile_name="test_profile",
            chunk_tick_limit=10,
        )

        # Stage a minimal TraceEvent so _rotate_chunk has something to process
        from src.core.diagnostic import TraceEvent
        event = TraceEvent(
            tick=1,
            system="test_system",
            event_type="test",
            payload={},
        )
        manager._buffer.record(event)

        # Call synchronously (async_write=False) to avoid thread races in test
        manager._rotate_chunk(end_tick=1, async_write=False)

    mock_registry.check.assert_called_once()
    call_args = mock_registry.check.call_args
    assert call_args[0][0] == "replay_chunk"
    assert isinstance(call_args[0][1], int)
