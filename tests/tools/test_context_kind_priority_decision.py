"""Tests for the Open Decision 7 resolution added to
docs/engine/contracts/context_packet_contract.md §5 (TCK-20260802-CONTEXT-KIND-PRIORITY).

Static, raw-source-text-parsing tests against the contract doc, following the same
Path.read_text()-only content-check technique tests/tools/test_shadow_packet_call_site.py already
uses (no ranking/selection logic exists anywhere in tools/ for this decision to import against —
this ticket is decision-document-only). A second guard verifies the four named tools/ modules
were not touched by this ticket, via a recorded content-hash fixture rather than a git-diff-
against-base-commit check, since the working tree carries unrelated concurrent changes that make
a single stable base commit impractical to pin here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACT_PATH = _REPO_ROOT / "docs" / "engine" / "contracts" / "context_packet_contract.md"

# Recorded at the time this ticket authored §5 — TCK-20260802-CONTEXT-KIND-PRIORITY made zero
# changes to any of these files. This is a one-off scope guard for this ticket, not a durable
# invariant: a future ticket that intentionally changes one of these files should update (or
# remove) the corresponding constant, not treat a failure here as a regression to work around.
_EXPECTED_TOOLS_HASHES = {
    "tools/context_packet_assembler.py": (
        "003565a6757a929b9560285364b0a6b58569acba783a806a4a56add1cd31fcde"
    ),
    "tools/hybrid_retrieval.py": (
        "da65a5d08c14fc562110786f84d810990b7ecf2d907b6661e00692633489b71e"
    ),
    "tools/parity_index.py": (
        "84c9b064d5cf4201803254d159434fefe8d7ae5fde034eeab7760e9715b42bae"
    ),
    "tools/generate_registry.py": (
        "28125dfedc5b81d936b1f3ccf3f0e6743675256420f0803be5460c927461ee6a"
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
    return _section(text, "## 5. Open Decision 7 Resolution", None)


# ---------------------------------------------------------------------------
# Section presence and verbatim quote of Open Decision 7
# ---------------------------------------------------------------------------

def test_section_5_heading_exists_after_section_4():
    text = _contract_text()
    assert "## 5. Open Decision 7 Resolution" in text
    idx_4 = text.index("## 4. Verification Path")
    idx_5 = text.index("## 5. Open Decision 7 Resolution")
    assert idx_5 > idx_4


def test_section_5_quotes_open_decision_7():
    section = _section_5_text(_contract_text())
    assert "how competing candidates of" in section
    assert "*different* `kind`s are ranked or chosen" in section
    assert "What cross-kind candidate-selection/ranking policy" in section
    assert "applies?" in section


# ---------------------------------------------------------------------------
# AC1 — cites _resolve_subject_conflicts() same-kind precedent and generalization verdict
# ---------------------------------------------------------------------------

def test_decision_doc_cites_resolve_subject_conflicts_precedent():
    section = _section_5_text(_contract_text())
    assert "_resolve_subject_conflicts" in section
    assert "subject_key" in section
    assert "freshness" in section
    assert (
        "structurally" in section
        or "does not generalize" in section
        or "same-kind" in section
    )


# ---------------------------------------------------------------------------
# AC2 — explicit position on both named concrete examples
# ---------------------------------------------------------------------------

def test_decision_doc_addresses_unrated_code_symbol_vs_p1_doc_example():
    section = _section_5_text(_contract_text())
    assert "code_symbol" in section
    assert "P1" in section
    assert "human sign-off" in section or "deferred" in section


def test_decision_doc_addresses_p0_parity_entry_inclusion_floor():
    section = _section_5_text(_contract_text())
    assert "parity_ledger_entry" in section
    assert "P0" in section
    assert "inclusion" in section or "floor" in section


# ---------------------------------------------------------------------------
# AC3 — plain human-sign-off statement for the residual value judgment
# ---------------------------------------------------------------------------

def test_decision_doc_states_human_signoff_needed_if_value_judgment():
    section = _section_5_text(_contract_text())
    assert "human sign-off" in section
    assert "value judgment" in section


# ---------------------------------------------------------------------------
# AC4 — §3/§4 untouched, no code changes to the named tools/ modules
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


def test_no_code_changes_to_named_tools_modules():
    for relative_path, expected_hash in _EXPECTED_TOOLS_HASHES.items():
        actual_hash = hashlib.sha256((_REPO_ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, (
            f"{relative_path} content changed during a decision-document-only ticket "
            "(TCK-20260802-CONTEXT-KIND-PRIORITY); this ticket's scope forbids touching it"
        )
