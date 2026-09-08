"""Tests for the Knowledge Gateway MCP Phase 5 repeated-demand measurement
(TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT).

This ticket is measurement-only -- no gateway/cache/router source file is touched. The runner under
test (`tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`) is a pure
offline data-transform over two frozen snapshot fixtures
(`tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json`,
`tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json`) -- no gateway mocking is needed here,
unlike `test_kgmcp_phase4_direct_tool_comparison.py`'s live-gateway-calling runner.

The real, honest, reproduced result this ticket certifies: 17/521 conservative repeated-demand pairs
in the primary source (`agent-monitoring/events.jsonl` Investigate-phase summaries), 372/1411 in the
secondary source (`tickets/working_log.csv` title+summary) -- both independently re-verified during
Planning and re-reproduced fresh by this test suite against the frozen snapshots.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_TOOLS_DIR = _REPO_ROOT / "tools"

_RUNNER_MODULE_PATH = (
    _MONITORING_TOOLS_DIR / "kgmcp_phase5_repeated_demand_measurement_runner.py"
)
_RESULTS_FIXTURE_PATH = (
    _REPO_ROOT
    / "tests"
    / "tools"
    / "fixtures"
    / "kgmcp_phase5_repeated_demand_measurement_results.json"
)
_EVENTS_SNAPSHOT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase5_events_investigate_snapshot.json"
)
_WORKING_LOG_SNAPSHOT_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase5_working_log_snapshot.json"
)

_THIS_TICKET_ID = "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_phase5_repeated_demand_measurement_runner import (  # noqa: E402
    CAMEL_RE,
    PARITY_ID_RE,
    _CAMEL_MIN_LEN,
    classify_intent,
    extract_identifiers,
    run,
)

_RUNNER_SOURCE = _RUNNER_MODULE_PATH.read_text()
_RUNNER_AST = ast.parse(_RUNNER_SOURCE)
_RESULTS_FIXTURE = json.loads(_RESULTS_FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# 1. CamelCase regex false-positive discipline
# ---------------------------------------------------------------------------

def test_camel_regex_excludes_bare_acronyms_and_digit_joined_tokens():
    for false_positive in ("INFRA", "STRAT", "TOWN", "TCK", "E2E"):
        assert not CAMEL_RE.match(false_positive) or len(false_positive) < _CAMEL_MIN_LEN, (
            f"{false_positive!r} must not be extracted as a specific CamelCase symbol"
        )

    for real_symbol in ("EventRecorder", "ResourceNodeUpdate", "DecisionTraceIndex"):
        matches = CAMEL_RE.findall(real_symbol)
        assert matches and any(len(m) >= _CAMEL_MIN_LEN for m in matches), (
            f"{real_symbol!r} must be extracted as a specific CamelCase symbol"
        )


# ---------------------------------------------------------------------------
# 2. Parity-ID regex specificity
# ---------------------------------------------------------------------------

def test_parity_id_regex_extracts_specific_entries_not_bare_prefixes():
    for specific_id in ("INFRA-206", "STRAT-227", "TOWN-173"):
        assert PARITY_ID_RE.search(specific_id), f"{specific_id!r} must match PARITY_ID_RE"

    assert not PARITY_ID_RE.search("a bare INFRA with no trailing number"), (
        "a bare category prefix with no trailing -NNN must not match PARITY_ID_RE"
    )


# ---------------------------------------------------------------------------
# 3. Intent classifier — real data drawn from the frozen snapshot
# ---------------------------------------------------------------------------

def test_intent_classifier_buckets_known_summaries_correctly():
    events = json.loads(_EVENTS_SNAPSHOT_PATH.read_text())
    by_id = {e["run_id"]: e["summary"] for e in events}

    a_summary = by_id["TCK-20260619-E22C-REST-API"]
    b_summary = by_id["TCK-20260702-OBSISO-TRACE-ASYNC"]

    assert classify_intent(a_summary) == "mechanism_explanation"
    assert classify_intent(b_summary) == "mechanism_explanation"

    a_ids = extract_identifiers(a_summary)
    b_ids = extract_identifiers(b_summary)
    assert "DecisionTraceIndex" in a_ids["camel"]
    assert "DecisionTraceIndex" in b_ids["camel"]


# ---------------------------------------------------------------------------
# 4. Conservative-matching guarantee: tag-alone never counts
# ---------------------------------------------------------------------------

def test_repeated_pair_requires_same_intent_and_specific_identifier_not_tag_alone():
    from kgmcp_phase5_repeated_demand_measurement_runner import _build_records, _compare_records

    tag_only = [
        {"run_id": "A", "summary": "Confirmed the mcp gateway pipeline is working correctly."},
        {"run_id": "B", "summary": "Confirmed the mcp routing pipeline design in detail."},
    ]
    records = _build_records(tag_only, "run_id", lambda e: e["summary"])
    pairs, tag_only_count = _compare_records(records)
    assert pairs == []
    assert tag_only_count >= 1

    identifier_match = [
        {"run_id": "C", "summary": "Confirmed how EventRecorder flushes its buffer."},
        {"run_id": "D", "summary": "Confirmed EventRecorder's flush call chain in detail."},
    ]
    records2 = _build_records(identifier_match, "run_id", lambda e: e["summary"])
    pairs2, _ = _compare_records(records2)
    assert len(pairs2) == 1
    assert pairs2[0]["shared_identifiers"] == ["EventRecorder"]


# ---------------------------------------------------------------------------
# 5. Load-bearing reproducibility guarantee
# ---------------------------------------------------------------------------

def test_phase5_measurement_reproduces_committed_fixture_counts():
    fresh = run()

    assert fresh["primary"]["total_tickets"] == 521
    assert fresh["primary"]["conservative_repeated_pair_count"] == 17
    assert fresh["primary"]["distinct_tickets_in_repeated_pairs"] == 30

    assert fresh["secondary"]["total_tickets"] == 1411
    assert fresh["secondary"]["conservative_repeated_pair_count"] == 372
    assert fresh["secondary"]["distinct_tickets_in_repeated_pairs"] == 261

    committed_primary = _RESULTS_FIXTURE["primary"]
    committed_secondary = _RESULTS_FIXTURE["secondary"]
    assert fresh["primary"]["total_tickets"] == committed_primary["total_tickets"]
    assert (
        fresh["primary"]["conservative_repeated_pair_count"]
        == committed_primary["conservative_repeated_pair_count"]
    )
    assert (
        fresh["primary"]["distinct_tickets_in_repeated_pairs"]
        == committed_primary["distinct_tickets_in_repeated_pairs"]
    )
    assert fresh["secondary"]["total_tickets"] == committed_secondary["total_tickets"]
    assert (
        fresh["secondary"]["conservative_repeated_pair_count"]
        == committed_secondary["conservative_repeated_pair_count"]
    )
    assert (
        fresh["secondary"]["distinct_tickets_in_repeated_pairs"]
        == committed_secondary["distinct_tickets_in_repeated_pairs"]
    )


# ---------------------------------------------------------------------------
# 6. Self-contamination guard (Architecture Review 1st pass, required)
# ---------------------------------------------------------------------------

def test_events_snapshot_excludes_this_tickets_own_run_id():
    events = json.loads(_EVENTS_SNAPSHOT_PATH.read_text())
    assert len(events) == 521
    assert all(e["run_id"] != _THIS_TICKET_ID for e in events), (
        "the frozen events.jsonl snapshot must never contain this ticket's own run_id -- "
        "including it would self-taint the exact dataset this ticket measures"
    )


# ---------------------------------------------------------------------------
# 7. Qualitative-reading grounding (Test phase gap-check, required)
# ---------------------------------------------------------------------------

def test_qualitative_reading_examples_are_real_committed_pairs():
    """`docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md`'s
    "Qualitative reading" section makes a claim -- "the large majority are not the same question
    asked twice... natural, incremental, sequential investigation" -- and grounds it in two named
    pair examples: the ResourceNodeUpdate incremental-investigation pair
    (TCK-20260619-E21B-REGEN-SERVICE / TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION) and the
    COMMUNITY-SKILL-SWAP same-day genuine-recurrence pair. This mirrors the exact gap class Test
    phase found and closed on the Phase 4 Direct-Tool-Comparison ticket: a "false positive" claim
    that turned out to be prose-only, with no test backing. This test pins both citations against
    the actual committed primary-pairs fixture, so a future fixture regeneration that silently
    drops either example (e.g. a regex/intent-classifier change) fails this test instead of leaving
    the doc's qualitative claim unverified.
    """
    primary_pairs = _RESULTS_FIXTURE["primary"]["pairs"]

    def _pair_present(id_a: str, id_b: str, shared_identifier: str) -> bool:
        for p in primary_pairs:
            if {p["a"], p["b"]} == {id_a, id_b} and shared_identifier in p["shared_identifiers"]:
                return True
        return False

    assert _pair_present(
        "TCK-20260619-E21B-REGEN-SERVICE",
        "TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION",
        "ResourceNodeUpdate",
    ), (
        "the doc's incremental-investigation example must be a real committed conservative pair, "
        "not a prose-only illustration"
    )

    assert _pair_present(
        "TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED",
        "TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED",
        "WebSearch",
    ), (
        "the doc's same-question-recurrence example must be a real committed conservative pair, "
        "not a prose-only illustration"
    )


# ---------------------------------------------------------------------------
# Anti-drift guards
# ---------------------------------------------------------------------------

def test_candidate_tags_from_text_is_imported_not_reimplemented():
    imported_from_registry_query = set()
    for node in ast.walk(_RUNNER_AST):
        if isinstance(node, ast.ImportFrom) and node.module == "registry_query":
            imported_from_registry_query |= {alias.name for alias in node.names}
    assert "candidate_tags_from_text" in imported_from_registry_query

    defined_names = {
        node.name for node in ast.walk(_RUNNER_AST) if isinstance(node, ast.FunctionDef)
    }
    assert "candidate_tags_from_text" not in defined_names


def test_runner_reads_frozen_snapshot_paths_not_live_source_files():
    """Guards against a future edit reverting the live-file -> frozen-snapshot swap. Inspects only
    the two loader functions' own source (not the module's prose docstring, which legitimately
    names the live files it explicitly does NOT read) for any literal live-path string, and
    confirms both loaders' bodies reference the frozen snapshot path constants instead."""
    assert "kgmcp_phase5_events_investigate_snapshot.json" in _RUNNER_SOURCE
    assert "kgmcp_phase5_working_log_snapshot.json" in _RUNNER_SOURCE

    loader_names = {"load_investigate_events", "load_working_log_rows"}
    loader_nodes = {
        node.name: node
        for node in ast.walk(_RUNNER_AST)
        if isinstance(node, ast.FunctionDef) and node.name in loader_names
    }
    assert set(loader_nodes) == loader_names

    def _non_docstring_body_source(func_node: ast.FunctionDef) -> str:
        body = func_node.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]  # drop the docstring statement, which legitimately names the live
            # file it explicitly does NOT read
        return "\n".join(ast.get_source_segment(_RUNNER_SOURCE, stmt) for stmt in body)

    loader_bodies = {name: _non_docstring_body_source(node) for name, node in loader_nodes.items()}

    for name, src in loader_bodies.items():
        assert "agent-monitoring/events.jsonl" not in src, f"{name} must not open the live events.jsonl"
        assert "tickets/working_log.csv" not in src, f"{name} must not open the live working_log.csv"

    assert "_EVENTS_SNAPSHOT_PATH" in loader_bodies["load_investigate_events"]
    assert "_WORKING_LOG_SNAPSHOT_PATH" in loader_bodies["load_working_log_rows"]

    events = json.loads(_EVENTS_SNAPSHOT_PATH.read_text())
    working_log_rows = json.loads(_WORKING_LOG_SNAPSHOT_PATH.read_text())
    assert len(events) == 521
    assert len(working_log_rows) == 1411


def test_tag_only_pairs_never_merged_into_conservative_count():
    primary = _RESULTS_FIXTURE["primary"]
    secondary = _RESULTS_FIXTURE["secondary"]
    assert primary["tag_only_pair_count"] == 427
    assert secondary["tag_only_pair_count"] == 10347
    assert primary["conservative_repeated_pair_count"] == 17
    assert secondary["conservative_repeated_pair_count"] == 372
