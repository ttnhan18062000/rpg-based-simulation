"""Doc-quality regression guard for docs/brainstorm/core_rpg_design_direction.md §10.

TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW Scope item 5 (first bullet): the pointer sentence
to docs/plans/status_axis_model.md and the "**Status note (2026-09-24).**" heading were merged
into one run-on paragraph with no break. This is a formatting-only fix -- guards the paragraph
break, never asserts anything about the §10 vocabulary's own content.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_DOC_PATH = REPO_ROOT / "docs" / "brainstorm" / "core_rpg_design_direction.md"


def test_core_rpg_design_direction_section_10_has_no_run_on_paragraph():
    text = _DOC_PATH.read_text(encoding="utf-8")
    assert "Rule realization axis.\n\n**Status note (2026-09-24).**" in text, (
        "expected a blank line between the status_axis_model.md pointer sentence and the "
        "'Status note (2026-09-24).' heading in §10 -- run-on paragraph regressed"
    )
