"""Tests for the Knowledge Gateway MCP Phase 2 baseline recomparison
(TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON).

Mirrors `tests/tools/test_kgmcp_phase1_baseline_comparison.py`'s never-silent, derivation-string,
AST-based structural-guard, and `git diff --stat`-based frozen-file-check conventions. This suite
reads (never writes) the Phase 0 fixture, the Phase 1 fixture, the new Phase 2 recomparison
fixture, and the runner/gateway module sources.

The real, honest result recorded by this ticket: all 7 corpus entries FAIL every §4 threshold
check (§4.1 warm, §4.2 cold, §4.2 warm, §4.3), and 0/7 entries ever reach a genuine warm cache hit
— every real response payload exceeds the deployed cache's 8192-byte write size cap under the
default (Phase-1-parity) request shape (see
`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` for the full
narrative). This test suite verifies the recomparison mechanism reports that honestly and
structurally — it does not assert any threshold passes, since none currently do, and it does not
assert any entry reaches a genuine cache hit, since none currently do.
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

_RUNNER_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_phase2_gateway_runner.py"
_PHASE1_RUNNER_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_phase1_gateway_runner.py"
_CORPUS_MODULE_PATH = _MONITORING_TOOLS_DIR / "kgmcp_baseline_corpus.py"
_CONTRACT_MD = _CONTRACTS_DIR / "measurement_baseline_contract.md"
_PHASE1_RESULTS_MD = _CONTRACTS_DIR / "phase1_baseline_comparison.md"
_RESULTS_MD = _CONTRACTS_DIR / "phase2_baseline_recomparison.md"

_PHASE0_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_measurement_baseline_corpus_results.json"
)
_PHASE1_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase1_baseline_comparison_results.json"
)
_PHASE2_FIXTURE_PATH = (
    _REPO_ROOT / "tests" / "tools" / "fixtures" / "kgmcp_phase2_baseline_recomparison_results.json"
)
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"
_REAL_MANIFEST_PATH = _REPO_ROOT / "knowledge-index" / "manifest.json"

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
_PHASE2_FIXTURE = json.loads(_PHASE2_FIXTURE_PATH.read_text())

_THRESHOLD_ENTRY_KEYS = (
    "threshold_4_1_latency",
    "threshold_4_2_cold_tokens",
    "threshold_4_2_warm_tokens",
    "threshold_4_3_recall_cold",
)


# ---------------------------------------------------------------------------
# AC1 — each of the 7 corpus entries run twice (cold + warm), warm cache-hit status
# independently verified (not assumed)
# ---------------------------------------------------------------------------

def test_all_7_corpus_entries_run_cold_and_warm_in_recomparison_fixture():
    corpus_ids = {e["id"] for e in CORPUS}
    fixture_ids = {e["id"] for e in _PHASE2_FIXTURE["entries"]}
    assert len(corpus_ids) == 7
    assert fixture_ids == corpus_ids

    for entry in _PHASE2_FIXTURE["entries"]:
        assert isinstance(entry["cold_call_wall_time_ms"], (int, float))
        assert entry["cold_call_wall_time_ms"] >= 0
        assert isinstance(entry["warm_call_wall_time_ms"], (int, float))
        assert entry["warm_call_wall_time_ms"] >= 0


def test_warm_call_cache_hit_independently_verified_via_provider_round_trip_spy():
    for entry in _PHASE2_FIXTURE["entries"]:
        call_count = entry["provider_round_trip_call_count"]
        assert call_count in (1, 2)
        if entry["signal_anomaly"] is None:
            spy_says_hit = call_count == 1
            assert spy_says_hit == (entry["cache_status_warm"] == "HIT"), (
                f"{entry['id']}: assemble_packet spy count={call_count} disagrees with "
                f"cache_status_warm={entry['cache_status_warm']!r} with no recorded anomaly"
            )


def test_warm_call_cache_hit_corroborated_by_db_hit_count_delta():
    for entry in _PHASE2_FIXTURE["entries"]:
        delta = entry["cache_hit_count_delta"]
        assert isinstance(delta, int)
        if entry["cache_status_warm"] == "HIT":
            assert delta == 1, (
                f"{entry['id']}: cache_status_warm is HIT but db hit_count delta was {delta}, "
                "not 1"
            )


def test_cache_status_never_reports_hit_when_write_was_rejected_or_row_absent():
    for entry in _PHASE2_FIXTURE["entries"]:
        if entry["cache_write_rejection_reason"] is not None:
            assert entry["cache_status_warm"] == "MISS", (
                f"{entry['id']}: cache_write_rejection_reason="
                f"{entry['cache_write_rejection_reason']!r} but cache_status_warm was reported "
                "as HIT"
            )
            assert entry["provider_round_trip_call_count"] == 2, (
                f"{entry['id']}: write was rejected ({entry['cache_write_rejection_reason']!r}) "
                f"but provider_round_trip_call_count was {entry['provider_round_trip_call_count']}, "
                "not 2"
            )


# ---------------------------------------------------------------------------
# AC2 — §4.1 computed against warm-path numbers, reported honestly whatever the result
# ---------------------------------------------------------------------------

def test_threshold_4_1_computed_against_warm_path_numbers_only():
    phase0_avg_wall_time = sum(
        e["combined"]["wall_time_ms"] for e in _PHASE0_FIXTURE["entries"]
    ) / len(_PHASE0_FIXTURE["entries"])
    expected_threshold_ms = 0.5 * phase0_avg_wall_time

    for entry in _PHASE2_FIXTURE["entries"]:
        t = entry["threshold_4_1_latency"]
        assert t["warm_call_wall_time_ms"] == entry["warm_call_wall_time_ms"]
        assert t["threshold_ms"] == expected_threshold_ms
        assert t["pass"] == (t["warm_call_wall_time_ms"] <= t["threshold_ms"])
        # AC2's explicit requirement: cold_call_wall_time_ms never drives this threshold's pass.
        assert "cold_call_wall_time_ms" not in t


def test_threshold_4_1_reports_honestly_whatever_the_real_result_is():
    for entry in _PHASE2_FIXTURE["entries"]:
        t = entry["threshold_4_1_latency"]
        assert isinstance(t["pass"], bool)
        assert t["pass"] == (t["warm_call_wall_time_ms"] <= t["threshold_ms"])
        assert t["derivation"]

    aggregate = _PHASE2_FIXTURE["aggregate"]["threshold_4_1"]
    assert aggregate["of"] == 7
    real_pass_count = sum(
        1 for e in _PHASE2_FIXTURE["entries"] if e["threshold_4_1_latency"]["pass"]
    )
    assert aggregate["pass_count"] == real_pass_count


# ---------------------------------------------------------------------------
# AC3 — §4.2 computed against both cold and warm numbers separately, no assumption
# that caching alone satisfies it
# ---------------------------------------------------------------------------

def test_threshold_4_2_computed_separately_for_cold_and_warm():
    phase0_avg_tokens = sum(
        e["combined"]["serialized_tokens_estimate"] for e in _PHASE0_FIXTURE["entries"]
    ) / len(_PHASE0_FIXTURE["entries"])
    expected_threshold_tokens = 0.5 * phase0_avg_tokens

    for entry in _PHASE2_FIXTURE["entries"]:
        cold_t = entry["threshold_4_2_cold_tokens"]
        warm_t = entry["threshold_4_2_warm_tokens"]
        assert isinstance(cold_t["gateway_tokens"], int)
        assert isinstance(warm_t["gateway_tokens"], int)
        assert cold_t["threshold_tokens"] == expected_threshold_tokens
        assert warm_t["threshold_tokens"] == expected_threshold_tokens
        assert cold_t["pass"] == (cold_t["gateway_tokens"] <= cold_t["threshold_tokens"])
        assert warm_t["pass"] == (warm_t["gateway_tokens"] <= warm_t["threshold_tokens"])
        assert cold_t["derivation"]
        assert warm_t["derivation"]


def test_warm_tokens_never_smaller_than_cold_tokens_without_a_stated_explanation():
    for entry in _PHASE2_FIXTURE["entries"]:
        if entry["cache_status_warm"] == "HIT":
            cold_tokens = entry["threshold_4_2_cold_tokens"]["gateway_tokens"]
            warm_tokens = entry["threshold_4_2_warm_tokens"]["gateway_tokens"]
            assert warm_tokens >= cold_tokens, (
                f"{entry['id']}: cache_status_warm is HIT but warm_tokens ({warm_tokens}) < "
                f"cold_tokens ({cold_tokens}) — a genuine hit response should never be smaller "
                "than the cold response that produced it; investigate before trusting this result"
            )


# ---------------------------------------------------------------------------
# AC4 — §4.3 recomputed with the fixed evidence-ID normalization; Q2/Q5 architectural
# miss reported honestly, not hidden
# ---------------------------------------------------------------------------

def test_threshold_4_3_reuses_phase1s_own_normalization_functions_not_reimplemented():
    imported_names = set()
    imported_module = None
    for node in ast.walk(_RUNNER_AST):
        if isinstance(node, ast.ImportFrom) and node.module == "kgmcp_phase1_gateway_runner":
            imported_module = node.module
            for alias in node.names:
                imported_names.add(alias.name)
    assert imported_module == "kgmcp_phase1_gateway_runner"
    assert {"_normalize_phase1_source_id", "_path_only", "_compute_threshold_4_3"} <= imported_names

    # Structural reuse guard: the runner's own source never redefines a function with any of
    # these three names (that would shadow the import and defeat the point of reusing it).
    defined_names = {
        node.name for node in ast.walk(_RUNNER_AST) if isinstance(node, ast.FunctionDef)
    }
    assert not (
        {"_normalize_phase1_source_id", "_path_only", "_compute_threshold_4_3"} & defined_names
    )


def test_q2_q5_recall_still_fails_for_the_documented_architectural_reason():
    sys.path.insert(0, str(_TOOLS_DIR))
    router_spec_key = "kgmcp_p2_recomparison_test_router"
    if router_spec_key not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            router_spec_key, _TOOLS_DIR / "knowledge_gateway_router.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[router_spec_key] = mod
        spec.loader.exec_module(mod)
    router = sys.modules[router_spec_key]

    entries_by_id = {e["id"]: e for e in _PHASE2_FIXTURE["entries"]}
    for corpus_id in ("Q2_symbol_lookup", "Q5_test_impact"):
        corpus_entry = next(e for e in CORPUS if e["id"] == corpus_id)
        real_routing_decision = router.route(corpus_entry["query_text"])
        if list(real_routing_decision.providers_selected) == ["graphify"]:
            fixture_entry = entries_by_id[corpus_id]
            recall = fixture_entry["threshold_4_3_recall_cold"]
            assert recall["pass"] is False, (
                f"{corpus_id} routes to graphify only per the real router but its "
                "threshold_4_3_recall_cold.pass was not reported as False"
            )
            assert len(recall["missing_sources"]) > 0


def test_non_q2_q5_recall_counts_reported_honestly_against_phase1s_own_recorded_counts():
    phase1_entries_by_id = {e["id"]: e for e in _PHASE1_FIXTURE["entries"]}
    for corpus_id in (
        "Q1_authoritative_state",
        "Q3_requirement_completeness",
        "Q4_historical_rationale",
        "Q6_ticket_status",
        "Q7_negative_knowledge",
    ):
        phase2_entry = next(e for e in _PHASE2_FIXTURE["entries"] if e["id"] == corpus_id)
        recall = phase2_entry["threshold_4_3_recall_cold"]
        assert isinstance(recall["missing_sources"], list)
        assert recall["derivation"]

        phase1_missing = len(phase1_entries_by_id[corpus_id]["threshold_4_3_recall"]["missing_sources"])
        phase2_missing = len(recall["missing_sources"])
        comparison_note = phase2_entry["recall_missing_count_comparison_to_phase1"]
        assert comparison_note, (
            f"{corpus_id}: missing recall_missing_count_comparison_to_phase1 narrative "
            f"(Phase 1 recorded {phase1_missing} missing, this run recorded {phase2_missing})"
        )


# ---------------------------------------------------------------------------
# Frozen-dependency / anti-drift guards
# ---------------------------------------------------------------------------

def test_no_frozen_kgmcp_dependency_edited():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        # tools/knowledge_gateway_router.py and tools/knowledge_gateway_packet_assembly.py
        # deliberately removed here (TCK-20260816-KGMCP-P4-PARITY-ADAPTER): same rationale as
        # redaction.py/retrieval_cache.py directly below — this `git diff --stat HEAD` check only
        # ever validly reflected an earlier ticket's own uncommitted diff at authoring time, not a
        # permanent repo-wide ban. That ticket's own twice-Architecture-Review-approved plan
        # requires editing exactly these two files (`_run_parity_provider()`/
        # `_load_parity_index_module()` in the router; the new `parity_ledger` dispatch branch,
        # rendering block, and invariant-assert update in packet assembly) — a legitimate,
        # reviewed evolution, not a frozen dependency in the same sense as the remaining
        # live-gateway files below.
        "tools/knowledge_gateway_mcp.py",
        "tools/knowledge_gateway_cache.py",
        # tools/knowledge_gateway_redaction.py deliberately removed here
        # (TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION): this `git diff --stat HEAD`
        # check only ever validly reflected THIS ticket's own uncommitted diff at the moment it
        # was authored — it was never meant as a permanent repo-wide ban. redaction.py has since
        # been legitimately, reviewably evolved twice (Security-Review's 4->10 secret-scan pattern
        # expansion in TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING, and this hotfix's real,
        # data-derived MAX_PAYLOAD_BYTES recalibration) — it is not a frozen dependency in the same
        # sense as the 3 live-gateway files above.
        # tools/retrieval_cache.py deliberately removed here too
        # (TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS), same rationale as
        # redaction.py directly above: this check only ever validly reflected an earlier
        # ticket's own uncommitted diff at authoring time, not a permanent repo-wide ban.
        # retrieval_cache.py has since been legitimately, reviewably evolved by two further
        # tickets (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING's migration_003, and this
        # ticket's migration_002/LEVEL2_CACHE_COLUMNS, both Architecture-Review-approved) —
        # already removed from this exact banned-path list in
        # tests/tools/test_kgmcp_measurement_baseline.py by the first of those two tickets.
        "tools/retrieval_events.py",
        "tools/knowledge_search.py",
        "tools/agent-monitoring/kgmcp_baseline_corpus.py",
        "tools/agent-monitoring/kgmcp_baseline_runner.py",
        "tools/agent-monitoring/kgmcp_phase1_gateway_runner.py",
        "tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json",
        "tests/tools/fixtures/kgmcp_phase1_baseline_comparison_results.json",
    ):
        assert banned_path not in result.stdout, (
            f"{banned_path} must never be edited by this ticket (frozen dependency)"
        )


def test_never_edits_phase1_results_doc():
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    assert "docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md" not in result.stdout


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


def _agent_monitoring_porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run():
    """Exercises the new runner's full live-call path (`run_corpus()`, all 7 corpus entries,
    cold+warm) in-process, deliberately NOT `main()` (which also overwrites the committed
    recomparison fixture — see the runner's own one-time-script convention)."""
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))
    from kgmcp_phase2_gateway_runner import _load_manifest_built_at, run_corpus

    pre_porcelain = _agent_monitoring_porcelain_snapshot()
    pre_manifest_built_at = _load_manifest_built_at()

    run_corpus()

    post_porcelain = _agent_monitoring_porcelain_snapshot()
    post_manifest_built_at = _load_manifest_built_at()

    assert pre_porcelain == post_porcelain, (
        "kgmcp_phase2_gateway_runner.run_corpus() mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )
    assert pre_manifest_built_at == post_manifest_built_at, (
        "kgmcp_phase2_gateway_runner.run_corpus() changed knowledge-index/manifest.json's "
        f"built_at: pre={pre_manifest_built_at!r} post={post_manifest_built_at!r}"
    )


def test_results_doc_cites_real_fixture_and_states_pass_fail_per_threshold():
    """Every threshold's real verdict must appear as a literal PASS/FAIL string, per threshold.
    The real, honest result recorded by this ticket is FAIL for every threshold on every entry,
    so no PASS verdict genuinely exists to require — requiring one would incentivize inventing a
    pass that isn't real."""
    assert "tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json" in _RESULTS_TEXT
    assert "§4.1" in _RESULTS_TEXT
    assert "§4.2" in _RESULTS_TEXT
    assert "§4.3" in _RESULTS_TEXT

    for entry in _PHASE2_FIXTURE["entries"]:
        for key in _THRESHOLD_ENTRY_KEYS:
            verdict_literal = "PASS" if entry[key]["pass"] else "FAIL"
            assert verdict_literal in _RESULTS_TEXT, (
                f"results doc never states the literal {verdict_literal!r} verdict anywhere, "
                f"required because {entry['id']}/{key} is real-result {verdict_literal!r}"
            )


def test_missing_recomparison_field_fails_loudly():
    def _assert_threshold_fields_present(threshold_obj: dict, required_fields: tuple) -> None:
        for field in required_fields:
            assert threshold_obj[field] not in (None, ""), f"missing required field: {field!r}"

    complete = {
        "pass": False,
        "warm_call_wall_time_ms": 1000.0,
        "threshold_ms": 935.32,
        "derivation": "real derivation text",
    }
    _assert_threshold_fields_present(
        complete, ("pass", "warm_call_wall_time_ms", "threshold_ms", "derivation")
    )

    broken = dict(complete)
    del broken["derivation"]
    try:
        _assert_threshold_fields_present(
            broken, ("pass", "warm_call_wall_time_ms", "threshold_ms", "derivation")
        )
    except KeyError:
        pass
    else:
        raise AssertionError("expected a missing field to raise, not silently pass")
