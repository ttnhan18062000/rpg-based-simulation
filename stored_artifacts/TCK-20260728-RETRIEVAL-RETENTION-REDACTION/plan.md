---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-RETENTION-REDACTION
artifact_type: plan
tags: [ai, observability, agent-monitoring]
---

# Implementation Plan — TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Summary

This ticket is decision-only: it produces one new doc,
`docs/observability/retrieval_retention_redaction_policy.md`, that resolves Open Decision 4 for
the context-efficient-agent-retrieval epic, and updates that epic ticket's Open Decision 4 line to
point at it. No code changes land anywhere. The plan resolves all four open questions the
investigation surfaced as documented decisions (not left open for the implementer to improvise):
(1) "extending RetentionPolicy's categories" is a prose/conceptual extension only, not a code diff;
(2) retrieval *events* inherit agent-monitoring's existing retain-forever/append-only convention
(redaction-only, no duration), while *caches* are genuinely ephemeral/rebuildable and do get
duration-based expiry categories; (3) the doc lands at `docs/observability/` by direct structural
analogy to `docs/observability/loki_label_policy.md`; (4) each of the 3 cache levels
(embedding/index, query-result, context-packet) gets its own named category and duration,
by analogy to `retention.py`'s existing 7d/30d/permanent tiers, explicitly marked as placeholder
durations for a future calibration ticket. Because this is a doc-only ticket, there is exactly one
implementation step (author the doc) plus one cross-reference step (update the epic ticket), each
independently verifiable.

## Steps

### Step 1 — Author the decision doc
**Files:** `docs/observability/retrieval_retention_redaction_policy.md` (new file)

**Change:** Create the doc with this required content, in this order:

1. **Frontmatter** (validated by `tools/validate_frontmatter.py`):
   ```yaml
   ---
   status: active
   layer: ai
   authority: P1
   audience: agent
   ---
   ```
   Reuse `layer: ai` — matches this ticket's own layer and the sibling `docs/ai/*_decision.md` docs
   in this batch; do not register a new layer. `audience: agent` (not `developer`, unlike
   `loki_label_policy.md`) because the primary consumer is a future Phase 3+ implementation agent
   and the Verify-phase gate, consistent with the other three sibling decision docs in this batch.

2. **Purpose** section: state this doc resolves Open Decision 4 from
   `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`,
   citing Design Principle 5 (lines 74-76) and the Risks table row "Retrieval telemetry leaks
   sensitive content" (lines 305-315) as the binding constraints, and the Promotion approval gate
   (lines 250-262) as the future check this doc's MAY/PROHIBITED list must satisfy. State plainly,
   near the top: **"This is a decision-only document. No changes land in
   `src/observability/reporting/retention.py`, `src/core/retention.py`, or any
   `tools/agent-monitoring/*.py` writer as part of this doc."** — this is the literal text that
   satisfies AC3.

3. **MAY-contain vs PROHIBITED fields** section (resolves the core of Open Decision 4 / AC1):
   - MAY contain: content hashes, source/entity/ticket/run IDs, counts (candidate count, selected
     count, exclusion counts), reason codes (inclusion_reason, exclusion reason, adequacy verdict),
     scores (ranking score, authority/freshness ratings), latency, corpus/graph generation and
     retrieval version numbers, cache level/status (hit/miss/stale-rejected).
   - PROHIBITED: raw prompt text, raw retrieved chunk/source text, full tool payloads (unredacted),
     any field that reproduces source content rather than referencing it by hash/ID.
   - Cite explicitly that this vocabulary is not invented here: `hash` and `score` are already-named
     `ContextPacket.included[]` fields per `docs/engine/contracts/context_packet_contract.md`
     (sibling Decision 3 doc) — this doc's MAY-list must stay consistent with that field list, not
     add competing terminology.
   - Cite `docs/observability/loki_label_policy.md` as *structural* precedent only (a precisely
     enumerated MAY/PROHIBITED list) — state explicitly that its mechanism (label-cardinality
     control for Loki streams) is different from this doc's mechanism (content redaction) and its
     literal identifier list (`tick`, `entity_id`, `worker_id`, etc.) does not apply here. This
     guards against a future reader conflating the two.

4. **Decision A — "Extending RetentionPolicy's categories" is conceptual, not a code change**
   (resolves open question 1): State explicitly, in these terms: *"This document extends
   `RetentionPolicy`'s category taxonomy (the `recent_run` / `important_failed_run` /
   `baseline_source_run` naming and duration-tiering pattern) in prose/design only. The named
   categories introduced below (§Decision C) are new categories a future Phase 3+ implementation
   ticket would add to `src/observability/reporting/retention.py` or a sibling module — this ticket
   makes no such code change, consistent with its own Out of Scope."*

5. **Decision B — retrieval events are retain-forever/redaction-only; caches are duration-based**
   (resolves open question 2 — the central architectural call of this doc): State explicitly:
   - Retrieval *events* (the telemetry records themselves) land in `agent-monitoring/*.jsonl` per
     the idea doc's own "Retrieval Observability and Dashboard" architecture (§idea doc lines
     188-201). `docs/agent-monitoring/schema.md` establishes that `runs.jsonl`/`events.jsonl`/
     `tools.jsonl` are append-only-forever by explicit documented convention with no pruning
     mechanism today. Retrieval events inherit this convention unchanged: they are **not** a
     duration-based retention category. "Retention" for retrieval events means redaction-only
     (never store raw content per §3 above) — the records themselves are never deleted, exactly
     like every other row in those three files today.
   - *Caches* (embedding/index, query-result, context-packet — SQLite-backed per idea doc §"3.
     Cache design", lines 137-151) are a genuinely different kind of storage: ephemeral, rebuildable
     from source, and explicitly invalidated on defined triggers (content hash / corpus generation /
     policy version changes per the idea doc's own Key/Invalidation table). Caches ARE eligible for
     duration-based expiry and DO map onto new prose-extension categories of `RetentionPolicy`'s
     existing pattern.
   - State the rationale for the split plainly: mixing a duration-based model onto an
     append-only-forever convention would either silently break the existing agent-monitoring
     guarantee (data loss risk on a system with zero pruning code and an explicit "append-only for
     all writes going forward" convention) or require inventing a brand-new writer/pruning mechanism
     — both out of this ticket's scope (no `tools/agent-monitoring/*.py` writer changes permitted).

6. **Decision C — per-cache-level retention categories** (resolves open question 4 / AC2): a table
   with one row per cache level plus events, each with a named category (extending the
   `recent_run`/`important_failed_run`/`baseline_source_run` naming pattern), a placeholder
   duration, and a one-line rationale:

   | Level | Category name | Placeholder duration | Rationale |
   |---|---|---|---|
   | Embedding/index cache | `retrieval_index_cache` | ~30d (mirrors `important_failed_run`'s 30d tier) | Longest-lived of the three: expensive to rebuild (re-embedding/re-chunking a corpus), and content-hash-keyed per idea doc §3 so staleness is self-detecting (a hash mismatch forces recompute regardless of age) — the duration is a safety backstop, not the primary invalidation signal. |
   | Query-result cache | `retrieval_query_cache` | ~7d (mirrors `recent_run`'s 7d tier) | Shortest-lived: keyed by normalized query + corpus generation + retrieval version per idea doc §3, and queries/corpus drift fastest of the three levels — any indexed-source or ranking change invalidates it, so a short backstop duration limits staleness exposure between explicit invalidations. |
   | Context-packet cache | `retrieval_packet_cache` | ~14d, or bounded to the owning ticket/task lifetime if shorter | Medium-lived: keyed by task/ticket/phase + cited hashes per idea doc §3 — explicitly ticket/task-scoped, so it should not meaningfully outlive the ticket it was built for; 14d is a placeholder backstop for tickets that stay open longer than a query cache's lifetime but shorter than an index rebuild cycle. |
   | Retrieval events | `retrieval_event` (not a `RetentionPolicy` category) | permanent / append-only | Per Decision B above: inherits `agent-monitoring/*.jsonl`'s existing retain-forever convention. Listed here only for completeness of the AC's "plus retrieval events" requirement — it is explicitly NOT a duration-based category. |

   State explicitly, right after the table: *"These durations are placeholders by analogy to
   `retention.py`'s existing 7d/30d/permanent tiers (`src/observability/reporting/retention.py`
   L36-37, L54-55, L57), not measured values — no cache of any of these three kinds exists yet to
   measure against (Phase 3 is not yet implemented). A future Phase 3+ ticket that implements the
   caches must calibrate these numbers against real hit/miss/staleness data before they govern
   actual pruning behavior."* This satisfies the anti-drift hazard against fabricating precision
   this corpus cannot support.

7. **Decision D — doc location** (resolves open question 3): State explicitly: *"This doc lands at
   `docs/observability/retrieval_retention_redaction_policy.md` rather than `docs/ai/*_decision.md`
   (used by sibling Decisions 1-2) or `docs/engine/contracts/*.md` (used by sibling Decision 3)
   because it is neither a process-decision record nor a data-shape contract — it is an operational
   data-handling policy, the same shape as `docs/observability/loki_label_policy.md` (same
   directory, same 'policy' naming convention, same MAY/PROHIBITED-list structure). This is a
   direct structural analogy, not a default."*

8. **Out of Scope** section (mirrors the ticket's own, for a future reader who only opens this doc):
   list the same three paths as prohibited from touching: `src/observability/reporting/retention.py`,
   `src/core/retention.py`, `tools/agent-monitoring/*.py` writers. State this is decision/design
   only; a future Phase 3+ ticket performs the actual code work.

**Do NOT touch:** `src/observability/reporting/retention.py`, `src/core/retention.py`, any
`tools/agent-monitoring/*.py` writer file, `docs/agent-monitoring/schema.md` (read-only precedent,
not modified), `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(its "Open Decisions" list is never edited directly, per established sibling precedent), any
`docs/parity_ledger/*.yaml` file, `docs/guidelines/tag_registry.jsonl`,
`docs/guidelines/layer_registry.jsonl` (both registries already contain everything this doc needs:
`layer: ai`, tags `ai`/`observability`/`agent-monitoring`).

**Verify:** `python3 tools/validate_frontmatter.py docs/observability/retrieval_retention_redaction_policy.md`
(or the project's standard frontmatter-validation invocation) passes; manual inspection confirms
the doc contains all of: MAY/PROHIBITED field list, Decisions A-D above stated explicitly, and the
decision-only Out of Scope statement. Per test_plan.md, no new pytest test is required for this
step — the doc-presence/frontmatter check is the sole automated guard, and it is optional per
test_plan.md's recommendation (rely on `done-checker`'s existing `frontmatter_valid` condition
instead of adding a bespoke test).

### Step 2 — Update the epic ticket's Open Decision 4 line
**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`

**Change:** In the `## Assumptions / Open Questions` section, replace the current line:

```
- OPEN DECISION 4: What retention and redaction policy applies to retrieval events and cache entries?
```

with a `RESOLVED` line matching the exact shape used for Decisions 1-3 (see lines already present
for `OPEN DECISION 1/2/3` in that file), e.g.:

```
- OPEN DECISION 4 — **RESOLVED** (2026-07-29, `TCK-20260728-RETRIEVAL-RETENTION-REDACTION`): What
  retention and redaction policy applies to retrieval events and cache entries? Answer: retrieval
  events (landing in `agent-monitoring/*.jsonl`) inherit that system's existing retain-forever/
  append-only convention — "retention" for events means redaction-only (hashes/IDs/counts/reason
  codes/scores; never raw prompt or retrieved-content text), not a deletion duration. Caches
  (embedding/index, query-result, context-packet) are ephemeral/rebuildable and DO get
  duration-based expiry, each assigned its own placeholder category extending `RetentionPolicy`'s
  7d/30d/permanent naming pattern in prose only (no code change to `retention.py`). Full
  MAY/PROHIBITED field list, per-cache-level category table, and rationale:
  `docs/observability/retrieval_retention_redaction_policy.md`.
```

Use the actual doc-completion date for the `(2026-07-29, ...)` stamp when this step is executed.

**Do NOT touch:** the OPEN DECISION 1, 2, 3, 5, or 6 lines in this same section — leave them
byte-for-byte as they currently read. Do not touch any other section of the epic ticket (Scope,
Out of Scope, Acceptance Criteria, Related Tickets, Implementation Notes, etc.).

**Verify:** `git diff tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` shows a
change touching only the Open Decision 4 line (plus its multi-line continuation) and nothing else
in the file.

## Scope Guards

- Do NOT modify `src/observability/reporting/retention.py`.
- Do NOT modify `src/core/retention.py`.
- Do NOT modify any `tools/agent-monitoring/*.py` writer file.
- Do NOT implement any code (no new cache module, no new retrieval-event writer, no Phase 3
  implementation of any kind).
- Do NOT touch `docs/parity_ledger/*.yaml` — investigation confirmed zero overlap; no entry exists
  or is needed for this decision.
- Do NOT resolve, edit, or annotate Open Decisions 1, 2, 3, 5, or 6 on the epic ticket. 1-3 are
  already `RESOLVED` by sibling tickets; 5-6 remain open and are explicitly out of scope here.
- Do NOT edit the idea doc's own "Open Decisions" list
  (`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`)
  — resolution is recorded only on the epic ticket, per established sibling precedent.
- Do NOT register a new tag or layer — `layer: ai` and tags `ai`/`observability`/`agent-monitoring`
  are already registered and sufficient.
- Do NOT invent exact storage-size limits, byte-level payload caps, or dollar/compute costs not
  grounded in any existing measurement. Concrete day-based durations are explicitly permitted (the
  ticket asks for them, and `retention.py`'s existing tiers are a cited basis to extend by analogy)
  but must be labeled as placeholders per Step 1 item 6.
- Do NOT conflate `docs/observability/loki_label_policy.md`'s label-cardinality mechanism with this
  doc's content-redaction mechanism — cite it only as structural precedent for "a precisely
  enumerated MAY/PROHIBITED list."

## Dependency Map

- Step 1 and Step 2 are independent of each other in terms of file scope (different files, no
  shared edits) but Step 2's cross-reference line depends on Step 1's doc path/content existing
  first (the epic line cites the doc path and summarizes its Decision B/C answers). Recommended
  order: Step 1 then Step 2, but Step 2 could technically be drafted first if the final doc path
  and decision summary are already fixed by this plan (they are, per Step 1's spec above) — the
  planner recommends sequential execution (1 then 2) to avoid drafting a citation to content that
  hasn't been finalized yet.
- Neither step depends on any other sibling ticket in this batch; Decisions 1-3 are already landed
  and this plan only reads their resolved lines for citation consistency (§Decision A's field-name
  cross-check with `context_packet_contract.md`).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Doc enumerates MAY-contain vs PROHIBITED fields, resolving Open Decision 4 with a cited answer | Step 1 (items 3, 5, 6, 7 — MAY/PROHIBITED list + Decisions A/B/C/D) | Manual doc inspection; `validate_frontmatter.py` pass |
| AC2: Doc specifies a concrete retention duration/category for each of the 3 cache levels plus retrieval events, explicitly extending `RetentionPolicy`'s categories | Step 1 (item 6, Decision C table) | Manual doc inspection confirms all 4 rows (3 caches + events) present with named category, duration/permanence, and rationale |
| AC3: Doc declares itself decision-only: no changes land in `retention.py`, `core/retention.py`, or any `tools/agent-monitoring/*.py` writer | Step 1 (item 2 explicit statement, item 8 Out of Scope section) | `git diff --stat` restricted to those three path patterns shows zero changes at Verify time; regression suite `pytest tests/unit/observability/test_retention_manager.py tests/unit/core/test_retention.py -v` still passes unchanged |
| AC4: Parent epic's Open Decision 4 line is updated to cross-reference the new decision doc | Step 2 | `git diff tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` shows only the Open Decision 4 line changed, citing the new doc path |

## Anti-Drift Notes

- **"Extending RetentionPolicy's categories" is prose-only.** The ticket's Scope/AC wording sits
  directly next to an Out of Scope line forbidding any change to `retention.py`. Step 1 item 4
  (Decision A) states this explicitly inside the doc itself so a future reader or Verify-phase gate
  does not mistake "extending" for evidence that code should have landed.
- **Retrieval events vs caches are architecturally different retention regimes** — this is the
  single most consequential decision in this doc (Decision B). Do not let Step 1 collapse them into
  one duration-based table; events are explicitly retain-forever/redaction-only, caches are
  explicitly duration-based. Getting this backwards would contradict `docs/agent-monitoring/schema.md`'s
  documented append-only-forever convention for `runs.jsonl`/`events.jsonl`/`tools.jsonl`.
- **Do not fabricate precision this corpus cannot support.** All three cache durations in Decision
  C must be explicitly labeled placeholders pending a future Phase 3+ calibration ticket — no cache
  exists yet to measure real hit/miss/staleness rates against.
- **Finalize-time housekeeping note (not part of Steps 1-2, but relevant to the Finalize phase that
  follows this plan):** this ticket's real source todos file lives at
  `tickets/todos/context-retrieval-phase2/TCK-20260728-RETRIEVAL-RETENTION-REDACTION.md`, a
  *different* folder from `tickets/todos/context-efficient-retrieval/` (the already-completed
  Phase 0-1 batch, which the ticket's own Related Code Areas names but which is not this ticket's
  actual source folder). Finalize should `rm` the file from `context-retrieval-phase2/`, and since
  that folder has no `SEQUENCE.md` and will become fully empty once this file is removed, Finalize
  should remove the now-empty `context-retrieval-phase2/` directory too, per the "never leave a
  completed folder's skeleton in `tickets/todos/`" rule. Do not confuse this with
  `context-efficient-retrieval/`, which is unrelated and already fully archived except for its own
  `SEQUENCE.md`.
- **No parity ledger entry is created or touched** — investigation confirmed zero overlap across
  all 4 populated `docs/parity_ledger/*.yaml` files.
