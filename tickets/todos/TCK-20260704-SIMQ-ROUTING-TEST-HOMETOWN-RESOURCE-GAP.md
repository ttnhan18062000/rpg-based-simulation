---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP
phase: open
date: 2026-07-04
tags: [simulation-quality, world, adventure, bug]
---

# TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP

## Title
`simq_routing_test` world content gap: no resource node is tagged for the `hometown` spawn region, so any hero rolling `sociability < 0.2` is permanently stuck

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While investigating `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE` (AGENCY=F collapse in
`simq_routing_test` seed456), the investigation traced entity 23's permanent
`defer_with_reason` streak to two combined, independently-confirmed conditions:

1. **World content gap (this ticket's scope)**: `simq_routing_test`'s compiled world has 5
   resource nodes (`herb_patch → (near_forest, moon_cave)`, `wood_node → (near_forest,)`,
   `iron_vein → (old_mine,)`, `silver_vein → ()`, `crystal_outcrop → ()`). **None list `hometown`**
   in `source_region_tags`. All heroes in this world spawn with `navigation.region_id = "hometown"`
   (confirmed for all 30 entities, all 3 seeds — seed-independent). `ResourceOpportunityProvider
   .get_opportunities()` (`src/world/providers/resources.py:69`, `if current_region in
   res_def.source_region_tags:`) therefore **never** returns a `gather_resource` opportunity for
   any hero standing in `hometown`, regardless of seed or entity.
2. **Personality RNG roll (out of scope — not a bug, seed456-specific)**: `FORM_PARTY`
   (`src/domains/adventure/generator.py:124`, `if sociability >= 0.2:`) is the only other route
   family available to a `hometown`-spawned hero (no active needs/perceived weaknesses means
   `RECOVER`/`ASK_INFORMATION` never fire either — `generator.py:97,110`). In seed456, entity 23's
   compiled `sociability = 0.18816...`, just under the `0.2` gate. In seed42/123 the same entity
   rolls `0.534`/`0.407` — comfortably above the gate.

Condition (1) is the one that turns a single below-gate personality roll into a **total, permanent,
whole-run** dead end: with even one `hometown`-tagged resource node, an unlucky-`sociability` hero
would still have `gather_resource` as a fallback route. Without it, `sociability < 0.2` alone is
sufficient to strand a hero for its entire life, in every seed where that roll occurs — this is a
**seed-independent structural fragility** in this world's content, separate from (and not fixed by)
`TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`'s scoring-formula fix (which only bounds the *penalty* for
being stuck — it does not and should not un-stick a legitimately-stuck entity).

## Scope
- Add at least one resource node to `simq_routing_test`'s world content (`data/worlds/
  simq_routing_test/` — compiled via `WorldCompiler.compile()`, source spec/modules TBD by
  investigation) whose `source_region_tags` includes `hometown`, so a hero spawned there always has
  at least one non-`FORM_PARTY` route family available.
- Investigate whether this same gap exists in other calibration worlds that spawn heroes in a
  region not covered by any resource node's `source_region_tags` (a quick audit across
  `data/worlds/*` — not just `simq_routing_test` — before authoring the fix, to avoid a narrow
  point-fix if this is a recurring worldbuilding-authoring gap).
- Re-run `simq_routing_test` calibration for all 3 seeds post-fix and confirm the change doesn't
  regress AGENCY or any other pillar's grade for seed42/123 (which don't rely on this fallback
  today, since their entity 23 rolls above the `FORM_PARTY` gate).

## Out of Scope
- `AgencyScorer`'s stasis-penalty formula (already fixed in `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`)
- Adventure decision logic itself (`AdventureDecisionPhase`/`Generator`/`Service` — confirmed
  correct, not the bug; the fallback-guarantee behavior when `opts` is empty is working exactly as
  designed)
- Changing the `FORM_PARTY` `sociability >= 0.2` gate value itself (a separate design/balance
  question, not a content-authoring gap)

## Acceptance Criteria
- [ ] At least one resource node in `simq_routing_test` has `hometown` in its
      `source_region_tags`, confirmed via `WorldCompiler.compile()` inspection
- [ ] A hero spawned in `hometown` with `sociability < 0.2` and no active needs/perceived
      weaknesses now has at least one non-`defer_with_reason` candidate route
      (`gather_resource`) at every tick
- [ ] Cross-world audit performed: either confirmed `simq_routing_test`-only, or a broader fix
      applied if the same spawn-region/resource-tag mismatch exists elsewhere
- [ ] `simq_routing_test` seed42/123/456 calibrations re-run; no AGENCY (or other pillar)
      regression for seed42/123; seed456's AGENCY grade re-verified against whatever grade the
      scoring-formula fix (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE) left it at
- [ ] `grade_anchors.json` updated if seed456's AGENCY grade changes as a result of this content fix

## Related Tickets
- TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE (in progress at time of filing) — the scoring-formula
  fix this gap was discovered alongside; that ticket's investigation.md §2.1, §3, and its plan.md's
  Unresolved Question section are the primary evidence trail for this ticket
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP (done) — unrelated crash fix that first allowed
  `simq_routing_test` calibration to run to completion, surfacing both findings

## Related Docs
- `docs/mechanics/adventure_routing_contract.md` — documents the `generator.py:164-175`
  empty-candidate-set fallback (`defer_with_reason`) as intended when `opts` is empty; this ticket
  does not change that contract, only the world content that makes the fallback fire unnecessarily
  often for `hometown`-spawned heroes
- `docs/simulation_quality/eval_matrix_results.md` — AC6 section documents the seed456 AGENCY
  finding this gap contributes to

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE/` (once finalized) — investigation and
  plan documenting the discovery of this gap as a byproduct of the stasis-collapse investigation

## Related Code Areas
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`,
  `source_region_tags` gating (line 69)
- `data/worlds/simq_routing_test/` — the world spec/modules to be amended
- `src/domains/adventure/generator.py` — `FORM_PARTY` gate (line 124) and empty-candidate-set
  fallback (lines 164-175), read-only reference, not to be changed by this ticket

## Assumptions / Open Questions
- Whether this is unique to `simq_routing_test` or a broader worldbuilding-authoring convention gap
  across other calibration worlds is unconfirmed — first Scope item requires an audit before
  deciding whether this is a point-fix or a pattern-fix.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
