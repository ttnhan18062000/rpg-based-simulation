"""Tests for tools/knowledge_gateway_router.py — the deterministic Knowledge Gateway MCP
query router (TCK-20260815-KGMCP-P1-QUERY-ROUTER).

Mirrors tests/tools/test_search_mcp.py's own flat-file module-loading precedent: no
`tools/`-subpackage `__init__.py` exists, so the module under test is loaded via
`importlib.util.spec_from_file_location`.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_ROUTER_PATH = _REPO_ROOT / "tools" / "archive" / "knowledge_gateway_router.py"
_CONTEXT_SEARCH_TEST_HELPER_PATH = (
    _REPO_ROOT / "tests" / "archive" / "test_knowledge_gateway_contract_schemas.py"
)


def _load_router_module():
    spec = importlib.util.spec_from_file_location("knowledge_gateway_router_test", _ROUTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_gateway_router_test"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_router_module()


def _load_contract_schemas_module():
    spec = importlib.util.spec_from_file_location(
        "knowledge_gateway_contract_schemas_crosscheck", _CONTEXT_SEARCH_TEST_HELPER_PATH
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. Stable-identifier recognition
# ---------------------------------------------------------------------------

def test_recognizes_real_ticket_id_from_tickets_done():
    done_dir = _REPO_ROOT / "tickets" / "done"
    real_ticket_ids = [p.stem for p in done_dir.glob("TCK-*.md")]
    assert real_ticket_ids, "expected at least one real TCK-* ticket in tickets/done/"
    sample = real_ticket_ids[0]
    assert _mod.match_ticket_id(sample) == sample

    # Legacy pre-convention name — expected to NOT match (current convention only).
    legacy_path = done_dir / "adjust-01-action-speed-balance.md"
    assert legacy_path.exists(), "fixture assumption: legacy ticket file must exist"
    assert _mod.match_ticket_id("adjust-01-action-speed-balance") is None


@pytest.mark.parametrize(
    "parity_id",
    ["INFRA-334", "COMB-001", "SOC-CHRON-001", "FACTION-TENSION-001"],
)
def test_recognizes_real_parity_id_across_multiple_shard_prefixes(parity_id):
    assert _mod.match_parity_id(parity_id) == parity_id


def test_recognizes_real_parity_id_shape_only_no_existence_check():
    # D1: shape-only match. A plausible-but-nonexistent ID is still classified as
    # parity_id-shaped — the router attaches no existence guarantee.
    assert _mod.match_parity_id("ZZZZ-9999") == "ZZZZ-9999"


def test_recognizes_real_source_path_and_rejects_traversal():
    assert _mod.match_source_path("tools/search_mcp.py") == "tools/search_mcp.py"
    assert _mod.match_source_path("tools/definitely_not_a_real_file.py") is None
    assert _mod.match_source_path("../../etc/passwd") is None
    assert _mod.match_source_path("/etc/passwd") is None


def test_symbol_name_delegates_to_graphify_cli_not_a_new_symbol_table(monkeypatch):
    captured = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return MagicMock(returncode=0, stdout="NODE some_symbol", stderr="")

    monkeypatch.setattr(_mod.subprocess, "run", fake_run)
    result = _mod.match_symbol_name("compute_search_investigation_trend")

    assert captured["args"] == ["graphify", "query", "compute_search_investigation_trend"]
    assert captured["kwargs"]["cwd"] == str(_mod._REPO_ROOT)
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["kwargs"]["timeout"] == 120
    assert "shell" not in captured["kwargs"] or captured["kwargs"]["shell"] is False
    assert result["symbol"] == "compute_search_investigation_trend"
    assert result["returncode"] == 0


def test_recognizes_real_registered_document_path_from_registry():
    registry_path = _REPO_ROOT / "docs" / "REGISTRY.yaml"
    text = registry_path.read_text()
    assert "docs/core/README.md" in text
    assert _mod.match_registered_doc_path("docs/core/README.md") == "docs/core/README.md"
    assert _mod.match_registered_doc_path("docs/not_a_real_registered_doc.md") is None


def test_recognizes_real_subsystem_layer_id_from_layer_registry():
    real_layers = _real_layers()
    assert "ai" in real_layers
    assert _mod.match_subsystem_id("ai") == "ai"
    assert _mod.match_subsystem_id("not_a_real_layer") is None


def _real_layers():
    layers = set()
    for line in (_REPO_ROOT / "registries" / "layer_registry.jsonl").read_text().splitlines():
        line = line.strip()
        if line:
            layers.add(json.loads(line)["layer"])
    return layers


def test_all_real_registered_layers_recognized():
    real_layers = _real_layers()
    assert len(real_layers) >= 5
    for layer in real_layers:
        assert _mod.match_subsystem_id(layer) == layer


# ---------------------------------------------------------------------------
# 2. §8 routing table — one test per row, using the real, versioned CORPUS queries
#    (tools/agent-monitoring/kgmcp_baseline_corpus.py::CORPUS) as grounding.
# ---------------------------------------------------------------------------

def test_router_shape_ids_match_baseline_corpus_routing_shapes():
    baseline_corpus = _mod._load_baseline_corpus_module()
    assert set(_mod.ROUTING_TABLE.keys()) == baseline_corpus.ROUTING_SHAPES
    assert _mod.ROUTING_SHAPES == baseline_corpus.ROUTING_SHAPES


def _corpus_entry(entry_id: str) -> dict:
    baseline_corpus = _mod._load_baseline_corpus_module()
    for entry in baseline_corpus.CORPUS:
        if entry["id"] == entry_id:
            return entry
    raise AssertionError(f"no CORPUS entry with id {entry_id!r}")


def test_routes_definition_terminology_architecture_to_context_search():
    entry = _corpus_entry("Q1_authoritative_state")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "definition_terminology_architecture"
    assert decision.providers_selected == ["context_search"]


def test_routes_symbol_dependency_path_to_graphify():
    entry = _corpus_entry("Q2_symbol_lookup")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "symbol_lookup_callers_references"
    assert decision.providers_selected == ["graphify"]


def test_routes_requirement_completeness_to_context_search_and_parity_ledger():
    entry = _corpus_entry("Q3_requirement_completeness")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "requirement_completeness_verification"
    assert decision.providers_selected == ["context_search", "parity_ledger"]
    assert decision.not_yet_routed is None


def test_routes_ticket_historical_rationale_to_context_search_ticket_index():
    entry = _corpus_entry("Q4_historical_rationale")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "ticket_historical_rationale"
    assert decision.providers_selected == ["context_search"]
    assert "working_log" in _mod.ROUTING_TABLE["ticket_historical_rationale"].optional_providers


def test_routes_test_impact_of_change_to_graphify_code_test_index():
    entry = _corpus_entry("Q5_test_impact")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "test_impact_of_change"
    assert decision.providers_selected == ["graphify"]


def test_routes_ticket_work_status_to_ticket_index():
    entry = _corpus_entry("Q6_ticket_status")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "ticket_work_status"
    assert decision.providers_selected == ["context_search"]


def test_routes_broad_task_context_to_multiple_providers():
    entry = _corpus_entry("Q7_negative_knowledge")
    decision = _mod.route(entry["query_text"])
    assert decision.routing_shape == "broad_task_context"
    assert len(decision.providers_selected) > 1
    assert set(decision.providers_selected) == {"context_search", "graphify"}


def test_ticket_id_identifier_routes_via_ticket_work_status_row():
    done_dir = _REPO_ROOT / "tickets" / "done"
    sample = next(iter(done_dir.glob("TCK-*.md"))).stem
    decision = _mod.route(sample)
    assert decision.matched_identifier is not None
    assert decision.matched_identifier.category == "ticket_id"
    assert decision.routing_shape == "ticket_work_status"


def test_parity_id_identifier_routes_via_requirement_completeness_row():
    decision = _mod.route("INFRA-334")
    assert decision.matched_identifier is not None
    assert decision.matched_identifier.category == "parity_id"
    assert decision.routing_shape == "requirement_completeness_verification"
    assert decision.providers_selected == ["context_search", "parity_ledger"]
    assert decision.not_yet_routed is None


def test_requirement_completeness_row_no_longer_has_not_yet_routed_marker():
    row = _mod.ROUTING_TABLE["requirement_completeness_verification"]
    assert row.not_yet_routed is None
    assert "parity_ledger" in row.primary_providers


def test_parity_id_identifier_routes_to_parity_ledger_provider():
    decision = _mod.route("INFRA-349")
    assert "parity_ledger" in decision.providers_selected
    assert decision.matched_identifier.category == "parity_id"


# ---------------------------------------------------------------------------
# 3. Capability-aware routing
# ---------------------------------------------------------------------------

def test_router_loads_real_capability_descriptors_from_disk(tmp_path):
    original = _mod.load_capability_descriptor(_mod._CONTEXT_SEARCH_CAPS_PATH)
    assert original["deterministic_relationships"] == "NONE"

    mutated_path = tmp_path / "provider_capabilities_context_search.json"
    mutated_data = dict(original)
    mutated_data["deterministic_relationships"] = "FULL"
    mutated_path.write_text(json.dumps(mutated_data))

    reloaded = _mod.load_capability_descriptor(mutated_path)
    assert reloaded["deterministic_relationships"] == "FULL"
    # Confirms load is not cached across a different path — a distinct file's contents
    # are read fresh, not memoized from the first call.
    assert _mod.load_capability_descriptor(_mod._CONTEXT_SEARCH_CAPS_PATH)["deterministic_relationships"] == "NONE"


def test_capability_change_flips_routing_decision(tmp_path, monkeypatch):
    row = _mod.ROUTING_TABLE["definition_terminology_architecture"]

    # Real fixture: context_search's deterministic_relationships is "NONE" — a request that
    # needs FULL cannot be satisfied.
    before = _mod.apply_capability_constraints(row, "FULL")
    assert before[0].satisfied is False

    mutated_path = tmp_path / "provider_capabilities_context_search.json"
    data = json.loads(_mod._CONTEXT_SEARCH_CAPS_PATH.read_text())
    data["deterministic_relationships"] = "FULL"
    mutated_path.write_text(json.dumps(data))

    monkeypatch.setitem(_mod._PROVIDER_CAPS_PATHS, "context_search", mutated_path)
    after = _mod.apply_capability_constraints(row, "FULL")
    assert after[0].satisfied is True
    assert before != after


def test_router_never_claims_unadvertised_capability():
    contract_schemas = _load_contract_schemas_module()
    for instance_path in (contract_schemas._CONTEXT_SEARCH_INSTANCE, contract_schemas._GRAPHIFY_INSTANCE):
        descriptor = json.loads(instance_path.read_text())
        # Cross-check: the real router function must agree with the existing test-local stub.
        assert _mod.capability_allows(descriptor, "cancellation") == contract_schemas.capability_allows(
            descriptor, "cancellation"
        )
        assert _mod.capability_allows(descriptor, "timeout") == contract_schemas.capability_allows(
            descriptor, "timeout"
        )
        assert _mod.capability_allows(descriptor, "cancellation") is False
        assert _mod.capability_allows(descriptor, "timeout") is False


def test_negative_knowledge_support_none_does_not_assert_absence():
    context_search = _mod.load_capability_descriptor(_mod._CONTEXT_SEARCH_CAPS_PATH)
    graphify = _mod.load_capability_descriptor(_mod._GRAPHIFY_CAPS_PATH)
    assert context_search["negative_knowledge_support"] == "NONE"
    assert graphify["negative_knowledge_support"] == "NONE"
    # An empty provider result must never be synthesized by apply_capability_constraints into
    # a "confirmed not present" conclusion — the router's constraint logic never inspects
    # negative_knowledge_support at all (it only reasons about deterministic_relationships),
    # so it cannot fabricate an absence guarantee neither descriptor advertises.
    row = _mod.ROUTING_TABLE["broad_task_context"]
    constraints = _mod.apply_capability_constraints(row, None)
    for constraint in constraints:
        assert "negative" not in constraint.reason.lower()
        assert "absence" not in constraint.reason.lower()
        assert "not present" not in constraint.reason.lower()


# ---------------------------------------------------------------------------
# 4. Ambiguous-intent fallback
# ---------------------------------------------------------------------------

def test_ambiguous_intent_queries_bounded_provider_set(monkeypatch):
    calls = []

    def fake_context_search(query_text):
        calls.append("context_search")
        return {"provider_id": "context_search", "results": []}

    def fake_graphify(query_text):
        calls.append("graphify")
        return {"provider_id": "graphify", "results": {}}

    monkeypatch.setattr(_mod, "_run_context_search_provider", fake_context_search)
    monkeypatch.setattr(_mod, "_run_graphify_provider", fake_graphify)

    decision = _mod.route_ambiguous("some genuinely ambiguous free-text blob")

    assert set(decision.providers_consulted) == {"context_search", "graphify"}
    assert len(decision.providers_consulted) == 2
    assert calls == ["context_search", "graphify"]


def test_ambiguous_intent_does_not_silently_pick_one_provider(monkeypatch):
    monkeypatch.setattr(_mod, "_run_context_search_provider", lambda q: {"provider_id": "context_search"})
    monkeypatch.setattr(_mod, "_run_graphify_provider", lambda q: {"provider_id": "graphify"})

    decision = _mod.route_ambiguous("qqqqqqqq zzzzzzzz totally unclassifiable")

    assert len(decision.providers_consulted) > 1
    assert "context_search" in decision.providers_consulted
    assert "graphify" in decision.providers_consulted


def test_route_falls_through_to_ambiguous_for_unclassifiable_text(monkeypatch):
    monkeypatch.setattr(_mod, "_run_context_search_provider", lambda q: {"provider_id": "context_search"})
    monkeypatch.setattr(_mod, "_run_graphify_provider", lambda q: {"provider_id": "graphify"})

    decision = _mod.route("qqqqqqqq zzzzzzzz totally unclassifiable gibberish blob")
    assert decision.matched_identifier is None
    assert decision.routing_shape is None
    assert set(decision.providers_consulted) == {"context_search", "graphify"}


# ---------------------------------------------------------------------------
# 5. Scope-boundary guards
# ---------------------------------------------------------------------------

def test_router_output_is_plain_typed_record_not_mcp_envelope():
    decision = _mod.RoutingDecision(
        providers_selected=["context_search"],
        matched_identifier=None,
        routing_shape="definition_terminology_architecture",
        rationale="test",
    )
    field_names = {f for f in decision.__dataclass_fields__}
    assert field_names.isdisjoint({"jsonrpc", "id", "method"})


def test_router_module_introduces_zero_mcp_zero_packet_zero_cache_code():
    text = _ROUTER_PATH.read_text()
    assert "context_packet_assembler" not in text
    assert "retrieval_cache" not in text
    assert "def knowledge_context(" not in text
    assert "def knowledge_status(" not in text
    assert "lru_cache" not in text
    assert "ThreadPoolExecutor(" not in text
    assert "import concurrent.futures" not in text
    assert "import asyncio" not in text


def test_no_live_gateway_tool_code_or_mcp_registration_introduced():
    """`.mcp.json` now legitimately carries a `knowledge-gateway` entry
    (TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE) — updated in the same change per that ticket's own
    Regression Surface note. This router module itself must still never define the live
    `knowledge_context`/`knowledge_status` tool functions — that half of the guard is unchanged."""
    mcp_config = json.loads((_REPO_ROOT / ".mcp.json").read_text())
    assert set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github", "knowledge-gateway"}

    forbidden_names = {"knowledge_context", "knowledge_status"}
    for py_file in (_REPO_ROOT / "tools").glob("*.py"):
        if py_file.name == "knowledge_gateway_mcp.py":
            continue
        text = py_file.read_text()
        for name in forbidden_names:
            assert f"def {name}(" not in text, (
                f"{py_file}: found a live '{name}' tool implementation"
            )


# ---------------------------------------------------------------------------
# 6. Parity Ledger provider adapter (TCK-20260816-KGMCP-P4-PARITY-ADAPTER)
# ---------------------------------------------------------------------------

_PARITY_LEDGER_DIR = _REPO_ROOT / "docs" / "parity_ledger"


def test_run_parity_provider_returns_real_entry_for_existing_id(tmp_path, monkeypatch):
    pidx = _mod._load_parity_index_module()
    db_path = tmp_path / "parity.db"
    build_report = pidx.build(ledger_dir=_PARITY_LEDGER_DIR, db_path=db_path)
    assert build_report["status"] == "ok"
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", db_path)

    result = _mod._run_parity_provider("INFRA-349")
    assert result["provider_id"] == "parity_ledger"
    assert result["results"]["found"] is True
    assert result["results"]["record"]["id"] == "INFRA-349"
    # A found result never needs a staleness check.
    assert result["staleness"] is None


def test_stale_parity_index_is_disclosed_not_silently_trusted(tmp_path, monkeypatch):
    pidx = _mod._load_parity_index_module()
    ledger_copy = tmp_path / "ledger"
    shutil.copytree(_PARITY_LEDGER_DIR, ledger_copy)

    db_path = tmp_path / "parity.db"
    build_report = pidx.build(ledger_dir=ledger_copy, db_path=db_path)
    assert build_report["status"] == "ok"

    # Mutate the tmp-path ledger copy AFTER building, without rebuilding -- this is what makes
    # check_staleness() genuinely report STALE against this test's own isolated ledger state.
    infra_shard = ledger_copy / "infrastructure.yaml"
    infra_shard.write_text(
        infra_shard.read_text()
        + '\n- id: INFRA-999\n'
        '  text: "Test-only fixture entry added after build() to force a genuine STALE result."\n'
        '  status: verified\n'
        '  priority: P1\n'
        '  legacy_evidence: null\n'
        '  v2_evidence: "test fixture"\n'
        '  proof_type: differential\n'
        '  test_path: "tests/tools/test_knowledge_gateway_router.py::test_stale_parity_index_is_disclosed_not_silently_trusted"\n'
        '  divergence_note: null\n'
        '  support_boundary: "test fixture only, never a real ledger entry"\n'
    )

    # Dual monkeypatch (Architecture Review fix): both DEFAULT_DB_PATH and DEFAULT_LEDGER_DIR must
    # be patched together, or check_staleness() would silently recompute live_hash from the real
    # repo's own docs/parity_ledger/*.yaml shards instead of this test's mutated copy.
    monkeypatch.setattr(pidx, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(pidx, "DEFAULT_LEDGER_DIR", ledger_copy)

    result = _mod._run_parity_provider("ZZZZ-9999")
    assert result["results"]["found"] is False
    assert result["staleness"] is not None
    assert result["staleness"]["status"] == "STALE"


# ---------------------------------------------------------------------------
# 7. Anti-drift guards (TCK-20260816-KGMCP-P4-PARITY-ADAPTER)
# ---------------------------------------------------------------------------

def test_route_ambiguous_provider_set_is_unchanged():
    assert _mod._AMBIGUOUS_PROVIDERS == ("context_search", "graphify")


def _run_parity_provider_body_calls_and_kwargs():
    """AST-only inspection of _run_parity_provider's actual code body (never its docstring prose,
    which legitimately names impact()/health()/symbol as things this adapter does NOT call)."""
    source = inspect.getsource(_mod._run_parity_provider)
    tree = ast.parse(source)
    called_attrs = set()
    kwarg_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called_attrs.add(node.func.attr)
        if isinstance(node, ast.keyword) and node.arg is not None:
            kwarg_names.add(node.arg)
    return called_attrs, kwarg_names


def test_changed_path_impact_call_is_not_wired_by_this_ticket():
    called_attrs, kwarg_names = _run_parity_provider_body_calls_and_kwargs()
    assert "impact" not in called_attrs
    assert "changed_path" not in kwarg_names


def test_symbol_filter_on_impact_remains_unused_for_parity_provider():
    called_attrs, kwarg_names = _run_parity_provider_body_calls_and_kwargs()
    assert "impact" not in called_attrs
    assert "symbol" not in kwarg_names


def test_parity_index_module_is_never_modified():
    result = subprocess.run(
        ["git", "diff", "HEAD", "--", "tools/parity_index.py"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    assert result.stdout == "", "tools/parity_index.py must remain byte-unchanged for this ticket"


def test_context_search_and_graphify_capability_descriptors_are_byte_identical_to_before():
    result = subprocess.run(
        [
            "git", "diff", "HEAD", "--",
            "docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json",
            "docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_graphify.json",
        ],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    assert result.stdout == "", (
        "the two pre-existing capability descriptors must remain byte-unchanged for this ticket"
    )
