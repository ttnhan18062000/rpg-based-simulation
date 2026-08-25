---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260825-OPT-INV-001-STALE-TEST-CITATION
phase: open
date: 2026-08-25
tags: [performance, testing]
---

# TCK-20260825-OPT-INV-001-STALE-TEST-CITATION

## Title
`docs/performance/optimization_invariants.md`'s OPT-INV-001 cites a test file that doesn't exist

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`docs/performance/optimization_invariants.md:55` (OPT-INV-001's "Test Citation") reads:
`tests/integration/optimization/test_static_dirtyset_guard.py` (Proves zero direct dirty set
references exist across all gameplay systems)" -- **this file does not exist anywhere in the
repo**, confirmed by two independent `find` checks during `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`'s
Plan and Verify phases (that ticket's own `_refresh_dirty_set`/OPT-INV-002 fix is unrelated to this
stale citation; it just happened to be discovered while reading the same doc file).

That ticket's Verify pass identified the real, current guard test for this exact invariant:
`tests/static/test_no_direct_dirtyset_candidate_selection.py`, delivered by the already-closed
`tickets/done/TCK-20260517-STATIC-DIRTYSET-GUARD.md`. The citation in `optimization_invariants.md`
appears to predate a later rename/relocation of that test file and was never updated.

## Scope
- Update `docs/performance/optimization_invariants.md:55`'s Test Citation to reference the real,
  current file: `tests/static/test_no_direct_dirtyset_candidate_selection.py`.
- Confirm that file's actual test function(s) genuinely prove OPT-INV-001's claim ("zero direct
  dirty set references exist across all gameplay systems") before citing it -- read the file, don't
  just trust the name.
- Grep `docs/` more broadly for any other reference to the now-confirmed-nonexistent
  `test_static_dirtyset_guard.py` filename, in case the stale citation exists in more than one
  place.

## Out of Scope
- Any change to `src/` -- this is a pure doc-accuracy fix, no behavior change.
- `TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE`'s own OPT-INV-002 changes -- already landed, unrelated
  invariant.

## Acceptance Criteria
- [ ] `optimization_invariants.md:55`'s Test Citation references a file that genuinely exists
- [ ] The cited file's actual test(s) verified to prove OPT-INV-001's stated claim
- [ ] No other stale reference to the old filename remains anywhere in `docs/`

## Related Tickets
- TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE (where this was discovered, flagged, and deliberately not
  fixed as out of that ticket's own scope)
- TCK-20260517-STATIC-DIRTYSET-GUARD (original ticket that delivered the real, current guard test)

## Related Docs
- docs/performance/optimization_invariants.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/static/test_no_direct_dirtyset_candidate_selection.py

## Assumptions / Open Questions
- Whether the file was ever actually named `test_static_dirtyset_guard.py` and later renamed, or
  whether the doc citation was simply wrong from the start -- not investigated, doesn't change the
  fix (point the citation at the real file either way).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
