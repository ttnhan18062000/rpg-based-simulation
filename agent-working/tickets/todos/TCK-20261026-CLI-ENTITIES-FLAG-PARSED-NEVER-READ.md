---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261026-CLI-ENTITIES-FLAG-PARSED-NEVER-READ
phase: open
date: 2026-10-26
tags: []
---

# TCK-20261026-CLI-ENTITIES-FLAG-PARSED-NEVER-READ

## Title
Remove the `--entities` flag from the `cli` command: it is parsed but never read

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Issue #617. rpg-planner (u24) ruled on #593 issuecomment-6406593752 (item 3): **REMOVE**. `cli` parses `--entities`
(`src/cli/entry.py:39`, `cli.add_argument("--entities", type=int, default=None)`) but never reads it, and `serve` has
no such flag. The sandbox world sets its own population. A real population override would be a world-config feature,
not a CLI flag. The README side is already done (#741, `TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS`).
#617 closes when this lands.

Owner approval to take it on ubuntu, riding the U2 batch-1 PR: #715 issuecomment-6420343110.

## Scope
- Drop the `--entities` argument from the `cli` parser in `src/cli/entry.py`, and any help text that names it. Before
  deleting, confirm that nothing in `src/` reads `args.entities` (or `getattr(args, "entities"...)`).
- `tests/cli/test_entry_parity.py` passes `--entities 5` to the CLI at lines 19 and 59. Remove those arguments; the
  test's assertions stay the same. If the test depended on the flag for its population, report that instead of
  changing an assertion.
- Correct the docs that present it as a `cli` flag: `docs/guides/simulation.md:82` (the flag table row) and
  `docs/guides/observability.md:62` ("reduce entity count (`--entities`)"). Keep the observability advice, minus the
  flag. Run `make knowledge-index-update`.

## Out of Scope
- The separate `--entities` flags of `tools/perf/profile_tick.py`, `tools/perf/flag_attribution.py`,
  `tools/perf/profile_api_payload.py` and `tools/calibrate_simq.py`. Those are real, read flags of other tools.
- Any population-override feature.

## Acceptance Criteria
- [ ] `python3 -m src cli --help` no longer lists `--entities`. Passing it now fails as an unknown argument.
- [ ] `tests/cli/` passes, with no assertion changed.
- [ ] Neither doc presents `--entities` as a `cli` flag any more.
- [ ] It is hash-neutral: the batch PR's `paired --neutral` check covers it.

## Related Tickets
- `TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS` (#741): the README half.
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION`: the batch-1 PR this ticket rides.

## Related Docs
- `docs/guides/simulation.md`, `docs/guides/observability.md`.

## Related Stored Artifacts
- None.

## Related Code Areas
- `src/cli/entry.py`, `tests/cli/test_entry_parity.py`.

## Assumptions / Open Questions
- None. rpg-planner's ruling settles the direction.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
