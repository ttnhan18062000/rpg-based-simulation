---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-CALFIX
phase: open
date: 2026-06-30
tags: [simulation-quality, calibration, tooling, bug]
---

# TCK-20260630-SIMQ-CALFIX

## Title
Fix calibrate_simq.py to load world configs and fix occupancy collision bug

## Status
OPEN

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
- [ ] `dungeon_crawl` and `urban_political` calibration produce non-identical pillar scores
- [ ] `LAW-OCCUPANCY-COLLISION` does not appear in any calibration run
- [ ] WORLD or ECONOMY pillar events > 0 on at least one authored world
- [ ] `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json` contains
      world-specific results per run
- [ ] `--profile` loads the correct quality profile (dungeon_crawl.yaml / urban_political.yaml)

## Related Tickets
- TCK-20260630-SIMQ-RECALIBRATE (prior calibration — data invalidated by this fix)
- TCK-20260630-SIMQ-ANCHORS (regression anchors depend on correct calibration)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track A
- `docs/simulation_quality/quality_scoring_contract.md` §4.8 (calibration workflow)

## Related Stored Artifacts
- `data/calibration/` (current — all runs were generic sim, not world-specific)

## Related Code Areas
- `tools/calibrate_simq.py` — `_run_engine()` function (world loading gap, entity layout bug)
- `src/systems/world_systems/compiler.py` — `WorldCompiler.compile()`
- `config/simulation_quality/profiles/` — world-specific quality profiles

## Assumptions / Open Questions
- Can `WorldCompiler.compile()` run standalone without the DI container? Needs verification.
- If a world name has no matching profile, fall back to `default` profile.

## Implementation Notes
- `_run_engine()` currently hardcodes: `hero = gen.spawn_hero((64.0, 64.0))` and
  `monster = gen.spawn_goblin((60.0 + i, 60.0 + i))`. Fix: spawn goblins at least
  5 tiles from hero (e.g., cluster around (40.0, 40.0))
- World loading should be optional (fallback to generic if world not found) so the tool
  still works for quick generic benchmarks

## Test Summary
- Run calibration before/after for dungeon_crawl — WORLD events should appear after fix
- Assert no `LAW-OCCUPANCY-COLLISION` in calibration run logs
- Compare sandbox_world vs dungeon_crawl: should show different COMBAT/WORLD/FACTION levels

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
