---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE
artifact_type: investigation
tags: [simulation-quality, world, adventure, corpus, calibration]
---

# investigation.md — TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE

## Current Behavior (file:line refs)

The ticket's own Assumptions/Open Questions section explicitly flagged this as needing real
investigation, unlike gaps #1/#2/#5's more confident premises: "confirming or disputing whether
`hero_guild_routing` already partially satisfies this gap."

**Also relevant, discovered during this ticket's investigation:** the motivating urgency cited in
this ticket's Request Summary ("flagged higher... given the direct connection to the already-open
ECONOMY investigation") is now moot — `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`
closed earlier this session with a "no fix needed, confirmed correct scorer behavior" finding; it
never needed this ticket's substrate.

## Verification (real corpus data and content comparison)

**Scale comparison** — `hero_guild_routing` vs. its formal peer group (Unit tier) and the tier it
scale-matches (End-to-end):

| World | Tier (as classified) | Entities | Regions | Quests | Factions |
|---|---|---|---|---|---|
| `unit_faction_tension` | Unit | 18 | 3 | 6 | 3 |
| `unit_information_source`/`unit_selfmodel_pilot`/`unit_information_density` | Unit | 16 | 1 | 3 | 3 |
| **`hero_guild_routing`** | **Unit (as classified)** | **31** | **4** | **10** | **5** |
| `urban_political` | End-to-end | 30 | 3 | 9 | 4 |
| `dungeon_crawl` | End-to-end | 32 | 4 | 9 | 4 |
| `highland_traverse` | End-to-end | 18 | 5 | 6 | — |

`hero_guild_routing` is **dramatically larger and richer than every real Unit-tier world in the
corpus** (nearly 2x the entities, 3-4x the quests) and matches or exceeds End-to-end-tier peers
`urban_political` and `dungeon_crawl` on every axis. Its formal "Unit" classification (in
`corpus_tier_taxonomy.md`, reflecting its role isolating `ENABLE_ADVENTURE_ROUTING` in the test
suite) does not match its actual scale or content richness.

**Content comparison against `simq_routing_test`** (the explicit fixture baseline gap #4 wants to
distinguish from): `simq_routing_test`'s own header comment states plainly "Minimal world for
SimQ 10-pillar calibration" — an explicit fixture framing. `hero_guild_routing`'s own
`world.yaml` description instead reads: *"Real-scale routing-capable archetype: a hero guild's
home settlement dispatches adventuring parties across three competing destinations — a mountain
pass, a goblin camp, and haunted ruins — choosing between routes rather than following one linear
path... distinct from `urban_political`'s settlement/trade-pressure framing and `dungeon_crawl`'s
pure dungeon-exploration framing."* — already explicitly self-described as a real archetype at
authoring time (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`).

**Confirmed it composes real economic/social content**, matching what this ticket's own Scope
asked a new world to have ("a settled region with real economic/social content where entities
plausibly have reason to adventure, craft, buy, and trade as part of ordinary life"):
`hero_guild_routing` includes `frontier_village_core`, which provides a `shop`, `blacksmith`,
`town_hall`, `inn`, `healer_hut`, `resource_recipes` (wood/herb harvesting), trade relationships,
and a full village population (workers/guards/merchants/blacksmith) — verified by direct read of
`data/content/world_modules/frontier_village_core.yaml`.

**Quest diversity**: 10 quest_definitions spanning 6 distinct types (fetch, escort, defend, hunt,
explore, investigate) across 4 coherent regions (a home town plus 3 distinct wilderness
destinations) — verified via direct read of the resolved world spec, not just counts.

## Conclusion

**Gap #4 is already closed** by `hero_guild_routing` — the same staleness pattern found in gaps
#1/#2, but requiring deeper verification here since no per-world table entry explicitly claimed
"fills gap 4" (unlike gaps #1/#2's crowded_frontier/resource_dense_basin entries). The world's
formal "Unit" tier label reflects its role in the test suite (isolating one feature flag), not its
actual content scale, which already substantially exceeds every genuine Unit-tier fixture and
matches End-to-end peers. Authoring a new world would duplicate `hero_guild_routing`'s already-
established role. The correction needed is a documentation/classification fix — acknowledging
`hero_guild_routing` dual-serves both roles — not a new world.

**Reconciling with the earlier, more skeptical assessment cited in this ticket's own text**
("per this session's own investigation is itself closer to a routing-focused fixture than a broad
archetype"): that assessment predates this investigation's direct scale/content comparison and
appears to have been a surface-level read, not grounded in the comparative numbers above. This
investigation's evidence (hard entity/region/quest/faction counts against both peer groups, plus
direct content verification) supersedes it.

## Docs Requiring Update
- `docs/simulation_quality/corpus_tier_taxonomy.md`: gap #4 marked CLOSED, citing
  `hero_guild_routing`; its own per-world table entry (line 139) updated to acknowledge the dual
  role explicitly, rather than only describing it as a Unit-tier isolation world.

## Parity Ledger Overlap
None.

## Prior Work
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` — authored `hero_guild_routing`, already at
  real-archetype scale by design, just never formally credited with closing gap #4.
- `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS` (this session) — closed without needing
  this ticket's substrate; the motivating urgency for this ticket is now moot, independent of this
  investigation's own finding.
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`,
  `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE` (this session) — same staleness pattern,
  precedent for this correction.

## Risks and Open Questions
None outstanding. The scale/content comparison is conclusive and directly verified, not assumed.
