---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-CODEBASE-ROADMAP-TRUTH-PASS
phase: done
date: 2026-10-20
tags: [architecture, delivery]
---

# TCK-20261020-CODEBASE-ROADMAP-TRUTH-PASS

## Title
Bring the code-craft roadmap up to date (M5 and the import-linter flip done) and record the owner's M7 reopen of `src/`

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/plans/codebase_health/python_code_craft_roadmap.md` still describes finished work as pending. For example, the M5 row says the flip is "prepared on branch `import-linter-flip`", and the tickets paragraph lists "three blocked follow-ups still there". An agent reading it could re-plan finished work. The flip merged as #671 (`309715a72`), and #674 (`abef4d682`) added zero ruff findings in `codebase/` and stale-entry naming. Separately, the owner lifted decision 8.7 on 2026-10-20 for the M7 refactor lane only, and that decision must be recorded next to 8.7.

## Scope
In `docs/plans/codebase_health/` only:
1. Roadmap Section 7:
   - M5 row: done, with the import-linter step blocking since #671 and 7 class-E tests retired. The phase19 OFF-mode check stays with testing (#621).
   - The "Order" paragraph and the tickets paragraph get the same update: M5's carry-forwards are all done, and its folder is in `done/`.
2. Roadmap Section 8, under decision 7, add this text verbatim:
   "*Amended 2026-10-20 by owner (owner via lead-planner): `src/` is reopened for the M7 refactor lane only: one `src/` file per batch, starting with `src/api/server.py`, dispatched only after the ratchet round-2 and Pyrefly batches merge and after `rpg-planner` confirms no open work on that file (asked on a `for:rpg-planner` issue). Everything outside M7 stays frozen.*"
3. Roadmap M7 row: replace "Deferred until the owner reopens `src/`" with "Reopened 2026-10-20 (decision 7 amendment); first target `api/server.py`".
4. `import_linter_soak_review.md` and `import_linter_evaluation.md`: if either still reads as pending, add a one-line "Outcome: merged #671 (2026-10-19)". No rewrite of history.

## Out of Scope
- Any code, baseline or CI change.
- Rewriting past decisions or soak findings.

## Acceptance Criteria
- [x] No sentence in the roadmap still describes M5, the flip or self-lint as pending. Check with `grep -n "prepared on branch\|blocked follow-ups\|Deferred until the owner reopens"` (0 hits).
- [x] The decision 7 amendment text is present verbatim.
- [x] `tests/docs` passes. Frontmatter is valid. REGISTRY is regenerated.

## Related Tickets
- TCK-20261020-RATCHET-TIGHTEN-ROUND-2 (same batch)
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT (#671)
- TCK-20261018-CODEBASE-SELF-LINT (#674)

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/import_linter_soak_review.md
- docs/plans/codebase_health/import_linter_evaluation.md

## Related Stored Artifacts
None.

## Related Code Areas
None (docs only).

## Assumptions / Open Questions
None.

## Implementation Notes
Edited docs/plans/codebase_health/ only. Roadmap: M5 row, Order paragraph and tickets paragraph now say done (flip #671, `309715a72`; #674 `abef4d682`; M5 folder in `done/`; phase19 OFF-mode stays with testing #621); M7 row says reopened 2026-10-20; decision 7 amendment inserted verbatim (extracted from this ticket, checked by string match). `import_linter_evaluation.md` and `import_linter_soak_review.md` each got one line `**Outcome:** merged #671 (2026-10-19).`

## Test Summary
- `grep -n "prepared on branch\|blocked follow-ups\|Deferred until the owner reopens"` on the roadmap: 0 hits.
- Amendment verbatim: string match True.
- `pytest tests/docs`: 72 passed, 2 skipped, 1 xfailed.

## Files Changed
docs/plans/codebase_health/python_code_craft_roadmap.md, import_linter_evaluation.md, import_linter_soak_review.md; docs/REGISTRY.yaml; this ticket.

## Completion Summary
Roadmap no longer describes finished M5/flip work as pending and records the M7 reopen next to decision 7.
