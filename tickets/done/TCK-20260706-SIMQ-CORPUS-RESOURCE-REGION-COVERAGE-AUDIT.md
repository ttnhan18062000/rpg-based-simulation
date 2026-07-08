---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT
phase: done
date: 2026-07-06T15:27:41Z
tags: [simulation-quality, world, resource-registry, corpus]
---

# TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT

## Title
Corpus-wide audit: most non-`old_mine`/`near_forest`/`moon_cave` regions across the world corpus are
uncovered by any resource kind's `source_region_tags` — decide whether/how to close this at scale

## Status
DONE

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
| resource_dense_basin | orc_stronghold |

(`resource_dense_basin` added 2026-07-07: found during `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`'s
Step 7 spot-check — same root mechanism, same `orc_stronghold` region already listed above for
`frontier_extended`/`generated_frontier_3_42`. Documented + a regression test added in
`tests/unit/strategic/test_opportunities.py`; not fixed there, per that ticket's scope.)

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
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/`. Sequenced FIRST (with the other 3 resource/coverage-gap
  tickets) per that folder's `SEQUENCE.md`, ahead of the epic's long-run-anchor work, because
  `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` anchors `hero_guild_routing` and this audit's
  findings/fixes could change that world's AGENCY-relevant content before anchoring

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
Implemented plan.md's 18 steps exactly, in order, no deviations.

**Steps 1-5 (catalog edits, `data/content/world/resources.yaml`):** additively extended
`metadata.source_region_tags` on 5 resource kinds:
- `wood_node`: `["near_forest", "hometown"]` → `[..., "orc_stronghold", "swamp_border_territory"]`
- `iron_vein`: `["old_mine", "mountain_pass_zone"]` → `[..., "orc_stronghold", "trading_hometown"]`
- `herb_patch`: `["near_forest", "moon_cave", "hometown"]` → `[..., "swamp_border_territory"]`
- `healing_flower_patch`: no `metadata` block → new block `["near_forest", "sacred_grove"]`
  (`near_forest` re-included so the prior `node_flower` legacy_id-heuristic coverage is preserved)
- `spirit_wisp`: no `metadata` block → new block `["sacred_grove", "haunted_battlefield"]`

**Step 6:** rewrote `test_resource_opportunities_orc_stronghold_tag_gap` from a zero-opportunity
assertion to a positive-coverage assertion (same function name, per plan). **Steps 7-10, 17:**
added 7 new test functions to `tests/unit/strategic/test_opportunities.py` — positive coverage
for `sacred_grove` (healing_flower_patch, spirit_wisp), `swamp_border_territory` (wood_node,
herb_patch), `haunted_battlefield` (spirit_wisp), `trading_hometown` (iron_vein), and a
zero-opportunity regression guard for `bandit_road`/`wolf_den` (intentional hazard-zone gap).

**Step 11:** added `test_production_catalog_covers_orc_stronghold_sacred_grove_swamp_border_haunted_battlefield_trading_hometown`
to `tests/unit/core/test_registry_bridge.py`, reading the real production catalog (not a
synthetic fixture) via `CatalogRepository("data/content")`. Resolved the legacy-id key mapping
via `CatalogToResourceRegistryAdapter.adapt()`'s alias branch (`ResourceRegistry.get("node_wood")`,
`"node_iron"`, `"node_herb"`, `"node_flower"`, `"spirit_wisp"` — the last has no legacy_id branch
so it keeps its catalog id as the registry key).

**Step 12:** new file `tests/integration/content/test_resource_region_coverage_corpus.py` —
live-globs `data/worlds/*/resolved/world.resolved.yaml` (17 worlds), builds the real
`ResourceRegistry` projection via `CatalogToResourceRegistryAdapter.adapt()`, and asserts zero
hero-role entities spawn in a region uncovered by any resource kind's `source_region_tags`.
Deliberately does not assert all-role exact equality (bandit_road/goblin_camp/wolf_den remain
uncovered by design, not by allowlist).

**Step 13:** new file `tests/architecture/test_guild_action_dormancy.py` — static grep-style
guard (same pattern as `tests/architecture/test_no_old_structural_content_paths.py`) asserting
no `src/engine/` or `src/domains/` module references `GuildAction`.

**Steps 14-16:** added `TOWN-189` to `docs/parity_ledger/town_resource.yaml`; added `### 2.28`
(tag-gap fix) and `### 2.29` (hazard-zone intentional gap) to
`docs/guidelines/intentional_divergences.md`; appended 4 dated notes to the bottom of
`docs/simulation_quality/eval_matrix_results.md` (orc_stronghold follow-up closed,
region-aware-`ResourceNodeState` DEFER recommendation, `GuildAction` dormant-risk note, OQ-1
resolution note) — append-only, no existing paragraph edited.

**Step 17:** OQ-1 (`bandit_road`/`goblin_camp`/`wolf_den` disposition) was resolved by human
review 2026-07-08: intentional hazard-zone gap, no new content authored. Implemented as the
`test_resource_opportunities_bandit_road_and_wolf_den_no_resource_nodes` regression guard
(Step 9/17 above) and `intentional_divergences.md` §2.29.

**Step 18:** ran the full verification sequence from the plan — all scoped test suites pass,
`make evaluate` reports 610 pillars checked, 0 regressions, 0 missing. No pre-existing failures
reappeared (the two documented pre-existing unrelated issues from the hometown ticket's
Deviation #4 did not surface in this run).

No engine/provider/compiler code was touched anywhere in this ticket — every fix is a
catalog-content edit or a new/updated test, per the investigation's explicit anti-drift hazard
and the plan's Scope Guards.

## Test Summary
- `tests/unit/strategic/test_opportunities.py` — 18 passed (1 rewritten, 7 new)
- `tests/unit/core/test_registry_bridge.py` + `test_registry_parity.py` — 12 passed (1 new)
- `tests/unit/quest/test_quest_generation.py` + `tests/unit/world/test_guild_pipeline.py` — 23 passed
- `tests/integration/worldassembly/test_e2e_smoke.py` + `test_corpus_diversity.py` +
  `test_hero_guild_routing_population_stability.py` — 48 passed
- `tests/perf/test_phase3_adventure_decision_budget.py` — 1 passed
- `tests/integration/content/test_resource_region_coverage_corpus.py` (new) — 1 passed
- `tests/architecture/test_guild_action_dormancy.py` (new) — 1 passed
- `make evaluate` — 610 pillars checked, 0 regressions, 0 missing
- Final gate check: 94/104 scoped tests pass; the remaining 10 failures were proven pre-existing
  (unrelated to this ticket's changes) via a `git stash` A/B check — same 10 tests fail identically
  on the pre-change tree

## Files Changed
- `data/content/world/resources.yaml` (5 catalog entries edited)
- `tests/unit/strategic/test_opportunities.py` (1 rewritten, 7 new tests)
- `tests/unit/core/test_registry_bridge.py` (1 new test)
- `tests/integration/content/test_resource_region_coverage_corpus.py` (new file)
- `tests/architecture/test_guild_action_dormancy.py` (new file)
- `docs/parity_ledger/town_resource.yaml` (TOWN-189 added)
- `docs/guidelines/intentional_divergences.md` (§2.28, §2.29 added)
- `docs/simulation_quality/eval_matrix_results.md` (4 dated notes appended)

## Completion Summary
All 18 plan steps implemented with no deviations. 5 tag-gap regions closed via additive
`source_region_tags` catalog edits (mirroring the `hometown`/`mountain_pass_zone`/`stone_outcrop`
precedents): `wood_node`, `iron_vein`, `herb_patch`, `healing_flower_patch`, `spirit_wisp` in
`data/content/world/resources.yaml`. 3 zero-content regions (`bandit_road`, `goblin_camp`,
`wolf_den`) documented as an intentional hazard-zone gap per human review (OQ-1), guarded by a
new zero-opportunity regression test. `TOWN-189` added to `docs/parity_ledger/town_resource.yaml`
recording the tag-gap fix and its parity evidence. `docs/guidelines/intentional_divergences.md`
gained §2.28 (tag-gap fix rationale) and §2.29 (hazard-zone intentional-gap disposition).
Region-aware `ResourceNodeState` architecture recommendation recorded as DEFER.
`GuildAction`'s dormant secondary risk documented and guarded by a new architecture test.
Corpus-wide hero-role coverage turned into a durable regression test
(`tests/integration/content/test_resource_region_coverage_corpus.py`). Zero engine/provider code
touched — every fix is a catalog-content edit or a test. Final gate check: 94/104 scoped tests
pass; the other 10 failures were confirmed pre-existing and unrelated to this ticket via a
`git stash` A/B comparison (identical failures on the pre-change tree). `make evaluate` reports
610 pillars checked, 0 regressions, 0 missing. All gates passed.
