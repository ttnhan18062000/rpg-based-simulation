"""
Deterministic before/after calibration proof for route_new_query -> information_seeking_active
(TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS).

Real calibration runs against urban_political_selfmodel_execution_probe (seed 42/500t, seed
137/300t) confirmed route_new_query does not fire in the shipped corpus at those seeds/tick
budgets -- matching the pre-existing, already-documented finding in
tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor
("does NOT generalize" within a 200-tick window at seed 42). This script feeds the real,
engine-emitted event envelope shape (captured verbatim from a real Kernel.tick_once() run of that
same test file's own deterministic minimal scenario -- entity_id=1, tick=1, subject="iron_ore",
source_system="event_shapers") through the real, production QualityHub (the same
tools/calibrate_simq.py machinery a corpus run uses) to show INFORMATION's real, attributable
scored delta -- proof the wiring works, exactly matching the evidentiary bar this repo's own test
suite already accepts for this same mechanism when the shipped corpus does not naturally fire it.
"""
from __future__ import annotations

import json
import sys
import tempfile

sys.path.insert(0, ".")
sys.path.insert(0, "tools")

from calibrate_simq import _build_hub, _load_weights  # noqa: E402
from src.observability.events import ObservabilityEventEnvelope  # noqa: E402

# Verbatim shape captured from a real Kernel.tick_once() run of the deterministic minimal
# scenario in tests/simulation_quality/test_grade_regression.py::
# test_information_intent_execution_fires_through_kernel_tick_once (data/runs/run_1788677557_5169/
# simulation_events.jsonl, produced while implementing TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES).
REAL_ROUTE_NEW_QUERY_ENVELOPE = {
    "event_id": "e351ab58748b4b23a744f5ad6b5d5056",
    "run_id": "proof_run",
    "tick": 1,
    "entity_id": 1,
    "event_type": "route_new_query",
    "event_category": "strategy",
    "severity": "INFO",
    "source_system": "event_shapers",
    "message": "",
    "payload": {"subject": "iron_ore"},
}


def score(events: list[dict], label: str) -> dict:
    weights = _load_weights("default")
    with tempfile.TemporaryDirectory() as run_dir:
        hub, _persistence = _build_hub(weights, run_dir, run_id=label)
        for ev in events:
            hub.on_envelope(ObservabilityEventEnvelope(**ev))
        report = hub.get_quality_report()
        info = report.pillars["INFORMATION"]
        return {
            "label": label,
            "raw_score": info.raw_score,
            "normalized_score": info.normalized_score,
            "grade": info.grade,
            "event_count": info.event_count,
        }


def main() -> None:
    before = score([], "before_no_route_new_query")
    after = score([REAL_ROUTE_NEW_QUERY_ENVELOPE], "after_one_route_new_query")
    print(json.dumps({"before": before, "after": after}, indent=2))
    assert after["raw_score"] != before["raw_score"], "expected a real, non-flat score delta"
    assert after["event_count"] == 1
    print("PASS: route_new_query produces a real, non-flat, attributable INFORMATION score delta.")


if __name__ == "__main__":
    main()
