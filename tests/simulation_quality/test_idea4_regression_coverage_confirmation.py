"""Idea 4 (Unified Modification) corpus-test AC (TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS):
confirms `tests/simulation_quality/test_grade_regression.py`'s own existing anchors already pin
COMBAT-pillar scores for `urban_political_seed42_200t` and `simq_routing_test_seed42_500t` within
tolerance -- this idea needs zero new authoring, only a citation-level confirmation that the
regression infrastructure already covers it.
"""
from __future__ import annotations

import json
from pathlib import Path

ANCHORS_PATH = Path("tests/simulation_quality/fixtures/grade_anchors.json")


def test_combat_pillar_already_regression_anchored_for_target_worlds():
    anchors = json.loads(ANCHORS_PATH.read_text())

    for run_key in ("urban_political_seed42_200t", "simq_routing_test_seed42_500t"):
        assert run_key in anchors, f"expected an existing anchor entry for {run_key}"
        combat = anchors[run_key].get("COMBAT")
        assert combat is not None, f"{run_key} has no COMBAT pillar anchor"
        assert "grade" in combat and "score" in combat, f"{run_key} COMBAT anchor missing fields"
