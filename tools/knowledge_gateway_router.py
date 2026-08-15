"""Deterministic query router for the Knowledge Gateway MCP Phase 1
(TCK-20260815-KGMCP-P1-QUERY-ROUTER).

Implements `docs/plans/knowledge-gateway-mcp-proposal.md` §8: recognize stable identifiers
(ticket IDs, parity IDs, source paths, symbol names, registered document paths, subsystem IDs)
before classifying free text, route via the 7-row intent/shape table, and consult the two
frozen `provider_capabilities_*.json` descriptors before selecting a provider — never claiming
a capability a descriptor does not advertise.

This module is pure decision logic: no MCP server code, no packet/statement/evidence assembly,
no caching. `route()` recomputes every call; capability descriptors are read from disk on every
consult so a fixture edit is observable immediately (see `test_capability_change_flips_routing_decision`).

Module layout follows `tools/search_mcp.py`'s own precedent: single flat file, `importlib.util`
sibling-loading for cross-file imports within `tools/` (no `__init__.py`-based subpackage exists
anywhere in `tools/` today).
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"

_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_CONTEXT_SEARCH_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_context_search.json"
_GRAPHIFY_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_graphify.json"

_REGISTRY_YAML_PATH = _REPO_ROOT / "docs" / "REGISTRY.yaml"
_LAYER_REGISTRY_PATH = _REPO_ROOT / "registries" / "layer_registry.jsonl"


def _load_baseline_corpus_module():
    if "kgmcp_baseline_corpus" in sys.modules:
        return sys.modules["kgmcp_baseline_corpus"]
    corpus_path = _MONITORING_TOOLS_DIR / "kgmcp_baseline_corpus.py"
    spec = importlib.util.spec_from_file_location("kgmcp_baseline_corpus", corpus_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kgmcp_baseline_corpus"] = mod
    spec.loader.exec_module(mod)
    return mod


ROUTING_SHAPES: frozenset[str] = _load_baseline_corpus_module().ROUTING_SHAPES


# ── Step 1: Capability descriptor loader ──────────────────────────────────────

def load_capability_descriptor(path: Path) -> dict:
    """Read and parse a `provider_capabilities_*.json` file. Loaded fresh from disk on every
    call (no module-level cache) so a fixture edit is observable to the next call."""
    return json.loads(path.read_text())


# ── Step 2: Six stable-identifier matchers ────────────────────────────────────

_TICKET_ID_RE = re.compile(r"^TCK-\d{8}-[A-Z0-9-]+$")
_PARITY_ID_RE = re.compile(r"^[A-Z]+(-[A-Z]+)*-\d+$")


def match_ticket_id(text: str) -> Optional[str]:
    if _TICKET_ID_RE.match(text):
        return text
    return None


def match_parity_id(text: str) -> Optional[str]:
    """Shape-only match (Design Decision D1) — accepts any string shaped like a parity ID
    (`PREFIX(-PREFIX)*-digits`) regardless of whether it exists in a real ledger shard.
    Existence is a downstream Context-Search/Parity-Ledger concern, not this router's."""
    if _PARITY_ID_RE.match(text):
        return text
    return None


def match_source_path(text: str) -> Optional[str]:
    """Pure `pathlib` check, no shell/subprocess. Guards against path traversal escaping the
    repo root (Python 3.9+ `Path.is_relative_to`; this repo's venv is 3.12, so no
    `os.path.commonpath` fallback is required)."""
    candidate = (_REPO_ROOT / text).resolve()
    if not candidate.is_relative_to(_REPO_ROOT.resolve()):
        return None
    if not candidate.exists():
        return None
    return text


def match_symbol_name(text: str) -> dict:
    """Always delegates to the real `graphify query` CLI — no new symbol table is built.
    Mirrors `tools/agent-monitoring/kgmcp_baseline_runner.py:92-114`'s `_run_graphify` call
    shape exactly (list-form args, no `shell=True`).

    `timeout=120` is a caller-side process safeguard only — both provider capability
    descriptors declare `"timeout": false`, i.e. Graphify itself offers no bounded-latency
    guarantee; this is never surfaced as a provider guarantee in any rationale text.
    """
    proc = subprocess.run(
        ["graphify", "query", text],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "symbol": text,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
    }


def match_registered_doc_path(text: str) -> Optional[str]:
    entries = yaml.safe_load(_REGISTRY_YAML_PATH.read_text()) or []
    doc_paths = {entry["path"] for entry in entries if entry.get("type") == "doc"}
    if text in doc_paths:
        return text
    return None


def match_subsystem_id(text: str) -> Optional[str]:
    layers = set()
    for line in _LAYER_REGISTRY_PATH.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        layers.add(json.loads(line)["layer"])
    if text in layers:
        return text
    return None


# ── Step 3: 7-row routing table ───────────────────────────────────────────────

@dataclass(frozen=True)
class RoutingTableRow:
    shape_id: str
    primary_providers: tuple[str, ...]
    optional_providers: tuple[str, ...] = ()
    not_yet_routed: Optional[str] = None


ROUTING_TABLE: dict[str, RoutingTableRow] = {
    "definition_terminology_architecture": RoutingTableRow(
        shape_id="definition_terminology_architecture",
        primary_providers=("context_search",),
        optional_providers=("registry", "graphify"),
    ),
    "symbol_lookup_callers_references": RoutingTableRow(
        shape_id="symbol_lookup_callers_references",
        primary_providers=("graphify",),
        optional_providers=("context_search",),
    ),
    "requirement_completeness_verification": RoutingTableRow(
        shape_id="requirement_completeness_verification",
        primary_providers=("context_search",),
        not_yet_routed="parity_ledger",
    ),
    "ticket_historical_rationale": RoutingTableRow(
        shape_id="ticket_historical_rationale",
        primary_providers=("context_search",),
        optional_providers=("working_log", "registry"),
    ),
    "test_impact_of_change": RoutingTableRow(
        shape_id="test_impact_of_change",
        primary_providers=("graphify",),
    ),
    "ticket_work_status": RoutingTableRow(
        shape_id="ticket_work_status",
        primary_providers=("context_search",),
        optional_providers=("working_log",),
    ),
    "broad_task_context": RoutingTableRow(
        shape_id="broad_task_context",
        primary_providers=("context_search", "graphify"),
    ),
}

assert set(ROUTING_TABLE.keys()) == ROUTING_SHAPES, (
    "ROUTING_TABLE keys must exactly match kgmcp_baseline_corpus.ROUTING_SHAPES"
)


# ── Step 4: Capability-aware routing-consequence logic ────────────────────────

def capability_allows(descriptor: dict, capability_name: str) -> bool:
    """Same signature/semantics as the test-local stand-in at
    `tests/tools/test_knowledge_gateway_contract_schemas.py:287-293` — this is the real
    implementation that helper's docstring anticipates."""
    return bool(descriptor[capability_name])


@dataclass(frozen=True)
class CapabilityConstraint:
    satisfied: bool
    reason: str


_DETERMINISTIC_RELATIONSHIPS_RANK = {"NONE": 0, "PARTIAL": 1, "FULL": 2}

_PROVIDER_CAPS_PATHS = {
    "context_search": _CONTEXT_SEARCH_CAPS_PATH,
    "graphify": _GRAPHIFY_CAPS_PATH,
}


def apply_capability_constraints(
    row: RoutingTableRow, requested_guarantee: Optional[str]
) -> list[CapabilityConstraint]:
    """Implements §8.1's routing-consequence examples: a request that needs a specific
    `deterministic_relationships` guarantee level (e.g. `"FULL"`) only counts as satisfied if
    at least one of the row's primary providers actually advertises it — never silently
    claimed. `requested_guarantee=None` means no explicit guarantee was requested, which is
    always trivially satisfied.
    """
    if requested_guarantee is None:
        return [CapabilityConstraint(satisfied=True, reason="no explicit capability guarantee requested")]

    required_rank = _DETERMINISTIC_RELATIONSHIPS_RANK[requested_guarantee]
    advertised_by = []
    for provider_id in row.primary_providers:
        caps_path = _PROVIDER_CAPS_PATHS.get(provider_id)
        if caps_path is None:
            continue
        descriptor = load_capability_descriptor(caps_path)
        provider_rank = _DETERMINISTIC_RELATIONSHIPS_RANK[descriptor["deterministic_relationships"]]
        if provider_rank >= required_rank:
            advertised_by.append(provider_id)

    if advertised_by:
        return [
            CapabilityConstraint(
                satisfied=True,
                reason=f"{', '.join(advertised_by)} advertises deterministic_relationships >= {requested_guarantee}",
            )
        ]
    return [
        CapabilityConstraint(
            satisfied=False,
            reason=f"no primary provider advertises {requested_guarantee} deterministic_relationships",
        )
    ]


# ── Step 5: Sequential-bounded ambiguous-intent fallback ─────────────────────

_AMBIGUOUS_PROVIDERS: tuple[str, ...] = ("context_search", "graphify")


def _run_context_search_provider(query_text: str) -> dict:
    _KS_PATH = _TOOLS_DIR / "knowledge_search.py"
    if "knowledge_search" not in sys.modules:
        spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
        _ks = importlib.util.module_from_spec(spec)
        sys.modules["knowledge_search"] = _ks
        spec.loader.exec_module(_ks)

    _SM_PATH = _TOOLS_DIR / "search_mcp.py"
    if "knowledge_gateway_router_search_mcp" not in sys.modules:
        spec = importlib.util.spec_from_file_location("knowledge_gateway_router_search_mcp", _SM_PATH)
        _sm = importlib.util.module_from_spec(spec)
        sys.modules["knowledge_gateway_router_search_mcp"] = _sm
        spec.loader.exec_module(_sm)
    _sm = sys.modules["knowledge_gateway_router_search_mcp"]
    return {"provider_id": "context_search", "results": _sm._run_search(query_text)}


def _run_graphify_provider(query_text: str) -> dict:
    result = match_symbol_name(query_text)
    return {"provider_id": "graphify", "results": result}


def route_ambiguous(query_text: str) -> "RoutingDecision":
    """Queries exactly the bounded set `{context_search, graphify}`, sequentially — not via
    `ThreadPoolExecutor` or any concurrency primitive (Design Decision D3: no existing
    concurrency precedent in `tools/`, and true parallelism is a latency optimization out of
    this ticket's scope, not a Phase 1 correctness requirement).
    """
    providers_consulted: list[str] = []
    for provider_id in _AMBIGUOUS_PROVIDERS:
        if provider_id == "context_search":
            _run_context_search_provider(query_text)
        elif provider_id == "graphify":
            _run_graphify_provider(query_text)
        providers_consulted.append(provider_id)

    return RoutingDecision(
        providers_selected=list(_AMBIGUOUS_PROVIDERS),
        matched_identifier=None,
        routing_shape=None,
        rationale="ambiguous intent — no stable identifier matched and no confident routing-shape "
        "classification; queried bounded provider set sequentially",
        capability_constraints=[],
        not_yet_routed=None,
        providers_consulted=providers_consulted,
    )


# ── Step 6: Plain typed RoutingDecision output record + dispatcher ───────────

@dataclass(frozen=True)
class IdentifierMatch:
    category: str
    value: str


@dataclass(frozen=True)
class RoutingDecision:
    providers_selected: list[str]
    matched_identifier: Optional[IdentifierMatch]
    routing_shape: Optional[str]
    rationale: str
    capability_constraints: list[CapabilityConstraint] = field(default_factory=list)
    not_yet_routed: Optional[str] = None
    providers_consulted: list[str] = field(default_factory=list)


_SHAPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "symbol_lookup_callers_references": ("where is", "defined", "calls it", "callers", "references"),
    "requirement_completeness_verification": ("fully implemented", "is complete", "feature complete"),
    "ticket_historical_rationale": ("why was", "removed", "rationale", "history of"),
    "test_impact_of_change": ("what tests", "test impact", "must run if"),
    "ticket_work_status": ("status of", "current status"),
    "definition_terminology_architecture": ("what is", "who may", "definition of"),
    "broad_task_context": (
        "currently used", "used in this repository", "anywhere in", "across the codebase",
        "full context", "broad context", "everything about",
    ),
}

_SHAPE_CLASSIFICATION_ORDER: tuple[str, ...] = (
    "symbol_lookup_callers_references",
    "requirement_completeness_verification",
    "ticket_historical_rationale",
    "test_impact_of_change",
    "ticket_work_status",
    "definition_terminology_architecture",
    "broad_task_context",
)


def _classify_routing_shape(query_text: str) -> Optional[str]:
    """Deterministic keyword/heuristic classification only — no model call, no embedding
    similarity (ticket Out of Scope: model-based intent classification)."""
    lowered = query_text.lower()
    for shape_id in _SHAPE_CLASSIFICATION_ORDER:
        for keyword in _SHAPE_KEYWORDS[shape_id]:
            if keyword in lowered:
                return shape_id
    return None


_SYMBOL_SHAPE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _match_identifier(text: str) -> Optional[IdentifierMatch]:
    """Fixed order per plan Step 6: ticket_id -> parity_id -> source_path ->
    registered_doc_path -> subsystem_id -> symbol_name (symbol_name last since it is the most
    expensive/subprocess-bound check).

    `symbol_name` is only attempted (i.e. only shells out to `graphify`) when the whole query
    text is single-identifier-shaped (no whitespace, valid identifier characters) — a full
    natural-language sentence is never a "symbol name" on its own, it is free text that belongs
    to Step 6's shape classification instead. This gating lives in the dispatcher, not in
    `match_symbol_name` itself, which always delegates once called (per its own contract).
    """
    if match_ticket_id(text):
        return IdentifierMatch(category="ticket_id", value=text)
    if match_parity_id(text):
        return IdentifierMatch(category="parity_id", value=text)
    if match_source_path(text):
        return IdentifierMatch(category="source_path", value=text)
    if match_registered_doc_path(text):
        return IdentifierMatch(category="registered_doc_path", value=text)
    if match_subsystem_id(text):
        return IdentifierMatch(category="subsystem_id", value=text)
    if _SYMBOL_SHAPE_RE.match(text):
        result = match_symbol_name(text)
        if result["returncode"] == 0 and result["stdout"].strip():
            return IdentifierMatch(category="symbol_name", value=text)
    return None


def route(query_text: str, requested_guarantee: Optional[str] = None) -> RoutingDecision:
    """Top-level dispatcher: identifier match first, then routing-shape classification, then
    the ambiguous-intent fallback. Applies Step 4's capability constraints to whichever
    row/provider was selected before returning."""
    identifier_match = _match_identifier(query_text)
    if identifier_match is not None:
        shape_id = {
            "ticket_id": "ticket_work_status",
            "parity_id": "requirement_completeness_verification",
            "source_path": "definition_terminology_architecture",
            "registered_doc_path": "definition_terminology_architecture",
            "subsystem_id": "definition_terminology_architecture",
            "symbol_name": "symbol_lookup_callers_references",
        }[identifier_match.category]
        row = ROUTING_TABLE[shape_id]
        constraints = apply_capability_constraints(row, requested_guarantee)
        return RoutingDecision(
            providers_selected=list(row.primary_providers),
            matched_identifier=identifier_match,
            routing_shape=shape_id,
            rationale=f"matched stable identifier ({identifier_match.category}) -> routed via "
            f"'{shape_id}' row",
            capability_constraints=constraints,
            not_yet_routed=row.not_yet_routed,
            providers_consulted=[],
        )

    shape_id = _classify_routing_shape(query_text)
    if shape_id is not None:
        row = ROUTING_TABLE[shape_id]
        constraints = apply_capability_constraints(row, requested_guarantee)
        return RoutingDecision(
            providers_selected=list(row.primary_providers),
            matched_identifier=None,
            routing_shape=shape_id,
            rationale=f"classified free text into routing shape '{shape_id}' via keyword heuristic",
            capability_constraints=constraints,
            not_yet_routed=row.not_yet_routed,
            providers_consulted=[],
        )

    return route_ambiguous(query_text)
