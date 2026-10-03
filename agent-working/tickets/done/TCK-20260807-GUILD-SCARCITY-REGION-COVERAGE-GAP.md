---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP
phase: done
date: 2026-08-07
tags: [strategy, simulation-quality]
---

# TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP

## Title
`GuildAction.visit()`'s scarcity computation can silently report `scarcity=0.0` (fully abundant)
for regions with incomplete `source_region_tags` catalog coverage — now live, no longer dormant

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` (DONE) found `GuildAction.visit()`
(`src/town/guild.py`) independently reimplements the same `region_id in
res_def.source_region_tags` matching as `ResourceOpportunityProvider` to compute a `scarcity`
signal feeding `QuestPressureProfile`/`QuestGenerator.generate_quests()`'s pressure-weighted
template selection — but explicitly documented this as a **dormant** risk, since `GuildAction`
was not wired into any dispatched pipeline phase at the time: "if/when it is ever wired into a
dispatched action, it would silently report `scarcity = 0.0` (not 'unknown data' — literally
treated as 'fully abundant') for any entity in an uncovered region... worth flagging... not
something this ticket needs to fix."

`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` (DONE) wired `GuildAction.visit()` live via a new
`GuildVisitPhase`, gated behind `ENABLE_GUILD_QUEST_GENERATION` (default `OFF`). Per the original
audit's own explicit guidance, this ticket exists to give that risk "its own region-coverage
evaluation" now that it's active whenever the flag is `ON` — not silently inherited or ignored.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm exactly which regions in the real content corpus have resource nodes whose catalog
     `source_region_tags` do NOT include that region (the actual coverage gap) — cross-reference
     against `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`'s own findings (option
     (a)/(b) fixes it considered but did not implement, since `GuildAction` was dormant at the
     time — check whether those recommendations are still the right fix now, or need
     re-verification against current catalog state).
   - Confirm the actual real-world impact: does `scarcity=0.0` (vs. the true value) meaningfully
     change `QuestGenerator`'s template selection in practice, or is the effect bounded/rare?
     Run a real, non-mocked comparison (patched scarcity vs. real) if the investigation can't
     determine this from static analysis alone.
2. **Plan**: design the fix — likely a catalog-content change (adding missing
   `source_region_tags` entries), per the original audit's own classification ("a catalog/content
   change, not a code or mechanics-law change... consistent with how `stone_outcrop` and the
   `hometown`/`mountain_pass_zone` precedents were classified").
3. **Implement**: apply the catalog fix; do not touch `GuildAction.visit()`'s own computation
   logic unless the investigation finds a genuine code-level bug distinct from the catalog gap.
4. Update `docs/parity_ledger/strategic_cognition.yaml`'s `STRAT-244` entry and `town_resource.yaml`
   (new entries for any regions fixed, following the `hometown`/`TOWN-188` precedent's exact
   format).

## Out of Scope
- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own wiring — already DONE, not touched here.
- `ResourceOpportunityProvider`/`AdventureDecisionPhase`'s own hero-role gating — already fully
  covered by the original audit, unaffected by this ticket.

## Acceptance Criteria
- [x] `investigation.md` confirms the exact regions/catalog entries affected and the real
      practical impact on quest-template selection (`river_ford`, real tag-gap; `deep_forest`/
      `survivor_outpost`, zero-content; scarcity 0.0→0.8 confirmed for `river_ford`)
- [x] Catalog fix applied (`river_ford` added to `herb_patch`'s `source_region_tags`); the 2
      zero-content regions' bounded-impact disposition explicitly documented, extending the
      already-human-reviewed §2.29 accepted-gap class rather than needing a fix
- [x] `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-244`) and `town_resource.yaml`
      (new `TOWN-191`) updated
- [x] Scoped pytest run passes (633/633)

## Related Tickets
- TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT (DONE — original dormant-risk finding)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (DONE — made this risk active)

## Related Docs
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-244`)
- `docs/parity_ledger/town_resource.yaml` (`TOWN-188`, the `hometown` fix precedent)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT/investigation.md`
  (§4, the original finding)

## Related Code Areas
- `src/town/guild.py` (`GuildAction.visit()`'s scarcity computation)
- Resource catalog content files (`source_region_tags` — exact location per the original audit)

## Assumptions / Open Questions
- Whether the original audit's option (a)/(b) catalog fixes are still the right approach, or need
  re-verification against current catalog state (content may have changed since 2026-07-06) — not
  assumed, this ticket's own Investigate phase must re-confirm.

## Implementation Notes
Re-verified the original 2026-07-06 audit's own findings first: all 5 of its tag-gap fixes are
still live in `data/content/world/resources.yaml` today — the premise driving this ticket
(re-evaluate the risk now that `GuildAction` is live) was correct to check, but the original fix
itself was never the gap; corpus drift since then was. A live corpus-wide re-scan (same
methodology as the original audit, but checking ALL entity roles instead of just hero) found 3
new regions unaccounted for: `river_ford` (a genuine new tag-gap — `herb_patch` physically placed
there, module biome already trusted by `herb_patch`'s own `source_region_tags`, fixed additively)
and `deep_forest`/`survivor_outpost` (both genuinely zero-content by design, extending the
already-human-reviewed §2.29 accepted-gap disposition rather than needing a fix or a fresh
decision).

Also found and fixed a real scope gap in the existing regression test
(`test_no_hero_role_entity_spawns_in_an_uncovered_region_corpus_wide`): it only ever checked
hero-role spawns, which was correct while `GuildAction` was dormant (its only two live consumers
were hero-gated) but is now stale — `GuildNeedScorer` has no role gate at all. Added a new
corpus-wide test checking all roles, closing this for future drift regardless of which role
discovers a new region first.

## Test Summary
New tests: `tests/unit/strategic/test_opportunities.py`
(`test_resource_opportunities_river_ford_herb_patch`,
`test_resource_opportunities_deep_forest_and_survivor_outpost_no_resource_nodes`) and
`tests/integration/content/test_resource_region_coverage_corpus.py`
(`test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide`). Full regression sweep
(`tests/unit/strategic/`, `tests/unit/core/test_registry_bridge.py`,
`tests/architecture/test_guild_action_dormancy.py`, `tests/unit/world/`, `tests/unit/quest/`,
`tests/integration/content/`): 633/633 pass. Real-kernel-adjacent verification: `GuildAction.visit()`'s
scarcity formula for an entity in `river_ford` computed 0.0 before this fix, 0.8 after — confirmed
the practical impact directly rather than asserting it was bounded/negligible without evidence.

## Files Changed
- `data/content/world/resources.yaml` — `herb_patch`'s `source_region_tags` additively extended
  with `"river_ford"`
- `tests/unit/strategic/test_opportunities.py` — 2 new tests
- `tests/integration/content/test_resource_region_coverage_corpus.py` — `_ACCEPTED_ZERO_CONTENT_REGIONS`
  frozenset + 1 new all-roles corpus-wide regression test
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-244` update note
- `docs/parity_ledger/town_resource.yaml` — new `TOWN-191` entry
- `docs/guidelines/intentional_divergences.md` — §2.29 update note (extended accepted-gap list);
  new §2.32 (`river_ford` tag-gap fix)

## Completion Summary
Gave `GuildAction`'s region-coverage risk its own real evaluation, as the original audit
explicitly asked for once the action went live. Found the original fix was still fully intact,
but the corpus itself had drifted — 3 new regions since the last audit, one a genuine tag-gap
(`river_ford`, fixed) and two zero-content-by-design (extending an already-reviewed disposition
class, not a new decision). Closed a real role-scope gap in the existing regression test so future
corpus drift gets caught regardless of which entity role discovers a new region first — directly
relevant now that `GuildAction` is a live, role-agnostic consumer, unlike the hero-only
`AdventureDecisionPhase` the original test was scoped around. Verified the practical impact
directly (scarcity 0.0→0.8) rather than assuming it was negligible. Zero engine code touched —
every fix is a catalog-content edit or a test, per this ticket's own Scope.
