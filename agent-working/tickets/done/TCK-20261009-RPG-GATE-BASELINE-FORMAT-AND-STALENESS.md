---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS
phase: done
date: 2026-10-09
tags: [testing, regression, simulation-quality]
---

# TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS

## Title
The rpg gate baseline is a versioned, immutable file with provenance, staleness, a dual reference and a cited re-baseline

## Status
DONE

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
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS/`

## Related Code Areas
- `tests/mutation/baselines/` (the convention), the new module under `tools/test_architecture/`

## Assumptions / Open Questions
- The baselines path (`tests/simulation_quality/rpg_gate/baselines/`), the config shape (worlds, seeds, ticks, stale_after_days, stop_lines) and the stop-line semantics (a row's value outside `[min, max]`) are testing's proposal; rpg-planner confirms. No baseline file is checked in: baseline content is rpg's.
- The harness hash is a parameter of `staleness()` (child 3 supplies it); an unknown hash counts as stale.

## Implementation Notes
- New `tools/test_architecture/rpg_gate_baseline.py` (schema `rpg-gate-baseline/v1`, documented in its docstring and in `reference/rpg_gate_baseline_format.md`): `lint_baseline` / `lint_dir` (schema, file name vs version, provenance, rows, re-baseline record, version sequence without a gap); `load_baselines` (an invalid file raises, never skipped); `resolve_references` (LAST plus FIRST of the last one's milestone; `None` is the report's no-data case); `staleness` (past stale_after, harness hash differs or unknown, worlds/seeds/ticks differ from the config; every reason is listed); `rebaseline` and CLI `lint` / `rebaseline`.
- Re-baseline refuses without a divergence id and/or memo row, without a PR, past a stop line (or with an undecided world-semantic change) without an `owner_ruling`; the first baseline has nothing to cite. The before/after is computed from the two files, not typed. The file is opened with exclusive create, so an existing version is never overwritten.
- `recorded_at` defaults to now and `stale_after` to that plus `stale_after_days`.
- Metric ids are never named; rows are keyed `(id, world, group, key, tick)`.

## Test Summary
`pytest tests/unit/tools/test_rpg_gate_baseline.py` 23 passed: the first baseline and its defaulted times, each schema break, a version gap and bad JSON, the checked-in baselines lint clean (none yet), the dual reference (last and milestone-first; one baseline; none), an invalid file refused by the loader, staleness by date / harness hash / unknown hash / worlds / seeds / ticks and all reasons together, the refused re-baselines (no citation, no PR, stop line without a ruling, undecided change), the accepted ones (memo row alone; a ruling) writing a new file with the old bytes unchanged and the computed before/after, the exclusive-create guard, appearing and disappearing rows, stop-line bounds and patterns, the config loader and the CLI.

## Files Changed
- new: `tools/test_architecture/rpg_gate_baseline.py`, `tests/unit/tools/test_rpg_gate_baseline.py`, `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`

## Completion Summary
The rpg gate baseline has a versioned immutable format with provenance, a dual-reference loader, a staleness check that never lets a stale baseline pass, a lint, and a re-baseline CLI that refuses without a citation or past a stop line without an owner ruling. Gap stated: no real baseline, config or stop line exists yet (rpg's content), so the lint of the checked-in directory is vacuous until the first baseline is recorded; the harness hash arrives with child 3.
