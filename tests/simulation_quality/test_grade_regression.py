"""Grade regression anchors for canonical simulation scenarios.

These tests require actual simulation runs. Marked @pytest.mark.slow so they are
skipped in fast CI (pytest -m "not slow"). To regenerate anchors:
    python3 tools/generate_grade_anchors.py

When anchors contain "UNKNOWN", the test auto-skips with an informational message.
When anchors are populated, the test fails if any pillar grade changes by more than
one letter (e.g., B → D would fail; B → C is allowed).
"""
from __future__ import annotations
import json
import os
import pytest

_ANCHORS_PATH = os.path.join(os.path.dirname(__file__), "fixtures/grade_anchors.json")
_GRADE_ORDER = ["S", "A", "B", "C", "D", "F"]


def _grade_distance(g1: str, g2: str) -> int:
    try:
        return abs(_GRADE_ORDER.index(g1) - _GRADE_ORDER.index(g2))
    except ValueError:
        return 99


def _load_anchors() -> dict:
    with open(_ANCHORS_PATH) as f:
        return json.load(f)


@pytest.mark.slow
def test_sandbox_world_grade_anchors() -> None:
    """sandbox_world seed=42 100 ticks: verify no pillar drifts >1 letter from anchor."""
    anchors = _load_anchors()
    scenario_anchors = anchors.get("sandbox_world", {}).get("pillars", {})
    if all(v == "UNKNOWN" for v in scenario_anchors.values()):
        pytest.skip("Grade anchors not yet populated. Run tools/generate_grade_anchors.py first.")

    # Import here to avoid CI dependency on full engine
    try:
        from tests.simulation_quality.fixtures.run_sandbox_world import run_and_grade
    except ImportError:
        pytest.skip("run_sandbox_world fixture not available in this environment.")
        return

    actual_grades = run_and_grade(seed=42, ticks=100)
    for pillar, anchor_grade in scenario_anchors.items():
        if anchor_grade == "UNKNOWN":
            continue
        actual = actual_grades.get(pillar, "F")
        dist = _grade_distance(anchor_grade, actual)
        assert dist <= 1, (
            f"Pillar {pillar} drifted more than 1 letter: anchor={anchor_grade} actual={actual}"
        )


@pytest.mark.slow
def test_urban_political_grade_anchors() -> None:
    """urban_political seed=42 100 ticks: verify no pillar drifts >1 letter from anchor."""
    anchors = _load_anchors()
    scenario_anchors = anchors.get("urban_political", {}).get("pillars", {})
    if all(v == "UNKNOWN" for v in scenario_anchors.values()):
        pytest.skip("Grade anchors not yet populated. Run tools/generate_grade_anchors.py first.")

    try:
        from tests.simulation_quality.fixtures.run_urban_political import run_and_grade
    except ImportError:
        pytest.skip("run_urban_political fixture not available in this environment.")
        return

    actual_grades = run_and_grade(seed=42, ticks=100)
    for pillar, anchor_grade in scenario_anchors.items():
        if anchor_grade == "UNKNOWN":
            continue
        actual = actual_grades.get(pillar, "F")
        dist = _grade_distance(anchor_grade, actual)
        assert dist <= 1, (
            f"Pillar {pillar} drifted more than 1 letter: anchor={anchor_grade} actual={actual}"
        )


@pytest.mark.slow
def test_grade_anchor_file_exists_and_valid() -> None:
    """Sanity check: grade_anchors.json must exist and have the expected structure."""
    assert os.path.exists(_ANCHORS_PATH), f"Grade anchors file missing: {_ANCHORS_PATH}"
    anchors = _load_anchors()
    assert "sandbox_world" in anchors
    assert "urban_political" in anchors
    for scenario in ("sandbox_world", "urban_political"):
        assert "seed" in anchors[scenario]
        assert "ticks" in anchors[scenario]
        pillars = anchors[scenario]["pillars"]
        assert len(pillars) == 10, f"{scenario}: expected 10 pillars, got {len(pillars)}"
        for pillar, grade in pillars.items():
            assert grade in _GRADE_ORDER + ["UNKNOWN"], (
                f"{scenario}/{pillar}: invalid grade '{grade}'"
            )
