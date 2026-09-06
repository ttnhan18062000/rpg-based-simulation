"""Doc-structure tests for the artifact retention classification doc
(TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION).

This is the M2 deliverable of `telemetry_retention_epic.md`: a committed doc classifying every
repo artifact class outside the already-resolved `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`
weekly shards. These tests assert doc *structure* (required section headings, required phrases
present as distinct, individually matchable text) — never runtime behavior — mirroring the
static-assertion pattern `tests/docs/test_redaction_retention_policy_doc.py` uses for the
Knowledge Gateway MCP redaction/retention policy doc.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_DOC = _REPO_ROOT / "docs" / "guidelines" / "artifact_retention_classification.md"

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

_TAXONOMY_CATEGORIES = [
    "Ephemeral",
    "Run-scoped",
    "Ticket-scoped",
    "Long-lived",
]


def _read_doc() -> str:
    return _DOC.read_text()


def test_artifact_retention_classification_doc_exists_and_has_required_sections():
    assert _DOC.exists(), f"missing required doc: {_DOC}"
    text = _read_doc()

    for artifact_class in _ARTIFACT_CLASS_STRINGS:
        assert artifact_class in text, f"missing artifact class: {artifact_class}"

    for category in _TAXONOMY_CATEGORIES:
        assert category in text, f"missing taxonomy category: {category}"


def test_artifact_retention_classification_doc_resolves_both_open_questions():
    text = _read_doc()

    graphify_start = text.index("### `graphify-out/` resolution")
    knowledge_index_start = text.index("### `knowledge-index/` resolution")
    related_docs_start = text.index("## Related Docs")

    graphify_section = text[graphify_start:knowledge_index_start]
    knowledge_index_section = text[knowledge_index_start:related_docs_start]

    graphify_evidence_tokens = [".gitignore:260", ".gitignore:261", "zero"]
    assert any(token in graphify_section for token in graphify_evidence_tokens), (
        "graphify-out/ resolution section is missing concrete evidence tokens"
    )
    assert "open question" not in graphify_section.lower(), (
        "graphify-out/ resolution section must not read as a still-open question"
    )

    knowledge_index_evidence_tokens = [".gitignore:264", "Makefile:331"]
    assert any(token in knowledge_index_section for token in knowledge_index_evidence_tokens), (
        "knowledge-index/ resolution section is missing concrete evidence tokens"
    )
    assert "open question" not in knowledge_index_section.lower(), (
        "knowledge-index/ resolution section must not read as a still-open question"
    )


def test_working_log_csv_row_references_parser_ticket_by_id_only():
    text = _read_doc()

    ticket_id = "TCK-20260904-WORKING-LOG-CSV-PARSER"
    assert ticket_id in text, f"missing reference to {ticket_id}"

    idx = text.index(ticket_id)
    window = text[max(0, idx - 200): idx + len(ticket_id) + 200].lower()
    assert "blocked on" not in window, "working_log.csv row must not use gating language"
    assert "gated on" not in window, "working_log.csv row must not use gating language"
