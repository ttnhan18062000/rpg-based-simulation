---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS
phase: open
date: 2026-10-08
tags: [testing]
---

# TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS

## Title
The Perf / cert / arena lane runs on a PR for any `src/` change except a short, justified list of folders that cannot affect a simulation

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
In `.github/workflows/test.yml`, the `changed-files` job gates the `perf-cert-arena` job on `PERF_RE`. Its `src/` part lists 14 folders by name (`ai api certification cognition config core domains engine observability perf platform replay world worldbuilding`). The perf, certification and arena tests run whole simulations, yet a PR that changes only `src/systems`, `src/strategy`, `src/entities`, `src/progression`, `src/economy`, `src/quests`, `src/town`, `src/worldgeneration`, `src/worldmodules`, `src/worldassembly`, `src/content`, `src/content_semantics`, `src/scenarios`, `src/runtime`, `src/actions` (and others) skips the lane. `main` runs it after the merge (non-PR events set every flag true), so a break surfaces only post-merge. No harm is on record yet: the last 40 `main` Tests runs contain no failure. The lane is cheap: about 2 min 11 s in run 37724069820. Found in testing-planner's test.yml gap review (2026-10-08); the owner approved filing it.

## Scope
1. Replace the `src/` allowlist in `PERF_RE` with "any `src/` path", **except** an explicit exclusion list of folders that cannot affect a simulation result. Derive the exclusion list from evidence, not by name: a folder qualifies only if no module reachable from the simulation kernel's run path imports it (use `graphify` or an import scan; record the method and the result). Expected candidates are presentation and tooling only (for example `src/api`, `src/views`, `src/rendering`, `src/cli`), but the scan decides.
2. Keep the non-`src` triggers as they are (`tests/(perf|certification|arena)/`, `Makefile`, `requirements.txt`, `pyproject.toml`, `uv.lock`, `test.yml`).
3. The scenario lane depends on `PERF_COVERS` (it runs only when the perf lane does not cover the change, `tools/test_architecture/scenario_lane_paths.py --perf-covers`). Check what widening `PERF_RE` does to scenario routing, and keep its intent: a scenario-affecting change is still tested by exactly one of the two jobs. `tests/unit/tools/test_scenario_lane_paths.py` reads `PERF_RE` from the workflow, and `test_src_progression_only_routes_to_the_dedicated_job` is Epic B criterion 4's stand-in test. If its expectation must change, record why in the ticket and in the test docstring, and tell testing-planner before changing it.
4. Write the exclusion list and its derivation in a comment next to `PERF_RE`.
5. Tests: extend the routing tests so a PR touching only one of the formerly-missed folders (at least `src/systems`, `src/strategy`, `src/progression`) sets `run_perf_cert_arena=true`, and a PR touching only an excluded folder sets it `false`.

## Out of Scope
- Making any test job a required status check (the owner's decision; not asked).
- The `MIG_RE` and `FRONTEND_RE` gates, and the resync-gate skip rule.
- The perf tests' content and thresholds.

## Acceptance Criteria
1. `PERF_RE` (or an equivalent "src minus exclusions" rule) triggers on every `src/` folder outside the evidence-derived exclusion list. The list and its derivation are in the workflow comment and the ticket.
2. Scenario routing keeps its intent per Scope 3. Any changed expectation is recorded and was cleared with testing-planner first.
3. The Scope 5 tests pass, and the existing `tests/unit/tools/test_scenario_lane_paths.py` passes.
4. Live check on the PR itself: the PR touches `test.yml`, so all lanes run on it. Record the lane durations, so the cost is measured, not assumed.

## Related Tickets
- TCK-20261008-SLOW-REGRESSION-SCHEDULE-WATCHDOG (same review stream, test CI)
- TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION (Epic B; criterion 4 and the scenario lane routing)

## Related Docs
- `.github/workflows/test.yml` (`changed-files`, `perf-cert-arena`, `scenario-lane`)
- `docs/plans/test_architecture/roadmap.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `.github/workflows/test.yml`
- `tools/test_architecture/scenario_lane_paths.py`
- `tests/unit/tools/test_scenario_lane_paths.py`

## Assumptions / Open Questions
- Assumed: about 2 min per extra PR run is acceptable (testing-planner's call, under the owner's go-ahead of 2026-10-08).
- Open: if the import scan finds that every `src/` folder is reachable from the kernel, the exclusion list is empty, and that is a valid result.

## Implementation Notes
- Method (also in the comment next to PERF_RE): AST import closure over every src module (all import nodes incl. lazy ones, "src.x" string literals, importlib targets) from every src module imported by tests/perf, certification, arena, mechanic_scenarios, helpers, conftest, plus src/__main__ (tests/helpers/runtime.py launches `python -m src`). Result 2026-10-08: 544 of 760 modules reachable; 0 reachable in actions, lab, rendering, runtime, testing, views, worldgeneration (the only outside importer of any of them is src/worldbuilding/cli.py -> worldgeneration, itself outside the closure). Every other folder (cli, scenarios, api, progression, systems, strategy, ...) has reachable modules. A first pass without `src/__main__` and without tests/mechanic_scenarios wrongly listed cli, scenarios and others, hence both roots.
- PERF_RE src part: `src/(?!(?:actions|lab|rendering|runtime|testing|views|worldgeneration)/)`, so a new src/ folder triggers the lane by default. It needs PCRE, so both uses are `grep -qP`, now through one `perf_match()` that fails OPEN (exit >= 2 -> true plus a ::warning::); the step computes PERF_COVERS once and reuses it for the output.
- Scenario routing (Scope 3), cleared with testing-planner 2026-10-08: src/progression and src/systems are now perf-covered, so the scenario tests run in perf-cert-arena (which runs tests/mechanic_scenarios), exactly once, and the dedicated job runs only for non-src triggers and the 7 excluded folders. test_src_progression_only_routes_to_the_dedicated_job and the systems/social twin were rewritten to assert perf True / dedicated job False (docstrings cite Epic B criterion 4 and this ticket); stand-ins for the dedicated job kept (data/content/..., src/testing/...); a matrix test asserts "exactly one job runs the scenario tests".
- tests/static/test_ci_narrow_path_filtered_jobs.py::test_perf_cert_arena_path_set_covers_all_actually_imported_src_dirs did a substring test for folder names in PERF_RE; it now compiles PERF_RE and matches a path per imported dir (same intent, fits the exclusion-list shape).

## Test Summary
tests/unit/tools/test_scenario_lane_paths.py + tests/static/test_ci_narrow_path_filtered_jobs.py: 82 passed locally. AC4 (lane durations from this PR's own run) open until the PR run finishes.

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
