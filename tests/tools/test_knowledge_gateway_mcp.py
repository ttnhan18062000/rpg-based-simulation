"""Tests for tools/knowledge_gateway_mcp.py — the Knowledge Gateway MCP Phase 1 FastMCP server
(TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE).

Exercises the real, invocable `knowledge_context`/`knowledge_status` tools over the frozen
router (`tools/knowledge_gateway_router.py`) and packet assembler
(`tools/knowledge_gateway_packet_assembly.py`), validating responses against the frozen
`docs/engine/contracts/knowledge_gateway_mcp/*.schema.json` files with a real
`jsonschema.Draft7Validator` — mirrors `tests/tools/test_search_mcp.py`'s own direct
`_mod._run_search(...)`-style calling convention and
`tests/tools/test_knowledge_gateway_packet_assembly.py`'s monkeypatch-at-sibling-module-boundary
isolation pattern.

Per Design Decision D1 (re-verified, twice reviewed): none of `tools/retrieval_events.py`'s 3
Wrapper functions has an undistorted real call site in this module's pipeline, and this module
does not import or call `tools/retrieval_events.py` at all — test 7 below proves that honest
zero-invocation finding structurally, not just by absence of an import.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_MCP_MODULE_PATH = _TOOLS_DIR / "knowledge_gateway_mcp.py"


def _load_mcp_module():
    spec = importlib.util.spec_from_file_location("knowledge_gateway_mcp_test", _MCP_MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_gateway_mcp_test"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_mcp_module()


@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    """DD14 (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING) — mirrors
    tests/tools/test_retrieval_cache.py's own `_isolated_cache_db` fixture. Every test in this
    file now potentially reads/writes real Level 1 cache rows via `_mod._run_knowledge_context()`/
    `_mod._run_knowledge_status()`; without isolation, repeated runs would pollute the real
    on-disk `knowledge-index/retrieval_cache.db` and/or produce flaky cross-test cache hits.
    `_MANIFEST_PATH` is also isolated (beyond DD14's own one-line sketch, following
    `test_retrieval_cache.py`'s own precedent exactly) so `_corpus_generation()`-driven tests never
    read or depend on the real `knowledge-index/manifest.json`.
    """
    from tools import retrieval_cache as rc

    monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")
    monkeypatch.setattr(rc, "_MANIFEST_PATH", tmp_path / "manifest.json")
    yield


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _validate_response(instance: dict) -> None:
    resolver = jsonschema.RefResolver(
        base_uri=_CONTRACTS_DIR.resolve().as_uri() + "/",
        referrer=_load_json(_CONTRACTS_DIR / "knowledge_context_response.schema.json"),
    )
    validator = jsonschema.Draft7Validator(
        _load_json(_CONTRACTS_DIR / "knowledge_context_response.schema.json"), resolver=resolver
    )
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    assert not errors, [e.message for e in errors]


def _validate_status_response(instance: dict) -> None:
    validator = jsonschema.Draft7Validator(
        _load_json(_CONTRACTS_DIR / "knowledge_status_response.schema.json")
    )
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    assert not errors, [e.message for e in errors]


# ---------------------------------------------------------------------------
# 1/2 — real invocation validates against the frozen response schemas (AC #1)
# ---------------------------------------------------------------------------

def test_knowledge_context_tool_real_invocation_validates_against_response_schema():
    response = _mod._run_knowledge_context("what is the damage formula")
    _validate_response(response)
    assert response["status"] in {"OK", "PARTIAL", "CONFLICTED", "UNVERIFIED", "ERROR"}


def test_knowledge_status_tool_real_invocation_validates_against_response_schema():
    response = _mod._run_knowledge_status()
    _validate_status_response(response)
    assert response["gateway_version"]
    assert response["reported_schema_version"] == 1


# ---------------------------------------------------------------------------
# 3 — request validation rejects a forbidden/unexpected field (AC #2)
# ---------------------------------------------------------------------------

def test_knowledge_context_rejects_forbidden_request_field():
    with pytest.raises(TypeError):
        _mod._run_knowledge_context("some query", provider_weights={"context_search": 1.0})


def test_knowledge_context_value_level_validation_rejects_invalid_enum_value():
    response = _mod._run_knowledge_context("some query", mode="not_a_real_mode")
    assert response["status"] == "ERROR"
    assert "error" in response
    _validate_response(response)


# ---------------------------------------------------------------------------
# 4 — knowledge_status never fabricates a cache-specific field value (AC #3)
# ---------------------------------------------------------------------------

# Narrowed by TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DD13): cache_entry_counts/
# cache_hit_rate/cache_miss_rate/cache_stale_rejection_rate are removed from this omission set —
# they are now genuinely populated once the real cache has at least one row (see
# test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes below). This is a
# legitimate, read-and-justify correction of a Phase-1-scoped assumption that has since expired by
# this ticket's own in-scope behavior change — not a routed-around gate — mirroring
# TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS's own DD3/Step 6 precedent for
# test_kgmcp_measurement_baseline.py's banned-path tuple. The remaining guarantee (these 3 fields
# plus latency_summary_ms stay honestly omitted — this ticket adds no latency instrumentation and
# does not populate these) is preserved unweakened.
_CACHE_SPECIFIC_FIELDS = {
    "recent_invalidation_reasons",
    "cache_rebuildable",
    "provider_fallback_rate",
}


def test_knowledge_status_omits_all_cache_specific_fields_enumerated():
    response = _mod._run_knowledge_status()

    for field in _CACHE_SPECIFIC_FIELDS:
        assert field not in response, f"{field} must be omitted, never a fabricated placeholder"

    # No real call site emits any latency data (Design Decision D1/D5, still true post-Phase-2) —
    # the entire top-level key is omitted, not just its cache-domain sub-fields.
    assert "latency_summary_ms" not in response

    # This test's own isolated cache DB (see _isolated_cache_db fixture) has zero rows at this
    # point — the cache-domain fields therefore stay genuinely absent here too (DD12's own
    # `if stats["total_rows"] > 0` gate), so the exact-keys assertion still holds.
    assert set(response.keys()) == {"gateway_version", "reported_schema_version", "providers", "branch_scope"}
    assert response["providers"]
    assert response["branch_scope"]["branch"]


def test_provider_context_search_adapter_version_null_not_fabricated():
    response = _mod._run_knowledge_status()
    context_search_entries = [p for p in response["providers"] if p["provider_id"] == "context_search"]
    assert len(context_search_entries) == 1
    assert "generation" not in context_search_entries[0], (
        "context_search's adapter_version is genuinely null — 'generation' must be absent, "
        "never a fabricated string or a null value"
    )


# ---------------------------------------------------------------------------
# 5/6 — .mcp.json gains exactly one new entry; frozen files provably untouched (AC #4a)
# ---------------------------------------------------------------------------

def test_mcp_json_gains_exactly_one_new_server_entry():
    mcp_config = _load_json(_REPO_ROOT / ".mcp.json")
    assert set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github", "knowledge-gateway"}

    entry = mcp_config["mcpServers"]["knowledge-gateway"]
    assert entry["command"] == "bash"
    assert entry["args"] == ["tools/start_knowledge_gateway_mcp.sh"]
    assert entry["env"] == {}
    assert entry["description"]

    knowledge_search_entry = mcp_config["mcpServers"]["knowledge-search"]
    assert knowledge_search_entry == {
        "command": "bash",
        "args": ["tools/start_search_mcp.sh"],
        "env": {},
        "description": "Local semantic search over project docs, tickets, and investigations",
    }


def test_search_mcp_py_provably_untouched():
    """`tools/knowledge_gateway_packet_assembly.py` was a frozen dependency only for this file's
    own originating ticket (TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE) — it was dropped from this
    banned-path tuple by TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT, whose entire,
    twice-Architecture-Review-approved scope was to make targeted edits to exactly that module
    (dedup identity, conflict-vs-dedup guard, budget-truncation marker).

    `tools/knowledge_gateway_router.py` is dropped from this tuple the same way by
    TCK-20260816-KGMCP-P4-PARITY-ADAPTER, whose own twice-Architecture-Review-approved plan
    requires adding `_run_parity_provider()`/`_load_parity_index_module()` to that module and
    wiring `ROUTING_TABLE["requirement_completeness_verification"]` to a real `parity_ledger`
    primary provider (closing Phase 1's deliberate `not_yet_routed="parity_ledger"` placeholder).
    The remaining two paths stay genuinely frozen for every Knowledge Gateway MCP ticket, this one
    included (per its own Out-of-Scope)."""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        "tools/search_mcp.py",
        "tools/retrieval_events.py",
    ):
        assert banned_path not in result.stdout, (
            f"{banned_path} must never be edited by this ticket (DONE/frozen dependency)"
        )


# ---------------------------------------------------------------------------
# 7 — honest finding: zero of the 3 named wrappers genuinely apply (AC #4b)
# ---------------------------------------------------------------------------

def test_wrapper_functions_genuinely_not_applicable_zero_invoked(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "knowledge_gateway_mcp_test_retrieval_events", _TOOLS_DIR / "retrieval_events.py"
    )
    retrieval_events_mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_gateway_mcp_test_retrieval_events"] = retrieval_events_mod
    spec.loader.exec_module(retrieval_events_mod)

    spies = {}
    for name in ("wrap_hybrid_retrieval", "wrap_retrieval_cache_check", "wrap_context_packet_assembly"):
        spy = MagicMock()
        monkeypatch.setattr(retrieval_events_mod, name, spy)
        spies[name] = spy

    _mod._run_knowledge_context("what is the damage formula")
    _mod._run_knowledge_status()

    for name, spy in spies.items():
        assert spy.call_count == 0, f"{name} must never be invoked from this ticket's real call site"

    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD", "--", "tools/retrieval_events.py"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    assert result.stdout == "", "tools/retrieval_events.py must be fully frozen for this ticket"


# ---------------------------------------------------------------------------
# 8 — exactly {knowledge_context, knowledge_status} registered (AC #5)
# ---------------------------------------------------------------------------

def test_only_knowledge_context_and_knowledge_status_registered():
    server = _mod._build_server()
    registered = set(server._tool_manager._tools.keys())
    assert registered == {"knowledge_context", "knowledge_status"}


# ---------------------------------------------------------------------------
# 9 — router/assembler failure passes through unswallowed
# ---------------------------------------------------------------------------

def test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing(monkeypatch):
    router_mod = _mod._load_router_module()
    pa_mod = _mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fake_decision = SimpleNamespace(providers_selected=["context_search"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(pa_search_mod, "_run_search", lambda q: {"error": "index not found"})

    response = _mod._run_knowledge_context("some query")
    assert response["status"] == "PARTIAL"
    _validate_response(response)


# ---------------------------------------------------------------------------
# 10 — never null for typed-string fields (context/evidence path/authority)
# ---------------------------------------------------------------------------

def test_knowledge_context_omits_null_path_and_authority_never_returns_null_for_typed_string_fields(
    monkeypatch,
):
    router_mod = _mod._load_router_module()
    pa_mod = _mod._load_packet_assembly_module()
    pa_router_mod = pa_mod._load_router_module()

    fake_decision = SimpleNamespace(providers_selected=["graphify"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(
        pa_router_mod,
        "match_symbol_name",
        lambda q: {"symbol": q, "returncode": 0, "stdout": "graphify traversal output"},
    )

    response = _mod._run_knowledge_context("some_symbol")
    _validate_response(response)

    graphify_context_entries = [c for c in response["context"] if c["kind"] == "graphify"]
    assert graphify_context_entries, "expected at least one graphify-sourced context entry"
    for entry in graphify_context_entries:
        assert "path" not in entry
        assert "authority" not in entry

    assert response["evidence"], "expected at least one graphify-sourced evidence entry"
    for entry in response["evidence"]:
        assert "path" not in entry


# ---------------------------------------------------------------------------
# 11 — AC1: identical repeated call is a genuine cache hit
# (TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING)
# ---------------------------------------------------------------------------

def _patch_small_cacheable_search(monkeypatch, matched_identifier=None):
    """Shared scaffold: a real routing decision shape (matched_identifier included, unlike tests
    9/10's deliberately-partial SimpleNamespace) plus a small, real-shaped context_search result
    that stays comfortably under the §5 8KB redacted-payload cap so a real cache write succeeds."""
    router_mod = _mod._load_router_module()
    pa_mod = _mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fake_decision = SimpleNamespace(
        providers_selected=["context_search"], matched_identifier=matched_identifier
    )
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)

    search_calls = []

    def spy(q):
        search_calls.append(q)
        return [{"excerpt": "a short, cacheable answer", "source_path": "docs/foo.md"}]

    monkeypatch.setattr(pa_search_mod, "_run_search", spy)
    return search_calls


def test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit(monkeypatch):
    """TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING (test_plan.md's own flagged
    re-verification note): Level 2 is now checked before Level 1, so an unmodified repeat call
    would become a Level 2 hit instead, no longer exercising this test's own original Level 1
    intent. Level 2's lookup is forced to always miss here so this test continues to demonstrate
    Level 1's own unmodified hit behavior specifically — the dedicated Level 2 version lives in
    test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit."""
    kgc_mod = _mod._load_cache_module()
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)
    search_calls = _patch_small_cacheable_search(monkeypatch)

    response1 = _mod._run_knowledge_context("some cache query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    response2 = _mod._run_knowledge_context("some cache query")
    assert response2["cache"] == "HIT"
    assert len(search_calls) == 1, "the second identical call must never reach _run_search() again"
    assert response2["answer"] == response1["answer"]
    _validate_response(response2)


# ---------------------------------------------------------------------------
# 12 — AC2: cache hit rejected/refreshed on a real corpus_generation bump
# (PROVIDER_GENERATION-level — the only fingerprint-mismatch path either real live provider can
# exercise today; see plan.md/investigation.md Risks item 2. The SYMBOL/FILE-kind path is
# fixture-tested in tests/tools/test_knowledge_gateway_cache.py, not here.)
# ---------------------------------------------------------------------------

def test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists(monkeypatch):
    from tools import retrieval_cache as rc

    search_calls = _patch_small_cacheable_search(monkeypatch)

    rc._MANIFEST_PATH.write_text(json.dumps({"version": 1, "built_at": "gen-1", "paths": {}}))
    response1 = _mod._run_knowledge_context("generation query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    rc._MANIFEST_PATH.write_text(json.dumps({"version": 1, "built_at": "gen-2", "paths": {}}))
    response2 = _mod._run_knowledge_context("generation query")
    assert response2["cache"] == "MISS", "a corpus_generation bump must force a genuine refresh"
    assert len(search_calls) == 2


# ---------------------------------------------------------------------------
# 13 — AC4: branch/working-tree scope is real
# ---------------------------------------------------------------------------

def test_cached_result_from_feature_branch_not_served_on_different_branch(monkeypatch):
    """Level 2's lookup is forced to always miss (see
    test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit's own note above) so
    this test continues to demonstrate Level 1's own unmodified branch-scope behavior specifically
    — the dedicated Level 2 version lives in
    test_level2_cached_result_from_feature_branch_not_served_on_different_branch."""
    kgc_mod = _mod._load_cache_module()
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)
    search_calls = _patch_small_cacheable_search(monkeypatch)

    monkeypatch.setattr(kgc_mod, "_current_repo_branch_scope", lambda: "repo::feature-x")
    response1 = _mod._run_knowledge_context("branch query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    monkeypatch.setattr(kgc_mod, "_current_repo_branch_scope", lambda: "repo::main")
    response2 = _mod._run_knowledge_context("branch query")
    assert response2["cache"] == "MISS", "a cached result from a different branch must never be served"
    assert len(search_calls) == 2


def test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged(monkeypatch):
    """§5 rule 1 — this ticket's identity/validity computation never derives from HEAD commit SHA
    at all (only branch name, via _current_repo_branch_scope()), so a real hit persists across
    repeated calls with no commit-tracking anywhere to force a miss. Level 2's lookup is forced to
    always miss so this test continues to demonstrate Level 1's own unmodified behavior
    specifically (see test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit's own
    note above)."""
    kgc_mod = _mod._load_cache_module()
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)
    search_calls = _patch_small_cacheable_search(monkeypatch)

    response1 = _mod._run_knowledge_context("commit-stable query")
    assert response1["cache"] == "MISS"

    response2 = _mod._run_knowledge_context("commit-stable query")
    assert response2["cache"] == "HIT"
    assert len(search_calls) == 1


# ---------------------------------------------------------------------------
# 14 — AC5: cache writes go through the redaction write-path
# ---------------------------------------------------------------------------

def test_cache_write_calls_evaluate_write_candidate_before_any_insert(monkeypatch):
    """TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING (Risk 6, double-write on a genuine
    full miss): evaluate_write_candidate is now called twice on a real full miss — once for the
    Level 2 write (which runs first) and once for the Level 1 write immediately after — both
    calls happen before Level 1's own real INSERT, so the original single-call assertion is
    updated to [1, 1] rather than silently left asserting a now-false [1]."""
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    calls = []
    original = kgc_mod.rk.evaluate_write_candidate

    def spy(*args, **kwargs):
        calls.append(1)
        assert rc.provider_result_cache_stats()["total_rows"] == 0, (
            "evaluate_write_candidate must be called before any real Level 1 INSERT"
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(kgc_mod.rk, "evaluate_write_candidate", spy)

    _mod._run_knowledge_context("redaction-gated query")
    assert calls == [1, 1]
    assert rc.provider_result_cache_stats()["total_rows"] == 1


def test_cache_write_reject_verdict_results_in_zero_rows_written(monkeypatch):
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    reject_decision = kgc_mod.rk.WriteDecision(
        verdict=kgc_mod.rk.REJECT, rejection_category="oversized_payload",
        redacted_payload=None, redacted_hash=None, redaction_policy_version=1,
    )
    monkeypatch.setattr(kgc_mod.rk, "evaluate_write_candidate", lambda **kw: reject_decision)

    response = _mod._run_knowledge_context("rejected query")
    assert response["cache"] == "MISS"
    assert rc.provider_result_cache_stats()["total_rows"] == 0


# ---------------------------------------------------------------------------
# 15 — AC6: knowledge_status's cache-domain fields are real and populated
# ---------------------------------------------------------------------------

def test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes(monkeypatch):
    """Level 2's lookup is forced to always miss so this test continues to demonstrate Level 1's
    own unmodified cache_entry_counts/rate fields specifically (a real Level 2 hit on the second
    call would otherwise mean Level 1's own hit-recording is never reached at all — see
    test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit's own note above). The
    dedicated Level 2/Level 1-distinct version lives in
    test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1."""
    kgc_mod = _mod._load_cache_module()
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_write", lambda *a, **k: None)
    search_calls = _patch_small_cacheable_search(monkeypatch)

    _mod._run_knowledge_context("status query")  # MISS + real write
    _mod._run_knowledge_context("status query")  # genuine HIT
    assert len(search_calls) == 1

    status = _mod._run_knowledge_status()
    _validate_status_response(status)
    assert status["cache_entry_counts"] == [{"kind": "provider_result", "count": 1}]
    assert status["cache_hit_rate"] == 0.5
    assert status["cache_miss_rate"] == 0.5
    assert status["cache_stale_rejection_rate"] == 0.0
    assert "latency_summary_ms" not in status
    assert "provider_fallback_rate" not in status


# ---------------------------------------------------------------------------
# 16 — fail-open: a cache-layer failure never prevents the direct provider path from succeeding
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 17/18 — TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT: budget-truncation marker
# ---------------------------------------------------------------------------

def test_knowledge_context_response_schema_accepts_new_budget_marker_field(monkeypatch):
    router_mod = _mod._load_router_module()
    pa_mod = _mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fake_decision = SimpleNamespace(providers_selected=["context_search"], matched_identifier=None)
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)

    text_a = "first statement text that costs some real budget"
    text_b = "second statement text that costs additional real budget beyond the first"
    monkeypatch.setattr(
        pa_search_mod,
        "_run_search",
        lambda q: [
            {"excerpt": text_a, "source_path": "docs/a.md"},
            {"excerpt": text_b, "source_path": "docs/b.md"},
        ],
    )

    cost_a = pa_mod.kgmcp_char_heuristic_v1(text_a.strip())
    response = _mod._run_knowledge_context("budget marker query", budget_tokens=cost_a)
    _validate_response(response)
    assert response["budget_truncated"] is True
    assert response["omitted_statement_count"] == 1


def test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker(monkeypatch):
    router_mod = _mod._load_router_module()
    pa_mod = _mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fake_decision = SimpleNamespace(providers_selected=["context_search"], matched_identifier=None)
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(
        pa_search_mod,
        "_run_search",
        lambda q: [{"excerpt": "a short answer that fits easily", "source_path": "docs/a.md"}],
    )

    response = _mod._run_knowledge_context("not truncated query", budget_tokens=10_000)
    _validate_response(response)
    assert response["budget_truncated"] is False
    assert response["omitted_statement_count"] == 0


def test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path(monkeypatch):
    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated cache-layer failure")

    monkeypatch.setattr(kgc_mod, "perform_cache_lookup", boom)
    monkeypatch.setattr(kgc_mod, "perform_cache_write", boom)

    response = _mod._run_knowledge_context("fail-open query")
    assert response["status"] == "OK"
    assert response["cache"] == "MISS"
    _validate_response(response)


# ---------------------------------------------------------------------------
# 19+ — TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING: Level 2 (assembled-packet) cache
# lookup/write wired in front of Level 1, checked first.
# ---------------------------------------------------------------------------

def test_level2_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path(monkeypatch):
    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated Level 2 cache-layer failure")

    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", boom)
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_write", boom)

    response = _mod._run_knowledge_context("level2 fail-open query")
    assert response["status"] == "OK"
    assert response["cache"] == "MISS"
    _validate_response(response)


# --- Cross-cutting: Risk 6 double-write *independence* — plan.md Step 5(b) explicitly keeps the
# Level 2 and Level 1 cache-write hooks in their own separate try/except blocks "so a Level 2
# write failure can never suppress the Level 1 write, and vice versa." The fail-open tests above
# only prove the overall response still succeeds when *both* levels fail together; these two
# prove each write is genuinely independent of the other's failure, not merely that the request
# as a whole degrades gracefully. ---

def test_level2_write_failure_does_not_prevent_or_corrupt_the_level1_write(monkeypatch):
    """plan.md Step 5(b): the Level 2 write hook's own try/except must not suppress the Level 1
    write hook immediately after it. Breaking only the Level 2 write must still leave exactly one
    real Level 1 row written."""
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated Level 2 write failure")

    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_write", boom)

    response = _mod._run_knowledge_context("level2 write failure independence query")
    assert response["status"] == "OK"
    assert response["cache"] == "MISS"
    _validate_response(response)
    assert rc.context_packet_cache_stats()["total_rows"] == 0, (
        "the simulated Level 2 write failure must mean no Level 2 row was written"
    )
    assert rc.provider_result_cache_stats()["total_rows"] == 1, (
        "a Level 2 write failure must never prevent or corrupt the independent Level 1 write"
    )


def test_level1_write_failure_does_not_prevent_or_corrupt_the_level2_write(monkeypatch):
    """The reverse of the test above: breaking only the Level 1 write (which runs second, after
    the Level 2 write hook) must not retroactively corrupt or roll back the Level 2 row that was
    already independently written first."""
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    def boom(*args, **kwargs):
        raise RuntimeError("simulated Level 1 write failure")

    monkeypatch.setattr(kgc_mod, "perform_cache_write", boom)

    response = _mod._run_knowledge_context("level1 write failure independence query")
    assert response["status"] == "OK"
    assert response["cache"] == "MISS"
    _validate_response(response)
    assert rc.provider_result_cache_stats()["total_rows"] == 0, (
        "the simulated Level 1 write failure must mean no Level 1 row was written"
    )
    assert rc.context_packet_cache_stats()["total_rows"] == 1, (
        "a Level 1 write failure must never prevent or corrupt the independent Level 2 write "
        "that already happened before it in the call sequence"
    )


# --- AC1: identical repeated call is a genuine Level 2 hit, never reaching packet assembly or
# the Level 1 lookup at all ---

def test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit(monkeypatch):
    kgc_mod = _mod._load_cache_module()
    pa_mod = _mod._load_packet_assembly_module()
    search_calls = _patch_small_cacheable_search(monkeypatch)

    response1 = _mod._run_knowledge_context("level2 repeat query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    assemble_calls = []
    original_assemble = pa_mod.assemble_packet
    monkeypatch.setattr(
        pa_mod, "assemble_packet",
        lambda *a, **k: assemble_calls.append(1) or original_assemble(*a, **k),
    )
    lookup_calls = []
    original_lookup = kgc_mod.perform_cache_lookup
    monkeypatch.setattr(
        kgc_mod, "perform_cache_lookup",
        lambda *a, **k: lookup_calls.append(1) or original_lookup(*a, **k),
    )

    response2 = _mod._run_knowledge_context("level2 repeat query")
    assert response2["cache"] == "HIT_L2"
    assert len(search_calls) == 1, "the second identical call must never reach _run_search() again"
    assert assemble_calls == [], "a genuine Level 2 hit must never reach assemble_packet()"
    assert lookup_calls == [], "a genuine Level 2 hit must never reach the Level 1 lookup at all"
    assert response2["answer"] == response1["answer"]
    _validate_response(response2)


# --- AC2: a Level 2 miss correctly falls through to Level 1's existing, unmodified lookup ---

def test_level2_miss_falls_through_to_unmodified_level1_lookup(monkeypatch):
    kgc_mod = _mod._load_cache_module()
    pa_mod = _mod._load_packet_assembly_module()
    search_calls = _patch_small_cacheable_search(monkeypatch)

    response1 = _mod._run_knowledge_context("level2 fallthrough query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    # Forces a genuine Level 2 miss on the second call (never matches), leaving the real Level 1
    # row (written by the first call above) as the only real hit candidate.
    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)

    lookup_calls = []
    original_lookup = kgc_mod.perform_cache_lookup
    monkeypatch.setattr(
        kgc_mod, "perform_cache_lookup",
        lambda *a, **k: lookup_calls.append(1) or original_lookup(*a, **k),
    )
    assemble_calls = []
    original_assemble = pa_mod.assemble_packet
    monkeypatch.setattr(
        pa_mod, "assemble_packet",
        lambda *a, **k: assemble_calls.append(1) or original_assemble(*a, **k),
    )

    response2 = _mod._run_knowledge_context("level2 fallthrough query")
    assert response2["cache"] == "HIT", "Level 1's own unmodified lookup must serve the hit"
    assert lookup_calls == [1], "Level 1's perform_cache_lookup() must be consulted on a Level 2 miss"
    assert assemble_calls == [], "a genuine Level 1 hit must never reach assemble_packet()"
    assert len(search_calls) == 1


# --- AC3: a Level 2 hit is rejected/refreshed when dependency-invalidation logic determines it
# stale ---

def test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh(monkeypatch):
    search_calls = _patch_small_cacheable_search(monkeypatch)

    response1 = _mod._run_knowledge_context("level2 changed paths query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    response2 = _mod._run_knowledge_context(
        "level2 changed paths query", changed_paths=["docs/foo.md"]
    )
    assert response2["cache"] == "MISS", (
        "a changed_paths intersection with the packet's own evidence_dependencies must force a "
        "genuine refresh, never a stale Level 2 hit"
    )
    assert len(search_calls) == 2


def test_level2_hit_rejected_on_provider_generation_bump_real_call(monkeypatch):
    from tools import retrieval_cache as rc

    search_calls = _patch_small_cacheable_search(monkeypatch)

    rc._MANIFEST_PATH.write_text(json.dumps({"version": 1, "built_at": "gen-1", "paths": {}}))
    response1 = _mod._run_knowledge_context("level2 generation query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    rc._MANIFEST_PATH.write_text(json.dumps({"version": 1, "built_at": "gen-2", "paths": {}}))
    response2 = _mod._run_knowledge_context("level2 generation query")
    assert response2["cache"] == "MISS", (
        "a corpus_generation bump must force a genuine Level 2 refresh"
    )
    assert len(search_calls) == 2


# --- AC4: Level 2 cache writes independently verified to go through redaction/secret-scan/
# size-cap enforcement, no bypass path ---

def test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert(monkeypatch):
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    calls = []
    original = kgc_mod.rk.evaluate_write_candidate

    def spy(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            assert rc.context_packet_cache_stats()["total_rows"] == 0, (
                "evaluate_write_candidate must be called before any real Level 2 INSERT"
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(kgc_mod.rk, "evaluate_write_candidate", spy)

    _mod._run_knowledge_context("level2 redaction-gated query")
    assert len(calls) == 2, (
        "evaluate_write_candidate must be called once for the Level 2 write and once for the "
        "Level 1 write"
    )
    assert rc.context_packet_cache_stats()["total_rows"] == 1


def test_level2_write_reject_verdict_results_in_zero_rows_written(monkeypatch):
    from tools import retrieval_cache as rc

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    reject_decision = kgc_mod.rk.WriteDecision(
        verdict=kgc_mod.rk.REJECT, rejection_category="oversized_payload",
        redacted_payload=None, redacted_hash=None, redaction_policy_version=1,
    )
    monkeypatch.setattr(kgc_mod.rk, "evaluate_write_candidate", lambda **kw: reject_decision)

    response = _mod._run_knowledge_context("level2 rejected query")
    assert response["cache"] == "MISS"
    assert rc.context_packet_cache_stats()["total_rows"] == 0


def test_level2_write_respects_max_payload_bytes_size_cap_with_real_measured_packet(monkeypatch):
    from tools import knowledge_gateway_redaction as rk

    kgc_mod = _mod._load_cache_module()
    _patch_small_cacheable_search(monkeypatch)

    measured_sizes = []
    original_check = rk.check_size_cap

    def spy(redacted_payload):
        measured_sizes.append(len(redacted_payload.encode("utf-8")))
        return original_check(redacted_payload)

    monkeypatch.setattr(kgc_mod.rk, "check_size_cap", spy)

    _mod._run_knowledge_context("level2 real size measurement query")

    assert measured_sizes, "the size-cap check must have run for the real Level 2 write"
    assert measured_sizes[0] <= rk.MAX_PAYLOAD_BYTES, (
        f"real assembled Level 2 packet measured at {measured_sizes[0]} bytes must stay under "
        f"MAX_PAYLOAD_BYTES ({rk.MAX_PAYLOAD_BYTES})"
    )


# --- AC5: branch/working-tree scope from the dependency ticket is genuinely enforced before a
# Level 2 hit is served ---

def test_level2_cached_result_from_feature_branch_not_served_on_different_branch(monkeypatch):
    kgc_mod = _mod._load_cache_module()
    search_calls = _patch_small_cacheable_search(monkeypatch)

    monkeypatch.setattr(kgc_mod, "_current_branch", lambda: "feature-x")
    response1 = _mod._run_knowledge_context("level2 branch query")
    assert response1["cache"] == "MISS"
    assert len(search_calls) == 1

    monkeypatch.setattr(kgc_mod, "_current_branch", lambda: "main")

    original_lookup = kgc_mod.perform_context_packet_cache_lookup
    lookup_results = []

    def spy(*args, **kwargs):
        result = original_lookup(*args, **kwargs)
        lookup_results.append(result)
        return result

    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", spy)

    _mod._run_knowledge_context("level2 branch query")
    assert lookup_results == [None], (
        "the real Level 2 lookup orchestrator must reject a row written under a different branch, "
        "never serve it as a genuine hit"
    )


# --- AC6: knowledge_status's Level 2 cache-domain fields are real and populated, distinct from
# Level 1's ---

def test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1(
    monkeypatch,
):
    kgc_mod = _mod._load_cache_module()
    search_calls = _patch_small_cacheable_search(monkeypatch)

    _mod._run_knowledge_context("status level2 query")               # MISS -> writes L1 + L2
    hit1 = _mod._run_knowledge_context("status level2 query")        # genuine L2 hit
    hit2 = _mod._run_knowledge_context("status level2 query")        # genuine L2 hit again
    assert hit1["cache"] == "HIT_L2"
    assert hit2["cache"] == "HIT_L2"
    assert len(search_calls) == 1

    monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a, **k: None)
    _mod._run_knowledge_context("status level1 only query")          # MISS -> writes L1 (+ L2 row)
    hit3 = _mod._run_knowledge_context("status level1 only query")   # Level1-only hit (L2 forced miss)
    assert hit3["cache"] == "HIT"
    assert len(search_calls) == 2

    status = _mod._run_knowledge_status()
    _validate_status_response(status)

    kinds = {entry["kind"]: entry["count"] for entry in status["cache_entry_counts"]}
    assert kinds["provider_result"] == 2
    assert kinds["context_packet"] == 2

    assert status["cache_hit_rate"] == pytest.approx(1 / 3)
    assert status["level2_cache_hit_rate"] == pytest.approx(2 / 4)
    assert status["cache_hit_rate"] != status["level2_cache_hit_rate"], (
        "Level 2's hit rate must be a real, independently-computed value, never an alias of "
        "Level 1's own rate"
    )
    assert status["cache_hit_attribution"] == {"level1_hits": 1, "level2_hits": 2}


def test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows():
    status = _mod._run_knowledge_status()
    assert "level2_cache_hit_rate" not in status
    assert "level2_cache_miss_rate" not in status
    assert "cache_hit_attribution" not in status
    assert "cache_entry_counts" not in status


# `test_knowledge_gateway_router_py_provably_untouched` (AC7 of
# TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING) was removed by
# TCK-20260816-KGMCP-P4-PARITY-ADAPTER. History: that guard asserted
# `tools/knowledge_gateway_router.py` stays byte-unchanged forever, for that ticket's own scope
# boundary. TCK-20260816-KGMCP-P4-PARITY-ADAPTER's own twice-Architecture-Review-approved plan
# requires editing exactly that file (`_run_parity_provider()`, `_load_parity_index_module()`,
# `ROUTING_TABLE["requirement_completeness_verification"]`'s real `parity_ledger` primary
# provider) — the same reasoning `test_search_mcp_py_provably_untouched` above already applies to
# dropping this same path from its own banned-path tuple. No file remains that this specific,
# single-purpose guard's reasoning still protects, so the test was deleted rather than left
# vacuously/dangerously asserting an invariant this ticket's own approved scope deliberately
# breaks. `tools/knowledge_gateway_router.py`'s real, still-relevant behavioral contracts remain
# covered by its own full test suite (`tests/tools/test_knowledge_gateway_router.py`).


# --- Cross-cutting: Risk 6 double-write question ---

def test_level2_double_write_on_full_miss_writes_both_level1_and_level2_rows(monkeypatch):
    from tools import retrieval_cache as rc

    _patch_small_cacheable_search(monkeypatch)
    _mod._run_knowledge_context("double write query")
    assert rc.provider_result_cache_stats()["total_rows"] == 1
    assert rc.context_packet_cache_stats()["total_rows"] == 1
