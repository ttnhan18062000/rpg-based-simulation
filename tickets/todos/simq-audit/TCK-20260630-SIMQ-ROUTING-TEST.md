---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260630-SIMQ-ROUTING-TEST
phase: open
date: 2026-06-30
tags: [simulation-quality, calibration, world-config, p0-a]
---

# TCK-20260630-SIMQ-ROUTING-TEST

## Title
Create simq_routing_test world to enable all 10 pillars for calibration

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
7/10 SimQ pillars produce zero signal on all authored worlds because `ENABLE_ADVENTURE_ROUTING`
(P0-A) is OFF by default. Create a minimal test world with this flag enabled and sufficient
infrastructure so that all 10 pillars generate signal. This unblocks full-pillar calibration
without touching P0-A in production worlds.

## Scope
1. Create `data/worlds/simq_routing_test/` with a world composition that includes:
   - `ENABLE_ADVENTURE_ROUTING: true`
   - ≥ 2 resource nodes (for ECONOMY: harvest, craft, trade)
   - ≥ 1 information NPC archetype (for INFORMATION: paid transactions)
   - ≥ 2 factions with territory (for FACTION: diplomacy, tension)
   - ≥ 1 open social group (for SOCIAL: cooperation, group join)
   - Spawn configuration with ecology cadence (for WORLD: ecology cycle, boss spawn)
2. Create `config/simulation_quality/profiles/simq_routing_test.yaml` with equal weights
   for all 10 pillars (no overrides — baseline measurement)
3. Run 500-tick calibration with the new world and record which pillars become active
4. Verify time-gate negative penalties fire at correct tick boundaries:
   - `zero_harvest_after_tick` → should NOT fire (harvest should be active)
   - `belief_system_dormant` (100-tick window) → should NOT fire (belief updates expected)

## Out of Scope
- Enabling P0-A in existing authored worlds
- Full world narrative/scenario authoring (minimal infra only)
- Broker mode calibration

## Acceptance Criteria
- [ ] `simq_routing_test` world compiles without errors via WorldCompiler
- [ ] 500-tick calibration shows ≥ 7/10 pillars with event_count > 0
- [ ] ECONOMY pillar shows non-zero events (resource_harvested or item_crafted)
- [ ] WORLD pillar shows non-zero events (ecology_cycle or spawn_cadence)
- [ ] AGENCY pillar shows non-zero events (action_executed or route_selected)
- [ ] Calibration result committed to `data/calibration/simq_routing_test_seed42_500t/`

## Related Tickets
- TCK-20260630-SIMQ-CALFIX (prerequisite — tool must load worlds correctly first)
- TCK-20260630-SIMQ-ANCHORS (anchors for all 10 pillars come from this world)
- TCK-20260630-SIMQ-TIMEGATE (time-gate verification uses this world)

## Related Docs
- `docs/plans/simq_deep_audit_plan.md` §5 Track B
- `docs/simulation_quality/quality_scoring_contract.md` §5 (pillar infrastructure requirements)
- `docs/mechanics/03_economic_laws.md` (resource loop prerequisites)

## Related Code Areas
- `data/worlds/` — new world directory
- `config/simulation_quality/profiles/` — new quality profile
- `tools/calibrate_simq.py` — runs after TCK-20260630-SIMQ-CALFIX is done

## Assumptions / Open Questions
- Should this world be programmatic or authored YAML? Recommendation: authored YAML for
  reproducibility and inspection. Must validate against WorldModuleSpec schema.
- 15 entities recommended for calibration (richer signal than 10, faster than 23).

## Implementation Notes
- Minimal world — do not over-engineer. The goal is pillar coverage, not narrative richness.
- `ENABLE_ADVENTURE_ROUTING: true` must appear in world flags or be set via env var for the run.
- Verify after TCK-20260630-SIMQ-CALFIX is complete so the world is actually loaded.

## Test Summary
- Calibration run with 500 ticks, verify pillar event counts > 0 for ≥ 7 pillars
- No hard law violations in run
- Quality profile loads correctly (all weights = 1.0)

## Files Changed
(to be filled at implementation)

## Completion Summary
(to be filled at completion)
