"""Fail-open and failure-semantics test matrix for the Knowledge Gateway MCP Phase 1
(TCK-20260815-KGMCP-P1-FAILOPEN-TESTS).

`docs/plans/knowledge-gateway-mcp-proposal.md` §16 defines 7 failure rows and states the gateway
"is never a correctness dependency." This file proves the 5 Phase-1-applicable rows against the
real gateway built by TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE, TCK-20260815-KGMCP-P1-QUERY-ROUTER,
and TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY, rather than trusting those tickets' own happy-path
tests to have covered failure semantics as a side effect.

Deliberately not tested here (documented deferral, not a vacuous test standing in for real
behavior — per this ticket's AC #2 anti-pattern rule):

- **Graphify stale** (§16 row 4) — no code anywhere in this pipeline computes or compares a
  staleness/generation-fingerprint signal. `freshness` is a hardcoded literal `"UNKNOWN"` at
  `tools/knowledge_gateway_packet_assembly.py:643` (confirmed by reading the whole module — no
  other line reads or writes any freshness-adjacent state). There is no real behavior to prove; a
  test that monkeypatches a capability-descriptor field and asserts nothing observably different
  happens would be the exact vacuous-test anti-pattern this ticket's AC forbids.
- **Context Search stale** (§16 row 5) — identical finding and identical reason as Graphify
  stale above (same hardcoded `"UNKNOWN"` literal governs both providers; there is exactly one
  `freshness` computation site in the whole pipeline, not one per provider).
- **Cache missing or corrupt** (§16 row 1) — pre-authorized as Phase-2-only by this ticket's own
  Scope. No cache read/write path exists anywhere in `tools/knowledge_gateway_packet_assembly.py`
  today, confirmed by that module's own existing guard test
  `tests/tools/test_knowledge_gateway_packet_assembly.py::test_module_does_not_modify_or_import_retrieval_cache`
  (asserts `"retrieval_cache" not in source` and `"sqlite3" not in source`). A "there is no cache,
  so trivially no cache can be corrupt" test would pass for the wrong reason.
- **Cached evidence mismatch** (§16 row 2) — same disposition and same evidence as "Cache missing
  or corrupt" above; both rows depend on cache-identity machinery
  (`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §4) that does
  not exist in Phase 1.

Building real staleness-detection or cache-identity logic to make these 4 rows testable would be
new-feature work ("building the gateway"), categorically different from this ticket's actual job
of surfacing already-computed data (see plan.md Design Decisions D1/D2) — that is
TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE's job in a later phase, not this ticket's.

Mirrors the existing `tests/tools/test_knowledge_gateway_*.py` flat-file,
`importlib.util`-loading convention (no `conftest.py`/subpackage magic).
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_MCP_MODULE_PATH = _TOOLS_DIR / "archive" / "knowledge_gateway_mcp.py"

# A stable, made-up single-identifier-shaped string: not a ticket id, not a parity id, not an
# existing repo-relative path, not a registered doc path, not a subsystem id — reaches
# `_match_identifier()`'s symbol-shape branch inside `route()` (the router-internal call site).
_BARE_SYMBOL_SHAPED_QUERY = "some_kgmcp_nonexistent_symbol_zzq"

# A multi-word, `symbol_lookup_callers_references`-shape-classified query — is never
# identifier-shaped (contains whitespace), so `route()` never calls `match_symbol_name()`
# internally; the graphify call happens only inside `call_providers_for_routing_decision()`
# (the packet-assembly call site).
_SHAPE_CLASSIFIED_GRAPHIFY_QUERY = "where is X defined"


# ---------------------------------------------------------------------------
# Section A — gateway process unavailable (§16 row 1): pure subprocess/static checks.
# Deliberately does not reference `_load_mcp_module`/`kg_mod` anywhere in this section — the
# whole point is proving the fallback tools work with the gateway module never touched by
# these tests' own subprocess calls (each spawns a fresh interpreter/binary that never
# inherits this pytest process's `sys.modules`).
# ---------------------------------------------------------------------------

def test_gateway_down_search_mcp_test_mode_still_works():
    """Mirrors the `mcp-server-test` Makefile target's own invocation shape exactly
    (`Makefile:380-382`)."""
    sys.path.insert(0, str(_TOOLS_DIR))
    from search_mcp import _DB_PATH
    if not _DB_PATH.exists():
        pytest.skip("knowledge index not built — run make knowledge-index")

    result = subprocess.run(
        [sys.executable, "tools/search_mcp.py", "--test"],
        input=json.dumps({"query": "damage formula", "top_k": 3}),
        text=True,
        capture_output=True,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    parsed = json.loads(result.stdout)
    assert parsed


def test_gateway_down_graphify_cli_still_works():
    """`"assemble_packet"` is a real, stable symbol name from this ticket's own subject module —
    safe to hardcode (verified live: `graphify query "assemble_packet"` returns 18+ result
    lines)."""
    if shutil.which("graphify") is None:
        pytest.skip("graphify CLI not installed in this environment")
    if not (_REPO_ROOT / "graphify-out" / "graph.json").exists():
        # graphify-out/ is gitignored and no CI step builds it (this file's own docstring and
        # tests/tools/test_code_test_index.py both establish this suite never depends on the
        # real, live 41.9MB graphify-out/graph.json). This test's actual purpose (see its own
        # docstring above) is proving graphify CLI's independence from the Knowledge Gateway,
        # not proving graphify's own index-building -- skip gracefully rather than treat a
        # not-yet-built index as this test's own failure, matching the graphify-binary-missing
        # skip above for the same class of "prerequisite infrastructure isn't present" reason.
        pytest.skip("graphify-out/graph.json not built in this environment (run /graphify first)")

    result = subprocess.run(
        ["graphify", "query", "assemble_packet"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip()


def test_neither_provider_tool_imports_knowledge_gateway_mcp():
    """The structural guarantee underlying the two subprocess smoke tests above: `search_mcp.py`
    never references any Knowledge Gateway module for any legitimate reason."""
    source = (_TOOLS_DIR / "search_mcp.py").read_text()
    for banned in (
        "knowledge_gateway_mcp",
        "knowledge_gateway_router",
        "knowledge_gateway_packet_assembly",
    ):
        assert banned not in source


# ---------------------------------------------------------------------------
# Shared loading/validation helpers for Sections B/C — deliberately NOT invoked at module import
# time (only inside a module-scoped fixture), so nothing in this file imports
# `knowledge_gateway_mcp`/`_router`/`_packet_assembly` until a test that actually needs it runs.
# ---------------------------------------------------------------------------

def _load_mcp_module():
    spec = importlib.util.spec_from_file_location(
        "knowledge_gateway_failure_semantics_mcp", _MCP_MODULE_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_gateway_failure_semantics_mcp"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def kg_mod():
    return _load_mcp_module()


@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    """Added by TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING — this file's real
    `_run_knowledge_context()` calls now genuinely read/write the Level 1 provider-result cache
    (previously a no-op before this ticket). Mirrors `tests/tools/test_knowledge_gateway_mcp.py`'s
    own `_isolated_cache_db` fixture (DD14) so this file's tests never touch the real on-disk
    `knowledge-index/retrieval_cache.db`, and so the repeated same-query calls in
    `test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result` cannot be served
    a stale cross-run cached row."""
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


def _context_search_index_missing_response(kg_mod, monkeypatch) -> dict:
    router_mod = kg_mod._load_router_module()
    pa_mod = kg_mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fake_decision = SimpleNamespace(providers_selected=["context_search"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(pa_search_mod, "_run_search", lambda q: {"error": "index not found"})

    return kg_mod._run_knowledge_context("some query")


def _graphify_succeeds_alone_response(kg_mod, monkeypatch) -> dict:
    """A second, independently deterministic non-empty-statements scenario for Section C's
    structural guard — deliberately does NOT call the real, live `_run_search()` (unlike a bare
    'real end-to-end query' would), because `tests/tools/test_search_mcp.py` stubs
    `sys.modules["knowledge_search"]` with a `MagicMock` at ITS OWN module import time (its own
    file's comment: 'do NOT stub sentence_transformers/sqlite_vec at module level to avoid
    poisoning other test files' — `knowledge_search` itself was missed by that same guard). Since
    `sys.modules` is process-global and un-teardown'd, any test file collected after
    `test_search_mcp.py` in the same pytest session would see a live index query silently return
    empty results — exactly the flaky, collection-order-dependent behavior this repo's Testing
    Rule forbids. Every scenario in this file therefore drives content through the same
    monkeypatch boundary the rest of this suite already uses, never the live index."""
    router_mod = kg_mod._load_router_module()
    pa_mod = kg_mod._load_packet_assembly_module()
    pa_router_mod = pa_mod._load_router_module()

    fake_decision = SimpleNamespace(providers_selected=["graphify"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(
        pa_router_mod,
        "match_symbol_name",
        lambda q: {
            "symbol": q,
            "returncode": 0,
            "stdout": "UNIQUE_GRAPHIFY_ONLY_MARKER real graphify traversal output",
        },
    )

    return kg_mod._run_knowledge_context("some_symbol_query")


def _mixed_context_search_fails_graphify_succeeds_response(kg_mod, monkeypatch) -> dict:
    """One provider fails, one provider genuinely returns content — the honest shape of §16's
    "partial result with explicit provider failure" row (a pure single-provider-failure scenario
    with zero surviving providers never actually demonstrates 'partial', only 'empty')."""
    router_mod = kg_mod._load_router_module()
    pa_mod = kg_mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()
    pa_router_mod = pa_mod._load_router_module()

    fake_decision = SimpleNamespace(providers_selected=["context_search", "graphify"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(pa_search_mod, "_run_search", lambda q: {"error": "index not found"})
    monkeypatch.setattr(
        pa_router_mod,
        "match_symbol_name",
        lambda q: {"symbol": q, "returncode": 0, "stdout": "UNIQUE_MIXED_MARKER real graphify output"},
    )

    return kg_mod._run_knowledge_context("some query")


# ---------------------------------------------------------------------------
# Section B — one provider unavailable (§16 row 3): partial result with explicit provider
# failure, and "flag code-graph/docs result unavailable" as a real response field.
# ---------------------------------------------------------------------------

def test_context_search_index_missing_yields_partial_status_via_real_mcp_call(kg_mod, monkeypatch):
    response = _context_search_index_missing_response(kg_mod, monkeypatch)
    assert response["status"] == "PARTIAL"
    assert "context_search: index not found" in response["provider_failures"]
    _validate_response(response)


def test_provider_unavailable_is_a_real_response_field_not_silent_omission(kg_mod, monkeypatch):
    """This test's pass/fail outcome is the direct proof that Step 1/Step 2 of the plan closed
    the gap investigation.md's Risk 2 identified — must not be weakened to `status == "PARTIAL"`
    alone, which would just duplicate the test above."""
    response = _context_search_index_missing_response(kg_mod, monkeypatch)
    assert "provider_failures" in response
    assert isinstance(response["provider_failures"], list)
    assert response["provider_failures"]


def test_mixed_provider_failure_still_returns_real_content_from_surviving_provider(kg_mod, monkeypatch):
    response = _mixed_context_search_fails_graphify_succeeds_response(kg_mod, monkeypatch)
    assert response["status"] == "PARTIAL"
    assert "context_search: index not found" in response["provider_failures"]
    assert response["statements"], "the surviving provider's real content must not be dropped"
    assert any("UNIQUE_MIXED_MARKER" in s["text"] for s in response["statements"])
    _validate_response(response)


def test_graphify_subprocess_timeout_yields_partial_status(kg_mod, monkeypatch):
    """Monkeypatches `subprocess.run` at the router-module boundary — same point as
    `test_knowledge_gateway_router.py::test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table`.
    `subprocess` is a single global module object shared by every `import subprocess` call site
    in this repo, so patching one loaded router instance's `subprocess.run` patches it for all of
    them (the real router module, the packet-assembly-loaded instance, and this file's own
    imported `subprocess`)."""
    router_mod = kg_mod._load_router_module()

    def _fake_run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args, timeout=kwargs.get("timeout", 120))

    monkeypatch.setattr(router_mod.subprocess, "run", _fake_run)

    response = kg_mod._run_knowledge_context(_BARE_SYMBOL_SHAPED_QUERY)
    assert response["status"] == "PARTIAL"
    assert "graphify: subprocess timeout" in response["provider_failures"]
    _validate_response(response)


def test_graphify_binary_missing_via_router_internal_identifier_match(kg_mod, monkeypatch):
    """Variant 1 of 2 — a bare single-identifier query reaches `_match_identifier()`'s
    symbol-shape branch inside `route()` itself, which is *not* covered by the packet-assembly
    fix alone (Design Decision D3). Exercises Step 2's `try/except` around the `route(query)`
    call site in `knowledge_gateway_mcp.py`."""
    router_mod = kg_mod._load_router_module()

    def _fake_run(args, **kwargs):
        raise FileNotFoundError("graphify binary not found")

    monkeypatch.setattr(router_mod.subprocess, "run", _fake_run)

    response = kg_mod._run_knowledge_context(_BARE_SYMBOL_SHAPED_QUERY)
    assert response["status"] == "PARTIAL"
    assert "graphify: binary not found on PATH" in response["provider_failures"]
    _validate_response(response)


def test_graphify_binary_missing_via_packet_assembly_provider_call(kg_mod, monkeypatch):
    """Variant 2 of 2 — a shape-classified free-text query never calls `match_symbol_name()`
    inside `route()` itself (no whitespace-free identifier shape), so the same
    `FileNotFoundError` is instead raised inside
    `call_providers_for_routing_decision()`'s graphify branch — exercises Step 1's
    `except FileNotFoundError` clause in `knowledge_gateway_packet_assembly.py`."""
    router_mod = kg_mod._load_router_module()

    def _fake_run(args, **kwargs):
        raise FileNotFoundError("graphify binary not found")

    monkeypatch.setattr(router_mod.subprocess, "run", _fake_run)

    response = kg_mod._run_knowledge_context(_SHAPE_CLASSIFIED_GRAPHIFY_QUERY)
    assert response["status"] == "PARTIAL"
    assert "graphify: binary not found on PATH" in response["provider_failures"]
    _validate_response(response)


def test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result(kg_mod, monkeypatch):
    """The explicit, no-longer-vacuous proof that Step 1 distinguishes a real crash
    (non-zero returncode) from a legitimate 'found nothing' (returncode 0, empty stdout) —
    previously these were identical (investigation.md Risk 2)."""
    router_mod = kg_mod._load_router_module()

    class _FakeCompletedProcess:
        def __init__(self, returncode: int, stdout: str):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = ""

    monkeypatch.setattr(
        router_mod.subprocess, "run",
        lambda args, **kwargs: _FakeCompletedProcess(returncode=1, stdout=""),
    )
    response_crash = kg_mod._run_knowledge_context(_SHAPE_CLASSIFIED_GRAPHIFY_QUERY)
    assert "graphify: subprocess exited with code 1" in response_crash["provider_failures"]
    assert response_crash["status"] == "PARTIAL"

    monkeypatch.setattr(
        router_mod.subprocess, "run",
        lambda args, **kwargs: _FakeCompletedProcess(returncode=0, stdout=""),
    )
    response_empty = kg_mod._run_knowledge_context(_SHAPE_CLASSIFIED_GRAPHIFY_QUERY)
    assert response_empty["provider_failures"] == []


# ---------------------------------------------------------------------------
# Section C — token-budget assembly failure (§16 row 7) and the cross-cutting structural
# no-fabrication guard (AC #4).
# ---------------------------------------------------------------------------

def test_budget_assembly_failure_via_real_mcp_call_returns_smaller_list_not_fabricated(kg_mod, monkeypatch):
    router_mod = kg_mod._load_router_module()
    pa_mod = kg_mod._load_packet_assembly_module()
    pa_search_mod = pa_mod._load_search_mcp_module()

    fixed_result = {
        "doc_id": "chunk-1",
        "title": "Some Title",
        "heading": "Some Heading",
        "source_path": "docs/mechanics/02_combat_laws.md",
        "section": "",
        "score": 0.9,
        "semantic_score": 0.9,
        "keyword_score": 0.9,
        "excerpt": "UNIQUE_BUDGET_FAILURE_MARKER " + "x" * 500,
    }
    fake_decision = SimpleNamespace(providers_selected=["context_search"])
    monkeypatch.setattr(router_mod, "route", lambda q, requested_guarantee=None: fake_decision)
    monkeypatch.setattr(pa_search_mod, "_run_search", lambda q: [fixed_result])

    response = kg_mod._run_knowledge_context("some query", budget_tokens=1)

    assert response["statements"] == []
    assert response["budget_returned"] == 0
    assert response["status"] == "PARTIAL"
    assert response["evidence"], "real provider output must survive as evidence even when no statement fits"
    for entry in response["evidence"]:
        assert entry["evidence_hash"]
    _validate_response(response)


def _assert_response_statements_trace_to_real_evidence(response: dict) -> None:
    """The AC #4-mandated structural (not hardcoded-placeholder-string) fabrication guard —
    every returned statement's evidence_ids resolve to a real response['evidence'] entry.
    Adapted from `test_knowledge_gateway_packet_assembly.py`'s
    `_assert_answer_traces_to_statement_evidence()` helper to the response-dict shape."""
    evidence_ids = {e["evidence_id"] for e in response["evidence"]}
    for statement in response["statements"]:
        assert statement["evidence_ids"], f"{statement['statement_id']} has no evidence_ids"
        for evidence_id in statement["evidence_ids"]:
            assert evidence_id in evidence_ids, f"{evidence_id} missing from response['evidence']"


@pytest.mark.parametrize(
    "scenario_name",
    ["graphify_succeeds_alone", "mixed_context_search_fails_graphify_succeeds"],
)
def test_every_response_statement_traces_to_a_real_evidence_id_across_all_failure_modes(
    kg_mod, monkeypatch, scenario_name,
):
    """Parametrized over every scenario in this file that produces non-empty `statements`. The
    budget-assembly-failure scenario above always has `statements == []` by construction and is
    excluded, not skipped — it is not a candidate for this check, not a gap in it. A pure
    provider-unavailable scenario with zero surviving providers is also excluded for the same
    reason (see `_mixed_...` docstring) — real content is required to make this check non-vacuous."""
    if scenario_name == "graphify_succeeds_alone":
        response = _graphify_succeeds_alone_response(kg_mod, monkeypatch)
    else:
        response = _mixed_context_search_fails_graphify_succeeds_response(kg_mod, monkeypatch)

    assert response["statements"], (
        f"{scenario_name} scenario must produce non-empty statements to make this a "
        "non-vacuous structural check"
    )
    _assert_response_statements_trace_to_real_evidence(response)
