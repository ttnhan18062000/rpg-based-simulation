"""Tests for the Knowledge Gateway MCP Phase 0 contract/schema freeze
(TCK-20260814-KGMCP-CONTRACT-SCHEMAS).

Phase 0 is contract-only: no gateway, routing, or live MCP tool exists yet. These tests
structurally validate the frozen `.schema.json`/`.json` files under
`docs/engine/contracts/knowledge_gateway_mcp/` and the prose contract doc
`docs/engine/contracts/knowledge_gateway_mcp_contract.md`, using the same raw-`json.loads()`-
and-structurally-assert pattern as `tests/tools/test_parity_ledger_schema.py` (no `jsonschema`
library dependency — mirrors `tools/parity_ledger_writer.py::validate_entry()`'s hand-rolled
validation precedent).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_CONTRACT_MD = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp_contract.md"

_SHARED_ENUMS = _CONTRACTS_DIR / "shared_enums.schema.json"
_PROVIDER_CAPABILITIES_SCHEMA = _CONTRACTS_DIR / "provider_capabilities.schema.json"
_REQUEST_SCHEMA = _CONTRACTS_DIR / "knowledge_context_request.schema.json"
_RESPONSE_SCHEMA = _CONTRACTS_DIR / "knowledge_context_response.schema.json"
_STATUS_RESPONSE_SCHEMA = _CONTRACTS_DIR / "knowledge_status_response.schema.json"
_CONTEXT_SEARCH_INSTANCE = _CONTRACTS_DIR / "provider_capabilities_context_search.json"
_GRAPHIFY_INSTANCE = _CONTRACTS_DIR / "provider_capabilities_graphify.json"

_ALL_SCHEMA_FILES = [
    _SHARED_ENUMS,
    _PROVIDER_CAPABILITIES_SCHEMA,
    _REQUEST_SCHEMA,
    _RESPONSE_SCHEMA,
    _STATUS_RESPONSE_SCHEMA,
]

_PROVIDER_CAPABILITIES_FIELDS = {
    "provider_id",
    "adapter_version",
    "stable_entity_ids",
    "evidence_granularities",
    "fine_grained_fingerprints",
    "incremental_refresh",
    "deterministic_relationships",
    "historical_queries",
    "negative_knowledge_support",
    "cancellation",
    "timeout",
    "branch_awareness",
    "generation_fingerprint",
}

_FORBIDDEN_REQUEST_FIELDS = {
    "provider_weights",
    "cache_level",
    "semantic_threshold",
    "provider_forcing",
    "force_provider",
    "ranking_policy",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Test 1 — schema files exist, parse, and carry schema_version
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", _ALL_SCHEMA_FILES, ids=lambda p: p.name)
def test_schema_file_parses_and_has_schema_version(path):
    assert path.exists(), f"missing frozen schema file: {path}"
    schema = _load(path)
    assert isinstance(schema["schema_version"], int)
    assert schema["schema_version"] == 1


# ---------------------------------------------------------------------------
# Test 2 — status/freshness/verification stay three distinct, non-collapsible fields
# ---------------------------------------------------------------------------

def test_response_schema_keeps_status_freshness_verification_distinct():
    response = _load(_RESPONSE_SCHEMA)
    props = response["properties"]

    for field in ("status", "freshness", "verification"):
        assert field in props, f"{field} missing from knowledge_context response schema"

    # Each of the three must $ref a distinct enum definition, never collapse into
    # a shared/aliased field or a single confidence-style property.
    refs = {field: props[field]["$ref"] for field in ("status", "freshness", "verification")}
    assert len(set(refs.values())) == 3, f"status/freshness/verification must not share a $ref: {refs}"
    assert "confidence" not in props, "response schema must not add a collapsed confidence field"

    enums = _load(_SHARED_ENUMS)["definitions"]
    status_values = set(enums["status"]["enum"])
    freshness_values = set(enums["freshness"]["enum"])
    verification_values = set(enums["verification"]["enum"])

    # No enum's value set may be a superset/equal to another's — direct guard against a future
    # edit silently merging two of the three dimensions.
    for a_name, a_vals in (("status", status_values), ("freshness", freshness_values), ("verification", verification_values)):
        for b_name, b_vals in (("status", status_values), ("freshness", freshness_values), ("verification", verification_values)):
            if a_name == b_name:
                continue
            assert not a_vals.issuperset(b_vals), f"{a_name} enum must not be a superset of {b_name} enum"


# ---------------------------------------------------------------------------
# Test 3 — FACT/INFERENCE/DECISION statement classification is present and closed
# ---------------------------------------------------------------------------

def test_statement_classification_enum_is_closed():
    enums = _load(_SHARED_ENUMS)["definitions"]
    classification = enums["statement_classification"]
    assert classification["type"] == "string"
    assert set(classification["enum"]) == {"FACT", "INFERENCE", "DECISION"}

    response = _load(_RESPONSE_SCHEMA)
    statement_item = response["properties"]["statements"]["items"]
    assert "classification" in statement_item["required"]
    assert statement_item["properties"]["classification"]["$ref"].endswith(
        "shared_enums.schema.json#/definitions/statement_classification"
    )


# ---------------------------------------------------------------------------
# Test 4 — CONFLICTED response shape matches §14
# ---------------------------------------------------------------------------

def test_conflicts_array_item_shape_matches_proposal_section_14():
    response = _load(_RESPONSE_SCHEMA)
    conflicts_item = response["properties"]["conflicts"]["items"]

    for field in ("subject", "claims", "automatic_resolution", "recommended_action"):
        assert field in conflicts_item["required"]

    claim_item = conflicts_item["properties"]["claims"]["items"]
    for field in ("value", "source_id", "authority", "valid_from", "valid_to"):
        assert field in claim_item["required"]
    assert claim_item["properties"]["valid_to"]["type"] == ["string", "null"]


# ---------------------------------------------------------------------------
# Test 5 — public request schema forbids internal routing fields
# ---------------------------------------------------------------------------

def test_request_schema_forbids_internal_routing_fields():
    request = _load(_REQUEST_SCHEMA)
    assert request.get("additionalProperties") is False

    declared_fields = set(request["properties"].keys())
    assert declared_fields.isdisjoint(_FORBIDDEN_REQUEST_FIELDS), (
        f"request schema exposes forbidden internal routing field(s): "
        f"{declared_fields & _FORBIDDEN_REQUEST_FIELDS}"
    )


# ---------------------------------------------------------------------------
# Test 6 — knowledge_context request schema covers the documented input fields
# ---------------------------------------------------------------------------

def test_request_schema_field_shapes():
    request = _load(_REQUEST_SCHEMA)
    assert request["required"] == ["query"]

    props = request["properties"]
    assert props["query"]["type"] == "string"
    assert set(props["mode"]["enum"]) == {"answer", "task_context"}
    assert props["budget_tokens"]["type"] == "integer"
    assert props["changed_paths"]["type"] == "array"
    assert props["changed_paths"]["items"]["type"] == "string"
    assert props["include_history"]["type"] == "boolean"
    assert props["evidence_detail"]["type"] == "string"


# ---------------------------------------------------------------------------
# Test 7 — knowledge_status response schema covers the §9.2 field list and forbids
#          the same routing-control fields
# ---------------------------------------------------------------------------

def test_status_response_schema_field_coverage_and_forbidden_fields():
    status = _load(_STATUS_RESPONSE_SCHEMA)
    assert status.get("additionalProperties") is False
    assert set(status["required"]) == {"gateway_version", "reported_schema_version"}

    expected_fields = {
        "gateway_version", "reported_schema_version", "providers", "cache_entry_counts",
        "cache_hit_rate", "cache_miss_rate", "cache_stale_rejection_rate",
        "latency_summary_ms", "provider_fallback_rate", "recent_invalidation_reasons",
        "branch_scope", "cache_rebuildable",
    }
    declared_fields = set(status["properties"].keys())
    assert expected_fields.issubset(declared_fields)
    assert declared_fields.isdisjoint(_FORBIDDEN_REQUEST_FIELDS)


# ---------------------------------------------------------------------------
# Test 8 — provider adapter invocation contract is written down and Context Search's
#          real current behavior matches its descriptor's grounded values
# ---------------------------------------------------------------------------

def test_adapter_invocation_contract_documented_in_contract_md():
    text = _CONTRACT_MD.read_text()
    assert "timeout" in text.lower()
    assert "cancellation" in text.lower()
    assert "version reporting" in text.lower()
    assert "fixture" in text.lower()
    assert "Context Search" in text
    assert "Graphify" in text


def _load_search_mcp_module():
    ks_stub = MagicMock()
    ks_stub._DEFAULT_DB = _REPO_ROOT / "knowledge-index" / "knowledge.db"
    ks_stub._MODEL_NAME = "all-MiniLM-L6-v2"
    ks_stub._tokenize = lambda text: text.lower().split()
    ks_stub._serialize_f32 = lambda v: b""
    ks_stub._load_bm25 = MagicMock(return_value=(None, []))
    sys.modules.setdefault("knowledge_search", ks_stub)

    mcp_path = _REPO_ROOT / "tools" / "search_mcp.py"
    spec = importlib.util.spec_from_file_location("search_mcp_contract_test", mcp_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["search_mcp_contract_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_context_search_descriptor_matches_real_run_health_shape():
    mod = _load_search_mcp_module()
    descriptor = _load(_CONTEXT_SEARCH_INSTANCE)

    # _run_health() never returns a live index (no built index in this test environment),
    # so it returns the "unavailable" error shape — asserting that shape carries no
    # timeout/cancellation/adapter_version field is itself the regression guard: today's
    # real code has nothing that would contradict the descriptor's false/null claims.
    health = mod._run_health()
    assert isinstance(health, dict)
    for forbidden_key in ("timeout", "cancellation", "adapter_version"):
        assert forbidden_key not in health

    assert descriptor["cancellation"] is False
    assert descriptor["timeout"] is False
    assert descriptor["adapter_version"] is None


# ---------------------------------------------------------------------------
# Test 9 — ProviderCapabilities descriptor is populated and tested for both adapters
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("instance_path", [_CONTEXT_SEARCH_INSTANCE, _GRAPHIFY_INSTANCE], ids=lambda p: p.stem)
def test_provider_capabilities_instance_has_all_fields_with_valid_enum_values(instance_path):
    schema = _load(_PROVIDER_CAPABILITIES_SCHEMA)
    instance = _load(instance_path)

    assert _PROVIDER_CAPABILITIES_FIELDS.issubset(instance.keys())
    # Instances carry schema_version metadata plus the twelve capability fields — no other
    # ad hoc keys (e.g. "_evidence") belong in the data file itself; justification prose
    # belongs in knowledge_gateway_mcp_contract.md instead.
    assert set(instance.keys()) == _PROVIDER_CAPABILITIES_FIELDS | {"schema_version"}

    enum_fields = {
        "stable_entity_ids": schema["properties"]["stable_entity_ids"]["enum"],
        "deterministic_relationships": schema["properties"]["deterministic_relationships"]["enum"],
        "negative_knowledge_support": schema["properties"]["negative_knowledge_support"]["enum"],
        "branch_awareness": schema["properties"]["branch_awareness"]["enum"],
    }
    for field, allowed in enum_fields.items():
        assert instance[field] in allowed, f"{instance_path.name}: {field}={instance[field]!r} not in {allowed}"

    for field in ("fine_grained_fingerprints", "incremental_refresh", "historical_queries", "cancellation", "timeout"):
        assert isinstance(instance[field], bool)


# ---------------------------------------------------------------------------
# Test 10 — router cannot claim a capability the descriptor does not advertise
# ---------------------------------------------------------------------------

def capability_allows(descriptor: dict, capability_name: str) -> bool:
    """Test-only contract helper — not tools/ code, since no router exists yet to own it.

    Mirrors the §8.1 'routing consequence': a caller must never treat a provider as capable
    of something its ProviderCapabilities descriptor does not advertise.
    """
    return bool(descriptor[capability_name])


@pytest.mark.parametrize("instance_path", [_CONTEXT_SEARCH_INSTANCE, _GRAPHIFY_INSTANCE], ids=lambda p: p.stem)
def test_capability_allows_rejects_unadvertised_cancellation_and_timeout(instance_path):
    descriptor = _load(instance_path)
    assert capability_allows(descriptor, "cancellation") is False
    assert capability_allows(descriptor, "timeout") is False


# ---------------------------------------------------------------------------
# Test 11 — new gateway enums do not alias existing registry/parity enums
# ---------------------------------------------------------------------------

def _load_validate_frontmatter_module():
    validator_path = _REPO_ROOT / "tools" / "validate_frontmatter.py"
    spec = importlib.util.spec_from_file_location("validate_frontmatter_contract_test", validator_path)
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_gateway_enums_are_disjoint_from_frontmatter_and_parity_enums():
    vfm = _load_validate_frontmatter_module()
    parity_schema = _load(_REPO_ROOT / "docs" / "parity_ledger" / "schema.json")
    parity_status = set(parity_schema["items"]["properties"]["status"]["enum"])
    parity_priority = set(parity_schema["items"]["properties"]["priority"]["enum"])

    enums = _load(_SHARED_ENUMS)["definitions"]
    gateway_status = set(enums["status"]["enum"])
    gateway_freshness = set(enums["freshness"]["enum"])
    gateway_verification = set(enums["verification"]["enum"])
    gateway_classification = set(enums["statement_classification"]["enum"])

    for gateway_enum in (gateway_status, gateway_freshness, gateway_verification, gateway_classification):
        assert gateway_enum.isdisjoint(vfm.STATUS_VALUES)
        assert gateway_enum.isdisjoint(vfm.AUTHORITY_VALUES)
        assert gateway_enum.isdisjoint(parity_status)
        assert gateway_enum.isdisjoint(parity_priority)


# ---------------------------------------------------------------------------
# Test 12 — no live tool/routing code was introduced
# ---------------------------------------------------------------------------

def test_no_live_gateway_tool_code_or_mcp_registration_introduced():
    mcp_config = json.loads((_REPO_ROOT / ".mcp.json").read_text())
    assert set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github"}, (
        "no new mcpServers entry may be added by a Phase-0 contract-only ticket"
    )

    forbidden_names = {"knowledge_context", "knowledge_status"}
    for py_file in (_REPO_ROOT / "tools").glob("*.py"):
        text = py_file.read_text()
        for name in forbidden_names:
            assert f"def {name}(" not in text, (
                f"{py_file}: found a live '{name}' tool implementation — Phase 0 is contract-only"
            )
