---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
phase: open
date: 2026-07-03
tags: [simulation_quality, worldbuilding, calibration, content, test-suite]
---

# TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS

## Title
Diversify the SimQ calibration world corpus — more entity/resource scale and content variety, not just more seeds of the same worlds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`TCK-20260702-SIMQ-EVAL-MATRIX` already extended the calibration corpus from single-seed point
estimates to a multi-seed × multi-tick matrix — but explicitly scoped that as more seeds/ticks of
the *same four worlds already producing signal* (`dungeon_crawl`, `urban_political`,
`simq_routing_test`, `sandbox_world`), and explicitly marked "worlds without confirmed non-C
signal in default mode" as out of scope. `data/worlds/` already has 10 compiled worlds and
`data/content/world_modules/` has 20 modules, but several (`frontier_extended`,
`frontier_living_world`, `generated_frontier_3_42`, `highland_traverse`, `swamp_border_world`,
`wilderness_survival`) are thin in the calibration corpus — some terminate early due to P2-B
(entity attrition outpaces spawn rate) at higher entity counts, per `docs/plans/audit_fix_plan.md`.

Per 2026-07-03 user direction: instead of continuing to seed FACTION/INFORMATION-style content
into just 1-2 more of the *existing* worlds, invest in genuinely broader world diversity — varied
entity counts, resource-node density/types, region counts, and content-module combinations — so
the calibration corpus functions as a real test suite across world *shapes*, not just more runs of
the same handful of world shapes. This is a bigger, longer-horizon investment than the FACTION/
INFORMATION single-world activations.

## Scope
1. Audit the current 10 worlds in `data/worlds/` and 20 modules in `data/content/world_modules/`
   for actual diversity: entity count range, resource node count/type range, region count range,
   which of the 10 SimQ pillars each world can even theoretically produce signal for (some worlds
   are structurally blind to certain pillars, e.g. `sandbox_world` is combat-only per
   `docs/audits/D20_simq_integration.md`).
2. Identify concrete gaps: e.g. no small-entity-count world, no world combining FACTION-relevant
   content with INFORMATION-relevant content, no world at a size between `sandbox_world` (small)
   and `frontier_extended`/`frontier_living_world` (56/46 entities, early-terminating per P2-B).
3. Author 2-4 new world compositions (or substantially extend existing thin ones) filling the
   identified gaps — using existing catalog content/modules where possible, new module content
   only where a genuine content gap blocks a useful scenario shape.
4. If P2-B (spawn/attrition imbalance) is still blocking the existing larger worlds from completing
   full-length calibration runs, either fix it as part of this ticket or file it as an explicit
   sub-blocker (do not silently work around it by only adding small worlds).
5. Add the new/extended worlds to the calibration corpus (`grade_anchors.json`,
   `test_grade_regression.py`) following the pattern `TCK-20260702-SIMQ-EVAL-MATRIX` established.
6. Update `docs/simulation_quality/eval_matrix_results.md` and
   `docs/audits/D20_simq_integration.md` with the expanded corpus's grade distributions.

## Out of Scope
- Re-running more seeds/ticks of the 4 already-well-covered worlds (that's
  `TCK-20260702-SIMQ-EVAL-MATRIX`'s completed scope)
- Fixing any SimQ pillar's underlying scoring/emission logic discovered to be broken by the new
  worlds (file a follow-up ticket instead, per the pattern in
  `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`)
- Seeding FACTION/INFORMATION-specific content (tension overrides, information source profiles)
  into the new worlds — that's a natural follow-on once this ticket's worlds exist, not part of
  this ticket's own scope

## Acceptance Criteria
- [ ] Current corpus diversity audited and gaps documented (entity/resource/region range, per-world
      pillar-reachability)
- [ ] At least 2 new or substantially-extended world compositions exist, filling identified gaps
- [ ] P2-B (spawn/attrition imbalance) status re-confirmed for any world this ticket touches —
      either fixed or explicitly tracked, not silently avoided
- [ ] New worlds added to `grade_anchors.json`/`test_grade_regression.py` following the established
      pattern
- [ ] `docs/simulation_quality/eval_matrix_results.md` and `docs/audits/D20_simq_integration.md`
      updated with the expanded corpus
- [ ] `make evaluate --dry-run` exits 0 (0 regressions on existing worlds)

## Related Tickets
- TCK-20260702-SIMQ-EVAL-MATRIX (done) — established the seed/tick matrix pattern this ticket
  extends to new world shapes instead
- TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE — should land first so validating this larger corpus
  doesn't take hours
- TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW — benefits from this ticket's expanded corpus existing

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/audits/D20_simq_integration.md`
- `docs/plans/audit_fix_plan.md` — P2-B (spawn cadence tuning), P2-C (archetype distribution,
  already resolved)
- `docs/guides/content_authoring.md` — world/composition authoring process

## Related Stored Artifacts
- `stored_artifacts/TCK-20260702-SIMQ-EVAL-MATRIX/` (if present)

## Related Code Areas
- `data/worlds/` — existing compiled worlds
- `data/content/world_modules/` — existing content modules
- `src/world/spawn.py`, `src/world/spawn_config.py` — spawn cadence (P2-B)
- `tools/calibrate_simq.py`, `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py`

## Assumptions / Open Questions
- UQ-1: Should new worlds be entirely new compositions, or substantial rework of the existing
  early-terminating ones (`frontier_extended`, `frontier_living_world`)? Investigate P2-B's actual
  current status first (per `docs/plans/audit_fix_plan.md`'s 2026-07-03 refresh, this was marked
  "unverified" — confirm before deciding whether new worlds or fixing existing ones is the right
  path).
- UQ-2: What is "good enough" for this test suite — is there a target number of worlds, or a target
  coverage matrix (e.g. every pillar reachable by at least 2 worlds of different sizes)? This
  should be decided during investigation/planning, not left implicit.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
