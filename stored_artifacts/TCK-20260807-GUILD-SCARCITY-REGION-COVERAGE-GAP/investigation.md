---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP
artifact_type: investigation
tags: [strategy, simulation-quality]
---

# Investigation: TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP

## Step 1: is the original coverage gap this ticket assumed still open?

Read `stored_artifacts/TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT/investigation.md`
and its ticket's own Completion Summary in full. Found the original 5 tag-gap regions
(`orc_stronghold`, `sacred_grove`, `swamp_border_territory`, `haunted_battlefield`,
`trading_hometown`) were **already fixed** by that ticket itself, additively, in
`data/content/world/resources.yaml` — confirmed live by grepping the current file: all 5
`source_region_tags` extensions are present today. `GuildAction`'s dormant risk was also already
"documented and guarded by a new architecture test"
(`tests/architecture/test_guild_action_dormancy.py`), which is the same file
`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` later updated to reflect its one deliberate dispatch
site. So this ticket's own premise ("give the risk its own region-coverage evaluation") was
written correctly at the time — the catalog fix predates the wiring by exactly one month, but
whether the fix is still complete against the *current* corpus (which may have grown since
2026-07-06) was the genuinely open question, not whether a fix ever happened.

## Step 2: live corpus-wide re-scan for drift since 2026-07-06

Per the ticket's own Assumptions/Open Questions ("content may have changed since 2026-07-06 —
this ticket's own Investigate phase must re-confirm"), re-ran the original audit's own
methodology fresh: loaded `ResourceRegistry`'s live `source_region_tags` coverage via
`CatalogToResourceRegistryAdapter`, then enumerated every region declared in every
`data/worlds/*/resolved/world.resolved.yaml` (19 worlds today, vs. the original audit's 10/11 —
confirmed corpus growth). Found 3 regions not covered by any resource kind's `source_region_tags`
that weren't in the original audit's disposition table at all: `river_ford`, `deep_forest`,
`survivor_outpost`.

## Step 3: per-region disposition trace (same methodology as the original audit)

| region | node(s) physically placed? | placing module | kind(s) | disposition |
|---|---|---|---|---|
| `river_ford` | **yes** — `resources: {herb_patch: 3}` | `river_crossing.yaml` (composed by `highland_traverse`, `quest_dense_frontier`) | `herb_patch` | (a) tag-gap |
| `deep_forest` | **no** — module's flat `resources:` dict (`healing_flower_patch:5, spirit_wisp:2`) placed entirely in its first-declared region, `sacred_grove` (same compiler quirk as `wolf_den`) | `forest_warden_grove.yaml` | — | (c) zero-content, extends existing accepted-gap disposition |
| `survivor_outpost` | **no** — module declares no `resources:` block at all | `survivor_camp_shelter.yaml` | — | (c) zero-content, extends existing accepted-gap disposition |

**`river_ford` evidentiary strength**: `river_crossing.yaml` declares `biomes: ["near_forest"]` —
a biome `herb_patch`'s `source_region_tags` already fully trusted — and its own description
states "Freshwater herb growth lines the banks along the ford," direct self-evident authoring
intent. This matches (and arguably exceeds) the evidentiary bar the original audit used to
justify its own 4-of-5 fixes (`preferred_biomes` self-evidence).

**`deep_forest`/`survivor_outpost`**: both are the exact same root-cause shape the original audit
already reviewed and accepted for `bandit_road`/`goblin_camp`/`wolf_den` (§2.29,
`docs/guidelines/intentional_divergences.md`) — extending an already-human-reviewed disposition
class to newly-discovered same-shape cases, not inventing new policy. Per CLAUDE.md's "Do not ask
questions already answered by repo patterns" rule, this did not require a fresh human decision.

## Step 4: practical impact — does this change GuildAction's scarcity output in practice?

Confirmed directly (not assumed): computed `GuildAction.visit()`'s scarcity formula manually for
an entity in `river_ford` standing near a `herb_patch` node at 2/10 remaining charges. Before this
fix: `scarcity = 0.0` (no `ratios` entries, since `river_ford` wasn't in `herb_patch`'s
`source_region_tags` — falsely "fully abundant"). After this fix: `scarcity = 0.8` (correctly
reflects the low charge ratio). This directly feeds `QuestPressureProfile.scarcity`, which weights
`QuestGenerator`'s GATHER-template selection (`PRESSURE_AFFINITY[QuestKind.GATHER] = "scarcity"`)
— a real, previously-silent misrepresentation now corrected.

Also confirmed: `GuildNeedScorer` (the scorer that makes `GuildAction.visit()` reachable) has no
role gate at all — unlike `AdventureDecisionPhase` (hero-only), any entity kind can trigger a
guild visit once `ENABLE_GUILD_QUEST_GENERATION=ON`. This means the original audit's hero-only
regression test (`test_no_hero_role_entity_spawns_in_an_uncovered_region_corpus_wide`) has a
real, now-relevant scope gap: it would never catch a non-hero entity spawning in an unresolved
region. Added a new corpus-wide test checking ALL roles
(`test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide`) to close this.

## Confirmed via re-running both new tests + the full existing suite

`tests/integration/content/test_resource_region_coverage_corpus.py`'s new all-roles test passes
against the current corpus, confirming every region any entity (any role) spawns in now has an
explicit disposition — either real coverage or a reviewed accepted-gap entry. No unresolved
regions remain, as of this ticket's fix.
