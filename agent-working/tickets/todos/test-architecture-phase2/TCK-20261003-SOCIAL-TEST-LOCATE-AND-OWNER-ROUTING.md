---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING

## Title
Phase 2 social items 1 and 6 (Locate, Triage): measure social test coverage, markers and placement, and add the social owner-routing row

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

Phase 2 plan §6 items 1 and 6. Measure, and record only: coverage and marker coverage of
`tests/unit/social/` (34 files) and the social tests elsewhere (`tests/simulation_quality/`,
`tests/architecture/`, `tests/integration/`), plus a placement audit against the Epic B taxonomy
(`docs/testing/test_taxonomy.md`). Then add one social owner-routing row to the triage procedure.
**No test file is touched.**

## Scope

1. Coverage of `src/systems/social_systems/` by the existing tests, per file, run unchanged (party*.py,
   memory.py and dormant paths are listed as excluded, not measured). Marker coverage: which social
   tests carry which markers today. Placement audit: a recorded misplacement list against the taxonomy.
   **No mass moves, no markers added, no file edited.**
2. A findings record (a new doc under `docs/testing/`, named at plan review) with full `origin/main`
   SHA, date, commands and sample sizes.
3. One social owner-routing row in the triage procedure (roadmap §4.5 class table is by failure class,
   not by domain; the row's home is confirmed at plan review, see Open Questions).

## Out of Scope

- Editing, moving, marking, deleting or strengthening any social RPG test (owner constraint, 2026-10-03).
- Party (`party*.py`), `memory.py`, `src/domains/perception/`, dormant paths.
- Writing tests or scenarios; changing coverage configuration.
- Ledger edits (C3 reports only).

## Acceptance Criteria

- [ ] `git diff --name-only` against `origin/main` shows no test file.
- [ ] The record states coverage per file, run command, SHA, date and what was excluded and why.
- [ ] The misplacement list names each file and the taxonomy rule it breaks, or states "none found".
- [ ] The routing row names an owner for a social failure by class and is placed where the reviewer
  approves; no other triage text changes.
- [ ] The record carries the RELATIONSHIP-VECTOR staleness line (measurements of `relationships.py`,
  `appraisal.py` and `consequence_events.py` go stale when
  `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` lands).
- [ ] Frontmatter valid on the new doc; `make knowledge-index-update` run.

## Related Tickets

- Parent: `TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL`.
- Siblings: C1 routing case, C3 oracle map, C4 mutation baseline.

## Related Docs

- `docs/plans/test_architecture/phase2_social_scale_out.md` §6 items 1 and 6
- `docs/testing/test_taxonomy.md`
- `docs/plans/test_architecture/roadmap.md` §4.5

## Related Stored Artifacts

None.

## Related Code Areas

- `tests/unit/social/` (read only)
- `src/systems/social_systems/` (read only)

## Assumptions / Open Questions

- Open: the home of the owner-routing row. Roadmap §4.5 has no per-domain table; the implementer
  searches for an existing per-domain routing table first and asks the reviewer before inventing one.
- Coverage is measured with the repo's existing pytest-cov setup and the social tests as they stand.

## Implementation Notes

All figures re-measured at the then-current `origin/main`, with the full SHA.

## Test Summary

Not run yet.

## Files Changed

None yet.

## Completion Summary

Not complete.
