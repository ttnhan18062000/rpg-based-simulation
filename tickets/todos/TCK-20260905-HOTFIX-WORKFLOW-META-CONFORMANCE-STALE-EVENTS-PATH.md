---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260905-HOTFIX-WORKFLOW-META-CONFORMANCE-STALE-EVENTS-PATH
phase: open
date: 2026-09-05
tags: [testing, ai, agent-monitoring]
---

# TCK-20260905-HOTFIX-WORKFLOW-META-CONFORMANCE-STALE-EVENTS-PATH

## Title
workflow_meta_conformance.py's DEFAULT_EVENTS_PATH still points at the pre-sharding unified file

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/gate_checks/workflow_meta_conformance.py:50` hardcodes
`DEFAULT_EVENTS_PATH = Path("agent-monitoring/events.jsonl")` — the old, pre-sharding unified
events file. This repo migrated to weekly shards (`agent-monitoring/data/YYYY-Www/events.jsonl`)
in PR #112/#120 (`TCK-20260902/903-MONITORING-*`). Because this path was never updated,
`check_workflow_meta_conformance()` (called as one of `implement-ticket.js`'s three advisory-only
Finalize-tail checks) always reports every declared phase as having "zero events found" for any
real run_id, regardless of how many events were actually recorded — the check is currently a
guaranteed FAIL for every single ticket closure. Confirmed reproducing on 3 independent ticket
closures in this same session (`TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`,
`TCK-20260904-TEST-SCOPER-HANG-GUARD`, `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`), each with a
real, verified event count in the correct weekly shard file.

This is advisory-only (per `implement-ticket.js`'s own design, a FAIL here is a logged warning,
never a block), so it has not caused any incorrect ticket closure — but as currently written the
check provides zero real signal, since it fails unconditionally.

## Scope
- Update `DEFAULT_EVENTS_PATH` (and any other stale unsharded-path assumption in this same file,
  e.g. `collect_run_event_statuses()`'s glob/read logic) to read from the weekly-sharded
  `agent-monitoring/data/YYYY-Www/events.jsonl` files, matching the pattern other callers in
  `tools/gate_checks/done_checker_static.py` already use for shard-glob reads
- Add or update a test in `tests/tools/` asserting the function actually finds real events for a
  run_id known to have them in a sharded file (regression test for this exact bug — a check that
  always fails silently passing hidden for however long is worse than no check)

## Out of Scope
- Any change to `check_monitoring_write_recorded` or `check_tag_drift` — confirmed unaffected,
  they already read from the correct sharded location
- Making this check blocking — it stays advisory-only per its existing design

## Acceptance Criteria
- [ ] `check_workflow_meta_conformance()` correctly finds events for a real run_id in the current
      week's shard, verified against an actual closed ticket's real event history
- [ ] A regression test exists asserting this (not just re-asserting the old, always-failing
      behavior)
- [ ] Re-run the check against a handful of recently-closed tickets and confirm it now correctly
      reports PASS where events genuinely exist

## Related Tickets
- Discovered during `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`, `TCK-20260904-TEST-SCOPER-HANG-GUARD`,
  and `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s Finalize-tail advisory checks (all three
  independently hit this same stale-path bug)
- Related to the broader weekly-shard migration: `TCK-20260902/903-MONITORING-*` (PR #112/#120)

## Related Docs
None identified yet — investigate whether `docs/agent-monitoring/README.md` or
`docs/ai/workflows.md` reference this check's behavior and need a correction once fixed.

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/gate_checks/workflow_meta_conformance.py`
- `tests/tools/test_workflow_meta_conformance.py`
- `tools/gate_checks/done_checker_static.py` (reference pattern for correct shard-glob reads)

## Assumptions / Open Questions
None yet — straightforward path-update bug, self-evident intent, hotfix tier.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
