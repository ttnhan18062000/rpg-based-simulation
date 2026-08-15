"""Tests for the Knowledge Gateway MCP Phase 1 baseline comparison
(TCK-20260815-KGMCP-P1-BASELINE-COMPARISON).

Mirrors `tests/tools/test_kgmcp_measurement_baseline.py`'s never-silent, derivation-string,
AST-based structural-guard, and `git diff --stat`-based frozen-file-check conventions. This suite
reads (never writes) the Phase 0 fixture, the new Phase 1 comparison fixture, and both runner/
gateway module sources.

The real, honest result recorded by this ticket: all 7 corpus entries FAIL all 3 §4 thresholds
(see `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md` for the full
narrative and root-cause analysis). This test suite verifies the comparison mechanism reports
that honestly and structurally — it does not assert any threshold passes, since none currently do.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"

_RUNNER_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_phase1_gateway_runner.py"
_CORPUS_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_baseline_corpus.py"
_CONTRACT_MD = _CONTRACTS_DIR / "measurement_baseline_contract.md"
_RESULTS_MD = _CONTRACTS_DIR / "phase1_baseline_comparison.md"

_PHASE0_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json"
)
_PHASE1_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase1_baseline_comparison_results.json"
)
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from kgmcp_baseline_corpus import CORPUS  # noqa: E402

_RUNNER_SOURCE = _RUNNER_MODULE_PATH.read_text()
_RUNNER_AST = ast.parse(_RUNNER_SOURCE)
_CONTRACT_TEXT = _CONTRACT_MD.read_text()
_RESULTS_TEXT = _RESULTS_MD.read_text()
_PHASE0_FIXTURE = json.loads(_PHASE0_FIXTURE_PATH.read_text())
_PHASE1_FIXTURE = json.loads(_PHASE1_FIXTURE_PATH.read_text())

_THRESHOLD_ENTRY_KEYS = ("threshold_4_1_latency", "threshold_4_2_tokens", "threshold_4_3_recall")


# ---------------------------------------------------------------------------
# AC1 — all 7 corpus entries run through the real gateway, not a subset/mock
# ---------------------------------------------------------------------------

def test_all_7_corpus_entries_present_in_comparison_fixture():
    corpus_ids = {e["id"] for e in CORPUS}
    fixture_ids = {e["id"] for e in _PHASE1_FIXTURE["entries"]}
    assert len(corpus_ids) == 7
    assert fixture_ids == corpus_ids


def test_comparison_runner_calls_real_run_knowledge_context_not_a_mock():
    called_names = set()
    for node in ast.walk(_RUNNER_AST):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
            elif isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
    assert "_run_knowledge_context" in called_names

    imported_names = set()
    for node in ast.walk(_RUNNER_AST):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[0])
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module.split(".")[0])
    assert "unittest" not in imported_names
    assert "mock" not in imported_names
    assert "MagicMock" not in _RUNNER_SOURCE


# ---------------------------------------------------------------------------
# AC2 — each §4 threshold computed and reported PASS/FAIL, per entry and aggregate
# ---------------------------------------------------------------------------

def test_each_entry_reports_latency_threshold_pass_fail_with_numbers():
    for entry in _PHASE1_FIXTURE["entries"]:
        t = entry["threshold_4_1_latency"]
        assert isinstance(t["pass"], bool)
        assert isinstance(t["gateway_wall_time_ms"], (int, float))
        assert t["gateway_wall_time_ms"] >= 0
        assert isinstance(t["threshold_ms"], (int, float))
        assert t["derivation"]


def test_each_entry_reports_token_threshold_pass_fail_with_numbers():
    for entry in _PHASE1_FIXTURE["entries"]:
        t = entry["threshold_4_2_tokens"]
        assert isinstance(t["pass"], bool)
        assert isinstance(t["gateway_tokens"], int)
        assert t["gateway_tokens"] >= 0
        assert isinstance(t["threshold_tokens"], (int, float))
        assert t["derivation"]


def test_each_entry_reports_recall_threshold_pass_fail_with_numbers():
    for entry in _PHASE1_FIXTURE["entries"]:
        t = entry["threshold_4_3_recall"]
        assert isinstance(t["pass"], bool)
        assert isinstance(t["baseline_sources"], list)
        assert isinstance(t["gateway_sources"], list)
        assert isinstance(t["missing_sources"], list)
        assert t["derivation"]
        # Never a silent coercion: pass must be exactly (missing_sources empty).
        assert t["pass"] == (len(t["missing_sources"]) == 0)


def test_aggregate_thresholds_summarize_all_7_entries_not_just_a_subset():
    aggregate = _PHASE1_FIXTURE["aggregate"]
    for key in ("threshold_4_1", "threshold_4_2", "threshold_4_3"):
        assert aggregate[key]["of"] == 7
        assert 0 <= aggregate[key]["pass_count"] <= 7

    entries = _PHASE1_FIXTURE["entries"]
    any_entry_threshold_fails = any(
        not entry[key]["pass"] for entry in entries for key in _THRESHOLD_ENTRY_KEYS
    )
    if any_entry_threshold_fails:
        assert aggregate["all_thresholds_pass"] is False


# ---------------------------------------------------------------------------
# AC3 — if a threshold is missed, it is stated plainly, never redefined/hidden
# ---------------------------------------------------------------------------

def test_no_threshold_formula_redefined_from_measurement_baseline_contract():
    phase0_avg_wall_time = sum(
        e["combined"]["wall_time_ms"] for e in _PHASE0_FIXTURE["entries"]
    ) / len(_PHASE0_FIXTURE["entries"])
    phase0_avg_tokens = sum(
        e["combined"]["serialized_tokens_estimate"] for e in _PHASE0_FIXTURE["entries"]
    ) / len(_PHASE0_FIXTURE["entries"])

    expected_threshold_ms = 0.5 * phase0_avg_wall_time
    expected_threshold_tokens = 0.5 * phase0_avg_tokens

    for entry in _PHASE1_FIXTURE["entries"]:
        assert entry["threshold_4_1_latency"]["threshold_ms"] == expected_threshold_ms
        assert entry["threshold_4_2_tokens"]["threshold_tokens"] == expected_threshold_tokens

    # Every entry uses the SAME threshold constants — never a per-entry-loosened threshold.
    latency_thresholds = {e["threshold_4_1_latency"]["threshold_ms"] for e in _PHASE1_FIXTURE["entries"]}
    token_thresholds = {e["threshold_4_2_tokens"]["threshold_tokens"] for e in _PHASE1_FIXTURE["entries"]}
    assert len(latency_thresholds) == 1
    assert len(token_thresholds) == 1


def test_predicted_q2_q5_recall_miss_is_reported_not_hidden():
    sys.path.insert(0, str(_TOOLS_DIR))
    router_spec_key = "kgmcp_p1_comparison_test_router"
    if router_spec_key not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            router_spec_key, _TOOLS_DIR / "knowledge_gateway_router.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[router_spec_key] = mod
        spec.loader.exec_module(mod)
    router = sys.modules[router_spec_key]

    entries_by_id = {e["id"]: e for e in _PHASE1_FIXTURE["entries"]}
    for corpus_id in ("Q2_symbol_lookup", "Q5_test_impact"):
        corpus_entry = next(e for e in CORPUS if e["id"] == corpus_id)
        real_routing_decision = router.route(corpus_entry["query_text"])
        if list(real_routing_decision.providers_selected) == ["graphify"]:
            fixture_entry = entries_by_id[corpus_id]
            recall = fixture_entry["threshold_4_3_recall"]
            assert recall["pass"] is False, (
                f"{corpus_id} routes to graphify only per the real router but its "
                "threshold_4_3_recall.pass was not reported as False"
            )
            assert len(recall["missing_sources"]) > 0


# ---------------------------------------------------------------------------
# AC4 — never-silent convention: a missing field must fail loudly, not degrade
# ---------------------------------------------------------------------------

def test_all_comparison_entries_carry_nonempty_derivation_strings():
    for entry in _PHASE1_FIXTURE["entries"]:
        assert entry["derivation"]
        for key in _THRESHOLD_ENTRY_KEYS:
            assert entry[key]["derivation"]


def _assert_threshold_fields_present(threshold_obj: dict, required_fields: tuple[str, ...]) -> None:
    for field in required_fields:
        assert threshold_obj[field] not in (None, ""), f"missing required field: {field!r}"


def test_missing_comparison_field_fails_loudly():
    complete = {
        "pass": False,
        "gateway_wall_time_ms": 1000.0,
        "threshold_ms": 935.32,
        "derivation": "real derivation text",
    }
    _assert_threshold_fields_present(complete, ("pass", "gateway_wall_time_ms", "threshold_ms", "derivation"))

    broken = dict(complete)
    del broken["derivation"]
    try:
        _assert_threshold_fields_present(broken, ("pass", "gateway_wall_time_ms", "threshold_ms", "derivation"))
    except KeyError:
        pass
    else:
        raise AssertionError("expected a missing field to raise, not silently pass")


# ---------------------------------------------------------------------------
# Frozen-dependency / anti-drift guards
# ---------------------------------------------------------------------------

def test_no_frozen_kgmcp_dependency_edited():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        "tools/knowledge_gateway_router.py",
        "tools/knowledge_gateway_packet_assembly.py",
        "tools/knowledge_gateway_mcp.py",
        "tools/retrieval_events.py",
        "tools/agent-monitoring/kgmcp_baseline_corpus.py",
        "tools/agent-monitoring/kgmcp_baseline_runner.py",
        "tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json",
    ):
        assert banned_path not in result.stdout, (
            f"{banned_path} must never be edited by this ticket (frozen dependency)"
        )


def test_new_runner_never_calls_emit_retrieval_event_or_wrap_functions():
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
    called_attrs = {
        node.func.attr
        for node in ast.walk(_RUNNER_AST)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not (called_names & banned_names)
    assert not (called_attrs & banned_names)


def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner():
    """Exercises the new runner's full live-call path (`run_corpus()`, all 7 corpus entries)
    in-process, deliberately NOT `main()` (which also overwrites the committed comparison
    fixture — see `kgmcp_phase1_gateway_runner.py`'s own one-time-script convention)."""
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from kgmcp_phase1_gateway_runner import run_corpus

    pre_porcelain = _porcelain_snapshot()
    run_corpus()
    post_porcelain = _porcelain_snapshot()

    assert pre_porcelain == post_porcelain, (
        "kgmcp_phase1_gateway_runner.run_corpus() mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )


def test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold():
    """Every threshold's real verdict must appear as a literal PASS/FAIL string, per threshold.
    This does not require the literal string "PASS" to appear anywhere — the real, honest result
    recorded by this ticket is FAIL for all 3 thresholds, so no PASS verdict genuinely exists to
    state; requiring one would incentivize inventing a pass that isn't real."""
    assert "tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json" in _RESULTS_TEXT
    assert "§4.1" in _RESULTS_TEXT
    assert "§4.2" in _RESULTS_TEXT
    assert "§4.3" in _RESULTS_TEXT

    for entry in _PHASE1_FIXTURE["entries"]:
        for key in _THRESHOLD_ENTRY_KEYS:
            verdict_literal = "PASS" if entry[key]["pass"] else "FAIL"
            assert verdict_literal in _RESULTS_TEXT, (
                f"results doc never states the literal {verdict_literal!r} verdict anywhere, "
                f"required because {entry['id']}/{key} is real-result {verdict_literal!r}"
            )
