"""Each synthetic worked example declares a lane, and that lane's CI pytest step covers the example's path."""

from pathlib import Path

import pytest

from tests.mechanic_scenarios.synthetic_examples import test_scenario_helper_examples as examples
from tools.test_architecture import core_rpg_report as report

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_PATH = "tests/mechanic_scenarios/synthetic_examples/test_scenario_helper_examples.py"


def test_examples_are_labelled_synthetic():
    assert examples.LABEL == "synthetic"


def test_declared_lane_covers_the_examples_in_ci():
    lanes = report.parse_lanes(REPO_ROOT / ".github" / "workflows" / "test.yml")
    matching = [lane for lane in lanes if lane["lane"].startswith(examples.LANE + "/")]
    assert matching, f"no CI lane named {examples.LANE!r}"
    assert any(report._lane_covers(lane, EXAMPLE_PATH) for lane in matching)
