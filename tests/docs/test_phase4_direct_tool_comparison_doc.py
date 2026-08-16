"""Structural regression proof for the Knowledge Gateway MCP Phase 4 direct-tool comparison
results doc (TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON).

Mirrors `tests/docs/test_redaction_retention_policy_doc.py`'s static-markdown section/phrase-
assertion pattern.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DOC_PATH = (
    _REPO_ROOT
    / "docs"
    / "engine"
    / "contracts"
    / "knowledge_gateway_mcp"
    / "phase4_direct_tool_comparison.md"
)
_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase4_direct_tool_comparison_results.json"
)

_DOC_TEXT = _DOC_PATH.read_text()
_FIXTURE = json.loads(_FIXTURE_PATH.read_text())


def test_results_doc_states_no_gold_answer_limitation():
    lowered = _DOC_TEXT.lower()
    assert "no gold" in lowered or "no gold-answer" in lowered
    assert "reviewer_judgment" in _DOC_TEXT
    assert "source_completeness" in _DOC_TEXT
    assert "not resolved by inventing a rubric" in lowered or "never dressed up as a computed metric" in lowered


def test_results_doc_cites_real_fixture_and_states_pass_fail_per_query_type():
    assert "tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json" in _DOC_TEXT

    for entry in _FIXTURE["entries"]:
        assert entry["id"] in _DOC_TEXT, f"{entry['id']} is never cited in the results doc"
        assert entry["routing_shape"] in _DOC_TEXT, (
            f"{entry['routing_shape']} (routing shape for {entry['id']}) is never cited in the "
            "results doc"
        )

    for shape in _FIXTURE["by_routing_shape"]:
        assert shape in _DOC_TEXT


def test_results_doc_reports_every_entrys_real_verdict_honestly():
    for entry in _FIXTURE["entries"]:
        verdict = entry["quality"]["reviewer_judgment"]["verdict"]
        # The doc must at least mention the verdict literal somewhere for a fully-favorable-gateway
        # aggregate to be impossible to claim while a real disfavoring entry exists undisclosed.
        assert verdict in _DOC_TEXT or verdict.replace("_", " ") in _DOC_TEXT.lower()


def test_results_doc_discloses_the_q3_stale_routing_reasoning():
    assert "INFRA-351" in _DOC_TEXT
    assert "stale" in _DOC_TEXT.lower()
    assert "Q3_requirement_completeness" in _DOC_TEXT


def test_results_doc_discloses_graphify_half_closure_of_design_decision_d3():
    lowered = _DOC_TEXT.lower()
    assert "design decision d3" in lowered
    assert "graphify" in lowered
    assert "n/a" in lowered or '"na"' in lowered or "not-yet" in lowered or "3-phase-old" in lowered
