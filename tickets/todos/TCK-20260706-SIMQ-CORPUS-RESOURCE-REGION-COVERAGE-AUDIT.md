---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT
phase: open
date: 2026-07-06T15:27:41Z
tags: [simulation-quality, world, resource-registry, corpus]
---

# TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT

## Title
Corpus-wide audit: most non-`old_mine`/`near_forest`/`moon_cave` regions across the world corpus are
uncovered by any resource kind's `source_region_tags` — decide whether/how to close this at scale

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4(ii)) performed a
corpus-wide, live-verified audit of every world under `data/worlds/*/resolved/world.resolved.yaml`
(10 worlds) for regions where entities spawn but no present resource kind's `source_region_tags`
covers that region. The result, across **all** entity roles (not just heroes):

| world | uncovered spawn regions |
|---|---|
| dungeon_crawl | bandit_road, goblin_camp, haunted_battlefield |
| frontier_extended | bandit_road, goblin_camp, haunted_battlefield, hometown, orc_stronghold, sacred_grove, wolf_den |
| frontier_living_world | bandit_road, goblin_camp, haunted_battlefield, hometown, wolf_den |
| generated_frontier_3_42 | bandit_road, goblin_camp, hometown, orc_stronghold |
| highland_traverse | hometown, wolf_den |
| sandbox_world | hometown, wolf_den |
| simq_routing_test | goblin_camp, hometown |
| swamp_border_world | hometown, swamp_border_territory, wolf_den |
| urban_political | bandit_road, hometown, trading_hometown |
| wilderness_survival | haunted_battlefield, wolf_den |

(`simq_routing_test`'s and `urban_political`'s `hometown` rows are already addressed for **hero-role**
entities by `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s catalog fix and tracked further
for `urban_political`'s profile-half by `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` —
those two rows are NOT part of this ticket's remaining scope, listed here only for completeness of
the original table.)

**Root mechanism (same as the parent ticket, at much larger scale):**
`ResourceOpportunityProvider.get_opportunities()` (`src/world/providers/resources.py:69`) gates
purely on a **global, catalog-wide, per-resource-kind** `source_region_tags` allowlist
(`ResourceRegistry.get(node.kind)`), never on a resource node's own placement region.
`ResourceNodeState` (`src/core/state.py:905-916`) has no region field at all. So any world that
places entities in a region not covered by any *kind*'s catalog tags will silently return zero
`gather_resource` opportunities for entities standing there, regardless of role, seed, or whether
any resource node physically exists nearby in-world.

Today this does not cause the specific "hero permanently stuck" calibration failure documented by
the parent ticket, because `AdventureDecisionPhase` (the only code path that can get permanently
stuck on `defer_with_reason`) only runs for `EntityRole.HERO` entities
(`src/domains/adventure/phase.py:75`), and only `simq_routing_test` and `urban_political` have
hero-role entities at all (both already covered by the parent ticket family). But the same silent
zero-opportunity condition affects any other role in any of the 10 worlds standing in these regions,
which may matter for other opportunity-consuming systems not traced further by the parent
investigation.

## Scope
1. **Audit + confirm.** Re-verify the table above live (do not just trust the parent investigation's
   copy — re-run the same `CatalogRepository`/`ResourceRegistry`/per-world resolved-spec live check)
   and determine, per uncovered region, whether any **non-hero** system currently consumes
   `ResourceOpportunityProvider` output for entities in that region (trace opportunity consumers
   beyond `AdventureDecisionPhase` — e.g. tactical/economic AI, quest generation, or any other
   strategic-cognition consumer of `get_opportunities()`).
2. **Decide, per finding, one of:**
   - (a) Add missing regions to existing resource kinds' catalog `source_region_tags` (the same
     additive-metadata-override mechanism used by `stone_outcrop` and by the parent ticket) — for
     regions where a resource kind is already physically placed there and the tag is just missing
     (mirrors the parent ticket's root cause exactly).
   - (b) Author new resource content for regions with no resource node placed at all today, if the
     audit determines that's a genuine content gap worth filling (not just a tag-projection bug).
   - (c) Explicitly document as an accepted/intentional gap (e.g. `wolf_den`/`bandit_road`-style
     hazard/combat regions may not be intended to have gatherable resources) — add the decision to
     `docs/guidelines/intentional_divergences.md` or an equivalent doc, not leave it silently unstated.
   - Evaluate `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation.md §3 rejected
     option (c) — making `ResourceNodeState` region-aware so gating is per-node-placement rather than
     per-kind-catalog — as one candidate **long-term architectural direction** given how widespread
     this pattern is at corpus scale. This ticket should record a recommendation (adopt now / defer /
     reject) but is **not required to implement** that architecture change itself.
3. Implement whichever combination of (a)/(b)/(c) the audit's findings justify, on a per-region basis
   — this ticket is scoped to "audit + fix-or-decide," not "must fix every row in the table."
4. Re-run `make evaluate --dry-run` after any catalog/content changes to confirm zero regressions
   across the corpus.

## Out of Scope
- `simq_routing_test`'s and `urban_political`'s `hometown` rows for hero-role entities — already
  handled by `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` and
  `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`. Do not duplicate that work.
- Making `ResourceNodeState` region-aware as a committed implementation in this ticket (evaluate as a
  recommendation only, per Scope item 2's last bullet — implementing it, if recommended, should be
  its own follow-up ticket given the durable-state schema change and blast radius across the
  compiler/provider/tests).
- Any decision-logic changes to `AdventureDecisionPhase`/`Generator` — this is a content/catalog
  audit, not a routing-logic change.

## Acceptance Criteria
- [ ] Live-reverified uncovered-region table (per world, per region) confirming or correcting the
      parent investigation's §4(ii) findings
- [ ] Non-hero opportunity-consumer trace completed — documents whether any system besides
      `AdventureDecisionPhase` is affected by these gaps today
- [ ] Each uncovered region has an explicit disposition recorded: fixed (tag added), fixed (content
      authored), or explicitly accepted-as-intentional-gap (with doc reference)
- [ ] Recommendation recorded (adopt-now / defer / reject) on the region-aware `ResourceNodeState`
      architecture option, with rationale
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions after any changes made
- [ ] `make knowledge-index-update` run if `docs/` files were modified

## Related Tickets
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP (parent — filed this ticket; its
  investigation.md §4(ii) is this ticket's primary evidence trail; its §3 rejected-option (c) is the
  architecture question this ticket must evaluate)
- TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP (sibling follow-up — covers the
  `urban_political` hero/hometown row specifically; do not duplicate)
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP — established the `metadata.source_region_tags`
  additive-override mechanism this ticket's option (a) reuses

## Related Docs
- `docs/mechanics/adventure_routing_contract.md`
- `docs/guidelines/intentional_divergences.md` — candidate location for option (c) dispositions and
  the region-aware-gating architecture recommendation

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP/` (once finalized) —
  investigation.md §4(ii)'s full table and rationale is this ticket's direct evidence source

## Related Code Areas
- `src/world/providers/resources.py` — `ResourceOpportunityProvider.get_opportunities()`
- `src/core/registries.py` — `CatalogToResourceRegistryAdapter.adapt()`, `ResourceDef`
- `src/core/state.py` — `ResourceNodeState` (region-aware-gating evaluation target, not to be
  changed without a separate decision)
- `data/content/world/resources.yaml` — likely target for option (a) fixes
- `data/worlds/*/resolved/world.resolved.yaml` — all 10 worlds, audit scope

## Assumptions / Open Questions
- Whether hazard/combat-flavored regions (`wolf_den`, `bandit_road`, `goblin_camp`,
  `haunted_battlefield`, `orc_stronghold`) are intentionally resource-free (a design choice —
  "you don't forage in the middle of a bandit camp") or an authoring oversight is unconfirmed; this
  ticket's Scope item 1-2 requires resolving that per-region before choosing (a)/(b)/(c), not
  assuming one answer for all of them.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
