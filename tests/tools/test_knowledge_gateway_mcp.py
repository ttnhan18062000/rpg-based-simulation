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

_CACHE_SPECIFIC_FIELDS = {
    "cache_entry_counts",
    "cache_hit_rate",
    "cache_miss_rate",
    "cache_stale_rejection_rate",
    "recent_invalidation_reasons",
    "cache_rebuildable",
    "provider_fallback_rate",
}


def test_knowledge_status_omits_all_cache_specific_fields_enumerated():
    response = _mod._run_knowledge_status()

    for field in _CACHE_SPECIFIC_FIELDS:
        assert field not in response, f"{field} must be omitted, never a fabricated placeholder"

    # No real call site emits any latency data in Phase 1 (Design Decision D1/D5) — the entire
    # top-level key is omitted, not just its cache-domain sub-fields.
    assert "latency_summary_ms" not in response

    # The Phase-1-populable fields ARE present with real values — a pure absence-check alone
    # would not catch a broken implementation that omits everything.
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
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    for banned_path in (
        "tools/search_mcp.py",
        "tools/knowledge_gateway_router.py",
        "tools/knowledge_gateway_packet_assembly.py",
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
