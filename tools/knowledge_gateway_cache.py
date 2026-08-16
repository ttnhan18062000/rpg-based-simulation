"""
tools/knowledge_gateway_cache.py — orchestrates Level 1 provider-result cache lookup and write for
the real, live Knowledge Gateway MCP gateway (`tools/knowledge_gateway_mcp.py::_run_knowledge_context()`).

What this is: pure orchestration. It computes lookup identity
(`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §1), evidence-
validity identity (§2/§3/§4), and branch/working-tree scope (§5/§12.3) as three genuinely separate
steps (the Non-collapse rule, §3 — a lookup hit is never itself a validity verdict), and drives
`tools/knowledge_gateway_redaction.py::evaluate_write_candidate()` plus
`tools/retrieval_cache.py::write_provider_result_cache()` on a miss. The literal SQL
(`SELECT`/`INSERT OR REPLACE`/`UPDATE`) against `retrieval_provider_result_cache_rows` lives in
`tools/retrieval_cache.py` itself, not here (plan.md DD2) — this module never issues a raw SQL
statement of its own.

What this is not: no routing logic (`tools/knowledge_gateway_router.py` is untouched, Out of
Scope), no packet-assembly/extractive-rendering logic (`tools/knowledge_gateway_packet_assembly.py`
is untouched, Out of Scope), no Level 2/Level 3 caching (semantic/fuzzy matching, verified-knowledge
caching — later phases).

Import style (Step 1's own documented latitude): this module imports `tools.retrieval_cache` and
`tools.knowledge_gateway_redaction` via the real package import (`from tools import ... as ...`),
not the `importlib.util` sibling-loading idiom the 3 other `knowledge_gateway_*` modules use for
*their* sibling loads. This is a deliberate choice, not an inconsistency: a package-style import
guarantees this module always references the exact same module *object* that
`tests/tools/test_retrieval_cache.py`/`tests/tools/test_knowledge_gateway_redaction.py`/
`tests/tools/test_knowledge_gateway_mcp.py`'s own `_isolated_cache_db` fixture already import via
`from tools import retrieval_cache as rc` — a sibling-loaded copy would be a *second*, independent
module object with its own `CACHE_DB_PATH`/`_write_locks`, silently defeating any
`monkeypatch.setattr(rc, ...)`-based test isolation or `monkeypatch.setattr(kgr, "evaluate_write_candidate", ...)`-
style spy. Since this module (unlike the other 3) is only ever reached via
`tools/knowledge_gateway_mcp.py`'s own sibling-loading (never imported by `python -m` package path
directly), it bootstraps its own `sys.path` entry for the repo root before importing, so the choice
works identically whether the whole process was started via `python3 tools/knowledge_gateway_mcp.py`
(script mode, `sys.path[0]` == `tools/`) or via pytest (`pythonpath = ["."]` already on `sys.path`).

`ROUTING_POLICY_VERSION` (DD7) lives here, not in `tools/knowledge_gateway_router.py` (explicit
Out of Scope) — it versions this module's own *assumption* about that frozen module's routing-table
shape, not a property the router itself exposes.

Reuse of `tools.retrieval_cache`'s private `_normalize_query()`/`_hash_text()` (Step 5): the
identity contract's own text says a future implementation "should reuse the same normalize-then-
hash shape, not invent a second one" — this module takes that instruction at face value and calls
those two functions directly rather than duplicating them, a deliberate difference from the sibling
redaction ticket's own choice to duplicate `_hash_text()` rather than reach into another module's
private surface (that ticket had no equivalent reuse instruction from its contract doc).

Built for TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import retrieval_cache as rc  # noqa: E402
from tools import knowledge_gateway_redaction as rk  # noqa: E402

_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_CAPS_PATH_BY_PROVIDER: dict[str, Path] = {
    "context_search": _CONTRACTS_DIR / "provider_capabilities_context_search.json",
    "graphify": _CONTRACTS_DIR / "provider_capabilities_graphify.json",
}

# ---------------------------------------------------------------------------
# Step 1 — constants
# ---------------------------------------------------------------------------

ROUTING_POLICY_VERSION: int = 1  # DD7 — versions this module's assumption about
                                  # knowledge_gateway_router.py's routing-table shape (ROUTING_TABLE's
                                  # 7 rows plus _match_identifier's fixed matcher order). Bump only if
                                  # a future router change would invalidate previously-cached lookup
                                  # identities.

_BUDGET_CLASS_SMALL_MAX = 500     # DD8 — reused from redaction_retention_policy.md §8's
_BUDGET_CLASS_MEDIUM_MAX = 2000   # provisional buckets (small/medium/large).


def compute_budget_class(budget_tokens: int) -> str:
    if budget_tokens <= _BUDGET_CLASS_SMALL_MAX:
        return "small"
    if budget_tokens <= _BUDGET_CLASS_MEDIUM_MAX:
        return "medium"
    return "large"


# ---------------------------------------------------------------------------
# Step 5 — lookup identity (§1)
# ---------------------------------------------------------------------------

_IDENTIFIER_CATEGORY_TO_FORM = {
    "ticket_id": "ticket:{}",
    "parity_id": "parity:{}",
    "registered_doc_path": "doc:{}",
    "subsystem_id": "subsystem:{}",
    "symbol_name": "symbol:{}",
    # "source_path" intentionally absent — DD6, no closed form exists in
    # evidence_cache_identity_contract.md §1 for this category (a real, frozen-contract
    # limitation, not an oversight this module has authority to "helpfully" patch).
}


def compute_resolved_entity_ids(routing_decision) -> list[str]:
    """Maps `routing_decision.matched_identifier` onto §1's 5 closed deterministic
    `resolved_entity_ids` forms (DD6). Returns `[]` for no match, an ambiguous fallback, or a
    `source_path` match (the one category with no closed form)."""
    match = routing_decision.matched_identifier
    if match is None:
        return []
    form = _IDENTIFIER_CATEGORY_TO_FORM.get(match.category)
    if form is None:
        return []
    return [form.format(match.value)]


def _current_repo_branch_scope() -> str:
    """Independent of `tools/knowledge_gateway_mcp.py::_git_branch_scope()` (this module is loaded
    BY that file, not the other way around — importing it back would be circular). Single atomic
    `git branch --show-current` read (DD11 — no TOCTOU risk of its own)."""
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=str(_REPO_ROOT),
        capture_output=True, text=True,
    ).stdout.strip() or "DETACHED"
    return f"{_REPO_ROOT}::{branch}"


def compute_lookup_identity(request: dict, routing_decision, effective_budget: int) -> dict:
    """Returns the §1 6-field lookup-identity tuple as a plain dict, plus the derived
    `query_hash` primary-key component. Called once per request — `routing_decision` is the
    just-computed real decision from `route()` (DD1's hook placement runs the cache-check after
    `route()`, not before, since `resolved_entity_ids` structurally requires it)."""
    filters = {
        k: request[k] for k in ("mode", "include_history", "evidence_detail") if k in request
    }
    normalized_intent = rc._normalize_query(request["query"])
    return {
        "normalized_intent": normalized_intent,
        "resolved_entity_ids_json": json.dumps(sorted(compute_resolved_entity_ids(routing_decision))),
        "filters_json": json.dumps(filters, sort_keys=True),
        "budget_class": compute_budget_class(effective_budget),
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "repo_branch_scope": _current_repo_branch_scope(),
        "query_hash": rc._hash_text(normalized_intent),
    }


# ---------------------------------------------------------------------------
# Step 6 — evidence-validity revalidation + branch/working-tree scope (§2/§3/§4/§5)
# A genuinely separate step from Step 5's lookup identity (DD9 — Non-collapse rule).
# ---------------------------------------------------------------------------

def select_validation_basis(capability_descriptor: dict) -> str:
    """§4's fallback rule, structural form. Returns 'PROVIDER_GENERATION' when the descriptor
    does not advertise `fine_grained_fingerprints`; 'FINER' otherwise. Never the default when
    finer evidence IS available (AC3)."""
    return "PROVIDER_GENERATION" if not capability_descriptor.get("fine_grained_fingerprints") else "FINER"


def _capability_descriptor_for(providers_selected: list[str]) -> dict:
    """Conservative merge over the real capability descriptors of every provider this request's
    routing decision selected: `fine_grained_fingerprints` is True only if *every* consulted
    provider's real descriptor advertises it — a mixed-capability provider set must never let a
    coarser provider's evidence be treated as finer-grained than it really is (AC3). Loaded fresh
    from disk on every call, mirroring `knowledge_gateway_router.py::load_capability_descriptor()`'s
    own "read fresh every call" precedent."""
    descriptors = [
        json.loads(_CAPS_PATH_BY_PROVIDER[pid].read_text())
        for pid in providers_selected
        if pid in _CAPS_PATH_BY_PROVIDER
    ]
    if not descriptors:
        return {"fine_grained_fingerprints": False}
    return {"fine_grained_fingerprints": all(d.get("fine_grained_fingerprints") for d in descriptors)}


def _adapter_versions_for(providers_consulted: list[str]) -> dict:
    versions: dict = {}
    for pid in providers_consulted:
        path = _CAPS_PATH_BY_PROVIDER.get(pid)
        if path is None:
            continue
        versions[pid] = json.loads(path.read_text()).get("adapter_version")
    return versions


def is_branch_compatible(row_repo_branch_scope: str, current_repo_branch_scope: str) -> bool:
    """§5 rule 2 — hard partition, checked before any fingerprint comparison."""
    return row_repo_branch_scope == current_repo_branch_scope


def working_tree_overlap_forces_revalidation(evidence_paths_json: str, changed_paths: list[str]) -> bool:
    """§5 rule 3 — changed_paths ∩ evidence dependency paths only, never a full-tree hash.
    `changed_paths` is read once by the caller from the validated request dict (DD11) and passed
    through unchanged — this function never re-queries git."""
    evidence_paths = set(json.loads(evidence_paths_json))
    return bool(evidence_paths & set(changed_paths))


def revalidate_cache_row(
    row: dict, *, capability_descriptor: dict, current_provider_generation: str,
    current_evidence_fingerprint: str | None, changed_paths: list[str],
) -> bool:
    """True = still valid (serve as a genuine HIT). False = stale (treat as MISS, refresh).
    A distinct step from the lookup (Step 2/DD9) — consulted only after a lookup hit."""
    if working_tree_overlap_forces_revalidation(row["working_tree_overlap"], changed_paths):
        return False
    basis = select_validation_basis(capability_descriptor)
    if basis == "PROVIDER_GENERATION":
        # Hard rule (§4): a SYMBOL/FILE-backed row (finer fingerprint recorded) must never be
        # invalidated by a bare PROVIDER_GENERATION bump alone.
        if (row.get("evidence_fingerprints") or "").startswith(("symbol:", "file:")):
            return True
        return row["provider_generation_at_validation"] == current_provider_generation
    return row["evidence_fingerprints"] == current_evidence_fingerprint


# ---------------------------------------------------------------------------
# Step 7 — perform_cache_lookup() orchestrator
# ---------------------------------------------------------------------------

def perform_cache_lookup(request: dict, routing_decision, effective_budget: int) -> dict | None:
    """Returns the cached response payload dict on a genuine, revalidated HIT; `None` on any
    MISS/stale result. Bumps hit stats only on a genuine hit (never on a bare lookup hit)."""
    identity = compute_lookup_identity(request, routing_decision, effective_budget)
    lookup = rc.check_provider_result_cache(
        identity["query_hash"], identity["repo_branch_scope"],
        normalized_intent=identity["normalized_intent"], filters_json=identity["filters_json"],
        budget_class=identity["budget_class"], routing_policy_version=identity["routing_policy_version"],
    )
    if lookup.status != rc.HIT:
        return None
    if not is_branch_compatible(lookup.row["repo_branch_scope"], identity["repo_branch_scope"]):
        return None
    capability_descriptor = _capability_descriptor_for(routing_decision.providers_selected)
    valid = revalidate_cache_row(
        lookup.row, capability_descriptor=capability_descriptor,
        current_provider_generation=rc._corpus_generation(),
        current_evidence_fingerprint=None,  # PROVIDER_GENERATION-only for both real providers today
        changed_paths=request.get("changed_paths", []),
    )
    if not valid:
        return None
    rc.record_provider_result_cache_hit(identity["query_hash"], identity["repo_branch_scope"])
    return json.loads(lookup.row["result_payload"])


# ---------------------------------------------------------------------------
# Step 8 — perform_cache_write() orchestrator
# ---------------------------------------------------------------------------

# Response keys stripped from the cached payload before redaction/storage — both describe this
# particular call's cache outcome, not stored evidence, and are freshly recomputed on every future
# read (a HIT sets them fresh; they must never be replayed verbatim from a prior write).
_RESPONSE_KEYS_EXCLUDED_FROM_CACHE_PAYLOAD = frozenset({"cache", "cache_key_version"})


def perform_cache_write(request: dict, routing_decision, response: dict, effective_budget: int) -> None:
    """Fire-and-forget from the caller's perspective (the caller wraps this in try/except for
    fail-open semantics) — never returns the write outcome to the response.

    Deliberate refinement of plan.md Step 8's literal signature (`packet` swapped for the
    already-fully-built `response` dict): plan.md's own Anti-Drift Notes require reusing "the same
    field set tools/knowledge_gateway_mcp.py's existing _omit_none()-based response building
    already constructs, to avoid two different serializations of the same packet fields." The most
    direct way to satisfy that is to serialize the same `response` dict `_run_knowledge_context()`
    already finished building (right before schema validation), rather than re-deriving a second,
    parallel serialization from the raw `PacketAssembly` dataclass here. Recorded per CLAUDE.md's
    never-silently-deviate rule; see this ticket's plan.md Deviations section.

    Never writes a PARTIAL-status response (budget-assembly failure or a real provider failure,
    per assemble_packet()'s own status derivation) — a degraded result is not a stable outcome
    worth replaying on a future identical request; a retry moments later may fully succeed. This
    also structurally prevents ever caching a provider_failures-bearing response as if it were a
    genuine answer (a real regression this ticket's own implementation surfaced against
    tests/tools/test_knowledge_gateway_failure_semantics.py's existing sequential-failure-mode
    tests — recorded in plan.md Deviations, not silently patched over)."""
    if response.get("status") == "PARTIAL":
        return
    identity = compute_lookup_identity(request, routing_decision, effective_budget)
    cache_key = f"{identity['query_hash']}:{identity['repo_branch_scope']}"
    if not rk.acquire_write_guard(cache_key):
        return  # another in-process write for this exact key is already in flight
    try:
        if not rk.check_db_size_within_limit(rc.CACHE_DB_PATH):
            return  # §9 ceiling — skip write, still return the live result to the caller

        providers_consulted = response.get("providers_consulted_this_call", [])
        source_type = (
            rk.SOURCE_TYPE_CONTEXT_SEARCH
            if "context_search" in providers_consulted
            else rk.SOURCE_TYPE_GRAPHIFY
        )
        raw_payload = json.dumps(
            {
                k: v
                for k, v in response.items()
                if k not in _RESPONSE_KEYS_EXCLUDED_FROM_CACHE_PAYLOAD
            },
            sort_keys=True,
        )
        decision = rk.evaluate_write_candidate(source_type=source_type, raw_content=raw_payload)
        if decision.verdict != rk.ALLOW:
            return

        provider_generation = rc._corpus_generation()
        context_entries = response.get("context", [])
        source_paths = sorted({c["path"] for c in context_entries if c.get("path")})
        rc.write_provider_result_cache(
            query_hash=identity["query_hash"],
            normalized_intent=identity["normalized_intent"],
            resolved_entity_ids_json=identity["resolved_entity_ids_json"],
            filters_json=identity["filters_json"],
            budget_class=identity["budget_class"],
            routing_policy_version=identity["routing_policy_version"],
            repo_branch_scope=identity["repo_branch_scope"],
            provider_name_json=json.dumps(sorted(providers_consulted)),
            adapter_version_json=json.dumps(_adapter_versions_for(providers_consulted)),
            result_payload=decision.redacted_payload,
            source_ids_json=json.dumps(sorted({c["source_id"] for c in context_entries if c.get("source_id")})),
            source_paths_json=json.dumps(source_paths),
            provider_generation=provider_generation,
            evidence_fingerprints_json=f"generation:{'+'.join(sorted(providers_consulted))}@{provider_generation}",
            validated_negative_scopes=None,  # honest omission — see plan.md Step 8 notes
            adapter_version_at_validation_json=json.dumps(_adapter_versions_for(providers_consulted)),
            working_tree_overlap_json=json.dumps(source_paths),
            provider_generation_at_validation=provider_generation,
            redaction_policy_version=decision.redaction_policy_version,
        )
    finally:
        rk.release_write_guard(cache_key)
