---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
phase: done
date: 2026-07-05
tags: [agent-monitoring, data-quality, schema]
---

# TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP

## Title
validate.py's working_log cross-check silently skips legacy-schema DONE runs

## Status
DONE

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
- [x] `validate.py`'s working-log cross-check reads `final_status` OR falls back to `status` when `final_status` is absent, before deciding whether a run needs a `working_log.csv` entry.
- [x] Running `python3 tools/agent-monitoring/validate.py` after the fix surfaces the previously-invisible missing-working-log cases as new warnings — 8 new cases surfaced (54→62 total), matching the ticket's estimate of "~9" within the expected drift as more runs landed between filing and implementation.
- [x] No previously-passing check (final_status-based runs already correctly flagged/not-flagged) changes behavior — guaranteed by construction (`or` fallback only fires when `final_status` is absent) and confirmed by spot-checking specific prior warnings still present unchanged.
- [x] `docs/guides/agent_monitoring.md` notes that `validate.py` tolerates the legacy `status` field.

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
`tools/agent-monitoring/validate.py` line 82: replaced `run.get("final_status") == "DONE"` with `status = run.get("final_status") or run.get("status")` followed by `if status == "DONE" and run_id not in log_tids:` — mirrors the exact fallback pattern already used in `tools/agent-monitoring/retro_nudge_hook.py:49` (`status = record.get("final_status") or record.get("status")`), no new pattern introduced. Added a note to `docs/guides/agent_monitoring.md`'s Validation section documenting the tolerance.

## Test Summary
No automated test harness exists for `tools/agent-monitoring/*.py` anywhere in this repo (confirmed: `record_run.py`, `record_events.py`, `pre_tool_hook.py`, `post_tool_hook.py`, `generate_retro.py`, `validate.py` all lack pytest coverage — a pre-existing, documented convention gap, not introduced or fixed by this ticket).

Verification performed:
- `python3 -c "import ast; ast.parse(...)"` — syntax valid.
- Ran `python3 tools/agent-monitoring/validate.py` before and after the fix: warning count went from 54 to 62 "Run marked DONE has no working_log entry" cases — the 8 newly-surfaced cases are exactly the previously-invisible legacy-`status`-field runs (confirmed by name: `TCK-20260614-REPLAY-BACKPRESSURE-9214654b`, `TCK-20260619-E11A-HERO-AUTHORING`, `TCK-20260629-SIMQ-EMIT-AGENCY-1782753561`, and others). No previously-surfaced warning changed or disappeared — confirmed via `diff` of the full warning list before/after.

## Files Changed
- `tools/agent-monitoring/validate.py`
- `docs/guides/agent_monitoring.md`

## Completion Summary
`validate.py`'s working-log cross-check now falls back to the legacy `status` field when `final_status` is absent, closing a validator blind spot that silently skipped 33 legacy-schema runs entirely. 8 previously-invisible missing-`working_log.csv`-entry cases now correctly surface as warnings. Whether to backfill those specific `working_log.csv` rows is an explicitly separate, un-actioned follow-up decision per this ticket's Out of Scope — not resolved here.
