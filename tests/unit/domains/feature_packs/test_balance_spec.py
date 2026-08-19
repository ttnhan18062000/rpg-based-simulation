"""Tests for BalanceExperimentSpec and BalanceExperimentRunner (E63D)."""

from __future__ import annotations

import pytest

from src.domains.feature_packs.balance_spec import (
    BalanceExperimentRunner,
    BalanceExperimentSpec,
)


def _spec(**kwargs) -> BalanceExperimentSpec:
    defaults = {
        "metric_path": "route_distribution.ESCORT_DIGNITARY",
        "baseline_pack": "demo_escort_pack",
        "threshold": 0.1,
        "tolerance": 0.0,
    }
    defaults.update(kwargs)
    return BalanceExperimentSpec(**defaults)


SNAPSHOT = {
    "route_distribution": {
        "ESCORT_DIGNITARY": 0.25,
        "RECOVER": 0.40,
    },
    "entity_count": 12,
}


# ── BalanceExperimentSpec ─────────────────────────────────────────────────────

def test_spec_defaults():
    s = _spec()
    assert s.tolerance == 0.0


def test_spec_frozen():
    s = _spec()
    with pytest.raises(Exception):
        s.threshold = 99.0  # type: ignore[misc]


def test_spec_round_trip():
    s = _spec(threshold=0.2, tolerance=0.05)
    assert BalanceExperimentSpec.from_dict(s.to_dict()) == s


def test_spec_rejects_negative_threshold():
    with pytest.raises(Exception):
        _spec(threshold=-0.1)


def test_spec_rejects_negative_tolerance():
    with pytest.raises(Exception):
        _spec(tolerance=-0.01)


# ── BalanceExperimentRunner ───────────────────────────────────────────────────

def test_runner_pass_when_above_threshold():
    s = _spec(threshold=0.1)
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert result.passed
    assert result.measured == pytest.approx(0.25)


def test_runner_fail_when_below_threshold():
    s = _spec(threshold=0.5)
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert not result.passed


def test_runner_pass_within_tolerance():
    # measured=0.25, threshold=0.3, tolerance=0.1 → 0.25 >= 0.3-0.1=0.2 → pass
    s = _spec(threshold=0.3, tolerance=0.1)
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert result.passed


def test_runner_fail_outside_tolerance():
    # measured=0.25, threshold=0.5, tolerance=0.1 → 0.25 >= 0.4? No → fail
    s = _spec(threshold=0.5, tolerance=0.1)
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert not result.passed


def test_runner_scalar_metric_path():
    s = _spec(metric_path="entity_count", threshold=10.0)
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert result.passed
    assert result.measured == 12.0


def test_runner_missing_path_raises_key_error():
    s = _spec(metric_path="nonexistent.key")
    with pytest.raises(KeyError):
        BalanceExperimentRunner.run(s, SNAPSHOT)


def test_runner_result_carries_spec():
    s = _spec()
    result = BalanceExperimentRunner.run(s, SNAPSHOT)
    assert result.spec is s
