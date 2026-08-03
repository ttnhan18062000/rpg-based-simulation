"""Tests for the Open Decision 9 resolution added to
docs/engine/contracts/context_packet_contract.md §7 (TCK-20260802-EXACT-LOOKUP-CONVENTION).

Static, raw-source-text-parsing tests against the contract doc, following the same
Path.read_text()-only content-check technique
tests/tools/test_context_kind_priority_decision.py and
tests/tools/test_stored_artifact_kind_decision.py already use (no exact-lookup-convention
scanner/module exists anywhere in tools/ for this decision to import against — this ticket is
decision-document-only). A second guard verifies the four named tools/ modules were not touched
by this ticket, via a recorded content-hash fixture rather than a git-diff-against-base-commit
check, matching both sibling tickets' own rationale for that technique.

The resolved verdict for Decision 9 is "no" (stay parity-specific, see §7's "Core resolution —
no." line and this ticket's plan.md "Decisions Made During Human Review" section) — so the
"if yes" applicability-criteria test below is expected to find no Branch-A content and skip,
while the "if no" parity-specific-rationale test exercises its main assertion and must pass.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACT_PATH = _REPO_ROOT / "docs" / "engine" / "contracts" / "context_packet_contract.md"
_EPIC_TICKET_PATH = (
    _REPO_ROOT / "tickets" / "inprogress" / "TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md"
)

# Recorded at the time this ticket authored §7 — TCK-20260802-EXACT-LOOKUP-CONVENTION made zero
# changes to any of these files. This is a one-off scope guard for this ticket, not a durable
# invariant: a future ticket that intentionally changes one of these files should update (or
# remove) the corresponding constant, not treat a failure here as a regression to work around.
_EXPECTED_TOOLS_HASHES = {
    "tools/parity_index.py": (
        "84c9b064d5cf4201803254d159434fefe8d7ae5fde034eeab7760e9715b42bae"
    ),
    "tools/hybrid_retrieval.py": (
        "da65a5d08c14fc562110786f84d810990b7ecf2d907b6661e00692633489b71e"
    ),
    "tools/context_packet_assembler.py": (
        "003565a6757a929b9560285364b0a6b58569acba783a806a4a56add1cd31fcde"
    ),
    "tools/generate_registry.py": (
        "28125dfedc5b81d936b1f3ccf3f0e6743675256420f0803be5460c927461ee6a"
    ),
}


def _contract_text() -> str:
    return _CONTRACT_PATH.read_text()


def _epic_ticket_text() -> str:
    return _EPIC_TICKET_PATH.read_text()


def _section(text: str, start_heading: str, end_heading: str | None) -> str:
    start = text.index(start_heading)
    end = text.index(end_heading, start) if end_heading is not None else len(text)
    return text[start:end]


def _section_3_text(text: str) -> str:
    return _section(text, "## 3. Open Decision 3 Resolution", "## 4. Verification Path")


def _section_5_text(text: str) -> str:
    return _section(text, "## 5. Open Decision 7 Resolution", "## 6. Open Decision 8 Resolution")


def _section_6_text(text: str) -> str:
    return _section(text, "## 6. Open Decision 8 Resolution", "## 7. Open Decision 9 Resolution")


def _section_7_text(text: str) -> str:
    return _section(text, "## 7. Open Decision 9 Resolution", None)


def _normalize_whitespace(text: str) -> str:
    without_blockquote_markers = re.sub(r"(?m)^>\s?", "", text)
    return re.sub(r"\s+", " ", without_blockquote_markers)


# ---------------------------------------------------------------------------
# Section presence and verbatim quote of Open Decision 9
# ---------------------------------------------------------------------------

def test_section_7_appears_after_section_6():
    text = _contract_text()
    assert "## 7. Open Decision 9 Resolution" in text
    idx_6 = text.index("## 6. Open Decision 8 Resolution")
    idx_7 = text.index("## 7. Open Decision 9 Resolution")
    assert idx_7 > idx_6


def test_section_7_quotes_open_decision_9_verbatim():
    section = _section_7_text(_contract_text())
    normalized = _normalize_whitespace(section)
    assert "exact-structural-lookup query" in normalized
    assert "never similarity-ranked, always" in normalized
    assert "gate-safe" in normalized
    assert "explicitly distinct from the fuzzy RRF-fused" in normalized
    assert "general project convention" in normalized
    assert "implicit, parity-specific pattern" in normalized


# ---------------------------------------------------------------------------
# AC1 — explicit yes/no verdict on the exact-vs-fuzzy convention
# ---------------------------------------------------------------------------

def test_section_7_states_explicit_yes_or_no_verdict():
    section = _section_7_text(_contract_text())
    assert "Core resolution" in section
    assert "no" in section.lower()


def test_section_7_cites_real_precedent_by_function_name():
    section = _section_7_text(_contract_text())
    assert "entry()" in section
    assert "impact()" in section
    assert "health()" in section
    assert "tools/parity_index.py" in section
    assert "reciprocal_rank_fusion" in section
    assert "hybrid_fuse_and_filter" in section
    assert "tools/hybrid_retrieval.py" in section


# ---------------------------------------------------------------------------
# AC2 — if yes, applicability criteria section (not applicable under the "no" verdict)
# ---------------------------------------------------------------------------

def test_section_7_applicability_criteria_present_if_yes_verdict():
    section = _section_7_text(_contract_text())
    if "### Applicability Criteria" not in section:
        pytest.skip(
            "Resolved verdict is 'no' (stay parity-specific) — no Branch-A "
            "'### Applicability Criteria' heading exists, per plan.md's Acceptance "
            "Criteria Map (AC2 satisfied-as-inapplicable)."
        )
    assert "### Applicability Criteria" in section


# ---------------------------------------------------------------------------
# AC3 — if no, explicit parity-specific rationale pending a second real use case
# ---------------------------------------------------------------------------

def test_section_7_states_parity_specific_rationale_if_no_verdict():
    section = _section_7_text(_contract_text())
    assert "Core resolution — no." in section
    assert "### Applicability Criteria" not in section
    assert "n=1" in section or "sample size of one" in section
    assert "second" in section.lower()
    assert "rule-of-three" in section
    assert "parity-domain retrieval quality" in section
    assert "generalizability" in section or "generalize" in section
    assert "docs/ai/parity_readpath_gate_a_decision.md" in section


# ---------------------------------------------------------------------------
# AC4 — plain human-sign-off statement for the genuine value judgment
# ---------------------------------------------------------------------------

def test_section_7_flags_human_sign_off_if_value_judgment():
    section = _section_7_text(_contract_text())
    assert "human sign-off" in section
    assert "value judgment" in section


# ---------------------------------------------------------------------------
# Generalizable properties documented as a citable, non-mandatory reference
# ---------------------------------------------------------------------------

def test_section_7_documents_generalizable_properties_as_non_mandatory_reference():
    section = _section_7_text(_contract_text())
    assert "### Applicability Criteria" not in section
    assert "non-mandatory" in section
    assert "Read-only access" in section or "read-only" in section.lower()
    assert "Exact equality" in section or "exact equality" in section.lower()
    assert "Deterministic sort" in section or "deterministic sort" in section.lower()
    assert "no-match response" in section
    assert "Zero mutation surface" in section or "zero mutation surface" in section.lower()


def test_section_7_states_reopening_condition():
    section = _section_7_text(_contract_text())
    assert "Reopening condition" in section
    assert "second real" in section
    assert "gate-safe exact lookup" in section


# ---------------------------------------------------------------------------
# §1-§6 untouched by the §7 append
# ---------------------------------------------------------------------------

def test_context_packet_contract_section_3_text_unchanged():
    text = _contract_text()
    section_3 = _section_3_text(text)
    assert "the packet must never imply" in section_3
    assert "defaulting to `P2`/`historical` as if that were a real registry read." in section_3
    assert "must never be silently" in section_3
    assert "coerced into REGISTRY's enum space." in section_3
    assert "superseded-by:<source_id of higher-ranked entry>" in section_3


def test_context_packet_contract_section_5_text_unchanged():
    text = _contract_text()
    section_5 = _section_5_text(text)
    assert "Human sign-off required" in section_5
    assert "No shared numeric scale" in section_5


def test_context_packet_contract_section_6_text_unchanged():
    text = _contract_text()
    section_6 = _section_6_text(text)
    assert "become its own" in _normalize_whitespace(section_6)
    assert "registry-indexed" in _normalize_whitespace(section_6)
    assert "join_artifact_files" in section_6
    assert "staging_artifacts" in section_6
    assert "permanent design decision" in section_6


def test_no_code_changes_to_named_tools_modules():
    for relative_path, expected_hash in _EXPECTED_TOOLS_HASHES.items():
        actual_hash = hashlib.sha256((_REPO_ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"{relative_path} content changed during a decision-document-only ticket "
            "(TCK-20260802-EXACT-LOOKUP-CONVENTION); this ticket's scope forbids touching it"
        )


# ---------------------------------------------------------------------------
# Epic ticket's OPEN DECISION 9 entry marked RESOLVED
# ---------------------------------------------------------------------------

def test_epic_ticket_decision_9_marked_resolved():
    text = _epic_ticket_text()
    idx_9 = text.index("OPEN DECISION 9")
    idx_end = text.index("## Implementation Notes", idx_9)
    decision_9_block = text[idx_9:idx_end]
    assert "**RESOLVED**" in decision_9_block
    assert "**UNRESOLVED**" not in decision_9_block
    assert "TCK-20260802-EXACT-LOOKUP-CONVENTION" in decision_9_block
    assert "context_packet_contract.md` §7" in decision_9_block

    for n in range(1, 9):
        idx_n = text.index(f"OPEN DECISION {n} ")
        idx_n_end = text.index("- OPEN DECISION", idx_n + 1)
        decision_n_block = text[idx_n:idx_n_end]
        assert "**RESOLVED**" in decision_n_block
