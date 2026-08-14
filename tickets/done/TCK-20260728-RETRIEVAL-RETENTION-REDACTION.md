---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-RETENTION-REDACTION
phase: done
date: 2026-07-28
tags: [ai, observability, agent-monitoring]
---

# TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Title
Define Retention and Redaction Policy for Retrieval Events and Cache Entries

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document resolving Open Decision 4: what retention and redaction policy applies to retrieval events and cache entries, consistent with the source doc's risk mitigation that telemetry must store only hashes, IDs, counts, and reason codes — never raw prompts or retrieved chunks. This matters because there is no existing "redaction" convention anywhere in the repo outside the Phase 2 planning docs, and getting this wrong risks durable-state that leaks raw prompt/content data through cache or event telemetry.

## Scope
- Author a decision document (expected: docs/observability/retrieval_retention_redaction_policy.md) enumerating fields a retrieval event/cache entry MAY contain (hashes, IDs, counts, reason codes, scores) vs PROHIBITED fields (raw prompt text, raw retrieved chunk/source text, unredacted tool payloads).
- Resolve Open Decision 4 with a cited answer.
- Specify a concrete retention duration/category for each of the 3 cache levels (embedding/index cache, query-result cache, context-packet cache) plus retrieval events themselves, explicitly extending src/observability/reporting/retention.py's RetentionPolicy categories (recent_run=7d, important_failed_run=30d, baseline_source_run=~permanent).
- Update the parent epic's Open Decision 4 line item to cross-reference the new decision doc once it lands.

## Out of Scope
- Any changes to src/observability/reporting/retention.py, src/core/retention.py, or any tools/agent-monitoring/*.py writer — decision-only, no code lands.
- Any src/ or tools/ implementation.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving any Open Decision other than Decision 4.

## Acceptance Criteria
- [ ] Written decision doc enumerates MAY-contain fields (hashes, IDs, counts, reason codes, scores) vs PROHIBITED fields (raw prompt text, raw retrieved chunk/source text, unredacted tool payloads), resolving Open Decision 4 with a cited answer.
- [ ] Doc specifies a concrete retention duration/category for each of the 3 cache levels (embedding/index cache, query-result cache, context-packet cache) plus retrieval events, explicitly extending retention.py's RetentionPolicy categories.
- [ ] Doc declares itself decision-only: no changes land in retention.py, core/retention.py, or any tools/agent-monitoring/*.py writer.
- [ ] Parent epic's Open Decision 4 line item is updated to cross-reference the new decision doc once it lands.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR
- TCK-20260721-MONITORING-WRITER-DECISION

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/observability/loki_label_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- src/observability/reporting/retention.py
- src/core/retention.py
- docs/observability/loki_label_policy.md
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/todos/context-efficient-retrieval/SEQUENCE.md
- expected: docs/observability/retrieval_retention_redaction_policy.md

## Assumptions / Open Questions
- No prior "redaction" convention exists anywhere in the repo outside the two Phase 2 planning docs — this ticket establishes new vocabulary even while reusing retention.py's duration/lifecycle pattern.
- The 3 differently-keyed/invalidated cache levels need per-level treatment, not one blanket policy.
- Exact doc location/filename is not prescribed by the source plan; docs/observability/retrieval_retention_redaction_policy.md is a working suggestion for the ticket's Plan phase, not a mandate.
- Whether this ticket should be standalone or bundled with siblings was flagged in investigation; TCK-20260721-MONITORING-WRITER-DECISION's precedent of bundling two decisions into one ticket exists as an alternative, but this batch keeps it standalone per the default one-concern-one-ticket rule.
- Tier is standard rather than hotfix because assigning concrete retention categories and a new redaction vocabulary across 3 cache levels plus events is policy-design work with privacy/security implications, not mere citation of already-produced evidence.

## Implementation Notes
This ticket was decision-only, per plan.md's 2 ordered steps.

**Step 1** — Authored `docs/observability/retrieval_retention_redaction_policy.md` with frontmatter
`layer: ai`, `authority: P1`, `audience: agent` (reusing the registered `ai` layer and existing tags,
no new registry entries). The doc contains, in order: a Purpose section with the literal
decision-only statement plus citations to the idea doc's Design Principle 5 (lines 74-76), Risks
table row (lines 305-315), and Promotion approval gate (lines 250-262); a MAY-contain vs PROHIBITED
field list cross-referenced against `context_packet_contract.md`'s `included[]` `hash`/`score`
fields, with `loki_label_policy.md` cited as structural-only precedent (mechanism explicitly
distinguished); Decision A (extending `RetentionPolicy`'s categories is prose-only, no code diff);
Decision B (the central call: retrieval *events* inherit agent-monitoring's existing
retain-forever/append-only convention and are redaction-only, while *caches* are ephemeral/
rebuildable and get duration-based expiry — this split is justified against
`docs/agent-monitoring/schema.md`'s documented append-only-forever convention); Decision C (a
4-row table: `retrieval_index_cache` ~30d, `retrieval_query_cache` ~7d, `retrieval_packet_cache`
~14d/ticket-lifetime, `retrieval_event` permanent/append-only — all three cache durations
explicitly labeled placeholders pending future Phase 3+ calibration, citing `retention.py` lines
36-37/54-55/57 as the analogy basis only); Decision D (doc location justified by direct structural
analogy to `docs/observability/loki_label_policy.md`); an Out of Scope section; and a final
Resolution section answering Open Decision 4 directly.

**Step 2** — Updated `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s
`OPEN DECISION 4` line in `## Assumptions / Open Questions` to `**RESOLVED**` (2026-07-29), in the
same multi-line format as the already-resolved Decisions 1-3, citing this ticket ID and the new
doc's path. No other Open Decision line (1, 2, 3, 5, 6) was touched — verified via
`git diff tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`, which shows only
the Open Decision 4 block changing (the `--stat` line-count also reflects decisions 1-3's prior
uncommitted resolution from sibling tickets earlier in this batch, not new changes from this
ticket).

No deviations from plan.md. Confirmed via `git status --porcelain` that no file matching
`retention.py` or `tools/agent-monitoring/*.py` was modified; `python3 tools/validate_frontmatter.py
docs/observability/retrieval_retention_redaction_policy.md` passed with no violations.

## Test Summary
No pytest test added or required — per test_plan.md's recommendation, the sole automated guard is
`done-checker`'s existing `frontmatter_valid` condition plus manual doc-content inspection (both
satisfied). Ran `python3 tools/validate_frontmatter.py docs/observability/retrieval_retention_redaction_policy.md`
— passed (`OK: 1 file(s) checked — no violations`). No code changed, so no regression suite applies;
confirmed via `git status` that `src/observability/reporting/retention.py`, `src/core/retention.py`,
and `tools/agent-monitoring/*.py` remain unmodified.

## Files Changed
- `docs/observability/retrieval_retention_redaction_policy.md` (new)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (Open Decision 4 line only)

## Completion Summary
Authored the decision doc resolving Open Decision 4 (retrieval-event and cache retention/redaction
policy) and cross-referenced it from the epic ticket's Open Decision 4 line, exactly per plan.md's
2 steps. No code changed anywhere; `retention.py`, `core/retention.py`, and all
`tools/agent-monitoring/*.py` writers remain untouched, satisfying AC3. All 4 acceptance criteria
are met: the MAY/PROHIBITED field list (AC1), the per-cache-level category table plus events row
with placeholder durations (AC2), the explicit decision-only declaration (AC3), and the epic
cross-reference (AC4).
