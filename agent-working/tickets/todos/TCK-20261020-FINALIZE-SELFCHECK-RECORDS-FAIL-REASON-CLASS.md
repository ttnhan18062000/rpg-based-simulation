---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-FINALIZE-SELFCHECK-RECORDS-FAIL-REASON-CLASS
phase: open
date: 2026-10-20
tags: [agent-monitoring, data-quality, retro]
---

# TCK-20261020-FINALIZE-SELFCHECK-RECORDS-FAIL-REASON-CLASS

## Title
The done-checker's Finalize self-check records a short reason class for each failing condition in its gate-verdict row

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
From RETRO-2026-W43's final note (40 runs), item 1, proposal B. The owner approved it on 2026-10-20, relayed by lead-planner.

The Finalize self-check (`done_checker_static.run_finalize_selfcheck`) gave 19 blocking verdicts out of 75 in W43. By condition:
- `registry_entry_regenerated`: 15;
- `migration_complete`: 5;
- `working_log_exactly_one_row`: 4;
- `ticket_finalized`: 1.

The gate-verdict row's `sub_results` stores only `PASS`/`FAIL`/`NA` per condition. So the retro can't tell why a condition failed. Each check's evidence text already tells the closer why, but that text never reaches the ledger.

The planner's reading of the code is a hypothesis, to be confirmed by the new field and not assumed. The hand CLI defaults to `regenerate_registry=False`. So `registry_entry_regenerated` FAILs whenever the closer runs the check before `make docs-registry`, and the check already tells "on-disk file stale" apart from "entry genuinely absent".

## Scope
1. **`tools/gate_checks/done_checker_static.py`.** Each of the four Finalize conditions gives a reason class when it FAILs, from a small closed set per condition:
   - `registry_entry_regenerated`:
     - `registry_file_missing`: the on-disk file doesn't exist.
     - `registry_stale_on_disk`: a fresh registry has the entry, the file on disk doesn't.
     - `entry_absent`: there's no `done/` entry even in a fresh or regenerated registry.
   - `migration_complete`, `working_log_exactly_one_row`, `ticket_finalized`: one class per distinct `return ("FAIL", ...)` branch. Examples: `stored_artifacts_missing`, `staging_not_cleaned`, `disposition_invalid`, `no_row`, `duplicate_rows`, `ticket_not_in_done`, `ticket_still_inprogress`. Name them from the code; one per branch.
   - **Mechanism:** your choice, with the smallest blast radius. Either a 3-tuple `(status, evidence, reason)` that `run_finalize_selfcheck` accepts alongside the 2-tuple, or an optional `reason` key on the result dicts. Every existing caller and test that reads `(status, evidence)` or the dict keys keeps working unchanged. That includes `implement-ticket.js`'s `python3 -c` one-liners and `tests/tools/test_done_checker_static.py`.
   - **Precheck conditions** keep their current behaviour, with no reason classes. They're out of scope.
2. **The gate-verdict row.**
   - `main()` passes a new optional field, `sub_reasons: {"finalize.<condition>": "<class>"}`, to `gate_verdicts.record_gate_verdict`. It's set only for FAILing conditions that have a class, and it's absent when nothing failed.
   - `tools/agent-monitoring/gate_verdicts.py` accepts and validates it: an object of string to string, with keys a subset of `sub_results`' keys. Unknown or missing values are never fatal; monitoring write failure must never fail the check.
3. **Docs.** In `docs/agent-monitoring/schema.md`'s gate-verdict table, add a `sub_reasons` row and list the classes per condition.
4. **Tests:**
   - each new class is produced by its branch (registry: missing file, stale on disk, and absent with `regenerate=True`);
   - the row carries `sub_reasons` only for FAILs;
   - the existing done-checker and gate-ledger tests pass unchanged.

## Out of Scope
- Changing any condition's PASS/FAIL logic or the CLI's `regenerate_registry` default.
- Backfilling past verdicts.
- A retro table for reasons. The W44 retro sizes the classes by query; a table can follow if it's worth it.
- Precheck conditions, and other gates (`post_native_run_check.py` etc.).

## Acceptance Criteria
- A blocking Finalize verdict row names, per FAILing condition, a reason class from the documented closed set.
- A `registry_entry_regenerated` FAIL is classed `registry_stale_on_disk` when a fresh registry has the entry (read-only CLI path).
- Existing callers and tests are unchanged and pass. The new tests pass. The schema doc lists the field and classes, and REGISTRY is regenerated after the last docs edit.

## Related Tickets
- TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES (the ledger row and the hand sites)
- TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES (CLI `regenerate=False` default)
- TCK-20261018-RETRO-GATE-FAILURES-ROW-CITES-LEDGER

## Related Docs
- agent-working/agent-monitoring/retro/RETRO-2026-W43.md (final note, item 1)
- docs/agent-monitoring/schema.md (gate_verdicts)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES/

## Related Code Areas
- tools/gate_checks/done_checker_static.py (`check_migration_complete`, `check_ticket_finalized`, `check_working_log_exactly_one_row`, `check_registry_entry_regenerated`, `run_finalize_selfcheck`, `main`)
- tools/agent-monitoring/gate_verdicts.py (`record_gate_verdict`)

## Assumptions / Open Questions
- Reason classes are a closed vocabulary, never the raw evidence text. Paths and ticket ids stay out of the ledger, as with the `error_class` precedent in TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS.

## Implementation Notes
- 2026-10-20 (agent-working-planner): owner yes (via lead-planner). Batch 7, dispatched to agent-working-implementer.

## Test Summary

## Files Changed

## Completion Summary
