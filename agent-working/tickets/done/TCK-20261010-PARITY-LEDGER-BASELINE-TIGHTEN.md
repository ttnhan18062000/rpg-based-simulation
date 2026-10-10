---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261010-PARITY-LEDGER-BASELINE-TIGHTEN
phase: done
date: 2026-10-10
tags: []
---

# TCK-20261010-PARITY-LEDGER-BASELINE-TIGHTEN

## Title
Tighten the parity-ledger schema baseline to the counts that have fallen

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Four rules had fallen below the baseline (2851 errors in the ledger vs 2862 in the baseline). Lower the baseline to the measured counts; lowering only, no ledger edits. Owner-approved 2026-10-10 via codebase-planner.

## Scope
- Run `python3 -m codebase.gates.parity_ledger_schema tighten --yes` and commit `codebase/baselines/parity_ledger_schema_baseline.json`

## Out of Scope
- Any edit to `docs/parity_ledger/**`
- Any rise or new key in the baseline

## Acceptance Criteria
- [x] Re-measured on `cd202049b`: 2851 errors, 0 rose, 0 new, 4 fell
- [x] Keyed before/after shows only the four counts lowered, no key added or removed, nothing rose
- [x] `git diff --stat` lists no path under `src/` or `docs/parity_ledger/`

## Related Tickets
- TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
- TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC

## Related Docs
- docs/parity_ledger/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/baselines/parity_ledger_schema_baseline.json

## Assumptions / Open Questions
None.

## Implementation Notes
- The four rules: combat_movement `allOf/0/then/properties/test_path/type` 241→238 and `allOf/2/else/then/properties/test_path/type` 269→265; social_narrative the same two rules 166→164 and 210→208.

## Test Summary
- `check` before: OK, 2851 errors, 4 fell. Keyed before/after script: 4 counts lowered, keys added [], keys removed [], rose [].

## Files Changed
- `codebase/baselines/parity_ledger_schema_baseline.json`

## Completion Summary
Baseline lowered by 11 (2862 → 2851) across four rules; nothing rose, nothing added. No ledger, `src/` or `tests/` change.
