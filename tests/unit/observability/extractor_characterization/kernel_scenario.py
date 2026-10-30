"""Record EventExtractor.extract over a short seeded run of the real Kernel, under every characterization config.

``audit_mode`` pins the kernel's governors to zeroed signals, so no wall clock changes what the run computes. Each tick's
(prior, current, update) triple is evaluated under every config in recorder_plugin.CONFIGS; the kernel itself runs unchanged.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.platform.rng import DeterministicRNG
from tests.unit.observability.extractor_characterization.recorder_plugin import (
    CONFIGS,
    _evaluate,
    canonical,
    digest_row,
    restore,
    snapshot,
)
from tools.calibrate_simq import _load_world_state


def record_kernel_run(world: str, seed: int, ticks: int) -> list[dict[str, Any]]:
    """One digest row per tick that the extractor was called for."""
    state, _report = _load_world_state(world, seed)
    rows: list[dict[str, Any]] = []
    original = EventExtractor.extract

    def wrapped(prior, current, update, mode=ObservabilityMode.LIGHT):
        snap = snapshot()
        results: dict[str, list[str]] = {}
        for name, (flags, mode_override) in CONFIGS.items():
            if name == "as_built":
                continue
            restore(snap)
            results[name] = [canonical(e) for e in _evaluate(original, prior, current, update, mode, flags, mode_override)]
        restore(snap)
        actual = original(prior, current, update, mode)
        results["as_built"] = [canonical(e) for e in actual]
        rows.append(digest_row({"test": f"{world}:{seed}", "call": len(rows), "mode": str(getattr(mode, "value", mode)), "results": results}))
        return actual

    EventExtractor.reset_run_state()
    EventExtractor.extract = staticmethod(wrapped)
    try:
        kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(state.seed),
                        flags={"no_frame_pacing": True, "audit_mode": True, "no_replay": True})
        try:
            for _ in range(ticks):
                kernel.tick_once()
        finally:
            kernel.shutdown()
    finally:
        EventExtractor.extract = staticmethod(original)
        EventExtractor.reset_run_state()
    return rows


if __name__ == "__main__":
    # python -m ...kernel_scenario <world> <seed> <ticks>: one digest row per line on stdout (corpus.run_kernel_scenario reads it).
    for row in record_kernel_run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3])):
        sys.stdout.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
