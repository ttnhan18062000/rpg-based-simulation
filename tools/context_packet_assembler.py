"""
tools/context_packet_assembler.py — Assembles a real `ContextPacket`
(docs/engine/contracts/context_packet_contract.md §2) from three already-built candidate
sources: `tools/hybrid_retrieval.py`'s `HybridResult` list (docs, tickets, investigations,
working-log rows), `tools/code_test_index.py`'s `build_records()` output (code symbols), and
hand-built `parity_ledger_entry`-shaped fixture dicts (the contract's §3 parity branch).

Read-only and standalone: this module does not implement C1's (`hybrid_retrieval.py`) fusion
logic or C3's (`retrieval_cache.py`) cache logic — it only shapes their already-decided output
into the contract's field format — and it is never imported by or referenced from any
`.claude/workflows/*.js` file.

Every adapter below computes a `Candidate.hash` at construction time from the source's raw
excerpt/record and then discards that raw content entirely. `Candidate` itself has no field
capable of holding raw text — this is a structural guarantee against the contract's "assembled
packet never contains raw prompt/chunk text" requirement, not a discipline-only convention.

Built for TCK-20260729-CONTEXT-PACKET-ASSEMBLY.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
from hybrid_retrieval import UNRATED, HybridResult, load_registry_index  # noqa: E402,F401

DEFAULT_EXCERPT_BUDGET: int = 200

# Open Decisions 5/6 (expansion escalation semantics) remain explicitly deferred by
# ticket_plan_structure_phase3.md — a plain string constant so this field can never accidentally
# expose a field resembling real escalation semantics (max_expansions/trigger/threshold).
EXPANSION_POLICY_STUB: str = (
    "not_yet_resolved: Open Decisions 5/6 (expansion escalation semantics) deferred — see "
    "docs/plans/agent_infrastructure/context_efficient_agent_retrieval/"
    "ticket_plan_structure_phase3.md"
)

_AUTHORITY_RANK: tuple[str, ...] = ("P0", "P1", "P2")

# Decision B's literal trigger condition (context_packet_contract.md §3): only docs both
# status:active or status:authoritative on the same subject enter conflict resolution.
_CONFLICT_ELIGIBLE_FRESHNESS: frozenset[str] = frozenset({"active", "authoritative"})


@dataclass(frozen=True)
class Candidate:
    """Normalized intermediate shape every adapter below maps its source into. Deliberately has
    no raw-text field of any kind — every adapter computes `hash` at construction time and
    discards the source text/record immediately, so `Candidate` cannot structurally leak raw
    text into an assembled packet.
    """

    source_id: str
    kind: str
    path: str
    heading_or_symbol: str
    hash: str
    score: float
    authority: str
    freshness: str
    last_verified: str | None = None
    subject_key: str | None = None


@dataclass(frozen=True)
class ContextPacket:
    packet_id: str
    corpus_generation: str
    retrieval_version: int
    budget_requested: int
    budget_returned: int
    included: list[dict]
    excluded_summary: list[dict]
    expansion_policy: str


def _hash_content(content: str | dict | list) -> str:
    """Mirrors retrieval_cache.py's hashlib.sha256(...).hexdigest() over
    json.dumps(..., sort_keys=True) convention inline, rather than importing the private,
    underscore-prefixed `retrieval_cache._hash_text` symbol.
    """
    if isinstance(content, str):
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# code_test_index.py adapter + generic unrated-kind builder (AC1)
# ---------------------------------------------------------------------------

def unrated_candidate(
    *,
    source_id: str,
    kind: str,
    path: str,
    heading_or_symbol: str,
    content_for_hash: str | dict | list,
    score: float = 0.0,
    subject_key: str | None = None,
) -> Candidate:
    """Implements context_packet_contract.md §3's "non-registry-backed source fallback" rule
    (`authority`/`freshness` both `unrated`) for any `kind` value — `code_symbol`, `test`,
    `graphify_node`, or an in-progress ticket body all resolve through this one builder.
    """
    return Candidate(
        source_id=source_id,
        kind=kind,
        path=path,
        heading_or_symbol=heading_or_symbol,
        hash=_hash_content(content_for_hash),
        score=score,
        authority=UNRATED,
        freshness=UNRATED,
        subject_key=subject_key,
    )


def candidate_from_code_index_record(record: dict, *, subject_key: str | None = None) -> Candidate:
    """`record` is one dict from `tools/code_test_index.py::build_records()`'s output —
    `docstring`/`associated_tests` (including the `DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP`
    sentinels) are part of the hashed record but never separately surfaced into a packet field.
    """
    return unrated_candidate(
        source_id=record["id"],
        kind="code_symbol",
        path=record["module"].replace(".", "/") + ".py",
        heading_or_symbol=record["symbol"],
        content_for_hash=record,
        subject_key=subject_key,
    )


# ---------------------------------------------------------------------------
# HybridResult adapter — REGISTRY-backed passthrough + last_verified lookup
# ---------------------------------------------------------------------------

def candidate_from_hybrid_result(
    result: HybridResult, registry_index: dict[str, dict], *, subject_key: str | None = None
) -> Candidate:
    """`authority`/`freshness` pass through verbatim — already resolved by C1's own
    `resolve_metadata()`, so this adapter never re-derives or re-checks REGISTRY membership.
    `hash` is computed once from `result.text`; that raw excerpt is never otherwise referenced.
    """
    heading_or_symbol = result.heading
    if result.section:
        heading_or_symbol = f"{result.heading} / {result.section}"
    return Candidate(
        source_id=result.doc_id,
        kind=result.kind,
        path=result.path,
        heading_or_symbol=heading_or_symbol,
        hash=_hash_content(result.text),
        score=result.rrf_score,
        authority=result.authority,
        freshness=result.freshness,
        last_verified=registry_index.get(result.path, {}).get("last_verified"),
        subject_key=subject_key,
    )


# ---------------------------------------------------------------------------
# Decision B conflict resolution and tie-break (AC2)
# ---------------------------------------------------------------------------

def _resolve_subject_conflicts(candidates: list[Candidate]) -> dict[str, str]:
    """Returns {source_id: inclusion_reason} for every candidate in a same-`subject_key`
    conflict group of two or more `active`/`authoritative` candidates. Candidates with
    `subject_key is None` are never grouped — Decision B only applies to explicitly-marked
    same-subject candidates. Both winner and loser(s) are returned; this function only decides
    `inclusion_reason` text, it never drops a candidate from the eventual included[] list.
    """
    groups: dict[str, list[Candidate]] = {}
    for candidate in candidates:
        if candidate.subject_key is None:
            continue
        groups.setdefault(candidate.subject_key, []).append(candidate)

    reasons: dict[str, str] = {}
    for group in groups.values():
        qualifying = [c for c in group if c.freshness in _CONFLICT_ELIGIBLE_FRESHNESS]
        if len(qualifying) < 2:
            continue
        # Two-pass stable sort: most-recent-first (missing last_verified sorts last, since ""
        # is the lexicographically smallest string), then authority ascending, stable so the
        # prior recency order survives an authority tie.
        by_recency = sorted(qualifying, key=lambda c: c.last_verified or "", reverse=True)
        ranked = sorted(by_recency, key=lambda c: _AUTHORITY_RANK.index(c.authority))
        winner = ranked[0]
        for loser in ranked[1:]:
            reasons[loser.source_id] = f"superseded-by:{winner.source_id}"
    return reasons


# ---------------------------------------------------------------------------
# parity_ledger_entry adapter — Decision A's parity branch (Scope item 2)
# ---------------------------------------------------------------------------

def candidate_from_parity_ledger_fixture(
    entry: dict, *, subject_key: str | None = None
) -> Candidate:
    """`entry` is a hand-built dict shaped like a docs/parity_ledger/schema.json entry (`id`,
    `text`, `status`, `priority`, optionally `path`). `authority`/`freshness` are populated from
    the entry's own `priority`/`status` verbatim — never looked up against or coerced into
    REGISTRY's `AUTHORITY_VALUES`/`STATUS_VALUES` enums, since the parity ledger's 5-value
    `status` vocabulary is not REGISTRY's 4-value `status` vocabulary.
    """
    return Candidate(
        source_id=entry["id"],
        kind="parity_ledger_entry",
        path=entry.get("path", "docs/parity_ledger/infrastructure.yaml"),
        heading_or_symbol=entry["id"],
        hash=_hash_content(entry),
        score=0.0,
        authority=entry["priority"],
        freshness=entry["status"],
        subject_key=subject_key,
    )


# ---------------------------------------------------------------------------
# included[]/excluded_summary[] builders and orchestration (AC3)
# ---------------------------------------------------------------------------

def build_included_entry(
    candidate: Candidate, *, inclusion_reason: str, excerpt_budget: int = DEFAULT_EXCERPT_BUDGET
) -> dict:
    return {
        "source_id": candidate.source_id,
        "kind": candidate.kind,
        "path": candidate.path,
        "heading_or_symbol": candidate.heading_or_symbol,
        "hash": candidate.hash,
        "authority": candidate.authority,
        "freshness": candidate.freshness,
        "score": candidate.score,
        "inclusion_reason": inclusion_reason,
        "excerpt_budget": excerpt_budget,
    }


def build_excluded_summary(excluded: list[tuple[Candidate, str]]) -> list[dict]:
    """Aggregates by (kind, reason); `source_id` is the first-encountered candidate's
    source_id within that group — a representative example, not an exhaustive list.
    """
    groups: dict[tuple[str, str], dict] = {}
    for candidate, reason in excluded:
        key = (candidate.kind, reason)
        if key not in groups:
            groups[key] = {
                "source_id": candidate.source_id,
                "kind": candidate.kind,
                "reason": reason,
                "count": 0,
            }
        groups[key]["count"] += 1
    return list(groups.values())


def assemble_context_packet(
    *,
    packet_id: str,
    corpus_generation: str,
    retrieval_version: int,
    budget_requested: int,
    included_candidates: list[Candidate],
    excluded: list[tuple[Candidate, str]] = (),
) -> ContextPacket:
    reasons = _resolve_subject_conflicts(included_candidates)
    included = [
        build_included_entry(
            candidate, inclusion_reason=reasons.get(candidate.source_id, "included")
        )
        for candidate in included_candidates
    ]
    return ContextPacket(
        packet_id=packet_id,
        corpus_generation=corpus_generation,
        retrieval_version=retrieval_version,
        budget_requested=budget_requested,
        budget_returned=len(included_candidates) * DEFAULT_EXCERPT_BUDGET,
        included=included,
        excluded_summary=build_excluded_summary(list(excluded)),
        expansion_policy=EXPANSION_POLICY_STUB,
    )
