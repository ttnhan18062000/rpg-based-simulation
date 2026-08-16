"""Doc-vs-fixture content-lock tests for the Knowledge Gateway MCP Phase 5 repeated-demand
measurement (TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT).

Mirrors `tests/docs/test_redaction_retention_policy_doc.py`'s static doc-structure-assertion
pattern: plain string containment against the doc file's own text, never runtime behavior.

Per this session's per-phase ownership convention, this ticket's own Implement step deliberately
does NOT edit `docs/plans/knowledge-gateway-mcp-proposal.md` (Document-Update's job) and does NOT
add the `INFRA-355` parity-ledger entry (Parity phase's job). Both tests below are therefore written
now, per plan.md's Step 5 spec, against the real current state of those two files as of Implement --
`test_infra_355_parity_entry_matches_committed_measurement_numbers` and the second half of
`test_phase5_proposal_doc_annotation_does_not_overclaim_done` (the narrative-paragraph-present
assertion) are expected to fail until Parity/Document-Update land their respective artifacts later
in this same ticket's pipeline. This is disclosed here rather than worked around by weakening the
assertions.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PROPOSAL_DOC_PATH = _REPO_ROOT / "docs" / "plans" / "knowledge-gateway-mcp-proposal.md"
_INFRASTRUCTURE_LEDGER_PATH = _REPO_ROOT / "docs" / "parity_ledger" / "infrastructure.yaml"
_RESULTS_FIXTURE_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase5_repeated_demand_measurement_results.json"
)

_THIS_TICKET_ID = "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"


def _load_infra_355_entry():
    data = yaml.safe_load(_INFRASTRUCTURE_LEDGER_PATH.read_text())
    entries = data["entries"] if isinstance(data, dict) else data
    for entry in entries:
        if entry.get("id") == "INFRA-355":
            return entry
    return None


def test_infra_355_parity_entry_matches_committed_measurement_numbers():
    entry = _load_infra_355_entry()
    assert entry is not None, (
        "INFRA-355 parity-ledger entry not found in docs/parity_ledger/infrastructure.yaml -- "
        "this ticket's Implement phase deliberately does not write it (Parity phase's job, per "
        "this session's per-phase ownership convention); this assertion is expected to start "
        "passing once Parity phase lands the entry"
    )

    fixture = json.loads(_RESULTS_FIXTURE_PATH.read_text())
    primary = fixture["primary"]
    secondary = fixture["secondary"]

    text = entry["text"]
    assert str(primary["conservative_repeated_pair_count"]) in text
    assert str(primary["total_tickets"]) in text
    assert str(secondary["conservative_repeated_pair_count"]) in text
    assert str(secondary["total_tickets"]) in text
    assert "5.8" in text
    assert "18.5" in text


def test_phase5_proposal_doc_annotation_does_not_overclaim_done():
    text = _PROPOSAL_DOC_PATH.read_text()

    overclaim_strings = [
        "Add canonical entity IDs and aliases. **Done",
        "Reuse results across compatible phrasings. **Done",
        "Add conservative semantic candidate matching with deterministic validation. **Done",
    ]
    for overclaim in overclaim_strings:
        assert overclaim not in text, (
            f"proposal doc must never mark this Phase 5 bullet Done -- nothing was built: "
            f"{overclaim!r}"
        )

    assert _THIS_TICKET_ID in text, (
        f"proposal doc's Phase 5 section must reference {_THIS_TICKET_ID} in a narrative "
        "paragraph recording this ticket's real measurement -- this ticket's own Implement phase "
        "deliberately does not add it (Document-Update's job, per this session's per-phase "
        "ownership convention); this assertion is expected to start passing once Document-Update "
        "lands the paragraph"
    )
