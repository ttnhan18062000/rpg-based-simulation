"""Tests for the Open Decision 8 resolution added to
docs/engine/contracts/context_packet_contract.md §6 (TCK-20260802-STORED-ARTIFACT-KIND).

Static, raw-source-text-parsing tests against the contract doc, following the same
Path.read_text()-only content-check technique tests/tools/test_context_kind_priority_decision.py
already uses (no stored_artifact-kind scanner logic exists anywhere in tools/ for this decision to
import against — this ticket is decision-document-only). A second guard verifies the four named
tools/ modules were not touched by this ticket, via a recorded content-hash fixture rather than a
git-diff-against-base-commit check, matching the sibling ticket's own rationale for that technique.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACT_PATH = _REPO_ROOT / "docs" / "engine" / "contracts" / "context_packet_contract.md"

# Recorded at the time this ticket authored §6 — TCK-20260802-STORED-ARTIFACT-KIND made zero
# changes to any of these files. This is a one-off scope guard for this ticket, not a durable
# invariant: a future ticket that intentionally changes one of these files should update (or
# remove) the corresponding constant, not treat a failure here as a regression to work around.
# This ticket's own named set differs from the sibling ticket's (`validate_frontmatter.py` swapped
# in for `parity_index.py`), per this ticket's own Out of Scope list.
#
# tools/generate_registry.py removed (TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP,
# 2026-08-17): this file has legitimately changed via unrelated later work since TCK-20260802-
# STORED-ARTIFACT-KIND's own Implementation start — confirmed via `git log` that TCK-20260802-
# STORED-ARTIFACT-KIND itself never touched it. This hash snapshot only ever validly reflected
# that ticket's own committed state at authoring time, not a permanent repo-wide ban. The
# remaining entries below still correctly protect the files that ticket's own diff actually left
# untouched.
#
# tools/validate_frontmatter.py ALSO removed (TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP,
# 2026-08-17): discovered stale beyond this ticket's own Investigate-phase pytest run, which only
# ever surfaced the tools/generate_registry.py mismatch above because this test's assert-in-a-loop
# stops at the first failing entry in dict iteration order (generate_registry.py was inserted
# before validate_frontmatter.py) — masking that validate_frontmatter.py had also drifted.
# Confirmed via `git log` that TCK-20260802-STORED-ARTIFACT-KIND never touched
# tools/validate_frontmatter.py either; its real last-touch commit (29d78798, 2026-08-14)
# postdates TCK-20260802-STORED-ARTIFACT-KIND's own Implementation start (2026-08-02).
_EXPECTED_TOOLS_HASHES = {
    "tools/context_packet_assembler.py": (
        "003565a6757a929b9560285364b0a6b58569acba783a806a4a56add1cd31fcde"
    ),
    "tools/hybrid_retrieval.py": (
        "da65a5d08c14fc562110786f84d810990b7ecf2d907b6661e00692633489b71e"
    ),
}


def _contract_text() -> str:
    return _CONTRACT_PATH.read_text()


def _section(text: str, start_heading: str, end_heading: str | None) -> str:
    start = text.index(start_heading)
    end = text.index(end_heading, start) if end_heading is not None else len(text)
    return text[start:end]


def _section_3_text(text: str) -> str:
    return _section(text, "## 3. Open Decision 3 Resolution", "## 4. Verification Path")


def _section_4_text(text: str) -> str:
    return _section(text, "## 4. Verification Path", "## 5. Open Decision 7 Resolution")


def _section_5_text(text: str) -> str:
    return _section(text, "## 5. Open Decision 7 Resolution", "## 6. Open Decision 8 Resolution")


def _section_6_text(text: str) -> str:
    return _section(text, "## 6. Open Decision 8 Resolution", None)


def _normalize_whitespace(text: str) -> str:
    without_blockquote_markers = re.sub(r"(?m)^>\s?", "", text)
    return re.sub(r"\s+", " ", without_blockquote_markers)


# ---------------------------------------------------------------------------
# Section presence and verbatim quote of Open Decision 8
# ---------------------------------------------------------------------------

def test_section_6_heading_exists_after_section_5():
    text = _contract_text()
    assert "## 6. Open Decision 8 Resolution" in text
    idx_5 = text.index("## 5. Open Decision 7 Resolution")
    idx_6 = text.index("## 6. Open Decision 8 Resolution")
    assert idx_6 > idx_5


def test_section_6_quotes_open_decision_8():
    section = _section_6_text(_contract_text())
    normalized = _normalize_whitespace(section)
    # The quoted phrase wraps across a markdown blockquote line break (with a
    # "> " continuation prefix in the middle), so the literal substring never
    # appears contiguously in the raw file text — normalize whitespace first.
    assert "become its own registry-indexed" in normalized
    assert "join_artifact_files" in section
    assert "staging_artifacts" in section
    assert "permanent design decision" in section


# ---------------------------------------------------------------------------
# AC1 — explicit yes/no verdict citing join_artifact_files()'s flat-list-only status quo
# ---------------------------------------------------------------------------

def test_decision_doc_states_yes_or_no_on_new_kind_and_cites_join_artifact_files():
    section = _section_6_text(_contract_text())
    assert "yes" in section.lower()
    assert "stored_artifact" in section
    assert "kind" in section
    assert "join_artifact_files" in section
    assert "generate_registry.py" in section


# ---------------------------------------------------------------------------
# AC2 — names exactly one of Decision 3's three branches with reasoning
# ---------------------------------------------------------------------------

def test_decision_doc_picks_one_of_decision_3s_three_branches_with_reasoning():
    section = _section_6_text(_contract_text())
    assert "Branch 1" in section
    assert "REGISTRY-backed direct mapping" in section
    assert "STATUS_VALUES" in section or "AUTHORITY_VALUES" in section
    assert "Branch 4" not in section
    assert "Branch 5" not in section


def test_decision_doc_confirms_last_verified_absent_from_artifact_frontmatter():
    section = _section_6_text(_contract_text())
    assert "no `last_verified` field" in section
    assert "_validate_artifact" in section


# ---------------------------------------------------------------------------
# AC3 — staging_artifacts/ exclusion is a reasoned, intentional-permanent-design paragraph
# ---------------------------------------------------------------------------

def test_decision_doc_contains_staging_artifacts_exclusion_paragraph():
    section = _section_6_text(_contract_text())
    assert "staging_artifacts" in section
    assert "intentional" in section
    assert "permanent design" in section


# ---------------------------------------------------------------------------
# Corpus-heterogeneity flagged as scope boundary, not resolved
# ---------------------------------------------------------------------------

def test_decision_doc_flags_corpus_heterogeneity_as_scope_boundary_not_resolved():
    section = _section_6_text(_contract_text())
    assert "index.md" in section
    assert "scope boundary" in section
    assert "does not resolve it" in section


# ---------------------------------------------------------------------------
# AC4 — §1-§5's existing text unchanged, no code changes to the named tools/ modules
# ---------------------------------------------------------------------------

def test_context_packet_contract_section_3_text_unchanged():
    text = _contract_text()
    section_3 = _section_3_text(text)
    assert "the packet must never imply" in section_3
    assert "defaulting to `P2`/`historical` as if that were a real registry read." in section_3
    assert "must never be silently" in section_3
    assert "coerced into REGISTRY's enum space." in section_3
    assert "superseded-by:<source_id of higher-ranked entry>" in section_3


def test_context_packet_contract_section_4_text_unchanged():
    text = _contract_text()
    section_4 = _section_4_text(text)
    assert "No code enforces this contract yet" in section_4
    assert "docs/parity_ledger/infrastructure.yaml" in section_4
    assert "INFRA-281 through INFRA-292" in section_4


def test_context_packet_contract_section_5_text_unchanged():
    text = _contract_text()
    section_5 = _section_5_text(text)
    assert "Human sign-off required" in section_5
    assert "No shared numeric scale" in section_5


def test_no_code_changes_to_named_tools_modules():
    for relative_path, expected_hash in _EXPECTED_TOOLS_HASHES.items():
        actual_hash = hashlib.sha256((_REPO_ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"{relative_path} content changed during a decision-document-only ticket "
            "(TCK-20260802-STORED-ARTIFACT-KIND); this ticket's scope forbids touching it"
        )
