"""FastMCP server for the Knowledge Gateway MCP Phase 1
(TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE).

Exposes `knowledge_context` (§9.1) and `knowledge_status` (§9.2) — the only two tools this
server registers — over the two frozen Phase 1 dependencies:
`tools/knowledge_gateway_router.py::route()` (INFRA-335) and
`tools/knowledge_gateway_packet_assembly.py::assemble_packet()` (INFRA-336). Both tools
validate their I/O against the frozen `docs/engine/contracts/knowledge_gateway_mcp/*.schema.json`
files using a real `jsonschema.Draft7Validator`.

`knowledge_learn`/`knowledge_promote`/`knowledge_verify`/any invalidation tool are never
registered here — §9.3, explicitly deferred to a later phase.

Wrapper-function finding (Design Decision D1 — re-verified against the real source, twice
reviewed): none of `tools/retrieval_events.py`'s 3 Wrapper functions (`wrap_hybrid_retrieval`,
`wrap_retrieval_cache_check`, `wrap_context_packet_assembly`) has an undistorted real call site
in this module's pipeline — `wrap_hybrid_retrieval` needs internal state only
`search_mcp.py::_run_search()` builds for itself; `wrap_retrieval_cache_check` needs a real
cache, out of scope pre-Phase-2; `wrap_context_packet_assembly` wraps a structurally different,
unrelated packet assembler (`tools/context_packet_assembler.py`). This module reports that
finding honestly rather than force-fitting a call or adding a new wrapper function.
`tools/retrieval_events.py` is not imported or called by this module at all.

Module layout follows `tools/search_mcp.py`'s own precedent: single flat file,
`importlib.util` sibling-loading for cross-file imports within `tools/` (no `__init__.py`-based
subpackage exists anywhere in `tools/` today).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Optional

# `jsonschema` is not directly declared in pyproject.toml but is already transitively pulled in
# by the `mcp>=1.0.0` dependency declared under `[project.optional-dependencies.search-mcp]`
# (verified live: `pip show jsonschema` reports `Required-by: mcp`) — no new dependency
# declaration is needed.
import jsonschema

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"

_REQUEST_SCHEMA_PATH = _CONTRACTS_DIR / "knowledge_context_request.schema.json"
_RESPONSE_SCHEMA_PATH = _CONTRACTS_DIR / "knowledge_context_response.schema.json"
_STATUS_RESPONSE_SCHEMA_PATH = _CONTRACTS_DIR / "knowledge_status_response.schema.json"

_CONTEXT_SEARCH_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_context_search.json"
_GRAPHIFY_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_graphify.json"


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text())


REQUEST_SCHEMA = _load_schema(_REQUEST_SCHEMA_PATH)
RESPONSE_SCHEMA = _load_schema(_RESPONSE_SCHEMA_PATH)
STATUS_RESPONSE_SCHEMA = _load_schema(_STATUS_RESPONSE_SCHEMA_PATH)

# The response schema's `status`/`freshness`/`verification` properties `$ref` relative-file
# definitions in shared_enums.schema.json — resolved once at import time. The request and
# status-response schemas have no cross-file `$ref`s, so no resolver is needed for them.
_RESPONSE_SCHEMA_RESOLVER = jsonschema.RefResolver(
    base_uri=_CONTRACTS_DIR.resolve().as_uri() + "/", referrer=RESPONSE_SCHEMA
)

REQUEST_VALIDATOR = jsonschema.Draft7Validator(REQUEST_SCHEMA)
RESPONSE_VALIDATOR = jsonschema.Draft7Validator(RESPONSE_SCHEMA, resolver=_RESPONSE_SCHEMA_RESOLVER)
STATUS_RESPONSE_VALIDATOR = jsonschema.Draft7Validator(STATUS_RESPONSE_SCHEMA)


def _load_pyproject_version() -> str:
    with (_REPO_ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


# Reuses the one real version string this repo already tracks (pyproject.toml [project].version)
# rather than inventing a second, untracked "gateway version" concept.
GATEWAY_VERSION: str = _load_pyproject_version()

# Kept in sync with knowledge_context_response.schema.json's and
# knowledge_status_response.schema.json's own top-level "schema_version": 1 fields.
REPORTED_SCHEMA_VERSION: int = 1

# Used only when the caller omits budget_tokens (the request schema does not mark it required).
DEFAULT_BUDGET_TOKENS: int = 4000


# ── Sibling-module loading (mirrors knowledge_gateway_packet_assembly.py:139-156) ────────────

def _load_router_module():
    key = "kgmcp_mcp_router"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _TOOLS_DIR / "knowledge_gateway_router.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_packet_assembly_module():
    key = "kgmcp_mcp_packet_assembly"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            key, _TOOLS_DIR / "knowledge_gateway_packet_assembly.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_search_mcp_module():
    key = "kgmcp_mcp_search_mcp"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _TOOLS_DIR / "search_mcp.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _omit_none(d: dict) -> dict:
    """Both `knowledge_status.providers[].generation` and `knowledge_context`'s
    `context[]`/`evidence[]` `path`/`authority` fields are typed plain `string` (no `null`
    variant) in their frozen schemas — verified live that passing `null` fails validation while
    omitting the key validates cleanly (Design Decision D4). Strip every `None`-valued key
    before returning a response dict fragment."""
    return {k: v for k, v in d.items() if v is not None}


# ── knowledge_context ─────────────────────────────────────────────────────────────────────────

def _run_knowledge_context(
    query: str,
    mode: Optional[str] = None,
    budget_tokens: Optional[int] = None,
    changed_paths: Optional[list[str]] = None,
    include_history: Optional[bool] = None,
    evidence_detail: Optional[str] = None,
) -> dict:
    """Core logic shared by the registered MCP tool and any direct/test-mode caller. Builds a
    request dict from only the non-`None` supplied arguments (never injects a fabricated default
    for an omitted optional field), validates it against the frozen request schema, then calls
    the frozen router and packet assembler directly and unwrapped (see module docstring's
    wrapper-function finding)."""
    request: dict = {"query": query}
    if mode is not None:
        request["mode"] = mode
    if budget_tokens is not None:
        request["budget_tokens"] = budget_tokens
    if changed_paths is not None:
        request["changed_paths"] = changed_paths
    if include_history is not None:
        request["include_history"] = include_history
    if evidence_detail is not None:
        request["evidence_detail"] = evidence_detail

    try:
        REQUEST_VALIDATOR.validate(request)
    except jsonschema.ValidationError as exc:
        error_response = {
            "status": "ERROR",
            "freshness": "UNKNOWN",
            "verification": "UNVERIFIED",
            "provenance_providers": [],
            "providers_consulted_this_call": [],
            "error": {"code": "INVALID_REQUEST", "message": str(exc.message)},
        }
        RESPONSE_VALIDATOR.validate(error_response)
        return error_response

    _kgr = _load_router_module()
    _kgpa = _load_packet_assembly_module()
    effective_budget = budget_tokens if budget_tokens is not None else DEFAULT_BUDGET_TOKENS

    try:
        routing_decision = _kgr.route(query)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        reason = (
            "graphify: binary not found on PATH"
            if isinstance(exc, FileNotFoundError)
            else "graphify: subprocess timeout"
        )
        fallback_response: dict = {
            "status": "PARTIAL",
            "freshness": "UNKNOWN",
            "verification": "UNVERIFIED",
            "provenance_providers": [],
            "providers_consulted_this_call": [],
            "answer": "",
            "budget_requested": effective_budget,
            "budget_returned": 0,
            "statements": [],
            "context": [],
            "evidence": [],
            "conflicts": [],
            "provider_failures": [reason],
        }
        if mode is not None:
            fallback_response["mode"] = mode
        RESPONSE_VALIDATOR.validate(fallback_response)
        return fallback_response

    packet = _kgpa.assemble_packet(routing_decision, query, effective_budget)

    response: dict = {
        "status": packet.status,
        "freshness": packet.freshness,
        "verification": packet.verification,
        "provenance_providers": packet.provenance_providers,
        "providers_consulted_this_call": packet.providers_consulted_this_call,
        "answer": packet.answer,
        "budget_requested": packet.budget_requested,
        "budget_returned": packet.budget_returned,
        "provider_failures": packet.provider_failures,
    }
    # `mode` is passed through only if the caller supplied it — never fabricate a default when
    # the request omitted it (the response schema does not require `mode`).
    if mode is not None:
        response["mode"] = mode

    response["statements"] = [
        _omit_none(
            {
                "statement_id": s.statement_id,
                "text": s.text,
                "classification": s.classification,
                "evidence_ids": s.evidence_ids,
                "verification": s.verification,
            }
        )
        for s in packet.statements
    ]
    response["context"] = [
        _omit_none(
            {
                "kind": c.kind,
                "summary": c.summary,
                "source_id": c.source_id,
                "path": c.path,
                "evidence_hash": c.evidence_hash,
                "authority": c.authority,
            }
        )
        for c in packet.context
    ]
    response["evidence"] = [
        _omit_none(
            {
                "evidence_id": e.evidence_id,
                "source_id": e.source_id,
                "path": e.path,
                "evidence_hash": e.evidence_hash,
            }
        )
        for e in packet.evidence
    ]
    response["conflicts"] = [
        {
            "subject": conflict.subject,
            "claims": [
                {
                    "value": claim.value,
                    "source_id": claim.source_id,
                    "authority": claim.authority,
                    "valid_from": claim.valid_from,
                    # `valid_to` is explicitly typed ["string", "null"] in the response schema —
                    # unlike path/authority above, a real None here passes through as JSON null
                    # unmodified, no omission needed.
                    "valid_to": claim.valid_to,
                }
                for claim in conflict.claims
            ],
            "automatic_resolution": conflict.automatic_resolution,
            "recommended_action": conflict.recommended_action,
        }
        for conflict in packet.conflicts
    ]

    RESPONSE_VALIDATOR.validate(response)
    return response


# ── knowledge_status ──────────────────────────────────────────────────────────────────────────

def _git_branch_scope() -> dict:
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True,
        ).stdout.strip()
    )
    return {"branch": branch, "working_tree_dirty": dirty}


def _run_knowledge_status() -> dict:
    """Phase-1 field subset only — no cache exists yet. Every cache-specific field (§9.2's 6
    named fields plus `latency_summary_ms` in its entirety, plus `provider_fallback_rate`) is
    omitted outright, never a fabricated `0`/`null`/`{}` placeholder (see plan.md Step 3's
    field-by-field disposition table). Only `gateway_version`, `reported_schema_version`,
    `providers`, and `branch_scope` are Phase-1-populable."""
    import shutil

    _sm = _load_search_mcp_module()
    health = _sm._run_health()
    context_search_provider = _omit_none(
        {
            "provider_id": "context_search",
            "available": health.get("status") == "ok",
            # context_search's real adapter_version is genuinely null (frozen descriptor) —
            # omit the key entirely rather than send a type-violating `generation: null`.
            "generation": None,
        }
    )

    graphify_caps = json.loads(_GRAPHIFY_CAPS_PATH.read_text())
    graphify_provider = _omit_none(
        {
            "provider_id": "graphify",
            "available": shutil.which("graphify") is not None,
            "generation": graphify_caps["adapter_version"],
        }
    )

    response: dict = {
        "gateway_version": GATEWAY_VERSION,
        "reported_schema_version": REPORTED_SCHEMA_VERSION,
        "providers": [context_search_provider, graphify_provider],
        "branch_scope": _git_branch_scope(),
    }

    STATUS_RESPONSE_VALIDATOR.validate(response)
    return response


# ── MCP server (requires mcp package) ────────────────────────────────────────────────────────

def _build_server():
    """Builds and returns the configured `FastMCP` instance without calling `.run()` — split out
    from `_run_mcp_server()` so tests can introspect the registered-tool set (e.g.
    `server._tool_manager._tools.keys()`) without blocking on the stdio transport."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("knowledge-gateway")

    @server.tool()
    def knowledge_context(
        query: str,
        mode: str = None,
        budget_tokens: int = None,
        changed_paths: list[str] = None,
        include_history: bool = None,
        evidence_detail: str = None,
    ) -> dict:
        """
        Route a query to the Knowledge Gateway's providers (Context Search, Graphify) and return
        a schema-conformant, provenance-tracked context packet.

        Args:
            query: Natural-language or exact-term query.
            mode: "answer" or "task_context" (optional).
            budget_tokens: Token budget for the assembled packet (optional).
            changed_paths: Repo-relative paths the caller has changed (optional).
            include_history: Whether to include historical context (optional).
            evidence_detail: Requested evidence detail level (optional, open string).
        """
        return _run_knowledge_context(
            query,
            mode=mode,
            budget_tokens=budget_tokens,
            changed_paths=changed_paths,
            include_history=include_history,
            evidence_detail=evidence_detail,
        )

    @server.tool()
    def knowledge_status() -> dict:
        """
        Report the Knowledge Gateway's Phase 1 status: gateway/schema version, provider
        availability and generation, and branch scope. Cache-specific fields are omitted — no
        cache exists yet (Phase 2).
        """
        return _run_knowledge_status()

    return server


def _run_mcp_server() -> int:
    try:
        server = _build_server()
    except ImportError:
        print(
            "ERROR: mcp package not installed.\n"
            "Run: pip install 'mcp>=1.0.0'\n"
            "Or add to pyproject.toml: pip install -e '.[search-mcp]'",
            file=sys.stderr,
        )
        return 1

    server.run()
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(_run_mcp_server())
