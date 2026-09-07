"""Tests for tools/agent_replay/defect_detectors.py (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #3).

M2's known-positive input is reconstructed from TCK-20260831-RACE-RELATIONS-MATRIX's real closing
commit and its own ticket text. That ticket's final (post-fix) `## Files Changed` prose itself
discloses the real historical gap: `docs/mechanics/02_combat_laws.md` "was not updated by the
original Implement pass" and was "added by Document-Update after" the gap was caught at Verify
(see staging_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/investigation.md Current Behavior
§5). Since the gap was caught and fixed before the ticket's single closing commit, the ticket's
*current* committed state has no live gap — this test reconstructs the pre-fix self-report moment
by using the real touched-docs set (from `git show`) against a declared-text excerpt that omits
the one real path the ticket's own prose confirms was originally missing, rather than fabricating
data.

M3's known-positive fixture is explicitly SYNTHETIC — see
tests/fixtures/agent_replay/pilot/m3_synthetic_known_positive.yaml's own header comment and
investigation.md Risks #1. It is never presented as equivalent to M2's real-historical instance.
"""
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.defect_detectors import (  # noqa: E402
    detect_m2_doc_update_gap,
    detect_m3_background_hang,
    extract_ticket_section,
)

_RACE_RELATIONS_TICKET_ID = "TCK-20260831-RACE-RELATIONS-MATRIX"
_RACE_RELATIONS_REAL_TOUCHED_DOCS = [
    "docs/content/content_semantics_contract.md",
    "docs/mechanics/02_combat_laws.md",
    "docs/mechanics/content_usage_matrix.md",
    "docs/parity_ledger/combat_movement.yaml",
    "docs/parity_ledger/social_narrative.yaml",
    "docs/parity_ledger/strategic_cognition.yaml",
    "docs/REGISTRY.yaml",
]

_M3_SYNTHETIC_FIXTURE_PATH = (
    _REPO_ROOT
    / "tests"
    / "fixtures"
    / "agent_replay"
    / "pilot"
    / "m3_synthetic_known_positive.yaml"
)


def _real_ticket_files_changed_and_related_docs_text() -> tuple:
    ticket_path = _REPO_ROOT / "tickets" / "done" / f"{_RACE_RELATIONS_TICKET_ID}.md"
    text = ticket_path.read_text(encoding="utf-8")
    return (
        extract_ticket_section(text, "Files Changed"),
        extract_ticket_section(text, "Related Docs"),
    )


def test_m2_doc_update_self_report_gap_detector_fires_on_known_positive():
    # Reconstructs the real pre-fix self-report state (see module docstring): the one real path
    # the ticket's own prose confirms was originally missing is deliberately omitted here.
    files_changed_text_pre_fix = (
        "- `docs/content/content_semantics_contract.md` — RelationProjectionService section "
        "updated.\n"
        "- `docs/mechanics/content_usage_matrix.md` — new table row.\n"
        "- `docs/parity_ledger/combat_movement.yaml` — new COMB-317 entry.\n"
        "- `docs/parity_ledger/strategic_cognition.yaml` — new STRAT-263 entry.\n"
        "- `docs/parity_ledger/social_narrative.yaml` — new SOC-257 entry.\n"
    )

    result = detect_m2_doc_update_gap(
        _RACE_RELATIONS_TICKET_ID,
        _RACE_RELATIONS_REAL_TOUCHED_DOCS,
        files_changed_text_pre_fix,
        "",
    )

    assert result.fired is True
    assert "docs/mechanics/02_combat_laws.md" in result.gap_paths
    # the mechanically-regenerated registry file must never itself count as a gap
    assert "docs/REGISTRY.yaml" not in result.gap_paths


def test_m2_detector_does_not_fire_on_clean_fixture():
    files_changed_text, related_docs_text = _real_ticket_files_changed_and_related_docs_text()

    result = detect_m2_doc_update_gap(
        _RACE_RELATIONS_TICKET_ID,
        _RACE_RELATIONS_REAL_TOUCHED_DOCS,
        files_changed_text,
        related_docs_text,
    )

    assert result.fired is False
    assert result.gap_paths == []


def test_m3_test_scoper_background_hang_detector_fires_on_known_positive():
    payload = yaml.safe_load(_M3_SYNTHETIC_FIXTURE_PATH.read_text(encoding="utf-8"))

    result = detect_m3_background_hang(payload)

    assert result.fired is True


def test_m3_detector_does_not_fire_on_clean_fixture():
    clean_payload = {"stop_hook_active": False, "agent_type": "test-scoper", "background_tasks": []}

    result = detect_m3_background_hang(clean_payload)

    assert result.fired is False
