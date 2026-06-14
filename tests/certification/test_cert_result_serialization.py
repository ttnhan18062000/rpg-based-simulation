"""Tests for CertificationResult safe serialization boundary.

Verifies that to_artifact_dict() builds the proof artifact field-by-field
without ever walking final_state, and that to_json() delegates fully to
to_artifact_dict() with no asdict() call.

TCK-20260614-CERT-SAFE-SERIAL
"""
from __future__ import annotations

import dataclasses
import json
import time

import pytest

from src.certification.models import (
    ArenaStopCondition,
    CertificationResult,
    EnvironmentCapture,
    FailureKind,
    HardwareClass,
    MeasurementPoint,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALLOWED_STATE_ATTRS = frozenset(
    {"tick", "seed", "entities", "resource_nodes", "regions", "buildings", "corpses", "ground_items"}
)


class PoisonState:
    """Test double that raises AssertionError on any unexpected attribute access.

    Only the eight attributes listed in _ALLOWED_STATE_ATTRS may be accessed.
    Any other access (including __class__, __dict__, __dataclass_fields__, etc.)
    raises AssertionError so that the test can detect whether _final_state_summary()
    leaks beyond its contracted boundary.
    """

    def __init__(self, *, tick=10, seed=42, entities=None, resource_nodes=None,
                 regions=None, buildings=None, corpses=None, ground_items=None):
        # Bypass __setattr__ by writing directly to __dict__ at construction time.
        object.__setattr__(self, "tick", tick)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "entities", entities if entities is not None else {"e1": ..., "e2": ...})
        object.__setattr__(self, "resource_nodes", resource_nodes if resource_nodes is not None else {"r1": ...})
        object.__setattr__(self, "regions", regions if regions is not None else {"reg1": ..., "reg2": ..., "reg3": ...})
        object.__setattr__(self, "buildings", buildings if buildings is not None else {})
        object.__setattr__(self, "corpses", corpses if corpses is not None else {"c1": ...})
        object.__setattr__(self, "ground_items", ground_items if ground_items is not None else {})

    def __getattribute__(self, name: str):
        # Allow dunder access needed by Python runtime itself (e.g. __class__)
        # but block any non-dunder attribute not in the allowed set.
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)
        if name not in _ALLOWED_STATE_ATTRS:
            raise AssertionError(
                f"PoisonState: unexpected attribute access '{name}' — "
                "_final_state_summary() must only access the 8 contracted fields."
            )
        return object.__getattribute__(self, name)


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
        mode="standard",
        memory_rss_mb=512.0,
        memory_trend_mb_per_tick=0.1,
        tick_compute_ms=20.0,
        tick_compute_ms_avg=18.5,
        work_debt=0,
        worker_utilization=0.75,
        queue_utilization=0.5,
        replay_pressure=0.1,
        active_workers=4,
        timestamp=time.time(),
    )


def _make_minimal_result(**overrides) -> CertificationResult:
    defaults = dict(
        run_id="run-001",
        timestamp=1700000000.0,
        commit_sha="abc123",
        profile_name="standard_gaming_profile",
        scenario_id="scen-001",
        seed=42,
        environment=_make_env(),
        measurements=[_make_measurement()],
        baseline_hash="hash-baseline",
        final_hash="hash-final",
        governor_mode_sequence=["standard"],
        conformance_passed=True,
    )
    defaults.update(overrides)
    return CertificationResult(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPoisonStateGuard:
    """Verify _final_state_summary() does not access forbidden attributes."""

    def test_to_artifact_dict_excludes_final_state(self):
        """PoisonState as final_state: artifact dict has final_state=None and correct summary."""
        poison = PoisonState(
            tick=10,
            seed=42,
            entities={"e1": ..., "e2": ...},          # 2 entities
            resource_nodes={"r1": ...},                 # 1 node
            regions={"reg1": ..., "reg2": ..., "reg3": ...},  # 3 regions
            buildings={},
            corpses={"c1": ...},                        # 1 corpse
            ground_items={},
        )
        result = _make_minimal_result(final_state=poison, final_hash="hash-final")

        # This must NOT raise AssertionError from PoisonState
        artifact = result.to_artifact_dict()

        assert artifact["final_state"] is None, "final_state must always be None in artifact dict"

        summary = artifact["final_state_summary"]
        assert summary is not None, "summary should be a dict when final_state is set"
        assert summary["tick"] == 10
        assert summary["seed"] == 42
        assert summary["entity_count"] == 2
        assert summary["resource_node_count"] == 1
        assert summary["region_count"] == 3
        assert summary["building_count"] == 0
        assert summary["corpse_count"] == 1
        assert summary["ground_item_count"] == 0
        assert summary["final_hash"] == "hash-final"


class TestToJsonNoCasdict:
    """Verify to_json() does not call dataclasses.asdict()."""

    def test_to_json_does_not_call_asdict(self, monkeypatch):
        """Monkeypatching dataclasses.asdict to raise must not affect to_json()."""
        import src.certification.models as models_module

        def _boom(*args, **kwargs):
            raise RuntimeError("asdict() must not be called by to_json()")

        monkeypatch.setattr(dataclasses, "asdict", _boom, raising=False)

        result = _make_minimal_result()
        raw = result.to_json()

        # Must return valid JSON
        parsed = json.loads(raw)
        assert parsed["schema_version"] == "certification_result.v1"
        assert parsed["final_state"] is None


class TestFinalStateSummaryNone:
    """Verify _final_state_summary() returns None when final_state is None."""

    def test_final_state_summary_none_when_no_state(self):
        result = _make_minimal_result(final_state=None)
        summary = result._final_state_summary()
        assert summary is None

        artifact = result.to_artifact_dict()
        assert artifact["final_state_summary"] is None


class TestRequiredKeys:
    """Verify all required AC keys are present in to_artifact_dict() output."""

    REQUIRED_KEYS = [
        "schema_version",
        "run_id",
        "timestamp",
        "commit_sha",
        "profile_name",
        "scenario_id",
        "seed",
        "environment",
        "measurements",
        "baseline_hash",
        "final_hash",
        "governor_mode_sequence",
        "conformance_passed",
        "stop_condition",
        "allowed_failure_observed",
        "failure_kind",
        "failure_reason",
        "peak_rss_mb",
        "total_cpu_sec",
        "final_state",
        "final_state_summary",
        "final_state_artifact",
    ]

    REQUIRED_ENV_KEYS = [
        "detected_hardware_class",
        "effective_hardware_class",
        "override_applied",
    ]

    def test_required_keys_present(self):
        result = _make_minimal_result()
        artifact = result.to_artifact_dict()

        for key in self.REQUIRED_KEYS:
            assert key in artifact, f"Missing required key: {key}"

        env = artifact["environment"]
        for key in self.REQUIRED_ENV_KEYS:
            assert key in env, f"Missing required environment key: {key}"

        # Enum values must be strings
        assert isinstance(artifact["stop_condition"], str)
        assert isinstance(artifact["failure_kind"], str)
        assert isinstance(env["detected_hardware_class"], str)
        assert isinstance(env["effective_hardware_class"], str)

        # Placeholders
        assert artifact["final_state"] is None
        assert artifact["final_state_artifact"] is None

        # Measurements list
        assert isinstance(artifact["measurements"], list)
        assert len(artifact["measurements"]) == 1
        mp = artifact["measurements"][0]
        for field in ("tick", "mode", "memory_rss_mb", "memory_trend_mb_per_tick",
                      "tick_compute_ms", "tick_compute_ms_avg", "work_debt",
                      "worker_utilization", "queue_utilization", "replay_pressure",
                      "active_workers", "timestamp"):
            assert field in mp, f"MeasurementPoint.to_dict() missing field: {field}"


class TestGuardRaisesOnMissingMetadata:
    """Verify ValueError is raised when required metadata is absent."""

    def test_guard_raises_on_missing_profile_name(self):
        result = _make_minimal_result(profile_name="")
        with pytest.raises(ValueError, match="profile_name is required"):
            result.to_artifact_dict()

    def test_guard_raises_on_none_profile_name(self):
        result = _make_minimal_result()
        object.__setattr__(result, "profile_name", None) if hasattr(result, "__slots__") else setattr(result, "profile_name", None)
        with pytest.raises(ValueError, match="profile_name is required"):
            result.to_artifact_dict()

    def test_guard_raises_on_missing_scenario_id(self):
        result = _make_minimal_result(scenario_id="")
        with pytest.raises(ValueError, match="scenario_id is required"):
            result.to_artifact_dict()

    def test_guard_raises_on_missing_environment(self):
        result = _make_minimal_result()
        result.environment = None
        with pytest.raises(ValueError, match="environment is required"):
            result.to_artifact_dict()
