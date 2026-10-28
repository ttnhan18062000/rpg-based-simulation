---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS-STATUS-CHANGES

## Title
Parity-ledger paydown, child 1b: resolve the world_dynamics.yaml entries that have no proving test, by status change or a new test

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
This is a sibling of TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS (child 1 of TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN).
Child 1 hit its AC4 split limit: research on WORLD-001..048 projected about 35-45 status changes, against a limit of about 15.
Under rpg-planner (u24)'s ruling, child 1 keeps the test_path citations (PR A), and the remaining entries move here, in a second PR.

rpg-planner's ruling of 2026-10-29, relayed by lead-planner-u24 and then lead-planner (not an owner approval), word for word:
"(b) Status for each kind of entry
- Retired feature (code removed from src by a decision): `unsupported` + support_boundary.
  - The boundary text names the removal: the ticket or commit that retired it (`git log -S<symbol>` or the ticket corpus). \"grep finds nothing\" alone is not enough evidence.
  - Keep the entry's text and priority unchanged.
- Intended but never built, or absent with no retirement decision: `missing` + support_boundary saying what's absent. List these separately, because a missing P0 is a disclosure the owner should see.
- divergent: only where V2 behaviour exists and differs. It needs a test_path, so it never fits retired code.
- Code exists but no test proves it (the ~7: 012, 022, 042, 043, 048 …): write the proving test in the sibling (tests/** only, no src; rpg owns tests) and cite it. If the code read can't confirm the claimed behaviour, use what the evidence supports, give the reason, and flag it in the table.
- Removing entries: NOT allowed. The ledger is the history, and the epic's three ways stand.
- The draft table comes to rpg-planner entry by entry before the sibling's PR: id, old -> new status, evidence (test, or removal commit/ticket), and reason."

Dispatch needs its own owner go (lead-planner is asking; it is not covered by #715 6474978097 item 1).

## Scope
1. Every world_dynamics.yaml entry with a test_path error that child 1's PR A did not resolve by citation.
2. Classify each entry under the ruling: retired -> unsupported; never built -> missing; code exists but untested -> write a
   proving test in tests/** and cite it.
3. Draft table first, sent to rpg-planner-ubuntu, which relays it to rpg-planner for entry-by-entry review. The table gives:
   id, priority, old -> new status, evidence (the test, or the removal commit/ticket found with `git log -S` or the ticket corpus),
   the support_boundary text, and the reason. The `missing` entries are listed in a separate section.
4. Only after rpg-planner OKs the table: write via parity_ledger_writer.py, in chunks of about 20 entries.
5. As the last step after the final sync with origin/main, run the tighten under codebase-planner's four conditions (as in child 1's AC7).

## Out of Scope
- Removing any ledger entry (not allowed).
- Any src/ change. If a new test shows the code contradicts the entry, record that and stop; don't fix the code.
- Changing an entry's text or priority.
- Other ledger files; the schema; the proof_type enum.

## Acceptance Criteria
1. world_dynamics.yaml has 0 P0 test_path errors and 0 proof_type errors at the PR head, together with child 1.
2. rpg-planner OK'd the draft table before any ledger write, with the OK recorded in the ticket.
3. Every `unsupported` boundary names the retiring ticket or commit, with the evidence command recorded. "grep finds nothing" alone is not accepted.
4. The `missing` P0 entries are listed separately in the ticket and the PR body, as an owner-visible disclosure.
5. Every new test is in tests/** and passes. Every cited test was run.
6. The tighten meets codebase-planner's four conditions. `parity_ledger_schema check` and `make code-health` are clean.

## Related Tickets
- TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS (child 1, PR A)
- TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN (parent)

## Related Docs
- docs/parity_ledger/world_dynamics.yaml, docs/parity_ledger/schema.json, docs/mechanics/05_world_evolution.md

## Related Stored Artifacts

## Related Code Areas
- docs/parity_ledger/world_dynamics.yaml, tests/**, codebase/baselines/parity_ledger_schema_baseline.json

## Assumptions / Open Questions
- Merge order: this sibling lands after PR A. The tighten is re-run on whichever lands last.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
