"""
Fallback retirement gate — CI-runnable architecture check.

Reads docs/guidelines/fallback_retirement_criteria.md and asserts that every
mapped test file exists on disk. If a test file is removed or renamed without
updating the criteria doc, this gate fails clearly.

This test does NOT run the mapped tests — it only verifies they exist and
are reachable by pytest. The actual gate passes when:
  1. All mapped test files exist
  2. No criterion has status UNMET or NOT_CHECKED
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

CRITERIA_DOC = Path("docs/guidelines/fallback_retirement_criteria.md")

# Explicit registry of the 9 retirement gate criteria.
# Each entry: (criterion_number, description_summary, mapped_test_file, expected_status)
RETIREMENT_CRITERIA = [
    (
        1,
        "Catalog-backed mode is default",
        "tests/unit/runtime/test_registry_bootstrap_modes.py",
        "MET",
    ),
    (
        2,
        "Strict mode passes",
        "tests/unit/runtime/test_registry_bootstrap_modes.py",
        "MET",
    ),
    (
        3,
        "Core scenario matrix passes",
        "tests/integration/scenarios/test_scenario_catalog_matrix.py",
        "MET",
    ),
    (
        4,
        "First content pack passes (frontier_extended_pack)",
        "tests/integration/content/test_strict_world_matrix.py",
        "MET",
    ),
    (
        5,
        "Second content pack passes (swamp_border_pack)",
        "tests/integration/content/test_swamp_border_pack.py",
        "MET",
    ),
    (
        6,
        "Legacy enum mapping is complete",
        "tests/architecture/test_enum_migration_report.py",
        "MET",
    ),
    (
        7,
        "Relation projection used in high-impact systems",
        "tests/integration/content/test_registry_projection_parity.py",
        "MET",
    ),
    (
        8,
        "Arena smoke has clean catalog equivalent",
        "tests/architecture/test_no_new_hardcoded_gameplay_truth.py",
        "MET",
    ),
    (
        9,
        "Hardcoded gameplay guard passes",
        "tests/architecture/test_no_old_structural_content_paths.py",
        "MET",
    ),
]


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

def test_criteria_doc_exists():
    """The retirement criteria document must exist at the expected path."""
    assert CRITERIA_DOC.exists(), (
        f"Retirement criteria doc not found at {CRITERIA_DOC}. "
        "Create docs/guidelines/fallback_retirement_criteria.md before proceeding."
    )


def test_criteria_doc_has_all_9_criteria():
    """The criteria doc must describe all 9 retirement conditions."""
    content = CRITERIA_DOC.read_text()
    # Count criterion headers (### 1. through ### 9.)
    found = re.findall(r"###\s+\d+\.", content)
    assert len(found) >= 9, (
        f"Expected 9 criteria in {CRITERIA_DOC}, found {len(found)}. "
        "Add missing criteria before proceeding."
    )


@pytest.mark.parametrize(
    "criterion_num,description,test_file,expected_status",
    RETIREMENT_CRITERIA,
    ids=[f"criterion_{c[0]}" for c in RETIREMENT_CRITERIA],
)
def test_mapped_test_file_exists(criterion_num, description, test_file, expected_status):
    """Each criterion's mapped test file must exist on disk."""
    assert os.path.exists(test_file), (
        f"[Criterion {criterion_num}: {description!r}] "
        f"Mapped test file {test_file!r} does not exist. "
        "Either create the missing test or update the criteria mapping."
    )


@pytest.mark.parametrize(
    "criterion_num,description,test_file,expected_status",
    RETIREMENT_CRITERIA,
    ids=[f"criterion_{c[0]}_status" for c in RETIREMENT_CRITERIA],
)
def test_criterion_is_met(criterion_num, description, test_file, expected_status):
    """Every criterion must have status MET before retirement proceeds."""
    assert expected_status == "MET", (
        f"[Criterion {criterion_num}: {description!r}] "
        f"Status is {expected_status!r}, expected 'MET'. "
        "Resolve the criterion before proceeding with fallback retirement."
    )


def test_all_criteria_are_met():
    """Top-level gate: all 9 criteria must be MET."""
    unmet = [
        (num, desc) for num, desc, _, status in RETIREMENT_CRITERIA
        if status != "MET"
    ]
    assert not unmet, (
        f"Fallback retirement BLOCKED. Unmet criteria: "
        + ", ".join(f"[{n}] {d}" for n, d in unmet)
    )


def test_no_criterion_is_not_checked():
    """No criterion may be left as NOT_CHECKED — each must have been evaluated."""
    not_checked = [
        (num, desc) for num, desc, _, status in RETIREMENT_CRITERIA
        if status == "NOT_CHECKED"
    ]
    assert not not_checked, (
        f"Criteria with NOT_CHECKED status must be evaluated: "
        + ", ".join(f"[{n}] {d}" for n, d in not_checked)
    )
