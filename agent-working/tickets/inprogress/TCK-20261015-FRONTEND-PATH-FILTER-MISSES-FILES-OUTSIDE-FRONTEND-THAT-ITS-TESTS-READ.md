---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261015-FRONTEND-PATH-FILTER-MISSES-FILES-OUTSIDE-FRONTEND-THAT-ITS-TESTS-READ
phase: inprogress
date: 2026-10-15
tags: [testing]
---

# TCK-20261015-FRONTEND-PATH-FILTER-MISSES-FILES-OUTSIDE-FRONTEND-THAT-ITS-TESTS-READ

## Title
test.yml's `FRONTEND_RE` also covers the files outside `frontend/` that the frontend tests read, and a static test keeps the two in step

## Status
INPROGRESS

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
agent-working-planner found this (relayed by lead-planner-u24, 2026-10-15), and testing-planner confirmed it on main:
- #596 (51b044c69) changed `visual_assets/catalog/definitions/visual_keys.yaml` and nothing under `frontend/`.
- `frontend/src/visualAssets/__tests__/iconScene.test.ts:16` reads that file, so its key-count assertions broke (36 vs 54, 22 vs 40; #598, asset-owned).
- `FRONTEND_RE='^(frontend/|\.github/workflows/test\.yml$)'` (test.yml ~line 821) did not match, so the Frontend job skipped on #596 and the red first showed on main, where every later PR inherited it.

Frontend tests on main read these repo-root paths outside `frontend/`:
- `visual_assets/catalog/definitions/visual_keys.yaml` (iconScene.test.ts:16)
- `visual_assets/review/pilot_colour_vision.py` (iconScene.test.ts:67)
- `docs/assets/pilot_terrain_m5_criteria.md` (two tests, via `resolve(__dirname, '../../../../docs/assets/...')`)

The filter is a skip optimisation. A path the tests read that the filter misses is a silent skip, the same failure class as an unmatched path in the other lanes.

## Scope
1. Widen `FRONTEND_RE` to cover `visual_assets/` and `docs/assets/pilot_terrain_m5_criteria\.md$`, keeping `frontend/` and `test.yml`. Prefer the whole `visual_assets/` directory over individual files there: the catalog and review files change together, and an over-trigger costs one Frontend job.
2. Extend the existing FRONTEND_RE coverage test in `tests/static/test_ci_narrow_path_filtered_jobs.py` (~line 342, `_extract_re_pattern(run_text, "FRONTEND_RE")`). Derive, rather than hard-code, the repo-root paths that `frontend/src/**/*.test.ts(x)` read outside `frontend/`, and assert that FRONTEND_RE matches each one. A small regex scan for the two forms used today is enough:
   - `read('<root>', ...)` joined to the repo root;
   - `resolve(__dirname, '../…/<path>')` resolved against the test file.

   The derivation must fail loudly if it finds zero paths (a positive control), so a scan that silently stops matching cannot pass.
3. Add a regression case: with the old pattern `^(frontend/|\.github/workflows/test\.yml$)`, the assertion fails, naming `visual_assets/catalog/definitions/visual_keys.yaml`.

## Out of Scope
- Fixing `iconScene.test.ts` or `visual_keys.yaml`: #598, asset-owned.
- The other lanes' regexes (PERF_RE, MIG_RE, DOCKER_RE).
- `tools/delivery/ci_lanes.py`. Its guard test (`tests/tools/test_delivery_ci_lanes.py`) checks regex names, not values, and must still pass unchanged.

## Acceptance Criteria
- [x] AC1: FRONTEND_RE matches `frontend/x`, `.github/workflows/test.yml`, every path under `visual_assets/`, and `docs/assets/pilot_terrain_m5_criteria.md`. It does not match e.g. `src/core/x.py` or `docs/mechanics/x.md`.
- [x] AC2: the static test derives the read paths from the frontend tests, asserts each is covered, and fails on zero derived paths.
- [x] AC3: there is a regression case showing the old pattern fails on `visual_keys.yaml`.
- [x] AC4: `pytest tests/static/test_ci_narrow_path_filtered_jobs.py tests/tools/test_delivery_ci_lanes.py` passes.
- [ ] AC5: the PR's own CI runs the Frontend job (its own test.yml change triggers it), and its result is recorded. A red from #598 is expected until asset fixes it, and is not this ticket's to fix.

## Related Tickets
- #596 (51b044c69), #598 (asset; the iconScene red)
- TCK-20261014-PRE-PUSH-CI-LANE-PARITY (ci_lanes.py, which mirrors these regexes)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/test.yml (`FRONTEND_RE`, changes job)
- tests/static/test_ci_narrow_path_filtered_jobs.py
- frontend/src/visualAssets/__tests__/iconScene.test.ts (read-only)

## Assumptions / Open Questions
- None. testing-planner owns test.yml and ruled the shape above.

## Implementation Notes
`FRONTEND_RE` is now `^(frontend/|visual_assets/|docs/assets/pilot_terrain_m5_criteria\.md$|\.github/workflows/test\.yml$)`. In tests/static/test_ci_narrow_path_filtered_jobs.py: `_frontend_test_outside_reads()` scans frontend/src/**/*.test.ts(x) for `read('<root>', ...)` and `resolve(__dirname, '../…')` and returns the paths outside frontend/ (today 3: visual_keys.yaml, pilot_colour_vision.py, pilot_terrain_m5_criteria.md); `test_frontend_path_set_covers_every_file_outside_frontend_that_its_tests_read` asserts each is matched and that the set is non-empty; `test_the_old_frontend_pattern_missed_visual_keys_and_the_new_one_catches_it` is the regression case. Mutation check: with the old pattern put back, exactly those two tests fail.

## Test Summary
tests/static + tests/tools/test_delivery_ci_lanes.py + test_ci_split_tools_jobs.py: 142 passed (delivery_ci_lanes unchanged). After merge of main: static narrow-path + ci_lanes + generate_registry: 117 passed.

## Files Changed
- .github/workflows/test.yml
- tests/static/test_ci_narrow_path_filtered_jobs.py

## Completion Summary
