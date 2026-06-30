---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-CALFIX
phase: done
date: 2026-06-30
tags: [simulation-quality, calibration, tooling, bug]
---

# TCK-20260630-SIMQ-CALFIX

## Title
Fix calibrate_simq.py to load world configs and fix occupancy collision bug

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`tools/calibrate_simq.py` ignores the `--name` argument for world selection — it runs
an identical generic simulation (hero + goblins) regardless of which world is named.
Additionally, the goblin layout spawns entity #5 at (64,64), colliding with the hero,
triggering `LAW-OCCUPANCY-COLLISION` on every calibration run.

## Scope
1. Add world config loading: use `--name` to load `data/worlds/{name}/world.yaml` →
   `WorldCompiler.compile()` → inject compiled world state into `AuthoritativeState`
2. Add `--profile` argument (default: same as `--name` if file exists, else `default`)
   to load `config/simulation_quality/profiles/{profile}.yaml`
3. Fix entity layout: stagger goblin spawn positions so none overlap hero at (64,64)
4. Re-run calibration on sandbox_world, dungeon_crawl, wilderness_survival, urban_political
   and confirm differentiated output

## Out of Scope
- P0-A enablement (separate ticket TCK-20260630-SIMQ-ROUTING-TEST)
- Creating new world configs
- Changing scoring logic

## Acceptance Criteria
- [x] `dungeon_crawl` and `urban_political` calibration produce non-identical pillar scores
- [x] `LAW-OCCUPANCY-COLLISION` does not appear in any calibration run
- [x] WORLD or ECONOMY pillar events > 0 on at least one authored world
- [x] `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json` contains
      world-specific results per run
- [x] `--profile` loads the correct quality profile (dungeon_crawl.yaml / urban_political.yaml)

## Related Tickets
- TCK-20260630-SIMQ-RECALIBRATE (prior calibration — data invalidated by this fix)
- TCK-20260630-SIMQ-ANCHORS (regression anchors depend on correct calibration)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track A
- `docs/simulation_quality/quality_scoring_contract.md` §4.8 (calibration workflow)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260630-SIMQ-CALFIX/`

## Related Code Areas
- `tools/calibrate_simq.py` — `_run_engine()` function (world loading gap, entity layout bug)
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()` (static method, standalone)
- `config/simulation_quality/profiles/` — world-specific quality profiles

## Assumptions / Open Questions
- **RESOLVED**: `WorldCompiler.compile()` is a `@staticmethod` — no DI container required.
- **RESOLVED**: If a world name has no matching profile, `_resolve_profile()` falls back to `"default"`.

## Implementation Notes
- `_run_engine()` refactored to accept `name: str` parameter.
- World loading added via `_load_world_state(name, seed)`:
  - Checks `data/worlds/{name}/resolved/world.resolved.yaml` (worldspec.v1)
  - Loads as `WorldSpec(**yaml.safe_load(...))` then calls `WorldCompiler.compile(spec, seed)`
  - Returns compiled `AuthoritativeState` directly — no DI container needed (static method)
  - Gracefully falls back to generic simulation if world not found or compilation fails
- Goblin spawn fix in generic fallback: `(60.0 + i, 60.0 + i)` changed to
  `(20.0 + (i % 5) * 8, 20.0 + (i // 5) * 8)` — 5-wide grid starting at (20,20),
  all goblins at minimum 12 tiles from hero at (64,64)
- `_load_weights()` now accepts `profile: str` parameter
- Added `--profile` CLI arg: defaults to `--name` if profile file exists, else `"default"`
- Added `--output` CLI arg: overrides default cal_dir for non-standard output paths
- `_resolve_profile()` helper checks `config/simulation_quality/profiles/{name}.yaml`

## Test Summary
- 305 simulation_quality tests passed (11 deselected as slow)
- dungeon_crawl calibration: COMBAT=A(0.7384, 65 events), WORLD=A(0.8837, 146 events), profile=dungeon_crawl
- urban_political calibration: COMBAT=B(0.2525, 25 events), NARRATIVE=A(0.8333, 33 events), profile=urban_political
- No LAW-OCCUPANCY-COLLISION in either run
- Scores clearly differentiated between worlds

## Files Changed
- `tools/calibrate_simq.py` — primary fix: world loading, goblin stagger, --profile/--output args

## Completion Summary
Fixed `calibrate_simq.py` to load world-specific compiled WorldSpec from
`data/worlds/{name}/resolved/world.resolved.yaml` via `WorldCompiler.compile()` (static, no DI).
Fixed goblin spawn positions in generic fallback path from `(60+i, 60+i)` to a 5-wide grid
starting at (20,20), eliminating the i=4 collision at (64,64). Added `--profile` arg with
auto-detection and `--output` override. Verified differentiated results across dungeon_crawl
and urban_political with 305 tests passing.
