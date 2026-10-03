---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING

## Title
Phase 2 social items 1 and 6 (Locate, Triage): measure social test coverage, markers and placement, and add the social owner-routing row

## Status
DONE

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
- [x] The `architecture_design_notes.md` §3.1 Social / narrative row is updated (reviewer decision at
  plan review, 2026-10-03); no other ownership-map or triage text changes.
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

No test was added or changed. Measurement runs (scratch coverage path, nothing committed): `tests/unit/social`
296 passed in 12.45 s; with the 20 social-importing files elsewhere, 372 passed in 47.65 s. Marker census by
collect-only over the same 372 tests. Branch head measured: `f13baaf24578eb4529948f4e7e045c8468ca6886`
(`origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6` plus the C1 case).

## Files Changed

- `docs/testing/social_test_report_2026-10-03.md` (section 2)
- `docs/plans/test_architecture/reference/architecture_design_notes.md` (§3.1 Social / narrative row only)

## Completion Summary

Done 2026-10-03. Coverage, markers and placement are recorded in section 2 of the shared report: 83.0%
line coverage of the non-party, non-memory social files with all 372 tests (75.9% from `tests/unit/social`
alone), `guilds.py` at 0%, no `domain`/`level` markers anywhere (not a defect under the taxonomy), one
candidate misplacement (`test_multi_hero.py` runs a real kernel under `tests/unit/`) and one ambiguous
placement (clan lifecycle tests under the faction component). Nothing was moved or marked. The social
ownership-map row now carries the measured roots, oracle documents and owner contact.
