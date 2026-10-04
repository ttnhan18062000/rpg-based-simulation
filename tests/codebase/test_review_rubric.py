"""Pins the review rubric in docs/guidelines/python_code_standard.md (TCK-20261004-REVIEW-RUBRIC)."""
from __future__ import annotations

from pathlib import Path

_STANDARD = Path(__file__).resolve().parent.parent.parent / "docs" / "guidelines" / "python_code_standard.md"


def _rubric() -> str:
    text = _STANDARD.read_text(encoding="utf-8")
    start = text.index("## 11. Review rubric")
    return text[start : text.index("\n## ", start + 1)]


def test_rubric_names_the_three_categories() -> None:
    """Important, Nit and Pre-existing are each defined."""
    rubric = _rubric()
    for category in ("**Important**", "**Nit**", "**Pre-existing**"):
        assert category in rubric


def test_rubric_says_only_important_blocks() -> None:
    """The blocking rule is one stable sentence."""
    assert "Only Important blocks." in _rubric()


def test_rubric_never_downgrades_a_correctness_bug() -> None:
    """An Important finding may name a concrete failure instead of a rule ID."""
    assert "for a correctness bug, the concrete failure" in _rubric()


def test_rubric_stays_short() -> None:
    """One table plus at most 6 bullets."""
    lines = _rubric().splitlines()
    assert sum(1 for line in lines if line.startswith("- ")) <= 6
    assert sum(1 for line in lines if line.startswith("| **")) == 3
