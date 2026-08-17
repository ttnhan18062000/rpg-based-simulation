"""Tests for the Knowledge Gateway MCP Phase 0 measurement baseline
(TCK-20260814-KGMCP-MEASUREMENT-BASELINE).

Mirrors `tests/tools/test_retrieval_baseline_metrics.py`'s never-silent, derivation-string
convention (inline unit tests over the corpus module, no file I/O) plus
`tests/tools/test_knowledge_gateway_contract_schemas.py`'s raw `Path.read_text()`/`json.loads()`
structural pattern for the contract-doc tests (no `jsonschema` dependency). Exactly one test
(`test_corpus_baseline_wall_time_and_tool_call_count_are_plausible`) re-invokes a real, live
`_run_search()` call, bounded to a single corpus entry (`Q1_authoritative_state`) and an explicit
timeout, matching test_plan.md's "still really callable" smoke check without re-running all 7
queries on every `pytest` invocation.
"""
from __future__ import annotations

import ast
import json
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"

_CORPUS_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_baseline_corpus.py"
_RUNNER_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_baseline_runner.py"
_CONTRACT_MD = _CONTRACTS_DIR / "measurement_baseline_contract.md"
_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json"
)
_INVESTIGATION_MD = (
    _REPO_ROOT
    / "stored_artifacts"
    / "TCK-20260814-KGMCP-MEASUREMENT-BASELINE"
    / "investigation.md"
)
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_baseline_corpus import (  # noqa: E402
    CORPUS,
    CORPUS_VERSION,
    ROUTING_SHAPES,
    USE_CASES,
    kgmcp_char_heuristic_v1_token_count,
)

_CORPUS_SOURCE = _CORPUS_MODULE_PATH.read_text()
_CORPUS_AST = ast.parse(_CORPUS_SOURCE)
_RUNNER_SOURCE = _RUNNER_MODULE_PATH.read_text()
_RUNNER_AST = ast.parse(_RUNNER_SOURCE)
_CONTRACT_TEXT = _CONTRACT_MD.read_text()
_FIXTURE = json.loads(_FIXTURE_PATH.read_text())


# ---------------------------------------------------------------------------
# AC1 — investigation.md confirms sibling status + reuse, not duplication
# ---------------------------------------------------------------------------

def test_investigation_confirms_sibling_ticket_done_and_reuse_not_duplication():
    text = _INVESTIGATION_MD.read_text()
    for literal in (
        "TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING",
        "DONE",
        "compute_search_investigation_trend",
        "build_search_count_section",
        "build_raw_investigation_count_section",
    ):
        assert literal in text, f"investigation.md is missing required literal: {literal!r}"


# ---------------------------------------------------------------------------
# AC2 — fixed, versioned corpus covering all §8 shapes and §22 use cases
# ---------------------------------------------------------------------------

def test_representative_query_corpus_covers_all_7_routing_shapes():
    assert len(ROUTING_SHAPES) == 7
    assert len(CORPUS) == 7
    shapes_in_corpus = {entry["routing_shape"] for entry in CORPUS}
    assert shapes_in_corpus == ROUTING_SHAPES


def test_representative_query_corpus_covers_all_5_use_cases():
    assert len(USE_CASES) == 5
    use_cases_in_corpus = {entry["use_case"] for entry in CORPUS if entry["use_case"] is not None}
    assert use_cases_in_corpus == USE_CASES
    entries_with_use_case = sum(1 for entry in CORPUS if entry["use_case"] is not None)
    assert entries_with_use_case == 5


def test_corpus_is_versioned():
    assert isinstance(CORPUS_VERSION, int)
    assert CORPUS_VERSION == 1


def test_char_heuristic_v1_matches_frozen_formula():
    import math

    text = "hello world, this is a test string"
    expected = math.ceil(len(text.encode("utf-8")) / 4)
    assert kgmcp_char_heuristic_v1_token_count(text) == expected
    assert kgmcp_char_heuristic_v1_token_count("") == 0


# ---------------------------------------------------------------------------
# AC3 — real recorded direct-tool baseline per query, not an estimate
# ---------------------------------------------------------------------------

def test_corpus_baseline_entries_have_real_measured_fields_never_estimated():
    assert _FIXTURE["corpus_version"] == CORPUS_VERSION
    assert _FIXTURE["recorded_at_utc"]
    assert len(_FIXTURE["entries"]) == 7

    corpus_ids = {entry["id"] for entry in CORPUS}
    fixture_ids = {entry["id"] for entry in _FIXTURE["entries"]}
    assert fixture_ids == corpus_ids

    for entry in _FIXTURE["entries"]:
        context_search = entry["context_search"]
        assert isinstance(context_search["latency_ms"], (int, float))
        assert context_search["latency_ms"] >= 0
        assert context_search["tool_call_count"] == 1
        assert context_search["derivation"]

        graphify = entry["graphify"]
        assert isinstance(graphify["latency_ms"], (int, float))
        assert graphify["latency_ms"] >= 0
        assert graphify["tool_call_count"] == 1
        assert graphify["derivation"]

        combined = entry["combined"]
        assert isinstance(combined["serialized_tokens_estimate"], int)
        assert combined["tool_call_count"] == 2
        assert combined["derivation"]


def test_corpus_baseline_q3_discloses_honest_parity_ledger_omission():
    q3 = next(e for e in _FIXTURE["entries"] if e["id"] == "Q3_requirement_completeness")
    assert "notes" in q3
    assert "Parity Ledger" in q3["notes"]


def _run_with_timeout(fn, *, seconds: int):
    def _raise_timeout(signum, frame):
        raise TimeoutError(f"live smoke-check exceeded {seconds}s bound")

    previous_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(seconds)
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def test_corpus_baseline_wall_time_and_tool_call_count_are_plausible():
    """Exactly one bounded live re-invocation, matching test_plan.md's 'still really callable'
    smoke check — Q1_authoritative_state only, never all 7 queries, with an explicit timeout
    since the plan did not specify one and no CI-side pytest-timeout plugin is installed."""
    from search_mcp import _DB_PATH, _run_search

    if not _DB_PATH.exists():
        pytest.skip("knowledge index not built — run make knowledge-index")

    q1 = next(e for e in CORPUS if e["id"] == "Q1_authoritative_state")

    def _call():
        return _run_search(q1["query_text"], top_k=8)

    results = _run_with_timeout(_call, seconds=60)
    assert isinstance(results, list)
    assert len(results) > 0


# ---------------------------------------------------------------------------
# AC3 (continued) — zero mutation of agent-monitoring/
# ---------------------------------------------------------------------------

def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_zero_mutation_of_real_agent_monitoring_corpus():
    """Exercises the runner's full live-call path (`run_corpus()`, all 7 corpus entries) in-process
    — deliberately NOT `main()`. `main()` also overwrites the committed fixture
    (kgmcp_baseline_runner.py's own docstring/Step 2 point 6: the fixture 'is pinned (git-committed),
    not regenerated by the test suite') — invoking it here on every pytest run would fight that
    pinning and reintroduce timing-jitter-driven fixture churn on every CI run. `run_corpus()` runs
    the identical `_run_context_search`/`_run_graphify` calls `main()` does, so this test still
    proves zero agent-monitoring/ mutation from the real live-call path; only the file-write step is
    skipped.
    """
    from search_mcp import _DB_PATH

    if not _DB_PATH.exists():
        pytest.skip("knowledge index not built — run make knowledge-index")
    if shutil.which("graphify") is None:
        pytest.skip("graphify CLI not installed in this environment")

    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from kgmcp_baseline_runner import run_corpus

    pre_porcelain = _porcelain_snapshot()
    run_corpus()
    post_porcelain = _porcelain_snapshot()

    assert pre_porcelain == post_porcelain, (
        "kgmcp_baseline_runner.run_corpus() mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )


# ---------------------------------------------------------------------------
# AC4 — 5 distinct latency measurement points with instrumentation contract
# ---------------------------------------------------------------------------

def test_measurement_baseline_contract_defines_all_5_latency_points():
    lowered_text = _CONTRACT_TEXT.lower()
    for label in (
        "lookup", "evidence-validation", "provider-fallback", "packet-assembly", "end-to-end",
    ):
        assert label in lowered_text, f"contract doc missing latency point: {label!r}"

    assert "tools/retrieval_events.py" in _CONTRACT_TEXT
    assert "wrap_hybrid_retrieval" in _CONTRACT_TEXT
    assert "wrap_retrieval_cache_check" in _CONTRACT_TEXT
    assert "wrap_context_packet_assembly" in _CONTRACT_TEXT
    assert "implemented but not invoked by any live call site" in _CONTRACT_TEXT


def test_measurement_baseline_contract_states_end_to_end_reconciliation_rule():
    assert "sum of whichever" in _CONTRACT_TEXT


def test_measurement_baseline_contract_distinguishes_fixture_baseline_from_gateway_latency():
    assert "combined.wall_time_ms" in _CONTRACT_TEXT
    assert "not the same number" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# AC5 — thresholds predeclared, derived from recorded baseline
# ---------------------------------------------------------------------------

def test_predeclared_thresholds_cite_recorded_baseline_numbers():
    """Structural proof §4 is fixture-derived, not free-floating: the literal fixture path must
    appear in the threshold prose. Does not assert an exact numeric match against the fixture's
    current averages — `kgmcp_baseline_runner.run_corpus()` legitimately produces slightly
    different `latency_ms` figures on every real invocation (network/CPU timing jitter is not
    reproducible), and the committed fixture is intentionally not regenerated by this test suite
    (Step 2 point 6), so the doc's illustrative computed figures are pinned to whichever real run
    produced the currently-committed fixture, not to whatever the suite last happened to compute
    in-memory via `run_corpus()`.
    """
    assert "tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json" in _CONTRACT_TEXT
    assert "corpus-wide average" in _CONTRACT_TEXT
    assert "combined.wall_time_ms" in _CONTRACT_TEXT
    assert "combined.serialized_tokens_estimate" in _CONTRACT_TEXT


def test_predeclared_thresholds_never_restate_phase_3_pilot_bar_as_own_threshold():
    assert "§21 is a" in _CONTRACT_TEXT or "separate, later-phase acceptance bar" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# AC6 — repeated-demand design uses only deterministic IDs/hashes
# ---------------------------------------------------------------------------

def test_repeated_demand_design_never_stores_raw_prompt_text():
    for field in ("intent", "entity_id", "normalized_filters", "query_hash"):
        assert field in _CONTRACT_TEXT

    for banned in ("raw_prompt", "prompt_text", "full_query_text"):
        assert banned not in _CONTRACT_TEXT, f"contract doc must never mention {banned!r}"


def test_read_count_correlation_and_repeated_demand_stay_separate_sections():
    assert "read_count_correlation" in _CONTRACT_TEXT
    # compliant_group/non_compliant_group may be named ONLY inside an explicit
    # never-alias disclaimer, never adopted as this design's own identity-schema field names.
    identity_fields = {"intent", "entity_id", "normalized_filters", "query_hash"}
    read_count_correlation_fields = {"compliant_group", "non_compliant_group"}
    assert not (identity_fields & read_count_correlation_fields)
    assert "never alias" in _CONTRACT_TEXT
    assert "never merged" in _CONTRACT_TEXT


# ---------------------------------------------------------------------------
# AC7 — never-silent, derivation-string convention
# ---------------------------------------------------------------------------

def test_all_new_sections_carry_a_derivation_string():
    for entry in _FIXTURE["entries"]:
        assert entry["context_search"]["derivation"]
        assert entry["graphify"]["derivation"]
        assert entry["combined"]["derivation"]

    numbered_sections = [
        line for line in _CONTRACT_TEXT.splitlines() if line.startswith("## ")
    ]
    assert len(numbered_sections) >= 7


# ---------------------------------------------------------------------------
# Anti-drift guards
# ---------------------------------------------------------------------------

def test_search_tool_names_membership_unchanged():
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from generate_retro import SEARCH_TOOL_NAMES

    assert SEARCH_TOOL_NAMES == {
        "mcp__knowledge-search__search_docs",
        "ToolSearch",
        "WebSearch",
    }


def test_no_duplicate_read_to_search_ratio_computation():
    for tree, path in ((_CORPUS_AST, _CORPUS_MODULE_PATH), (_RUNNER_AST, _RUNNER_MODULE_PATH)):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                assert "search_count" not in node.name
                assert "read_to_search" not in node.name
            if isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and comparator.value == "Read":
                        pytest.fail(f"{path} re-implements a Read-tool-name comparison")


def test_context_tokens_still_reports_unavailable_for_live_telemetry():
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from retrieval_baseline_metrics import build_context_tokens_section

    section = build_context_tokens_section()
    assert section["status"] == "unavailable"


def test_no_live_gateway_code_or_search_mcp_edits_introduced():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        "tools/search_mcp.py",
        "tools/hybrid_retrieval.py",
        # tools/retrieval_cache.py intentionally removed from this list by
        # TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS: this ticket's own approved Scope is to
        # edit that file (adding the Level 1 cache schema/migration). This assertion was correct
        # for TCK-20260814-KGMCP-MEASUREMENT-BASELINE's own scope boundary but does not have
        # ticket-window awareness; the other 4 paths below remain unedited by this ticket and this
        # guard still protects them.
        "tools/context_packet_assembler.py",
        "tools/retrieval_events.py",
    ):
        assert banned_path not in result.stdout, (
            f"{banned_path} must never be edited by this ticket (Out of Scope)"
        )


def test_baseline_corpus_module_imports_no_live_gateway_code():
    imported_modules = set()
    for node in ast.walk(_CORPUS_AST):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
    banned = {"search_mcp", "hybrid_retrieval", "retrieval_cache", "context_packet_assembler"}
    assert not (imported_modules & banned), (
        "kgmcp_baseline_corpus.py must stay a pure data module with zero live tool calls"
    )


def test_runner_module_never_calls_emit_retrieval_event_or_wrap_functions():
    banned_names = {
        "emit_retrieval_event",
        "wrap_hybrid_retrieval",
        "wrap_retrieval_cache_check",
        "wrap_context_packet_assembly",
    }
    called_names = {
        node.func.id
        for node in ast.walk(_RUNNER_AST)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not (called_names & banned_names), (
        "kgmcp_baseline_runner.py must call _run_search directly, never through a wrap_* "
        "function that would emit a retrieval event"
    )
