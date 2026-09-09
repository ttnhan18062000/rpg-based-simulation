"""Doc-structure tests for the subsystem ownership & lifecycle doc
(TCK-20260904-OWNERSHIP-LIFECYCLE-DOC).

This is the M3 deliverable of `telemetry_retention_epic.md`: the canonical table recording an
accountable role, update trigger, staleness signal, and removal condition for every
governance-relevant subsystem the AI-First Hardening epics touch. These tests assert doc
*structure* (required headings, required table columns, required phrases present as distinct,
individually matchable text) — never runtime behavior — mirroring the static-assertion pattern
`tests/docs/test_artifact_retention_classification_doc.py` uses.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_DOC = _REPO_ROOT / "docs" / "guidelines" / "subsystem_ownership_lifecycle.md"
_TELEMETRY_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "telemetry_retention_epic.md"
)
_GOVERNANCE_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "governance_capability_policy_epic.md"
)
_WORKFLOW_EPIC = (
    _REPO_ROOT / "docs" / "plans" / "agent_infrastructure" / "ai_first_hardening_epics"
    / "workflow_reliability_epic.md"
)
_ARTIFACT_RETENTION_DOC = (
    _REPO_ROOT / "docs" / "guidelines" / "artifact_retention_classification.md"
)

_REQUIRED_COLUMNS = [
    "Subsystem",
    "Accountable role",
    "Update trigger",
    "Staleness signal",
    "Removal condition",
]

_ROLE_VOCABULARY = [
    "Agent Configuration Maintainer",
    "Workflow Runtime Maintainer",
    "Documentation Governance Maintainer",
]

_BATCH_SUBSYSTEM_EVIDENCE = {
    "bash secret-scan hook": "TCK-20260904-BASH-SECRET-SCAN-HOOK",
    "tools frontmatter rollout": "TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE",
    "AST import-boundary enforcement": "TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC",
    "doc-coverage reverse-check": "TCK-20260904-DOC-COVERAGE-REVERSE-CHECK",
    "test-scoper hang guard": "TCK-20260904-TEST-SCOPER-HANG-GUARD",
}

_ARTIFACT_CLASS_STRINGS = [
    "agent-monitoring/data/",
    "stored_artifacts/",
    "tickets/done/",
    "retro/RETRO-*.md",
    "working_log.csv",
    "graphify-out/",
    "knowledge-index/",
    ".claude/current_run",
]


def _read(path: Path) -> str:
    return path.read_text()


def _table_rows(text: str) -> list[str]:
    """Return every markdown table-row line (starts with '| ') in the Ownership & Lifecycle Table."""
    start = text.index("## Ownership & Lifecycle Table")
    end = text.index("## Excluded Subsystems")
    section = text[start:end]
    return [line for line in section.splitlines() if line.strip().startswith("|")]


def test_subsystem_ownership_lifecycle_doc_exists_and_has_five_columns():
    assert _DOC.exists(), f"missing required doc: {_DOC}"
    text = _read(_DOC)
    rows = _table_rows(text)
    header = rows[0]
    for column in _REQUIRED_COLUMNS:
        assert column in header, f"table header missing column: {column}"


def test_subsystem_ownership_lifecycle_doc_covers_both_drafted_rows():
    text = _read(_DOC)
    rows = _table_rows(text)
    data_rows = rows[2:]  # skip header + separator

    capability_row = next(
        (r for r in data_rows if "Capability-envelope baseline" in r), None
    )
    assert capability_row is not None, "missing Capability-envelope baseline row"
    assert "Agent Configuration Maintainer" in capability_row
    cells = [c.strip() for c in capability_row.strip().strip("|").split("|")]
    assert len(cells) == 5 and all(cells), "capability-envelope row must have 5 non-empty cells"

    ticket_row = next(
        (r for r in data_rows if "Ticket-claim detection log" in r), None
    )
    assert ticket_row is not None, "missing Ticket-claim detection log row"
    assert "Workflow Runtime Maintainer" in ticket_row
    cells = [c.strip() for c in ticket_row.strip().strip("|").split("|")]
    assert len(cells) == 5 and all(cells), "ticket-claim row must have 5 non-empty cells"


def test_subsystem_ownership_lifecycle_doc_documents_each_batch_subsystem_or_justified_exclusion():
    text = _read(_DOC)
    for _label, ticket_id in _BATCH_SUBSYSTEM_EVIDENCE.items():
        assert ticket_id in text, f"missing evidence token for batch subsystem: {ticket_id}"


def test_subsystem_ownership_lifecycle_doc_defines_role_vocabulary():
    text = _read(_DOC)
    assert "## Accountable Role Vocabulary" in text
    vocab_start = text.index("## Accountable Role Vocabulary")
    vocab_end = text.index("## Ownership & Lifecycle Table")
    vocab_section = text[vocab_start:vocab_end]

    rows = _table_rows(text)
    data_rows = rows[2:]
    used_roles = set()
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) == 5:
            used_roles.add(cells[1])

    for role in used_roles:
        assert role in vocab_section, f"role used in table but not defined in vocabulary: {role}"


def test_accountable_role_column_never_names_a_person():
    text = _read(_DOC)
    rows = _table_rows(text)
    data_rows = rows[2:]
    for row in data_rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) == 5:
            assert cells[1] in _ROLE_VOCABULARY, (
                f"Accountable role cell is not a declared vocabulary role: {cells[1]!r}"
            )


def test_bash_secret_scan_hook_has_real_shipped_row():
    """TCK-20260904-BASH-SECRET-SCAN-HOOK shipped for real (PR #149) — the hook is live in
    .claude/settings.json's PreToolUse array, reusing tools/write_path_guard.py::scan_for_secrets().
    This subsystem is no longer speculative/pre-ship, so its table row must NOT be marked
    "BLOCKED"/"not yet built" (the opposite of the pre-ship expectation this test originally
    encoded), and it must no longer appear in "## Excluded Subsystems" — it has a real ownership
    row instead. This test's own name/body were updated by
    TCK-20260908-HOTFIX-OWNERSHIP-LIFECYCLE-DOC-STALE-PRESHIP-GUARD once the hook actually shipped.
    """
    text = _read(_DOC)
    rows = _table_rows(text)
    data_rows = rows[2:]
    matching_rows = [
        r for r in data_rows if re.search(r"secret[- ]scan|secret-exposure", r, re.I)
    ]
    assert matching_rows, "bash secret-scan hook must have a real ownership-table row now that it has shipped"
    for row in matching_rows:
        assert "BLOCKED" not in row and "not yet built" not in row, (
            "bash secret-scan hook has shipped — its row must no longer read as speculative/pre-ship"
        )
        assert "TCK-20260904-BASH-SECRET-SCAN-HOOK" in row, (
            "shipped row must cite the shipping ticket for traceability"
        )
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        assert len(cells) == 5 and all(cells), "shipped row must have 5 non-empty cells like every other row"
        assert cells[1] in _ROLE_VOCABULARY, (
            f"shipped row's accountable role must be a declared vocabulary role: {cells[1]!r}"
        )

    exclusions_start = text.index("## Excluded Subsystems")
    exclusions_end = text.index("## Related Docs")
    exclusions_section = text[exclusions_start:exclusions_end]
    assert "TCK-20260904-BASH-SECRET-SCAN-HOOK" not in exclusions_section, (
        "bash secret-scan hook has shipped and has a real ownership row — "
        "it must no longer be listed as an excluded/blocked subsystem"
    )


def test_telemetry_retention_epic_no_longer_cites_roadmap_role_vocabulary():
    text = _read(_TELEMETRY_EPIC)
    assert "roadmap's shared role vocabulary" not in text.lower()
    m3_start = text.index("### M3")
    assert "docs/guidelines/subsystem_ownership_lifecycle.md" in text[m3_start:]


def test_draft_m3_table_marked_historical_not_edited_in_place():
    text = _read(_TELEMETRY_EPIC)
    assert (
        "| Subsystem | Accountable role | Update trigger | Staleness signal |" in text
    ), "original 4-column M3 draft table header must remain textually intact"
    assert (
        "Capability-envelope baseline (from `governance_capability_policy_epic.md`) | "
        "Agent Configuration Maintainer | Any new legitimate permission need | "
        "Baseline diverges from a working local file |" in text
    ), "original capability-envelope draft row must remain textually intact"
    assert (
        "Ticket-claim detection log (from `workflow_reliability_epic.md`) | "
        "Workflow Runtime Maintainer | Continuous | Zero incidents after 30 days |" in text
    ), "original ticket-claim draft row must remain textually intact"
    assert "M3 is shipped" in text, "must add a shipped/historical marker note"


def test_sibling_epic_docs_link_to_canonical_ownership_doc():
    for path in (_GOVERNANCE_EPIC, _WORKFLOW_EPIC):
        text = _read(path)
        assert "docs/guidelines/subsystem_ownership_lifecycle.md" in text, (
            f"{path} does not link to the canonical ownership doc"
        )


def test_three_existing_ownership_docs_unmodified():
    for rel_path in (
        "docs/testing/content_migration_test_ownership.md",
        "docs/simulation/domains/domain_ownership_map.md",
        "docs/architecture/cognition_domain_ownership.md",
    ):
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", rel_path],
            cwd=_REPO_ROOT,
            capture_output=True,
        )
        assert result.returncode == 0, f"{rel_path} was modified by this ticket but must not be"


def test_artifact_retention_classification_row_count_unchanged():
    text = _read(_ARTIFACT_RETENTION_DOC)
    for artifact_class in _ARTIFACT_CLASS_STRINGS:
        assert artifact_class in text, f"missing pre-existing artifact class: {artifact_class}"
    start = text.index("## Retention Classification Table")
    body = text[start:]
    row_lines = [
        line for line in body.splitlines()
        if line.strip().startswith("|") and "---" not in line
    ]
    data_rows = row_lines[1:]  # drop header
    assert len(data_rows) == 8, (
        f"expected exactly 8 artifact-class rows, found {len(data_rows)} — "
        "this ticket must not add/remove rows in this file"
    )
