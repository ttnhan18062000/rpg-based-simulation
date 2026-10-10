---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS
phase: open
date: 2026-10-09
tags: [testing, regression, simulation-quality]
---

# TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS

## Title
The rpg gate baseline is a versioned, immutable file with provenance, staleness, a dual reference and a cited re-baseline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. The baseline convention reuses the mutation baselines (`tests/mutation/baselines/*_vN.json`: one immutable file per version, with provenance). The metric set v1 adds a dual reference and a cited re-baseline rule.

## Scope
1. A schema for `rpg_gate_vN.json` (path proposed: `tests/simulation_quality/rpg_gate/baselines/`; confirm with rpg-planner):
   - provenance: commit SHA, harness hash (child 3), worlds, seeds, ticks, recorded_at, stale_after, milestone id;
   - per metric id and group: the per-seed values (outcome) or the violation counts (validity), with the summary (mean, SE);
   - the re-baseline record: the previous version, a divergence id and/or memo row, the PR, the before/after on the standing set, and `owner_ruling` (required when an R1/R2 stop line is crossed).
2. A loader that resolves the LAST baseline and the FIRST baseline of the current milestone.
3. Staleness: a baseline is `stale` when past stale_after, when the harness hash differs from the current harness, or when its worlds/seeds/ticks differ from the config. A stale baseline never yields pass (principle 4).
4. A re-baseline CLI that writes vN+1 from a report, REFUSES without a divergence id or memo row plus a PR, and REFUSES past an R1/R2 stop line without `owner_ruling`. The stop lines are declared in rpg's config.
5. A schema test and a lint for every baseline file.

## Out of Scope
- Baseline content and the stop-line values (rpg).

## Acceptance Criteria
1. The schema is documented in the module docstring, plus a short section in `docs/plans/test_architecture/reference/` (or the roadmap §4.2 note).
2. Unit tests: the dual-reference resolution; stale by date, by harness hash and by config; the refused re-baselines (no citation; a stop line without a ruling); an accepted re-baseline writes a new file and never modifies an old one.
3. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; uses TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS (harness hash)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/mutation/baselines/` (the convention), the new module under `tools/test_architecture/`

## Assumptions / Open Questions
None.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
