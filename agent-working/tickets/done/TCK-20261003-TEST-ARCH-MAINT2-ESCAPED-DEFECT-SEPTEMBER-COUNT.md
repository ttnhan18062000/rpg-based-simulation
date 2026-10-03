---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-ESCAPED-DEFECT-SEPTEMBER-COUNT
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-TEST-ARCH-MAINT2-ESCAPED-DEFECT-SEPTEMBER-COUNT

## Title
Record the September 2026 escaped-defect count from the existing report

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary

Roadmap §4.7 calls for the `escaped-defect` tag count "per month in the report". Find out whether
`core_rpg_report.py` already emits it, and record the September 2026 figure with its SHA.

## Scope

1. Finding (already established at investigation, to be restated in the record): `escaped_defects_layer` in
   `core_rpg_report.py` already emits a per-month count and a state. A read-only preview at `origin/main`
   `f76fda2cc03dc32481f66c6ba18d980ed28bdff2`, `--as-of 2026-10-03`, gave state **counting**, tag registered
   2026-09-29, 2379 tickets scanned, **2026-09: 0**, 2026-10: 0, tagged outside the window: 0.
2. Re-run the tool at the then-current `origin/main` at implementation, write the figure into the roadmap
   record (or the report doc the reviewer names) as a dated line with: the count, the state, the tag
   registration date, the tickets-scanned denominator, the full SHA and the exact command.
3. State the limits the tool states: the September window opens on the tag's registration date (2026-09-29),
   so September covers 2 days; the count depends on tagging discipline; a **0 is reported as 0 with its
   state, never as missing**. A cross-check found no ticket with `escaped-defect` in its tags and no ticket
   with a `Failure class:` line, so the 0 means "none tagged", not "none escaped".

## Out of Scope

- Any code or tool change: no new tool; tooling follows evidence. Backfilling the tag onto old tickets.
- Judging whether any past defect "escaped".

## Acceptance Criteria

- [ ] The record states the count (0 if it is 0), the tool state, the window, the denominator, the SHA and
  the command, and says the zero is a tagging-discipline count.
- [ ] Re-run at implementation time; if the figure differs from the preview, the new figure is recorded with
  its own SHA and the difference is stated.
- [ ] `git diff --name-only origin/main...HEAD` shows no `src/` or parity-ledger path and `tests/` paths only
  under `tests/unit/tools/`.

## Related Tickets

- `TCK-20260929-ESCAPED-DEFECT-TAG` (done), `TCK-20260930-CORE-RPG-TEST-REPORT-V0` (done)
- Siblings: `TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN`, `TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304`

## Related Docs

- `docs/plans/test_architecture/roadmap.md` §4.7

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/test_architecture/core_rpg_report.py` (`escaped_defects_layer`, read only)

## Assumptions / Open Questions

- Where the dated line lives (roadmap §4.7 or the batch report) is the reviewer's call; proposed: a dated line
  under roadmap §4.7, since that section defines the metric.
- Context scan was by targeted reads; `search_docs` and graphify were unavailable.

## Implementation Notes

Approved by test-architecture-reviewer at plan review of `38423a1151a0ee2c9f6d6de0a55ad67406d009d4` with the home
(a dated line under roadmap §4.7), both caveats, and a one-or-two-line limit. No tool or code change: the
existing `escaped_defects_layer` is the source. The figure was re-run at the then-current tree, not copied
from the earlier preview.

## Test Summary

Records only. `core_rpg_report.py --as-of 2026-10-03 --sha bd8367a121d432ab43fccbfa54f554fa44a1b5fc` (the tree is
`origin/main` `599966e8dd18dcde97c1093e44d909f3cb7c0212` plus the M2-1 tool change, which does not touch the
escaped-defect layer: that layer was identical in the before/after comparison): state `counting`, tag registered
2026-09-29, **2387 tickets scanned**, 2026-09: **0**, 2026-10: 0, tagged outside the window: 0. The earlier preview
at `f76fda2cc` gave the same 0 with 2379 scanned; the denominator differs because tickets were added in between.
Cross-check: no ticket has `escaped-defect` in its tags and none has a `Failure class:` line, so the 0 means
"none tagged", not "none escaped".

## Files Changed

- `docs/plans/test_architecture/roadmap.md` (a two-line dated entry under §4.7 item 2)

## Completion Summary

Done 2026-10-03. The September 2026 escaped-defect count is **0 tagged** (state `counting`, 2387 tickets
scanned, window of 2 days from the tag's registration on 2026-09-29), recorded under roadmap §4.7 with the SHA and
command and the two caveats. The report tool already emitted the monthly count, so nothing was built.
