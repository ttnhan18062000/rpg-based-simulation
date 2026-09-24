"""Cross-reference proof for docs/plans/status_axis_model.md.

TCK-20260923-STATUS-VOCABULARY-RECONCILIATION.

AC 5 requires all four existing status-vocabulary homes to cross-reference the axis-model doc, so
no future reader meets one vocabulary without learning the other three exist. This is a permanent
guard (unlike the one-time AC 7 diff check for this same ticket) -- it should stay true forever, not
just at the moment this ticket lands.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

AXIS_MODEL_DOC = REPO_ROOT / "docs" / "plans" / "status_axis_model.md"

_REQUIRED_HOMES = [
    REPO_ROOT / "registries" / "mechanisms.yaml",
    REPO_ROOT / "docs" / "brainstorm" / "core_rpg_design_direction.md",
    REPO_ROOT / "docs" / "plans" / "simulation_semantic_control_plane" / "architecture.md",
    REPO_ROOT / "tools" / "mechanism_registry" / "registry.py",
]


def test_axis_model_doc_exists_and_is_non_empty() -> None:
    assert AXIS_MODEL_DOC.is_file(), f"missing {AXIS_MODEL_DOC}"
    assert AXIS_MODEL_DOC.read_text(encoding="utf-8").strip(), "status_axis_model.md is empty"


def test_all_required_homes_cross_reference_axis_model() -> None:
    missing = [
        str(path.relative_to(REPO_ROOT))
        for path in _REQUIRED_HOMES
        if "status_axis_model.md" not in path.read_text(encoding="utf-8")
    ]
    assert not missing, f"missing cross-reference to status_axis_model.md in: {missing}"
