---
status: active
layer: ai
authority: P1
audience: agent
---

# Retrieval Retention and Redaction Policy

## Purpose

This is a decision-only document. No changes land in
`src/observability/reporting/retention.py`, `src/core/retention.py`, or any
`tools/agent-monitoring/*.py` writer as part of this doc.

This doc resolves **Open Decision 4** of
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`:
*"What retention and redaction policy applies to retrieval events and cache entries?"*

The binding constraints come directly from that idea doc:

- **Design Principle 5** (lines 74-76): "Monitoring stores identifiers, hashes, counts, scores, and
  reason codes—not full prompts, full retrieved content, or unredacted tool payloads."
- **Risks table** (lines 305-315), row "Retrieval telemetry leaks sensitive content" — mitigation:
  "Store hashes, IDs, counts, and reason codes only; never raw prompts or chunks."
- **Promotion approval gate** (lines 250-262) lists "monitoring contains no raw prompts, raw
  retrieved source text, or sensitive tool payloads" as one of six conditions required before any
  scenario is promoted from advisory to default — this doc's MAY/PROHIBITED list is the standard
  that future gate check must satisfy.

## MAY-Contain vs PROHIBITED Fields

**MAY contain:**

- Content hashes (of a cited excerpt or source, for staleness detection).
- Source/entity/ticket/run IDs.
- Counts (candidate count, selected count, exclusion counts).
- Reason codes (`inclusion_reason`, exclusion reason, adequacy verdict).
- Scores (ranking score, `authority`/`freshness` ratings).
- Latency.
- Corpus/graph generation and retrieval version numbers.
- Cache level/status (hit / miss / stale-rejected).

**PROHIBITED:**

- Raw prompt text.
- Raw retrieved chunk/source text.
- Full tool payloads (unredacted).
- Any field that reproduces source content rather than referencing it by hash or ID.

This vocabulary is not invented here. `hash` and `score` are already-named
`ContextPacket.included[]` fields per `docs/engine/contracts/context_packet_contract.md` (lines
66-89, the sibling Decision 3 doc) — this doc's MAY-list stays consistent with that field list
rather than introducing competing terminology.

`docs/observability/loki_label_policy.md` is cited here only as **structural** precedent — a
precisely enumerated MAY/PROHIBITED list. Its mechanism (label-cardinality control for Loki
streams, preventing index explosion) is different from this doc's mechanism (content redaction,
preventing sensitive-data leakage), and its literal identifier list (`tick`, `entity_id`,
`worker_id`, `causal_id`, `transaction_id`, `run_id`, `target_id`, `quest_id`) does not apply here.
Do not conflate the two.

## Decision A — "Extending RetentionPolicy's Categories" Is Conceptual, Not a Code Change

This document extends `RetentionPolicy`'s category taxonomy (the `recent_run` /
`important_failed_run` / `baseline_source_run` naming and duration-tiering pattern from
`src/observability/reporting/retention.py` lines 36-57) in prose/design only. The named categories
introduced below (§Decision C) are new categories a future Phase 3+ implementation ticket would add
to `src/observability/reporting/retention.py` or a sibling module — this ticket makes no such code
change, consistent with its own Out of Scope.

## Decision B — Retrieval Events Are Retain-Forever/Redaction-Only; Caches Are Duration-Based

Retrieval *events* (the telemetry records themselves) land in `agent-monitoring/*.jsonl` per the
idea doc's "Retrieval Observability and Dashboard" architecture (lines 188-201).
`docs/agent-monitoring/schema.md` establishes that `runs.jsonl` / `events.jsonl` / `tools.jsonl`
are append-only-forever by explicit documented convention, with no pruning mechanism today — the
"Historical Corrections" section describes exactly one narrow, audited exception (a casing fix to
7 records) and explicitly states the files remain "append-only for all writes going forward."

Retrieval events inherit this convention unchanged: they are **not** a duration-based retention
category. "Retention" for retrieval events means redaction-only — never store raw prompt or
retrieved-content text per the MAY/PROHIBITED list above — the records themselves are never
deleted, exactly like every other row in those three files today.

*Caches* (embedding/index, query-result, context-packet — SQLite-backed per the idea doc's "3.
Cache design" section, lines 137-151) are a genuinely different kind of storage: ephemeral,
rebuildable from source, and explicitly invalidated on defined triggers (content hash / corpus
generation / policy version changes per the idea doc's own Key/Invalidation table). Caches ARE
eligible for duration-based expiry and DO map onto new prose-extension categories of
`RetentionPolicy`'s existing pattern.

The rationale for this split: mixing a duration-based deletion model onto an append-only-forever
convention would either silently break the existing agent-monitoring guarantee (data loss risk on
a system with zero pruning code and an explicit append-only-forever convention) or require
inventing a brand-new writer/pruning mechanism — both out of this ticket's scope (no
`tools/agent-monitoring/*.py` writer changes permitted).

## Decision C — Per-Cache-Level Retention Categories

| Level | Category name | Placeholder duration | Rationale |
|---|---|---|---|
| Embedding/index cache | `retrieval_index_cache` | ~30d (mirrors `important_failed_run`'s 30d tier) | Longest-lived of the three: expensive to rebuild (re-embedding/re-chunking a corpus), and content-hash-keyed per the idea doc's cache design so staleness is self-detecting (a hash mismatch forces recompute regardless of age) — the duration is a safety backstop, not the primary invalidation signal. |
| Query-result cache | `retrieval_query_cache` | ~7d (mirrors `recent_run`'s 7d tier) | Shortest-lived: keyed by normalized query + corpus generation + retrieval version, and queries/corpus drift fastest of the three levels — any indexed-source or ranking change invalidates it, so a short backstop duration limits staleness exposure between explicit invalidations. |
| Context-packet cache | `retrieval_packet_cache` | ~14d, or bounded to the owning ticket/task lifetime if shorter | Medium-lived: keyed by task/ticket/phase + cited hashes — explicitly ticket/task-scoped, so it should not meaningfully outlive the ticket it was built for; 14d is a placeholder backstop for tickets that stay open longer than a query cache's lifetime but shorter than an index rebuild cycle. |
| Retrieval events | `retrieval_event` (not a `RetentionPolicy` category) | permanent / append-only | Per Decision B above: inherits `agent-monitoring/*.jsonl`'s existing retain-forever convention. Listed here only for completeness of "3 cache levels plus retrieval events" — it is explicitly NOT a duration-based category. |

These durations are placeholders by analogy to `retention.py`'s existing 7d/30d/permanent tiers
(`src/observability/reporting/retention.py` lines 36-37, 54-55, 57), not measured values. Phase 3
is now implemented (`tools/retrieval_cache.py`, ticket TCK-20260729-RETRIEVAL-CACHE-LEVELS), but
the placeholder durations above have not yet been calibrated against real hit/miss/staleness data
from that implementation. A future ticket must calibrate these numbers before they govern actual
pruning behavior.

## Decision D — Doc Location

This doc lands at `docs/observability/retrieval_retention_redaction_policy.md` rather than
`docs/ai/*_decision.md` (used by sibling Decisions 1-2) or `docs/engine/contracts/*.md` (used by
sibling Decision 3) because it is neither a process-decision record nor a data-shape contract — it
is an operational data-handling policy, the same shape as `docs/observability/loki_label_policy.md`
(same directory, same "policy" naming convention, same MAY/PROHIBITED-list structure). This is a
direct structural analogy, not a default.

## Out of Scope

- Any changes to `src/observability/reporting/retention.py`.
- Any changes to `src/core/retention.py`.
- Any changes to any `tools/agent-monitoring/*.py` writer.
- Any Phase 3 cache implementation or Phase 4 event-writer implementation.

This is decision/design only; a future Phase 3+ ticket performs the actual code work.

## Resolution

**Open Decision 4 — resolved.** Retrieval events (landing in `agent-monitoring/*.jsonl`) inherit
that system's existing retain-forever/append-only convention: "retention" for events means
redaction-only (MAY contain hashes/IDs/counts/reason codes/scores; PROHIBITED: raw prompt or
retrieved-content text; never a deletion duration). Caches (embedding/index, query-result,
context-packet) are ephemeral/rebuildable and DO get duration-based expiry, each assigned its own
placeholder category — `retrieval_index_cache` (~30d), `retrieval_query_cache` (~7d),
`retrieval_packet_cache` (~14d or ticket-lifetime) — extending `RetentionPolicy`'s 7d/30d/permanent
naming pattern in prose only, with no code change to `retention.py`. See §Decision B for the
events-vs-caches rationale and §Decision C for the full per-level table.
