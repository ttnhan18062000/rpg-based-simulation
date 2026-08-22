---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260821-HOTFIX-MIGRATION-LANES-PLATFORM-COVERAGE-GAP
phase: done
date: 2026-08-21
tags: [testing, registry]
---

# TCK-20260821-HOTFIX-MIGRATION-LANES-PLATFORM-COVERAGE-GAP

## Title
Add `platform` to `migration-lanes`' MIG_RE trigger-path coverage

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/static/test_ci_narrow_path_filtered_jobs.py::test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies`
failed on PR #34 (`worldgen-organic-terrain` batch)'s "Architecture / docs / static" CI job. Root
cause: `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s new test file,
`tests/integration/worldassembly/test_wolf_den_noise_migration.py`, imports
`from src.platform.rng import DeterministicRNG` and `from src.core.enums import Domain` at module
level, and is marker-tagged `pytest.mark.worldassembly`. `.github/workflows/test.yml`'s
`migration-lanes` job's `MIG_RE` trigger-path regex covers `src/(core|content|runtime|scenarios|
worldassembly|worldbuilding|worldmodules|certification)/` but not `src/platform/` — so a future
change to `src/platform/rng.py` alone would not trigger `migration-lanes` to re-run, even though
this now-real marker-tagged test depends on it. Confirmed via a clean worktree checkout that this
exact static test passes on `origin/main` (two other, pre-existing marker-tagged test files already
import from `src/platform/rng.py`, but only inside function bodies, not at module level, so the
AST-based import scanner doesn't catch them) — this is a genuine regression introduced by this
session's own new test file, not pre-existing drift.

## Scope
- Add `platform` to `MIG_RE`'s `src/(...)/ ` alternation in `.github/workflows/test.yml`'s
  `changed-files` gate job.

## Out of Scope
- Any other `MIG_RE` coverage gap not caused by this session's own change.
- Converting the two pre-existing function-body-level `src.platform.rng` imports (in
  `test_corpus_diversity.py`/`test_hero_guild_routing_population_stability.py`) to module-level —
  not required, out of scope, unrelated to this fix.
- Rewriting `test_wolf_den_noise_migration.py`'s import style to route around the gate instead of
  fixing the actual CI path-filter coverage — this is a Gate Integrity violation; the test's finding
  is correct and must be honored, not evaded.

## Acceptance Criteria
- [x] `pytest tests/static/test_ci_narrow_path_filtered_jobs.py::test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies` passes
- [x] `pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow"` (the real CI job's exact scoped command) passes in full
- [x] `MIG_RE`'s only change is adding `platform` to the `src/(...)/ ` alternation — no other regex/job structure change

## Related Tickets
- TCK-20260821-WOLF-DEN-NOISE-MIGRATION (source of the new test file that surfaced this real gap)
- TCK-20260819-CI-NARROW-PATH-FILTERED-JOBS (original author of `MIG_RE` and this static guard)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix -- no staging artifacts).

## Related Code Areas
- .github/workflows/test.yml
- tests/static/test_ci_narrow_path_filtered_jobs.py
- tests/integration/worldassembly/test_wolf_den_noise_migration.py

## Assumptions / Open Questions
None.

## Implementation Notes
Confirmed via `git worktree add` against `origin/main` that
`test_migration_lanes_path_set_covers_all_marker_tagged_test_dependencies` genuinely passes on
`main` today — this is not pre-existing drift, it is a real regression from this session's own
`test_wolf_den_noise_migration.py` (module-level `from src.platform.rng import DeterministicRNG` /
`from src.core.enums import Domain` imports on a `pytest.mark.worldassembly`-tagged file). Fixed by
adding `platform` to `MIG_RE`'s alternation group in `.github/workflows/test.yml`:
`src/(core|content|runtime|scenarios|worldassembly|worldbuilding|worldmodules|certification)/` →
`src/(core|content|platform|runtime|scenarios|worldassembly|worldbuilding|worldmodules|certification)/`.

## Test Summary
`.venv/bin/python3 -m pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow" --tb=short -q`
— 150 passed, 2 skipped, 1 deselected, 2 xfailed, 0 failed (up from 1 failed before the fix).

## Files Changed
- `.github/workflows/test.yml` — added `platform` to `MIG_RE`'s `src/(...)/ ` alternation

## Completion Summary
Fixed a real CI path-filter coverage gap: `migration-lanes`' `MIG_RE` regex did not cover
`src/platform/`, but a new marker-tagged test file (from `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`)
now genuinely depends on `src/platform/rng.py` at module level. Confirmed via a clean `main`
worktree that this is a real regression, not pre-existing drift. Single-line regex fix, no other
change.
