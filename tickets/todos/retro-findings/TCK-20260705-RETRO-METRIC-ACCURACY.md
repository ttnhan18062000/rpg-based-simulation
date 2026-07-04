---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-RETRO-METRIC-ACCURACY
phase: open
date: 2026-07-05
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260705-RETRO-METRIC-ACCURACY

## Title
Fix two misleading metrics in generate_retro.py: empty-summary false alarm, epic DONE-rate miscalculation

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The first-ever real retro run (`RETRO-ALL.md`/`RETRO-2026-W27.md`, generated 2026-07-05 via `TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s tooling) produced two metrics that direct investigation shows are actively misleading, not just imprecise:

1. **"246 empty summaries — check agent prompts for `summary` field" is a false alarm.** Every single empty-summary event (246/246, confirmed by direct count) comes from an `events.jsonl` record with `agent: null`, and 239 of those 258 `agent: null` records use a pre-schema-normalization legacy format (`"event": "ticket_finalized"` / `"ticket_complete"` / `"epic_completed"` instead of the current `phase`+`agent`+`status`+`summary` schema) that never had a `summary` field to begin with. **0 of 1698 current-schema events (`agent` is set) have an empty summary** — verified directly. The report's advice ("check agent prompts") is actively wrong: there is no current agent-prompt problem to fix; the number is 100% legacy-data noise.
2. **The epic-tier "44% DONE rate" (26/58) undercounts real epic health.** `EPIC_SCOPED` is a correct, expected terminal status for scope-only epic tickets (per `implement-ticket.js`: epic tier returns `EPIC_SCOPED` and explicitly does no implementation) — it is not a failure or an incomplete run. 19 of the 58 epic-tier runs are `EPIC_SCOPED`. Excluding them, epics that actually attempted implementation are DONE at 31/39 = **79%**, not 44%. The report currently has no way to distinguish "epic correctly scoped, nothing more to do" from "epic incomplete."

A third, smaller finding survives scrutiny and should be preserved, not "fixed away": **38 current-schema events genuinely truncate past 200 chars** — a real, live prompt-verbosity issue, distinct from the empty-summary false alarm. The fix for finding 1 must not accidentally suppress or hide this real signal.

## Scope
- In `tools/agent-monitoring/generate_retro.py`'s Summary Quality section: compute the empty-summary count over current-schema events only (events where `agent` is set, or more precisely where the record's schema version is the current one — decide the exact predicate during Investigate, matching whatever the retro-loop-enforcement/validate.py tooling already uses to distinguish schema generations). Report legacy-schema records with no `summary` field as a separate, clearly-labeled bucket (e.g. "N legacy-format records, summary field not applicable") rather than silently excluding them or conflating them with genuine empty-summary problems.
- In the Tier Distribution section: exclude `EPIC_SCOPED` runs from the epic tier's DONE-rate denominator, or add a distinct column/row showing "scoped only, no implementation attempted" separately from the DONE-rate calculation, so `epic` tier's real completion rate (of runs that actually attempted implementation) is visible without being diluted by correctly-scope-only epics.
- Preserve the truncated-summary (>200 chars) count exactly as-is — this finding is real and should remain visible in the report.
- Add a short note to `docs/guides/agent_monitoring.md`'s "Report Sections" table clarifying both corrected semantics, so a future reader of the report doesn't need to re-derive this investigation from scratch.

## Out of Scope
- Fixing the 38 real truncated summaries themselves (tightening the actual agent prompts that produce them) — that's a prompt-engineering follow-up informed by this report, not part of fixing the report's own accuracy.
- Any change to `validate.py` (tracked separately in `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`) or to the run_id/event join issues (tracked in `TCK-20260705-MONITORING-RUNID-JOIN`) — this ticket only touches `generate_retro.py`'s metric computation and reporting.
- Re-running/regenerating the two already-committed reports (`RETRO-ALL.md`, `RETRO-2026-W27.md`) as part of this ticket — their existing Notes sections already manually document these findings; regenerating them with the fixed tool is a natural but separate follow-up action, not a blocking requirement of this ticket's Acceptance Criteria.

## Acceptance Criteria
- [ ] Empty-summary count in generated retro reports is computed over current-schema events only; legacy-schema records with no `summary` field are reported in a separate, clearly-labeled category, not merged into the same warning.
- [ ] Re-running `python3 tools/agent-monitoring/generate_retro.py --all` after the fix shows 0 (or very close to 0) empty summaries under the "current schema" count, with the ~246 legacy records now reported separately and clearly labeled as not applicable.
- [ ] Epic tier's DONE-rate calculation excludes `EPIC_SCOPED` runs from the denominator (or reports them in a separate column) — re-running the all-time report should show epic tier at approximately 79% (31/39), not 44% (26/58), once `EPIC_SCOPED` is excluded/separated.
- [ ] The truncated-summary (>200 char) count is unchanged by this fix and remains visible.
- [ ] `docs/guides/agent_monitoring.md`'s Report Sections table documents both corrected semantics.

## Related Tickets
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (shipped the tooling that produced the first real report surfacing these findings)
- TCK-20260705-MONITORING-RUNID-JOIN (sibling finding, distinct root cause — run_id/event join mismatches)
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (sibling finding, distinct root cause — validate.py's own blind spot)

## Related Docs
- docs/guides/agent_monitoring.md (Report Sections table — needs the clarifying note)
- agent-monitoring/retro/RETRO-ALL.md and RETRO-2026-W27.md (this ticket's originating findings, already documented in their Notes sections)
- docs/agent-monitoring/schema.md (for the precise legacy-vs-current schema distinction to reuse consistently)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (Summary Quality section, Tier Distribution section)
- agent-monitoring/events.jsonl, agent-monitoring/runs.jsonl (read-only — data being reported on)

## Assumptions / Open Questions
- The exact predicate for "current schema vs. legacy" should be decided consistently with however `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` and the broader schema-enforcement idea doc (`docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md`) end up defining it — ideally a single shared definition, not three independently-invented ones across different tools. Worth checking during Plan whether a small shared helper (e.g. `is_legacy_schema_record(record)`) belongs in a common location rather than being reimplemented per-tool.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
