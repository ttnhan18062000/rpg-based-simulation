"""Shared fixture for observability flows whose verdict must not depend on how fast the host ran a tick."""
import dataclasses

import pytest

from src.engine.signal_source import LiveSignalSource


@pytest.fixture
def tick_cost_ms(monkeypatch):
    """Return ``set(ms)``: from then on every tick records ``ms`` as its measured compute cost, whatever the clock said.

    The seam is ``LiveSignalSource.tick_end_signals``, the one place a tick's measured cost becomes the ``PressureSignals`` that the metric windows and the
    HighCPULatencyRule read. Nothing in ``src/`` changes. TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT.
    """
    original = LiveSignalSource.tick_end_signals
    pinned = {}

    def tick_end_signals(self, **kwargs):
        signals = original(self, **kwargs)
        return dataclasses.replace(signals, tick_compute_ms=pinned["ms"]) if "ms" in pinned else signals

    monkeypatch.setattr(LiveSignalSource, "tick_end_signals", tick_end_signals)
    return lambda ms: pinned.update(ms=float(ms))
