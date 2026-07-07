"""Grade regression anchors for canonical simulation scenarios.

Tests compare per-pillar grades in committed calibration reports against anchors stored
in tests/simulation_quality/fixtures/grade_anchors.json. A regression is flagged when
a pillar grade shifts by more than one letter from its anchor.

Band tolerance rule (±1 letter):
  anchor=B → accepts A, B, C — fails on D or S
  anchor=A → accepts S, A, B — fails on C or D
  GRADE_ORDER (ascending quality): D < C < B < A < S

Fast tests (200t / 500t runs) run in the standard suite.
Slow tests (1000t runs) require ``pytest -m slow`` or omit ``-m "not slow"``.

To update anchors after an intentional scoring change:
  1. Re-run calibration: ``make calibrate`` (or per-scenario variant)
  2. Inspect new grades in ``data/calibration/<run_key>/quality_report.json``
  3. Edit ``tests/simulation_quality/fixtures/grade_anchors.json`` with new grades
  4. Run this file to confirm all pass
  5. Commit both fixture and calibration data together
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRADE_ORDER = ["D", "C", "B", "A", "S"]  # ascending quality; index distance = band distance

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "grade_anchors.json"

# Calibration root relative to repo root (tests run from repo root).
_CALIBRATION_ROOT = Path("data/calibration")

FAST_ANCHOR_KEYS = [
    "sandbox_world_seed42_200t",
    "sandbox_world_seed137_200t",
    "sandbox_world_seed999_200t",
    "dungeon_crawl_seed42_200t",
    "urban_political_seed42_200t",
    "simq_routing_test_seed42_500t",
    # new — simq_routing_test additional seeds
    "simq_routing_test_seed123_500t",
    "simq_routing_test_seed456_500t",
    # new — dungeon_crawl 500t
    "dungeon_crawl_seed42_500t",
    "dungeon_crawl_seed123_500t",
    "dungeon_crawl_seed456_500t",
    # new — urban_political 500t
    "urban_political_seed42_500t",
    "urban_political_seed123_500t",
    "urban_political_seed456_500t",
    # new — TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS: 5 newly-anchored worlds, 3 seeds each
    "frontier_extended_seed42_200t",
    "frontier_extended_seed123_200t",
    "frontier_extended_seed456_200t",
    "frontier_living_world_seed42_200t",
    "frontier_living_world_seed123_200t",
    "frontier_living_world_seed456_200t",
    "wilderness_survival_seed42_200t",
    "wilderness_survival_seed123_200t",
    "wilderness_survival_seed456_200t",
    "highland_traverse_seed42_200t",
    "highland_traverse_seed123_200t",
    "highland_traverse_seed456_200t",
    "swamp_border_world_seed42_200t",
    "swamp_border_world_seed123_200t",
    "swamp_border_world_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO: 2 unit-tier worlds, 3 seeds each
    "unit_faction_tension_seed42_200t",
    "unit_faction_tension_seed123_200t",
    "unit_faction_tension_seed456_200t",
    "unit_information_source_seed42_200t",
    "unit_information_source_seed123_200t",
    "unit_information_source_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT: 1 unit-tier world, 3 seeds
    "unit_selfmodel_pilot_seed42_200t",
    "unit_selfmodel_pilot_seed123_200t",
    "unit_selfmodel_pilot_seed456_200t",
    # new — TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY: 1 unit-tier world, 3 seeds, 500t
    "hero_guild_routing_seed42_500t",
    "hero_guild_routing_seed123_500t",
    "hero_guild_routing_seed456_500t",
]

SLOW_ANCHOR_KEYS = [
    "dungeon_crawl_seed42_1000t",
    "sandbox_world_seed42_1000t",
    # new — dungeon_crawl 1000t
    "dungeon_crawl_seed123_1000t",
    "dungeon_crawl_seed456_1000t",
    # new — urban_political 1000t
    "urban_political_seed42_1000t",
    "urban_political_seed123_1000t",
    "urban_political_seed456_1000t",
    # new — dungeon_crawl 2000t
    "dungeon_crawl_seed42_2000t",
    "dungeon_crawl_seed123_2000t",
    "dungeon_crawl_seed456_2000t",
    # new — sandbox_world 2000t
    "sandbox_world_seed42_2000t",
]

MINIMUM_FAST_ANCHORS = set(FAST_ANCHOR_KEYS)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
    """Return True if *actual* grade is within *tolerance* positions of *anchor*.

    Uses GRADE_ORDER (ascending quality: D=0, C=1, B=2, A=3, S=4).
    Both grades must be valid members of GRADE_ORDER; unknown grades return False.
    """
    if actual not in GRADE_ORDER or anchor not in GRADE_ORDER:
        return False
    return abs(GRADE_ORDER.index(actual) - GRADE_ORDER.index(anchor)) <= tolerance


def _extract_pillar_grades(report: dict[str, Any]) -> dict[str, str]:
    """Extract ``{PILLAR: grade}`` mapping from a quality_report.json dict."""
    return {
        pillar: data["grade"]
        for pillar, data in report.get("pillars", {}).items()
    }


def _load_calibration_report(run_key: str) -> dict[str, Any] | None:
    """Load ``data/calibration/{run_key}/quality_report.json``.

    Returns None if the file does not exist (allows pytest.skip downstream).
    """
    path = _CALIBRATION_ROOT / run_key / "quality_report.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def grade_anchors() -> dict[str, Any]:
    """Load the committed grade anchor fixture (module-scoped, loaded once)."""
    return json.loads(FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# Fast anchor tests — 200t / 500t runs (excluded from slow CI mark)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("run_key", FAST_ANCHOR_KEYS)
def test_grade_within_anchor_band(run_key: str, grade_anchors: dict) -> None:
    """Each pillar grade must be within ±1 letter of the committed anchor.

    Reads the current calibration report from data/calibration/{run_key}/quality_report.json.
    Skips if the calibration file is not present (calibration not yet run for this key).
    """
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    anchors = grade_anchors[run_key]
    actual_grades = _extract_pillar_grades(report)

    failures: list[str] = []
    for pillar, anchor_grade in anchors.items():
        actual = actual_grades.get(pillar, "C")
        if not _within_band(actual, anchor_grade):
            failures.append(
                f"  {pillar}: actual={actual!r} is outside ±1 band of anchor={anchor_grade!r}"
            )

    assert not failures, (
        f"{run_key} — {len(failures)} pillar(s) drifted beyond anchor band:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Slow anchor tests — 1000t long runs
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("run_key", SLOW_ANCHOR_KEYS)
def test_grade_within_anchor_band_long_run(run_key: str, grade_anchors: dict) -> None:
    """Long-run anchor check (1000t). Marked slow — excluded from fast CI.

    Reads data/calibration/{run_key}/quality_report.json.
    Skips if the calibration file is not present.
    """
    if run_key not in grade_anchors:
        pytest.skip(f"No anchor entry for {run_key!r} in grade_anchors.json")

    report = _load_calibration_report(run_key)
    if report is None:
        pytest.skip(f"Calibration report not found: data/calibration/{run_key}/quality_report.json")

    anchors = grade_anchors[run_key]
    actual_grades = _extract_pillar_grades(report)

    failures: list[str] = []
    for pillar, anchor_grade in anchors.items():
        actual = actual_grades.get(pillar, "C")
        if not _within_band(actual, anchor_grade):
            failures.append(
                f"  {pillar}: actual={actual!r} is outside ±1 band of anchor={anchor_grade!r}"
            )

    assert not failures, (
        f"{run_key} — {len(failures)} pillar(s) drifted beyond anchor band:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Structural sanity test
# ---------------------------------------------------------------------------

def test_grade_anchor_file_exists_and_valid(grade_anchors: dict) -> None:
    """grade_anchors.json must exist and contain at least all fast anchor run keys.

    Each entry must have exactly 10 pillar grades, all in GRADE_ORDER.
    """
    assert FIXTURE_PATH.exists(), f"Grade anchors fixture missing: {FIXTURE_PATH}"

    missing_keys = MINIMUM_FAST_ANCHORS - set(grade_anchors.keys())
    assert not missing_keys, f"grade_anchors.json missing required run keys: {missing_keys}"

    for run_key in MINIMUM_FAST_ANCHORS:
        entry = grade_anchors[run_key]
        assert len(entry) == 10, (
            f"{run_key}: expected 10 pillars, got {len(entry)}: {list(entry.keys())}"
        )
        for pillar, grade in entry.items():
            assert grade in GRADE_ORDER, (
                f"{run_key}/{pillar}: grade {grade!r} not in GRADE_ORDER {GRADE_ORDER}"
            )
