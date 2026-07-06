---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP
phase: open
date: 2026-07-06T15:27:41Z
tags: [simulation-quality, world, adventure, bug]
---

# TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP

## Title
`urban_political` has the identical dormant `hometown` resource-opportunity gap as
`simq_routing_test` — currently inert only because its shipped calibration profile keeps
`ENABLE_ADVENTURE_ROUTING` off

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4, cross-world audit)
found that `urban_political` shares both `frontier_village_core` (places `wood_node`/`herb_patch` in
`hometown`) and `hero_adventurers` (spawns all 3 hero-role entities in `hometown`) with
`simq_routing_test` — the exact two modules whose combination produces the "hero permanently stuck
on `defer_with_reason`" failure mode when a hero's `sociability` roll lands under the `FORM_PARTY`
gate (`src/domains/adventure/generator.py:124`) and no resource node's `source_region_tags` covers
`hometown` (`src/world/providers/resources.py:69`).

`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s fix (adding `"hometown"` to
`wood_node`/`herb_patch`'s catalog `source_region_tags` in `data/content/world/resources.yaml`) is a
global, world-agnostic catalog change, so it **already closes the content half of this gap for
`urban_political` too**, as a confirmed side effect (see that ticket's Completion Summary for the
read-only verification performed). What remains unresolved for `urban_political` specifically is the
**profile half**: its shipped SimQ calibration profile does not currently force
`ENABLE_ADVENTURE_ROUTING=ON` (confirmed via `docs/simulation_quality/eval_matrix_results.md`'s
"AGENCY — Cross-World Design Note": `simq_routing_test` is documented as "the one calibration world
that forces `ENABLE_ADVENTURE_ROUTING=ON`"), so `AdventureDecisionPhase` never runs for
`urban_political` today and this gap cannot currently manifest as an observed calibration failure.
It would reproduce `simq_routing_test`'s identical failure mode the moment `urban_political` (or any
future world reusing `hero_adventurers`) enables adventure routing and an unlucky-`sociability` hero
lands in `hometown`.

This ticket is filed as a P2 (dormant, not currently observed failing) tracking item — not a P1/P0
active-failure fix — per the parent ticket's own explicit scope decision to not expand its own scope
to cover this.

## Scope
- Decide, with evidence, whether `urban_political`'s calibration profile should ever force
  `ENABLE_ADVENTURE_ROUTING=ON` (a design/roadmap question — check `docs/simulation_quality/` and any
  `urban_political`-specific archetype docs for whether "routing-capable" was ever intended for this
  world), or whether the dormant risk should simply be explicitly documented as an accepted
  archetype boundary (mirroring the "AGENCY=C is archetype-correct for non-routing worlds" note
  already in `eval_matrix_results.md`).
- If routing is ever enabled for `urban_political` (in this ticket or a future one triggered by that
  design decision), re-run its calibration (seeds 42/123/456) and confirm the now-fixed
  `wood_node`/`herb_patch` `hometown` tags actually prevent the stasis failure mode there too (do not
  assume — verify live, per this ticket family's established precedent).
- If routing is never enabled, close this ticket by adding an explicit "dormant, accepted" note
  to `docs/simulation_quality/eval_matrix_results.md`'s "AGENCY — Cross-World Design Note" section,
  cross-referencing this ticket and `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`, so a
  future reader doesn't have to re-derive this analysis from scratch.

## Out of Scope
- Re-fixing the `wood_node`/`herb_patch` catalog `source_region_tags` — already fixed globally by
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`; do not duplicate that work.
- The broader corpus-wide resource-tag/spawn-region coverage pattern for non-hero roles — tracked
  separately by `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`.
- Changing the `FORM_PARTY` `sociability >= 0.2` gate value — a separate design/balance question.

## Acceptance Criteria
- [ ] Explicit decision recorded (with rationale) on whether `urban_political` should ever force
      `ENABLE_ADVENTURE_ROUTING=ON`
- [ ] If enabled: `urban_political` calibration re-run for seeds 42/123/456, AGENCY grade confirmed
      not to collapse the way `simq_routing_test_seed456` originally did (the content fix should
      prevent it, but this must be live-verified, not assumed)
- [ ] If not enabled: `docs/simulation_quality/eval_matrix_results.md` updated with an explicit
      "dormant, accepted" note for `urban_political`'s `hometown` gap, cross-referencing this ticket
      and the parent content-fix ticket
- [ ] `grade_anchors.json` updated if a new `urban_political` calibration run changes any pillar's
      grade

## Related Tickets
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP (parent — filed this ticket; its content fix
  already closes this gap's content half as a side effect; its investigation.md §4(i) is this
  ticket's primary evidence trail)
- TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE — the scoring-formula fix for the same failure mode in
  `simq_routing_test`, for reference on how the failure mode was diagnosed and scored
- TCK-20260627-P0B-URBAN-RESOURCE-NODES — original ticket that placed `wood_node`/`herb_patch` in
  `hometown` via `frontier_village_core.yaml`, for both worlds using that module

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — "AGENCY — Cross-World Design Note" section
  (documents `simq_routing_test` as the only routing-forced world today)
- `docs/mechanics/adventure_routing_contract.md` — the `defer_with_reason` fallback contract this
  gap interacts with

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP/` (once finalized) —
  investigation.md §4(i) is the direct evidence source for this ticket

## Related Code Areas
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`
- `data/worlds/urban_political/` — world spec/modules and shipped calibration profile
- `data/content/world_modules/hero_adventurers.yaml`, `frontier_village_core.yaml` — shared modules
  causing this gap in both worlds
- `src/domains/optimization/feature_flags.py` — `ENABLE_ADVENTURE_ROUTING` flag default

## Assumptions / Open Questions
- Whether `urban_political` was ever intended to be "routing-capable" is unconfirmed — this ticket's
  first Scope item is to answer that question with evidence before deciding whether to enable the
  flag or document the dormancy as permanent.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
