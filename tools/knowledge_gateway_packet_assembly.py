"""Deterministic, extractive/template packet assembly for the Knowledge Gateway MCP Phase 1
(TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY).

Given a `RoutingDecision` (`tools/knowledge_gateway_router.py:315-323`) plus the original query
text, this module independently calls the two real providers named in
`RoutingDecision.providers_selected` — `tools/search_mcp.py::_run_search()` for `context_search`,
`tools/knowledge_gateway_router.py::match_symbol_name()` for `graphify` — and assembles a plain
typed `PacketAssembly` record: extractive `statements[]` (verbatim quotes of real provider
excerpts/stdout, never paraphrased or model-generated, per
`docs/plans/knowledge-gateway-mcp-proposal.md` §9.1), `context[]`/`evidence[]` built from the same
candidates using the 8 closed evidence-identity-kind forms
(`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`), an
honestly-scoped `NegativeClaimSupport` record (§13.1), structural-only `conflicts[]` (§14), and
§15 token-budgeted assembly using the real `kgmcp_char_heuristic_v1` callable with
dedup-before-truncation and the §16 budget-assembly-failure fallback.

Honesty notes (do not "fix" these by inventing heuristics — see the ticket's Anti-Drift Notes):

- `build_negative_claim_support()` is real, fully-branching logic, but with no `validated_scopes`
  ever threaded through today (`assemble_packet()`'s own single auto-trigger call site never
  supplies one — see TCK-20260816-KGMCP-P4-PARITY-ADAPTER's disclosed, deliberately deferred
  `validated_scopes`-threading gap) it can only ever return `verification="UNVERIFIED"` against a
  real, non-monkeypatched call, even though a third real provider (`parity_ledger`) now declares
  `negative_knowledge_support: "SCOPED"`. The `SCOPED`/`COMPLETE` branches are reachable only via
  a monkeypatched/temp-copy capability descriptor in tests — never exercised end-to-end against
  real provider data yet.
- `build_conflicts()` is real, tested logic that inspects explicit structural supersession/
  incompatibility signal keys on provider result dicts. Neither `_run_search()`'s nor
  `match_symbol_name()`'s real return shape exposes any such key today, so against real providers
  this always returns `[]`. No semantic/topical-similarity comparison is implemented — that is
  explicitly deferred to Phase 6.
- `Statement.priority_tier` defaults to `1` for negative-claim signals and `2` for ordinary
  context_search/graphify statements — the only two tiers any real Phase 1 provider call
  justifies. Tiers 3-5 exist and are fully supported by `assemble_within_budget()`'s generic
  sort/truncate logic, but are only reachable via directly-constructed `Statement` fixtures.
- `_evidence_id_for_graphify_result()` uses the literal queried string as a SYMBOL kind's
  qualified-name component (`symbol:<query_text>`) — `match_symbol_name()`'s raw `graphify query`
  stdout has no structured field to parse a true fully-qualified symbol name from without
  interpretation, which would violate §9.1's extractive-only mandate.

`tools/knowledge_gateway_router.py` is only ever imported/called from this module, never modified
— it is DONE and already ledgered (INFRA-335). No MCP server code, no caching, no
model-generated synthesis, and no durable claim/promotion records are introduced anywhere in this
module — §13's `FACT`/`INFERENCE`/`DECISION` labels are ephemeral, in-response-only labels on the
returned `PacketAssembly`.

Module layout follows `tools/knowledge_gateway_router.py`'s and `tools/search_mcp.py`'s own
precedent: single flat file directly under `tools/` (no `__init__.py`-based subpackage), so this
module stays covered by the router ticket's own `tools/*.py`-glob anti-drift guard tests.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"

_CONTRACTS_DIR = _REPO_ROOT / "docs" / "engine" / "contracts" / "knowledge_gateway_mcp"
_CONTEXT_SEARCH_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_context_search.json"
_GRAPHIFY_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_graphify.json"
_PARITY_CAPS_PATH = _CONTRACTS_DIR / "provider_capabilities_parity_ledger.json"

_PROVIDER_CAPS_PATHS: dict[str, Path] = {
    "context_search": _CONTEXT_SEARCH_CAPS_PATH,
    "graphify": _GRAPHIFY_CAPS_PATH,
    "parity_ledger": _PARITY_CAPS_PATH,
}

_NEGATIVE_KNOWLEDGE_NONE = "NONE"
_NEGATIVE_KNOWLEDGE_COMPLETE = "COMPLETE"


# ── Step 1: kgmcp_char_heuristic_v1 — real callable ───────────────────────────

def kgmcp_char_heuristic_v1(text: str) -> int:
    """The reproducible, dependency-free token-counting method ratified at
    `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8:
    `token_count ~= ceil(len(text.encode("utf-8")) / 4)`. This is the first real callable
    implementing that formula — no tokenizer library dependency is added.
    """
    return math.ceil(len(text.encode("utf-8")) / 4)


# ── Step 2: Evidence-identity derivation helpers ──────────────────────────────

_TICKET_PATH_RE = re.compile(r"^tickets/(?:inprogress|done)/(TCK-\d{8}-[A-Z0-9-]+)\.md$")
_SLUG_NONALNUM_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    return _SLUG_NONALNUM_RE.sub("-", text.lower()).strip("-")


def _evidence_id_for_context_search_result(result: dict, anchor_counts: dict[str, int]) -> str:
    """`result` is one element of `_run_search()`'s real return list. `doc_id` is a
    chunk-scoped retrieval ID, not a `docs/REGISTRY.yaml` registry-id, and is never used as the
    identity component — `source_path` is the correct registry-id-shaped field
    (`match_registered_doc_path()` already treats this same repo-relative-path form as a
    registry-id lookup key). `anchor_counts` is caller-owned, per-assembly-call state (never a
    module global) so duplicate-anchor disambiguation (`evidence_identity_kinds.schema.json`'s
    documented "second `## Overview` becomes `...#overview-2`" rule) stays scoped to one packet.
    """
    source_path = result["source_path"]

    if source_path.startswith("docs/"):
        anchor_source = result.get("heading") or result.get("section") or ""
        anchor = _slugify(anchor_source)
        key = f"{source_path}#{anchor}"
        count = anchor_counts.get(key, 0) + 1
        anchor_counts[key] = count
        if count > 1:
            anchor = f"{anchor}-{count}"
        return f"doc:{source_path}#{anchor}"

    ticket_match = _TICKET_PATH_RE.match(source_path)
    if ticket_match:
        return f"ticket:{ticket_match.group(1)}"

    return f"file:{source_path}"


def _evidence_id_for_graphify_result(query_text: str) -> str:
    """SYMBOL kind, using the literal queried string as the qualified-name component — the
    closest available proxy given `match_symbol_name()`'s unstructured stdout (see module
    docstring's honesty note). `query_text` is also exactly the value `match_symbol_name()`
    itself echoes back as its own `"symbol"` field, so this reuses the provider's own naming.
    """
    return f"symbol:{query_text}"


# ── Step 3: Provider-calling layer ────────────────────────────────────────────

def _load_search_mcp_module():
    key = "kgmcp_packet_assembly_search_mcp"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _TOOLS_DIR / "search_mcp.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _load_router_module():
    key = "kgmcp_packet_assembly_router"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, _TOOLS_DIR / "knowledge_gateway_router.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def call_providers_for_routing_decision(routing_decision, query_text: str) -> dict:
    """Independently calls the providers named in `routing_decision.providers_selected` — never
    `providers_consulted`, which stays empty except on the router's own ambiguous-fallback path.
    Returns `{"context_search": <raw _run_search() list | None>, "graphify": <raw
    match_symbol_name() dict | None>, "failures": list[str]}`. This is a second, independent
    invocation of the same read-only operations the router already performs internally on its
    ambiguous path — a documented latency/redundancy cost, never a correctness issue, and never a
    reason to modify the frozen router.
    """
    results: dict = {"context_search": None, "graphify": None, "parity_ledger": None, "failures": []}

    for provider_id in routing_decision.providers_selected:
        if provider_id == "context_search":
            _sm = _load_search_mcp_module()
            raw = _sm._run_search(query_text)
            if isinstance(raw, dict) and "error" in raw:
                results["failures"].append(f"context_search: {raw['error']}")
            else:
                results["context_search"] = raw
        elif provider_id == "graphify":
            _kgr = _load_router_module()
            try:
                raw = _kgr.match_symbol_name(query_text)
            except subprocess.TimeoutExpired:
                results["failures"].append("graphify: subprocess timeout")
                continue
            except FileNotFoundError:
                results["failures"].append("graphify: binary not found on PATH")
                continue
            if raw["returncode"] != 0:
                results["failures"].append(f"graphify: subprocess exited with code {raw['returncode']}")
                continue
            if not raw["stdout"].strip():
                # A successful call that legitimately found nothing is not a failure — absence,
                # not error (Step 6's negative-knowledge framing still governs this case only).
                continue
            results["graphify"] = raw
        elif provider_id == "parity_ledger":
            _kgr = _load_router_module()
            _pidx = _kgr._load_parity_index_module()
            try:
                raw = _kgr._run_parity_provider(query_text)
            except _pidx.IndexNotBuiltError as exc:
                results["failures"].append(
                    f"parity_ledger: index not built -- run `python3 tools/parity_index.py build` ({exc})"
                )
                continue
            results["parity_ledger"] = raw
        # else: no call function exists for "registry"/"working_log" — building one is new
        # provider-integration work outside this ticket's scope; silently skipped rather than
        # inventing a call.

    return results


# ── Step 4: Extractive statement/context/evidence construction ───────────────

@dataclass(frozen=True)
class Statement:
    statement_id: str
    text: str
    classification: str
    evidence_ids: list[str]
    priority_tier: int
    verification: Optional[str] = None
    evidence_hash: Optional[str] = None


@dataclass(frozen=True)
class ContextEntry:
    kind: str
    summary: str
    source_id: str
    path: Optional[str]
    evidence_hash: str
    authority: Optional[str]


@dataclass(frozen=True)
class EvidenceEntry:
    evidence_id: str
    source_id: str
    path: Optional[str]
    evidence_hash: str


def _content_hash(text: str) -> str:
    """Single source of truth for the content-hash formula used both for
    ContextEntry/EvidenceEntry.evidence_hash (render_candidates()) and as _dedup_key()'s
    hash-based fallback for directly-constructed Statement test fixtures. Strips text
    internally so callers may pass either already-stripped or raw text safely -- render_
    candidates() passes already-stripped text (a no-op re-strip), _dedup_key()'s fallback
    passes statement.text directly.
    """
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def render_candidates(
    provider_results: dict, query_text: str
) -> tuple[list[Statement], list[ContextEntry], list[EvidenceEntry]]:
    """Builds `Statement`/`ContextEntry`/`EvidenceEntry` from real provider results only.
    `evidence_id` is derived in the same loop iteration as its statement — structural
    traceability, not a separate documentation step. Never stores a provider's raw, unprocessed
    result blob anywhere — only the rendered `text` derived here.
    """
    statements: list[Statement] = []
    context_entries: list[ContextEntry] = []
    evidence_entries: list[EvidenceEntry] = []
    anchor_counts: dict[str, int] = {}
    n = 0

    for result in provider_results.get("context_search") or []:
        n += 1
        text = result["excerpt"].strip()
        source_path = result["source_path"]
        evidence_id = _evidence_id_for_context_search_result(result, anchor_counts)
        evidence_hash = _content_hash(text)

        statements.append(
            Statement(
                statement_id=f"stmt-{n:03d}",
                text=text,
                classification="FACT",
                evidence_ids=[evidence_id],
                priority_tier=2,
                verification="SUPPORTED",
                evidence_hash=evidence_hash,
            )
        )
        context_entries.append(
            ContextEntry(
                kind="context_search",
                summary=text,
                source_id=evidence_id,
                path=source_path,
                evidence_hash=evidence_hash,
                authority=None,
            )
        )
        evidence_entries.append(
            EvidenceEntry(
                evidence_id=evidence_id,
                source_id=evidence_id,
                path=source_path,
                evidence_hash=evidence_hash,
            )
        )

    graphify_result = provider_results.get("graphify")
    if graphify_result is not None:
        n += 1
        text = graphify_result["stdout"].strip()
        evidence_id = _evidence_id_for_graphify_result(query_text)
        evidence_hash = _content_hash(text)

        statements.append(
            Statement(
                statement_id=f"stmt-{n:03d}",
                text=text,
                classification="FACT",
                evidence_ids=[evidence_id],
                priority_tier=2,
                verification="SUPPORTED",
                evidence_hash=evidence_hash,
            )
        )
        context_entries.append(
            ContextEntry(
                kind="graphify",
                summary=text,
                source_id=evidence_id,
                path=None,
                evidence_hash=evidence_hash,
                authority=None,
            )
        )
        evidence_entries.append(
            EvidenceEntry(
                evidence_id=evidence_id,
                source_id=evidence_id,
                path=None,
                evidence_hash=evidence_hash,
            )
        )

    parity_result = provider_results.get("parity_ledger")
    if parity_result is not None and parity_result["results"].get("found") is True:
        n += 1
        record = parity_result["results"]["record"]
        text = record["text"].strip()
        evidence_id = f"parity:{record['id']}"
        evidence_hash = record["canonical_fragment_hash"]
        source_path = f"docs/parity_ledger/{record['shard']}"

        statements.append(
            Statement(
                statement_id=f"stmt-{n:03d}",
                text=text,
                classification="FACT",
                evidence_ids=[evidence_id],
                priority_tier=2,
                verification="SUPPORTED",
                evidence_hash=evidence_hash,
            )
        )
        context_entries.append(
            ContextEntry(
                kind="parity_ledger",
                summary=text,
                source_id=evidence_id,
                path=source_path,
                evidence_hash=evidence_hash,
                authority=None,
            )
        )
        evidence_entries.append(
            EvidenceEntry(
                evidence_id=evidence_id,
                source_id=evidence_id,
                path=source_path,
                evidence_hash=evidence_hash,
            )
        )

    return statements, context_entries, evidence_entries


# ── Step 5: Deduplication before truncation ───────────────────────────────────

def _dedup_key(statement: Statement) -> str:
    if statement.evidence_hash is not None:
        return statement.evidence_hash
    return _content_hash(statement.text)


def _conflict_signal_index_pairs(
    context_search_results: list[dict], graphify_result: Optional[dict]
) -> set[frozenset[int]]:
    """Lightweight companion to build_conflicts() (Step 7): reuses the identical
    _structural_supersession_signal() detection primitive build_conflicts() already calls -- this
    is NOT a second, parallel conflict-detection heuristic, just an earlier, index-pair-only use of
    the same real function. Index i here corresponds 1:1 to statements[i] as returned by
    render_candidates(), because both functions iterate context_search_results in the same order
    and append graphify_result last, if present (verified directly against render_candidates()'s
    own loop order). As of TCK-20260816-KGMCP-P4-PARITY-ADAPTER, render_candidates() also appends
    a third, parity_ledger-sourced statement/context/evidence block after the graphify block when
    present -- that block is deliberately excluded from this function's (and build_conflicts()'s)
    index-pair/conflict detection, since conflict detection over parity data is not requested by
    any acceptance criterion for that ticket.
    """
    all_results = list(context_search_results)
    if graphify_result is not None:
        all_results.append(graphify_result)

    pairs: set[frozenset[int]] = set()
    for i, result_a in enumerate(all_results):
        for j, result_b in enumerate(all_results[i + 1:], start=i + 1):
            if _structural_supersession_signal(result_a, result_b) is not None:
                pairs.add(frozenset({i, j}))
    return pairs


def deduplicate_statements(
    statements: list[Statement],
    conflict_index_pairs: Optional[set[frozenset[int]]] = None,
) -> list[Statement]:
    """Groups by content-hash identity (mechanical/structural, never a semantic-similarity
    judgment — §14's ban on semantic judgment governs *conflict* detection, not this §15-required
    dedup step) — the same fingerprint concept
    `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` establishes
    for its content-bearing kinds, via `_dedup_key()`/`_content_hash()`. Keyed only on rendered
    text's hash, never on provider — handles both same-provider duplicate chunks and the
    cross-provider case identically. For each duplicate group, the first-encountered statement
    survives; every other member's `evidence_ids` merge into it, order-preserved, no duplicate IDs.

    `conflict_index_pairs` (optional, per Gap 2/AC4): a set of index pairs into the same raw
    provider-result ordering `render_candidates()` used to build `statements[]`, identifying
    results flagged as mutually conflicting via `_structural_supersession_signal()`. If two
    statements would otherwise collapse into the same dedup group *and* their original indices are
    a known conflict-flagged pair, the later statement is forced into its own distinct group
    instead of being silently merged — two conflict-flagged items must never collapse into one
    even when their rendered text happens to be identical.
    """
    conflict_index_pairs = conflict_index_pairs or set()
    order: list[str] = []
    groups: dict[str, Statement] = {}
    group_anchor_index: dict[str, int] = {}

    for idx, statement in enumerate(statements):
        key = _dedup_key(statement)
        if key in groups and frozenset({idx, group_anchor_index[key]}) in conflict_index_pairs:
            # Conflict-flagged pair renders identical text -- must never silently merge (AC4/§14).
            # Force this statement into its own distinct group instead of collapsing it.
            key = f"{key}::conflict-{idx}"
        if key not in groups:
            groups[key] = statement
            group_anchor_index[key] = idx
            order.append(key)
            continue
        existing = groups[key]
        merged_ids = list(existing.evidence_ids)
        for evidence_id in statement.evidence_ids:
            if evidence_id not in merged_ids:
                merged_ids.append(evidence_id)
        groups[key] = replace(existing, evidence_ids=merged_ids)

    return [groups[key] for key in order]


# ── Step 6: NegativeClaimSupport (honestly-scoped) ────────────────────────────

@dataclass(frozen=True)
class NegativeClaimSupport:
    statement: str
    subject_ids: list[str]
    validated_scopes: list[str]
    scope_evidence_dependencies: list[str]
    providers_and_adapter_versions: list[str]
    exclusions_or_blind_spots: list[str]
    checked_at: str
    verification: str


def build_negative_claim_support(
    statement: str,
    subject_ids: list[str],
    provider_ids: list[str],
    validated_scopes: Optional[list[str]] = None,
) -> NegativeClaimSupport:
    """Real, fully-branching §13.1 logic. Loads all real capability descriptors fresh from disk
    each call (no module-level cache, mirroring the router's own convention) — this module defines
    its own `_PROVIDER_CAPS_PATHS` rather than importing the router's private constants.

    With no `validated_scopes` ever threaded through today (see module docstring), this always
    returns `verification="UNVERIFIED"` against a real, non-monkeypatched call — even though
    `parity_ledger`'s real descriptor now declares `negative_knowledge_support: "SCOPED"`. Never
    let a real call reach `"VERIFIED"`/`"SUPPORTED"`; only a monkeypatched/temp-copy descriptor
    declaring `"SCOPED"`/`"COMPLETE"` combined with a caller-supplied `validated_scopes` can do so.
    """
    validated_scopes = list(validated_scopes) if validated_scopes else []
    checked_at = datetime.now(timezone.utc).isoformat()

    contributing: list[tuple[str, dict]] = []
    adapter_versions: list[str] = []
    for provider_id in provider_ids:
        caps_path = _PROVIDER_CAPS_PATHS.get(provider_id)
        if caps_path is None:
            continue
        descriptor = json.loads(caps_path.read_text())
        adapter_versions.append(f"{provider_id}@{descriptor.get('adapter_version')}")
        if descriptor["negative_knowledge_support"] != _NEGATIVE_KNOWLEDGE_NONE:
            contributing.append((provider_id, descriptor))

    if not contributing:
        return NegativeClaimSupport(
            statement=statement,
            subject_ids=list(subject_ids),
            validated_scopes=[],
            scope_evidence_dependencies=[],
            providers_and_adapter_versions=adapter_versions,
            exclusions_or_blind_spots=[
                f"{pid}: negative_knowledge_support=NONE — cannot validate absence"
                for pid in provider_ids
            ],
            checked_at=checked_at,
            verification="UNVERIFIED",
        )

    if not validated_scopes:
        return NegativeClaimSupport(
            statement=statement,
            subject_ids=list(subject_ids),
            validated_scopes=[],
            scope_evidence_dependencies=[],
            providers_and_adapter_versions=adapter_versions,
            exclusions_or_blind_spots=[
                f"{pid}: validated_scopes not established as complete" for pid, _ in contributing
            ],
            checked_at=checked_at,
            verification="UNVERIFIED",
        )

    levels = {descriptor["negative_knowledge_support"] for _, descriptor in contributing}
    verification = "VERIFIED" if _NEGATIVE_KNOWLEDGE_COMPLETE in levels else "SUPPORTED"

    return NegativeClaimSupport(
        statement=statement,
        subject_ids=list(subject_ids),
        validated_scopes=validated_scopes,
        scope_evidence_dependencies=[pid for pid, _ in contributing],
        providers_and_adapter_versions=adapter_versions,
        exclusions_or_blind_spots=[],
        checked_at=checked_at,
        verification=verification,
    )


# ── Step 7: Structural-only conflict representation ───────────────────────────

@dataclass(frozen=True)
class ConflictClaim:
    value: str
    source_id: str
    authority: str
    valid_from: str
    valid_to: Optional[str]


@dataclass(frozen=True)
class Conflict:
    subject: str
    claims: list[ConflictClaim]
    automatic_resolution: Optional[str]
    recommended_action: str


def _structural_supersession_signal(result_a: dict, result_b: dict) -> Optional[Conflict]:
    id_a = result_a.get("source_path") or result_a.get("symbol") or ""
    id_b = result_b.get("source_path") or result_b.get("symbol") or ""

    mutually_referencing = (
        result_a.get("superseded_by") == id_b
        or result_a.get("supersedes") == id_b
        or result_b.get("superseded_by") == id_a
        or result_b.get("supersedes") == id_a
        or result_a.get("incompatible_with") == id_b
        or result_b.get("incompatible_with") == id_a
    )
    if not mutually_referencing:
        return None

    return Conflict(
        subject=f"{id_a} vs {id_b}",
        claims=[
            ConflictClaim(
                value=str(result_a.get("excerpt") or result_a.get("stdout") or ""),
                source_id=id_a,
                authority=result_a.get("authority", ""),
                valid_from=result_a.get("valid_from", ""),
                valid_to=result_a.get("valid_to"),
            ),
            ConflictClaim(
                value=str(result_b.get("excerpt") or result_b.get("stdout") or ""),
                source_id=id_b,
                authority=result_b.get("authority", ""),
                valid_from=result_b.get("valid_from", ""),
                valid_to=result_b.get("valid_to"),
            ),
        ],
        automatic_resolution=None,
        recommended_action="human review",
    )


def build_conflicts(
    context_search_results: list[dict], graphify_result: Optional[dict]
) -> list[Conflict]:
    """Real, generic logic that inspects each result dict for explicit structural
    supersession/incompatibility signal keys (`superseded_by`/`supersedes`/`incompatible_with`,
    via `dict.get()` so absence is safe) and only emits a `Conflict` when two results carry
    mutually-referencing or explicitly-incompatible signal values. Neither `_run_search()`'s nor
    `match_symbol_name()`'s real return shape exposes any such key today, so against real
    providers this always returns `[]` — see module docstring. No embedding/similarity/
    keyword-overlap heuristic is used to manufacture a non-empty result.
    """
    all_results = list(context_search_results)
    if graphify_result is not None:
        all_results.append(graphify_result)

    conflicts: list[Conflict] = []
    for i, result_a in enumerate(all_results):
        for result_b in all_results[i + 1:]:
            signal = _structural_supersession_signal(result_a, result_b)
            if signal is not None:
                conflicts.append(signal)
    return conflicts


# ── Step 8: Token-budgeted assembly ───────────────────────────────────────────

def _statement_included_content_cost(
    statement: Statement,
    context_by_id: dict[str, ContextEntry],
    evidence_by_id: dict[str, EvidenceEntry],
) -> int:
    """Real, measured cost of a statement PLUS every context/evidence entry that would ship
    alongside it once included (mirrors assemble_packet()'s own included_evidence_ids filter —
    a statement's evidence_ids is precisely what final_context/final_evidence get filtered by
    downstream, so this sums over the same evidence_ids). Never a length*constant estimate
    (assemble_within_budget()'s own docstring) — every term is a real kgmcp_char_heuristic_v1()
    call on real text/field content actually present on a real ContextEntry/EvidenceEntry.
    """
    cost = kgmcp_char_heuristic_v1(statement.text)
    for evidence_id in statement.evidence_ids:
        ctx = context_by_id.get(evidence_id)
        if ctx is not None:
            cost += kgmcp_char_heuristic_v1(ctx.summary)
        ev = evidence_by_id.get(evidence_id)
        if ev is not None:
            cost += kgmcp_char_heuristic_v1(ev.evidence_id)
            cost += kgmcp_char_heuristic_v1(ev.path or "")
            cost += kgmcp_char_heuristic_v1(ev.evidence_hash)
    return cost


def assemble_within_budget(
    statements: list[Statement],
    budget_requested: int,
    context_entries: Sequence[ContextEntry] = (),
    evidence_entries: Sequence[EvidenceEntry] = (),
) -> tuple[list[Statement], int]:
    """Sorts by `(priority_tier ascending, original candidate order)` — stable, deterministic.
    Greedily accumulates: cost is a real `kgmcp_char_heuristic_v1()` measurement of the exact
    text being included, never `len(candidates) * constant` (the anti-pattern at
    `tools/context_packet_assembler.py:287`). A statement is included only if
    `running_total + cost <= budget_requested`; otherwise assembly stops — this and all remaining
    lower-priority statements are dropped. `budget_returned` is the literal running total, so
    `budget_returned <= budget_requested` holds by construction, not by a post-hoc clamp.

    `context_entries`/`evidence_entries` (optional, default `()`) let the cost of each statement
    include its own matched `ContextEntry.summary`/`EvidenceEntry` fields — real response bytes
    that ship alongside the statement once included (see `_statement_included_content_cost()`).
    With the defaults, cost degrades to exactly `kgmcp_char_heuristic_v1(statement.text)` — not a
    special-cased "legacy mode," just the same formula correctly evaluating to zero extra terms
    when there is nothing to look up.

    Must be called only after `deduplicate_statements()` has already run (§15: "Deduplication
    should occur before truncation").
    """
    ordered_indices = sorted(range(len(statements)), key=lambda i: (statements[i].priority_tier, i))
    context_by_id = {c.source_id: c for c in context_entries}
    evidence_by_id = {e.evidence_id: e for e in evidence_entries}

    included: list[Statement] = []
    running_total = 0
    for i in ordered_indices:
        statement = statements[i]
        cost = _statement_included_content_cost(statement, context_by_id, evidence_by_id)
        if running_total + cost <= budget_requested:
            included.append(statement)
            running_total += cost
        else:
            break

    return included, running_total


def truncate_conflicts_within_budget(
    conflicts: list[Conflict], remaining_budget: int
) -> tuple[list[Conflict], int]:
    """Real-measured, greedy, original-order truncation of conflicts[] against whatever budget
    remains after statement+context+evidence assembly. Cost is the real sum of
    kgmcp_char_heuristic_v1() over each claim's real .value text -- the only prose-bearing field on
    a Conflict/ConflictClaim -- never a length*constant estimate. Never reorders conflicts; drops
    the first conflict (and everything after it in list order) that would overflow, mirroring
    assemble_within_budget()'s own break-on-first-overflow discipline.

    `conflicts[]` is never owned by any single statement (`Conflict.subject` is a
    `source_path`/`symbol` pair string, not linked to any `evidence_id`), so it cannot reuse the
    per-statement mechanism above and gets its own, separate pass.
    """
    included: list[Conflict] = []
    running_total = 0
    for conflict in conflicts:
        cost = sum(kgmcp_char_heuristic_v1(claim.value) for claim in conflict.claims)
        if running_total + cost <= remaining_budget:
            included.append(conflict)
            running_total += cost
        else:
            break
    return included, running_total


# ── Steps 9-10: Budget-failure fallback + top-level orchestrator ─────────────

@dataclass(frozen=True)
class PacketAssembly:
    status: str
    freshness: str
    verification: str
    provenance_providers: list[str]
    providers_consulted_this_call: list[str]
    answer: str
    statements: list[Statement]
    context: list[ContextEntry]
    evidence: list[EvidenceEntry]
    evidence_dependencies: list[str]
    conflicts: list[Conflict]
    budget_requested: int
    budget_returned: int
    budget_truncated: bool
    omitted_statement_count: int
    conflicts_truncated: bool
    omitted_conflict_count: int
    provider_failures: list[str]
    negative_claim_support: Optional[NegativeClaimSupport] = None


def _evidence_dependencies(context_entries: list[ContextEntry]) -> list[str]:
    """Aggregates the packet's real dependency-path set for the Level 2 evidence_dependencies
    column, from the packet's own final `context` items (post-dedup, post-budget-truncation) --
    NOT from `evidence` (`final_evidence`). The two carry identical .path values for every
    context_search-sourced result in the ordinary/truncated branches (same source_id/evidence_id
    filter -- verified by direct trace of render_candidates()/assemble_packet()), but diverge in
    the section-16 budget-assembly-failure branch, where final_context is correctly emptied
    (matching the packet's own empty answer/statements) while final_evidence is deliberately left
    as the full, unfiltered evidence_entries list. Reading final_context keeps
    evidence_dependencies consistent with what the packet actually claims, in every branch,
    without any branch-specific special-casing here. graphify-sourced entries carry path=None
    (symbol-kind evidence is not path-tracked by this module at all, matching Level 1's own
    identical limitation) and contribute nothing -- not a crash, not a literal "None" string.
    """
    return sorted({c.path for c in context_entries if c.path})


def _provider_id_for_evidence_id(evidence_id: str) -> str:
    """Three real providers exist as of TCK-20260816-KGMCP-P4-PARITY-ADAPTER — a SYMBOL-kind
    evidence_id (`symbol:...`) is always graphify-sourced, a PARITY_ENTRY-kind evidence_id
    (`parity:...`) is always parity_ledger-sourced, and every other closed kind this module
    produces (`doc:`/`file:`/`ticket:`) is context_search-sourced.
    """
    if evidence_id.startswith("symbol:"):
        return "graphify"
    if evidence_id.startswith("parity:"):
        return "parity_ledger"
    return "context_search"


def assemble_packet(routing_decision, query_text: str, budget_requested: int) -> PacketAssembly:
    """Top-level orchestrator, fixed order: call providers -> render statements/context/evidence
    -> dedup -> negative-claim auto-trigger (conditional on zero statements) -> conflicts ->
    priority sort + real-measurement truncation -> failure fallback (conditional). This ordering
    is load-bearing and must not be reordered.
    """
    provider_results = call_providers_for_routing_decision(routing_decision, query_text)
    providers_consulted_this_call = [
        pid for pid in routing_decision.providers_selected if pid in _PROVIDER_CAPS_PATHS
    ]

    statements, context_entries, evidence_entries = render_candidates(provider_results, query_text)
    conflict_index_pairs = _conflict_signal_index_pairs(
        provider_results.get("context_search") or [],
        provider_results.get("graphify"),
    )
    assert len(statements) == len(provider_results.get("context_search") or []) + (
        1 if provider_results.get("graphify") else 0
    ) + (
        1 if (provider_results.get("parity_ledger") or {}).get("results", {}).get("found") else 0
    ), (
        "statements[] <-> provider-result index correspondence invariant violated: "
        "_conflict_signal_index_pairs() assumes render_candidates() emits exactly one Statement "
        "per context_search result plus one more iff graphify is present, in that same order. "
        "If this fires, render_candidates() and _conflict_signal_index_pairs()/build_conflicts() "
        "have desynced and AC4's conflict-vs-dedup exclusion can silently misfire."
    )
    statements = deduplicate_statements(statements, conflict_index_pairs)

    negative_claim_support: Optional[NegativeClaimSupport] = None
    if not statements:
        # Structural auto-trigger only — "the real provider call(s) returned nothing" — never a
        # keyword-sniffed guess at whether query_text itself was phrased as a negative claim.
        negative_claim_support = build_negative_claim_support(
            statement=f"no content found for: {query_text}",
            subject_ids=[],
            provider_ids=providers_consulted_this_call,
        )

    conflicts = build_conflicts(
        provider_results.get("context_search") or [],
        provider_results.get("graphify"),
    )

    included_statements, budget_returned = assemble_within_budget(
        statements, budget_requested, context_entries, evidence_entries
    )
    omitted_statement_count = len(statements) - len(included_statements)
    budget_truncated = omitted_statement_count > 0

    # §16 budget-assembly-failure fallback: the budget was too small to admit even the single
    # lowest-cost, highest-priority statement — distinct from ordinary partial truncation, which
    # already leaves >=1 statement included.
    budget_assembly_failed = bool(statements) and not included_statements

    if budget_assembly_failed:
        final_statements: list[Statement] = []
        final_context: list[ContextEntry] = []
        final_evidence = evidence_entries
        answer = ""
        budget_returned = 0
    else:
        included_evidence_ids = {eid for s in included_statements for eid in s.evidence_ids}
        final_statements = included_statements
        final_context = [c for c in context_entries if c.source_id in included_evidence_ids]
        final_evidence = [e for e in evidence_entries if e.evidence_id in included_evidence_ids]
        answer = " ".join(s.text for s in included_statements)

    remaining_budget = max(budget_requested - budget_returned, 0)
    final_conflicts, _conflicts_cost = truncate_conflicts_within_budget(conflicts, remaining_budget)
    omitted_conflict_count = len(conflicts) - len(final_conflicts)
    conflicts_truncated = omitted_conflict_count > 0

    failures = provider_results.get("failures", [])
    if budget_assembly_failed or failures:
        status = "PARTIAL"
    elif final_conflicts:
        status = "CONFLICTED"
    else:
        status = "OK"

    verification = "SUPPORTED" if final_statements else "UNVERIFIED"
    freshness = "UNKNOWN"

    provenance_providers = sorted({
        _provider_id_for_evidence_id(evidence_id)
        for statement in final_statements
        for evidence_id in statement.evidence_ids
    })
    evidence_dependencies = _evidence_dependencies(final_context)

    return PacketAssembly(
        status=status,
        freshness=freshness,
        verification=verification,
        provenance_providers=provenance_providers,
        providers_consulted_this_call=providers_consulted_this_call,
        answer=answer,
        statements=final_statements,
        context=final_context,
        evidence=final_evidence,
        evidence_dependencies=evidence_dependencies,
        conflicts=final_conflicts,
        budget_requested=budget_requested,
        budget_returned=budget_returned,
        budget_truncated=budget_truncated,
        omitted_statement_count=omitted_statement_count,
        conflicts_truncated=conflicts_truncated,
        omitted_conflict_count=omitted_conflict_count,
        provider_failures=failures,
        negative_claim_support=negative_claim_support,
    )
