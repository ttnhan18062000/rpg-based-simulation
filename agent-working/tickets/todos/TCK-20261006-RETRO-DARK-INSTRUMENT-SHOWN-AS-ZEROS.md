---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261006-RETRO-DARK-INSTRUMENT-SHOWN-AS-ZEROS
phase: open
date: 2026-10-06
tags: [agent-monitoring, retro]
---

# TCK-20261006-RETRO-DARK-INSTRUMENT-SHOWN-AS-ZEROS

## Title
Retro Session-Layer section prints a table of zeros when its instrument has never recorded anything

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
RETRO-2026-W41 printed "Manual orchestration actions … Total: 0" and "session_role: unresolved 59". No
`manual_actions.jsonl` file has ever been written: the hooks never fire in live sessions (see
TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS). That zero cannot be told apart from "the layer works and
nobody needed reminding", which is exactly the conclusion the M7 review would draw from it.

`tools/agent-monitoring/session_layer_report.py::load_family()` (:22) globs `*/{filename}` and returns an empty
list in both cases. `render()` (:53) then prints the zero table.

## Scope
1. In `session_layer_report.py`, distinguish two cases:
   - **(a) never recorded:** no file of the family exists in any week folder. Print
     `_Instrument not running: no <family> records exist in any week. Zeros below would be meaningless, so the
     table is omitted._`
   - **(b) nothing in period:** files exist but none fall in the period. Keep the zero table and add
     "(instrument active; N records outside this period)".
2. Do the same for "Runs by session role" when every run in the period is `unresolved`: add a line saying no run
   had a resolved role, so role binding was not active.
3. Apply to both families, `manual_actions.jsonl` and `role_boundary.jsonl`.

## Out of Scope
- Making the hooks fire (TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS).
- Other retro sections. The spend-proxy section already states its coverage percentage.

## Acceptance Criteria
1. Tests for the never-recorded case (no files) and the nothing-in-period case (a file with only out-of-period
   rows). The two render different text, and the never-recorded case renders no zero table.
2. A test where every run is unresolved renders the all-unresolved line, and a mixed set does not.
3. Regenerating RETRO-2026-W41 (without `--force`; its Notes are preserved) shows the "Instrument not running"
   line for both families.

## Related Tickets
- TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT
- TCK-20261006-LIVE-SESSIONS-RUN-STALE-OR-NO-PROJECT-HOOKS

## Related Docs
- `agent-working/agent-monitoring/retro/RETRO-2026-W41.md` (Notes, proposal 2)
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/agent-monitoring/session_layer_report.py`, `tools/agent-monitoring/generate_retro.py`

## Assumptions / Open Questions
- None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
