"""
TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION:

Verifies the `resource_budget_large` pytest marker mechanism added to
tests/conftest.py's pytest_runtest_setup() hook — it must force the effective
--resource-budget to "large" for any test carrying the marker, unless the CLI
value is explicitly "off" (the profiler escape hatch, which always wins).
"""
from __future__ import annotations

import signal

import pytest

from tests import conftest as conftest_module


class _FakeMarker:
    name = "resource_budget_large"


class _FakeConfig:
    def __init__(self, budget: str) -> None:
        self._budget = budget

    def getoption(self, name: str) -> str:
        assert name == "--resource-budget"
        return self._budget


class _FakeItem:
    def __init__(self, budget: str, marked: bool) -> None:
        self.config = _FakeConfig(budget)
        self._marked = marked

    def get_closest_marker(self, name: str):
        if self._marked and name == "resource_budget_large":
            return _FakeMarker()
        return None


@pytest.fixture(autouse=True)
def _disable_alarm_after_each_test():
    yield
    signal.alarm(0)


def test_resource_budget_marker_applies_large_to_named_grade_stability_tests(monkeypatch):
    """A marked item resolves to the "large" branch's limits regardless of a
    smaller CLI default (medium)."""
    captured_limits = {}
    real_setrlimit = None
    try:
        import resource as resource_module
        real_setrlimit = resource_module.setrlimit

        def _spy_setrlimit(which, limits):
            captured_limits["mem"] = limits
            real_setrlimit(which, limits)

        monkeypatch.setattr(resource_module, "setrlimit", _spy_setrlimit)
    except ImportError:
        pass

    captured_alarm = {}
    real_alarm = signal.alarm

    def _spy_alarm(seconds):
        captured_alarm["time_limit"] = seconds
        return real_alarm(seconds)

    monkeypatch.setattr(signal, "alarm", _spy_alarm)

    item = _FakeItem(budget="medium", marked=True)
    conftest_module.pytest_runtest_setup(item)

    assert captured_alarm["time_limit"] == 600
    if real_setrlimit is not None:
        assert captured_limits["mem"] == (8 * 1024 * 1024 * 1024, 8 * 1024 * 1024 * 1024)


def test_resource_budget_marker_does_not_affect_unmarked_tests(monkeypatch):
    """An unmarked item keeps whatever the CLI default resolves to (medium here)."""
    captured_alarm = {}
    real_alarm = signal.alarm

    def _spy_alarm(seconds):
        captured_alarm["time_limit"] = seconds
        return real_alarm(seconds)

    monkeypatch.setattr(signal, "alarm", _spy_alarm)

    item = _FakeItem(budget="medium", marked=False)
    conftest_module.pytest_runtest_setup(item)

    assert captured_alarm["time_limit"] == 60


def test_resource_budget_off_short_circuits_regardless_of_marker(monkeypatch):
    """--resource-budget off always wins over the marker — no enforcement at all."""
    alarm_called = {"called": False}

    def _spy_alarm(seconds):
        alarm_called["called"] = True

    monkeypatch.setattr(signal, "alarm", _spy_alarm)

    item = _FakeItem(budget="off", marked=True)
    conftest_module.pytest_runtest_setup(item)

    assert not alarm_called["called"]
