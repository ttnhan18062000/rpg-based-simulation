---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
phase: open
date: 2026-07-05
tags: [agent-monitoring, data-quality, schema]
---

# TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP

## Title
validate.py's working_log cross-check silently skips legacy-schema DONE runs

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/agent-monitoring/validate.py`'s working-log cross-check (`main()`, the "3. Cross-check" block) only tests `run.get("final_status") == "DONE"` (line 82). Direct investigation of `agent-monitoring/runs.jsonl` found **33 `TCK-*` runs use the legacy `status` field instead of `final_status`** (`final_status` is `None` on these records — the same legacy-schema drift already documented in `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md`). Because the check only reads `final_status`, these 33 runs are silently never examined at all — not flagged as passing, not flagged as failing, simply invisible to the validator. **9 of those 33 are genuinely `status: "DONE"` and missing from `tickets/working_log.csv`** — a real gap the validator should be catching but currently cannot see.

This ticket is the second, independent finding from the same retro/validate investigation that produced `TCK-20260705-MONITORING-RUNID-JOIN` — distinct root cause (a validator code gap, not a data-write race), same originating session.

## Scope
- Update `validate.py`'s working-log cross-check to also examine `run.get("status")` when `final_status` is absent, matching the same "legacy field fallback" pattern already used elsewhere in this codebase (e.g. `tools/agent-monitoring/generate_retro.py`'s agent/workflow field handling, and the retro-nudge hook's `workflow = record.get("workflow") or record.get("agent")` pattern in `tools/agent-monitoring/retro_nudge_hook.py`).
- Ensure the fix surfaces the 9 currently-invisible missing-working-log-entry cases as new `WARNING:` lines, without changing behavior for any run that already has `final_status` set correctly.
- Do not silently start requiring `final_status` on every run (that would be a stricter behavior change than this ticket's scope) — only extend the *check* to also read the fallback field when the primary one is absent, consistent with how this repo currently treats legacy-schema data everywhere else (tolerate and read around it, don't reject it).

## Out of Scope
- Backfilling `final_status` onto the 33 legacy-schema runs themselves — append-only log, no rewrite of history (same precedent as every other schema-drift finding this session).
- The 9 genuinely-missing `working_log.csv` entries this fix will newly surface — once visible, whether to backfill those specific `working_log.csv` rows is a separate, small follow-up decision, not part of fixing the validator itself.
- Any other `validate.py` check (incomplete-run / no-events checks) — those already correctly examine both schema generations implicitly (they don't key off `final_status` specifically) and are not affected by this gap.
- `TCK-20260705-MONITORING-RUNID-JOIN`'s findings (crashed runs, zero-event runs) — a distinct root cause, tracked separately.

## Acceptance Criteria
- [ ] `validate.py`'s working-log cross-check reads `final_status` OR falls back to `status` when `final_status` is absent, before deciding whether a run needs a `working_log.csv` entry.
- [ ] Running `python3 tools/agent-monitoring/validate.py` after the fix surfaces the 9 previously-invisible missing-working-log cases as new warnings (confirm the exact count at implementation time — it will change slightly as more runs land between now and implementation).
- [ ] No previously-passing check (final_status-based runs already correctly flagged/not-flagged) changes behavior.
- [ ] `docs/agent-monitoring/schema.md` or `docs/guides/agent_monitoring.md` notes that `validate.py` tolerates the legacy `status` field, consistent with how the rest of the schema documents its own legacy-format handling.

## Related Tickets
- TCK-20260705-MONITORING-RUNID-JOIN (sibling finding from the same investigation, distinct root cause)
- TCK-20260705-RETRO-METRIC-ACCURACY (sibling finding, distinct root cause)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md (the broader schema-drift idea this finding is concrete evidence for)
- docs/guides/agent_monitoring.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/validate.py (line 82, the `final_status`-only check)
- tools/agent-monitoring/generate_retro.py (reference — already has legacy-field-fallback handling to mirror)
- tools/agent-monitoring/retro_nudge_hook.py (reference — same fallback pattern, `workflow = record.get("workflow") or record.get("agent")`)

## Assumptions / Open Questions
None — this is a narrow, well-evidenced, mechanical fix with clear precedent already established elsewhere in the same codebase.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
