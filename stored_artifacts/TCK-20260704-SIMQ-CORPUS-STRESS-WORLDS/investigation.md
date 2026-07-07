---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS
artifact_type: investigation
tags: [simulation-quality, world, corpus, calibration]
---

# Investigation — TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS

## Current Behavior

### Corpus scale/composition today (ground truth, `docs/simulation_quality/eval_matrix_results.md`
"Corpus World-Scale Summary" table + direct `world_compile_report.json` reads)

| World | Entities | Regions | Resource Nodes | Distinct Populated Factions |
|---|---|---|---|---|
| wilderness_survival | 11 | 4 | 4 | 2 |
| sandbox_world | 18 | 3 | 5 | 3 |
| highland_traverse | 18 | 5 | 3 | 3 |
| urban_political | 30 | 3 | 3 | 4 |
| dungeon_crawl | 32 | 4 | 3 | 4 |
| swamp_border_world | 26 | 4 | 7 | 4 |
| simq_routing_test | 30 | 3 | 5 | 5 |
| frontier_living_world | 46 | 7 | 9 | 6 |
| generated_frontier_3_42 | 44 | 6 | 9 | 7 |
| frontier_extended | 56 | 10 | 13 | 9 |

Faction count and world size move together monotonically (correlation the ticket's own Request
Summary calls out); resource-node density is 0.6–1.75 nodes/region with no outlier in either
direction; no world combines a large `distinct_populated_factions` count with a small
entity/region footprint. This is exactly what `docs/simulation_quality/corpus_tier_taxonomy.md`'s
"Named scale-diversity gaps" section documents (gaps 1–3 quoted verbatim in that doc, all three
in this ticket's scope).

### `WorldCompiler.compile()` — `distinct_populated_factions` metric

`src/worldbuilding/compiler.py:521-524`:
```python
"distinct_populated_factions": len({
    fid for e in entities.values()
    if (fid := e.properties.get("faction_id"))
}),
```
Counts unique `faction_id` values actually assigned to compiled entities — not the static 16-entry
`AuthoritativeState.factions` catalog. This is the numeric verification mechanism Scope item 3
requires for world (a).

### Module catalog — faction-populating capacity (direct read of every file in
`data/content/world_modules/*.yaml`, cross-referenced against `data/content/entities/populations.yaml`,
`data/content/entities/entity_archetypes.yaml`'s `faction` field, and `data/content/social/factions.yaml`)

A module's `factions:` list is descriptive; only factions that actually receive spawned population
(via `populations:` [referencing `populations.yaml` recipes] or inline `population_recipes:`) count
toward `distinct_populated_factions`. Per-module populated-faction/region/entity accounting
(entity counts for `scalable_bandit_camp`/`trading_company_hub` are parametrized and shown as their
default):

| Module | New regions | Populated factions | ~Entities | Resource nodes |
|---|---|---|---|---|
| `frontier_village_core` | hometown (1) | town_council, merchant_league | 13 | 13 (wood_node 8, herb_patch 5) |
| `bandit_road_trade_pressure` (requires `frontier_village_core`) | bandit_road (1) | bandit_company, +reinforces merchant_league/town_council | 8 | 0 |
| `goblin_camp_conflict` (requires `frontier_village_core`) | goblin_camp (1) | goblin_warband | 9 | 0 |
| `wolf_den_near_forest` | near_forest, wolf_den (2) | wild_beast_pack | 5 | 17 |
| `forest_warden_grove` (requires `frontier_village_core`+`wolf_den_near_forest`) | sacred_grove, deep_forest (2) | forest_wardens, spirit_court | 5 | 7 |
| `orc_clan_territory` | orc_stronghold (1) | orc_clan | 5 | 10 |
| `undead_battlefield` / `ruins_mystery_quest` (same region id `haunted_battlefield`, different bounds — pick one, not both) | haunted_battlefield (1) | undead_remnants | 6 | 2 / 0 |
| `moon_cult_ruins` (requires `frontier_village_core`) | moon_cave (1) | arcane_circle (NOT `moon_cult` — declared but never populated) | 4 | 7 |
| `sunken_swamp_border` | swamp_border_territory (1) | swamp_tribe | 8 | 7 |
| `old_mine_resource_loop` | old_mine (1) | wild_beast_pack (NOT `dwarven_mine_clan` — declared but never populated) | 5 | 14 |
| `hero_adventurers` | **0 new** (spawns into `hometown`) | hero_guild | 3 | 0 |
| `nomadic_herd` | near_forest, wolf_den (2, id-collides with `wolf_den_near_forest` if both used) | wild_beast_pack | 5 | 0 |
| `mountain_pass`, `river_crossing`, `settled_quarter`, `scalable_bandit_camp`(0 population_recipes evaluated to non-fractional in this read), `trading_company_hub`, `survivor_camp_shelter`, `forest_deep_ecology` | 1 each (or 0 for `forest_deep_ecology`) | none populated by these modules alone in isolation from the above | varies | 6 / 3 / 0 / varies / 6 / 0 / 0 |

Catalog-wide, only **12 of 16** factions in `data/content/social/factions.yaml` are ever populated by
any current module combination: `town_council`, `merchant_league`, `wild_beast_pack`,
`goblin_warband`, `bandit_company`, `forest_wardens`, `spirit_court`, `orc_clan`, `undead_remnants`,
`arcane_circle`, `swamp_tribe`, `hero_guild`. `moon_cult`, `dwarven_mine_clan`, `dragon_cult`,
`neutral` have zero module path to population today (`dragon_cult_elite_cell` exists in
`populations.yaml` but no module in `data/content/world_modules/` references it).

**Module composition mechanics that matter for authoring (from a targeted `Explore` sub-agent read
of `src/worldassembly/resolver.py` and `src/worldmodules/utils.py`):**
- `requires:` on a module is used **only** for topological load ordering among modules already
  selected for a world (`src/worldmodules/utils.py:16-21`) — it is never enforced as "this module
  cannot be used unless its `requires` targets are also present." A narrower check
  (`resolver.py:844-861`) validates only that a population recipe's *preferred spawn region*
  resolves among the composed modules' own regions, raising `ResolverError` if not.
- Region-id collisions across composed modules **raise `ValueError`** at merge time
  (`resolver.py:345-349`, same pattern for populations/resources/buildings) — they do not silently
  overwrite or merge. Concretely: `bandit_road_trade_pressure.yaml` and `scalable_bandit_camp.yaml`
  both declare region id `"bandit_road"` (different `grid_bounds`); `wolf_den_near_forest.yaml` and
  `nomadic_herd.yaml` both declare `"near_forest"`/`"wolf_den"`. **These pairs cannot be composed
  together in the same world.**
- No minimum/maximum region-count or entity-count validation exists anywhere in
  `src/worldassembly/` or `src/worldbuilding/` — any region/entity count a valid composition
  produces is accepted.

### Resource-node density outliers (for gap (b))

`frontier_village_core` (13 nodes/1 region) and `old_mine_resource_loop` (14 nodes/1 region,
`hazard_kind: NATURAL_TERRAIN` already declared, native faction `wild_beast_pack` already immune)
are both far denser than any current world's per-region average (max today: `swamp_border_world`
1.75/region). Composing `frontier_village_core` + `old_mine_resource_loop` + `orc_clan_territory`
(10 nodes/1 region, `hazard_kind` already declared, native faction already immune) yields 3 regions
/ ~37 resource nodes (~12.3/region) at a footprint smaller than any currently-anchored world except
`wilderness_survival`/`sandbox_world`/`highland_traverse` — a strong, low-authoring-risk candidate
for the **resource-saturated/small-map** direction of gap (b), achievable from existing catalog
content with modules that already carry correct `hazard_kind`/`hazard_immunities` pairings (no new
hazard-content-fix work needed, unlike several modules `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` had
to patch). The **sparse-resources/large-map** direction is also achievable (many modules —
`goblin_camp_conflict`, `bandit_road_trade_pressure`, `ruins_mystery_quest`, `scalable_bandit_camp`,
`settled_quarter`, `survivor_camp_shelter`, `forest_deep_ecology` — declare zero resource nodes) but
would require ~7-8 modules to reach a `frontier_extended`-comparable region count, most of which
already have or need `hazard_kind` declared (recompile-drift risk, per
`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s precedent of an 8-of-10-keys drift from exactly this
class of change) — meaningfully higher authoring/verification cost for the same gap. **Recommend
resource-saturated/small-map** as the lower-risk, catalog-supported choice; this is offered as
investigation evidence for the planner's decision (per UQ-2's explicit deferral), not a mandate.

### "Many-factions/small-map" world (gap a) feasibility

`hero_adventurers` is the only module that adds a populated faction (`hero_guild`) with **zero**
new regions (spawns into an existing `hometown`). Every other populated faction costs at least one
new region. Reaching 6-9 distinct populated factions therefore requires at minimum ~5-8 new
regions on top of `hometown` (since no other zero-region-cost faction module exists), and each
region-owning module contributes 5-13 entities of its own. A concrete low-region composition:
`frontier_village_core` (hometown; town_council+merchant_league, 13e) + `hero_adventurers` (0
regions; +hero_guild, 3e) + `bandit_road_trade_pressure` (bandit_road; +bandit_company, 8e) +
`goblin_camp_conflict` (goblin_camp; +goblin_warband, 9e) + `orc_clan_territory` (orc_stronghold;
+orc_clan, 5e) reaches **6 distinct populated factions across 4 regions, ~38 entities** — 4 regions
matches `wilderness_survival`'s region count, but ~38 entities is closer to `dungeon_crawl`/
`highland_traverse` scale than `wilderness_survival`(11)/`sandbox_world`(18). **The ticket's own
footprint framing ("comparable in entity/region footprint to... `wilderness_survival` 11/4,
`sandbox_world` 18/3") conflates region-count smallness and entity-count smallness — no catalog
combination found gets 6+ distinct populated factions under ~20 entities**, because faction-bearing
population recipes in `populations.yaml` are all sized 5-13 (no recipe under 3 entities except
`hero_adventurers`' individual hero recipes at 1 entity each). This tension is flagged in Risks
below rather than resolved unilaterally.

## Mechanics / Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md` — declarative topology and world-composition
  rules; module merge semantics (region/faction/population/resource dedup-or-error) originate here
  and are enforced by `WorldAssemblyResolver.assemble()` as read above.
- `docs/mechanics/05_world_evolution.md` §3 ("Native Endurance to a Region's Hazard Kind") — any
  region with `hazard_level > 0` must declare `hazard_kind`, or every populating faction takes
  unconditional hazard drain (the exact mechanism behind `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s
  Finding 3 population collapses). All modules identified above as stress-tier candidates already
  declare correct `hazard_kind`/`hazard_immunities` pairs (`bandit_road_trade_pressure`,
  `goblin_camp_conflict`, `orc_clan_territory`, `old_mine_resource_loop`, `wolf_den_near_forest`) —
  this is a load-bearing constraint on which modules are safe to compose without new content-fix
  work; `moon_cult_ruins` and `ruins_mystery_quest`/`undead_battlefield`'s `haunted_battlefield`
  variant have `hazard_level > 0` with mixed `hazard_kind` status (`undead_battlefield` declares
  `UNDEAD_CORRUPTION` + matching `undead_remnants` immunity; `ruins_mystery_quest`'s
  `haunted_battlefield` variant has `hazard_level: 3.5` and **no `hazard_kind`** — a genuine
  pre-existing gap if this variant is chosen over `undead_battlefield`'s).
- `docs/guidelines/design_patterns.md` "Compile-Time Pillar Activation Pattern" (Pattern 6) —
  governs how `faction_tension_overrides`/`information_source_profiles`/
  `pending_information_responses` seed FACTION/INFORMATION pillar activation; directly relevant to
  gap (c).
- `docs/guides/content_authoring.md` §7.6 — module_id must be globally unique (not a concern here,
  no new modules strictly required); the region-id-collision behavior documented above (§ Current
  Behavior) is **not** documented anywhere in this guide — a gap worth a documentation follow-up,
  not blocking for this ticket.

## Parity Ledger Overlap

- **`docs/parity_ledger/faction.yaml::FAC-012`** (status: verified, P1) — covers
  `WorldSpec.factions[].initial_tension_level` / `faction_tension_overrides` compile-time plumbing.
  Text/evidence currently only cites `urban_political`'s seeding — **not** updated by the sibling
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` ticket even though that ticket added
  `faction_tension_overrides` to 8 more worlds (inconsistent with how `INFRA-256`/`INFRA-257` in
  `infrastructure.yaml` *were* additively updated for the same work — flagged as a Prior Work
  inconsistency, not this ticket's defect to fix, but this ticket's own large-scale FACTION world
  (gap c) is the same mechanism and should decide whether to extend `FAC-012` additively too, for
  consistency).
- **`docs/parity_ledger/infrastructure.yaml::INFRA-256`** (status: verified, P1) — compile-time
  plumbing for `information_source_profiles`/`pending_information_responses`; already additively
  extended twice (`TCK-20260702-SIMQ-UPLIFT2-INFORMATION`'s original entry,
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s extension). Gap (c)'s world adds a third data
  point at a new scale and should extend this entry's text again, mirroring the existing additive
  pattern (do not rewrite existing paragraphs).
- **`docs/parity_ledger/infrastructure.yaml::INFRA-237`** and **`SIMQ-CALIBRATED-001`** — both carry
  `support_boundary` notes about `ENABLE_ADVENTURE_ROUTING`/AGENCY archetype-blocking; not directly
  in scope for this ticket (none of the 3 named gaps involve AGENCY/routing) but worth a read-only
  confirmation that none of the 3 new worlds accidentally enable `ENABLE_ADVENTURE_ROUTING` (would
  require additive extension per the `hero_guild_routing` precedent if so — out of scope here since
  the ticket doesn't ask for a routing-capable stress world).
- No parity-ledger entry exists for `distinct_populated_factions` or for resource-node density as a
  named mechanic — both are diagnostic/reporting metrics (`WorldCompiler.compile()`'s report dict),
  not durable engine behavior, so no new parity entry is expected for gaps (a)/(b) unless new
  scoring/emission logic is touched (it should not be, per this ticket's Out-of-Scope item 3).

## Prior Work

- **`stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/plan.md`** — establishes the
  compile→population-stability-test→3-seed-calibration→anchor→doc-update→parity-additive-extension
  pipeline this ticket should mirror (10-step structure), including the critical distinction between
  the generic `test_population_stability`/`POPULATION_STABILITY_WORLDS` guard (baseline, run at
  default flags) and any world-specific standalone test needed for a claim that guard cannot prove.
  For this ticket's 3 worlds, no non-default feature flag is being forced ON (unlike
  `hero_guild_routing`'s `ENABLE_ADVENTURE_ROUTING`), so the existing generic guard is likely
  sufficient — no new standalone test module is anticipated to be necessary, but the planner should
  confirm this once each world's actual profile/flags are finalized.
- **`stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/`** — establishes the
  per-world, non-copy-paste judgment-call discipline for `faction_tension_overrides`/
  `information_source_profiles` content (each world's tension pair and information subject must be
  archetype-honest, not templated) — directly applicable to gap (c)'s world. Also establishes the
  precedent of documenting "skip" cases honestly (e.g. `dungeon_crawl`/`wilderness_survival` have no
  settlement module, so INFORMATION content is a documented skip, not forced) — the many-factions
  world (gap a) and the resource-density world (gap b) are Stress tier, not End-to-end, so per
  `corpus_tier_taxonomy.md`'s own tier-purity rule they should **not** receive bespoke
  `faction_tension_overrides`/`information_source_profiles` content unless the planner deliberately
  decides one of them also incidentally exercises Pattern-6 content (permitted by the taxonomy doc's
  own "may also exercise a mechanic" carve-out, but not required).
- **`stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/`** — compile/verify/anchor workflow
  precedent (3-seed × 200t default calibration length unless a specific reason to deviate exists,
  per `hero_guild_routing`'s 500t deviation being explicitly re-justified); the hazard-kind
  recompile-drift risk class this ticket's module choices were screened against above.
- **`docs/simulation_quality/corpus_tier_taxonomy.md`** — the authoritative tier taxonomy and the
  direct source of the 3 named gaps this ticket addresses (verbatim gap text quoted in Current
  Behavior above).

## Risks and Open Questions

- **RISK (significant, needs planner decision) — gap (c)'s premise may already be partially stale.**
  Direct read of `data/worlds/frontier_extended/world.yaml` (lines 20-38) confirms it **already has**
  `faction_tension_overrides` (`orc_clan: 0.5`, `forest_wardens: 0.5`) and
  `information_source_profiles`/`pending_information_responses` seeded — added by the sibling
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` ticket, at exactly frontier_extended's scale (56
  entities/10 regions) that this ticket's Request Summary cites as having "no data point." The same
  is true of `frontier_living_world` (46e/7r). `docs/simulation_quality/corpus_tier_taxonomy.md`'s
  "Named scale-diversity gaps" section (gap 3) was **not** updated to reflect this — it still reads
  as if no large-scale world has this content, even though the same document's own "Current tier
  mapping" section (updated "as of 2026-07-07") documents the E2E-CONTENT-EXPANSION promotion. This
  is an internal doc inconsistency, not evidence the underlying facts are wrong. **This ticket's own
  Scope item 1(c) and AC still literally require authoring a NEW world with this content** (the
  Scope preamble says "author at minimum the following 3 [new worlds]"), so the concrete deliverable
  is unaffected — but the *rationale* ("the first data point... at frontier_extended's scale") is no
  longer accurate; it would be the **second and third** such data point. Recommend the planner
  explicitly acknowledge this in Implementation Notes (reframe as "an additional, stress-tier-
  justified data point at this scale, distinct from frontier_extended/frontier_living_world's
  end-to-end-tier framing") rather than silently reusing the now-inaccurate "first data point"
  language, and consider flagging the taxonomy doc's gap-3 staleness as a small follow-up doc fix
  (in scope for this ticket's own doc-update step, since it directly touches the same section).
- **OPEN QUESTION (blocks a design choice, not implementation start) — gap (a)'s footprint framing
  cannot be satisfied on both axes simultaneously with existing catalog content.** See Current
  Behavior's "many-factions/small-map feasibility" analysis: 6 distinct populated factions in 4
  regions is achievable, but only at ~38 entities (dungeon_crawl-adjacent scale), not
  `wilderness_survival`(11)/`sandbox_world`(18)-adjacent entity counts, because every
  faction-populating module (besides `hero_adventurers`) contributes 5+ entities. The planner must
  decide whether "small footprint" is judged primarily by region count (in which case the 4-region/
  ~38-entity composition above satisfies it) or by entity count (in which case reaching even 6
  factions may require authoring new, deliberately small population recipes — a materially larger
  scope than pure module reuse, and arguably in tension with UQ-1's instruction to prefer existing
  catalog content). This is a genuine design fork, not a fact to assume.
- **RISK — the `haunted_battlefield` region has two non-identical module definitions**
  (`ruins_mystery_quest.yaml` grid_bounds `[60,80,100,120]`, no `hazard_kind`; `undead_battlefield.yaml`
  grid_bounds `[120,20,160,60]`, `hazard_kind: UNDEAD_CORRUPTION`) — both populate only
  `undead_remnants` (`spirit_court` is declared but never actually populated by either). They **cannot
  be composed together** (region-id collision → `ValueError`). If a stress-tier world composition
  picks `ruins_mystery_quest` over `undead_battlefield`, it inherits a `hazard_level: 3.5` region
  with no `hazard_kind` — the exact structural gap `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` had to
  fix elsewhere. `undead_battlefield` is the pre-fixed variant and should be preferred.
- **RISK — `moon_cult` and `dwarven_mine_clan` (declared by `moon_cult_ruins`/`old_mine_resource_loop`
  respectively) are never actually populated by any current module.** If either is used in a
  composition expecting it to count toward `distinct_populated_factions`, the numeric verification
  (Scope item 3) will not reflect it — must count only the factions confirmed populated above.
- **OPEN QUESTION — `POPULATION_STABILITY_WORLDS`/`ANCHORED_WORLD_BANDS` inclusion for the 3 new
  worlds.** Per the coverage gap already tracked in `tickets/todos/TCK-20260707-CORPUS-POPULATION-
  STABILITY-COVERAGE-GAP.md` (backfilling old worlds, out of this ticket's scope), the 3 **new**
  worlds this ticket authors should be added to `POPULATION_STABILITY_WORLDS` and (since they get
  3-seed grade-anchor entries per Scope item 2) to `ANCHORED_WORLD_BANDS` and
  `EXPECTED_DISTINCT_POPULATED_FACTIONS` from the start — this is a smaller, cleaner ask than the
  backfill ticket and should not be deferred to it. Flagged for planner confirmation since it touches
  a shared test file (`tests/unit/worldassembly/test_corpus_diversity.py`) also touched by the
  coverage-gap ticket — sequencing/merge-conflict risk if both tickets land near-simultaneously.
- **Non-blocking process gap (already tracked):** the epic-scope source document
  (`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`) does not exist on
  disk — tracked by `tickets/todos/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md`. Every fact
  in this investigation attributed to "investigation.md §2"'s gap analysis has been independently
  re-derived from ground truth above (the scale-summary table, direct module reads), not assumed
  from the missing file.

## Anti-Drift Hazards

- Do not compose `bandit_road_trade_pressure` + `scalable_bandit_camp`, or
  `wolf_den_near_forest` + `nomadic_herd`, in the same world — both pairs declare colliding region
  ids and `WorldAssemblyResolver.assemble()` will raise `ValueError`.
- Do not assume `moon_cult` or `dwarven_mine_clan` count toward `distinct_populated_factions` merely
  because a module's `factions:` list names them — verify via the compiled
  `world_compile_report.json`'s `distinct_populated_factions` field (or a direct
  `entity.properties["faction_id"]` scan), not by eyeballing module YAML, per Scope item 3's own
  instruction.
- Do not add `faction_tension_overrides`/`information_source_profiles` content to the many-factions
  (gap a) or resource-density (gap b) worlds unless deliberately justified — per
  `corpus_tier_taxonomy.md`'s tier-purity rule, Stress-tier worlds' primary justification is scale,
  not archetype/Pattern-6 richness; adding such content without a stated reason is scope creep into
  End-to-end-tier territory.
- Do not silently reuse `frontier_extended`'s or `frontier_living_world`'s exact
  `faction_tension_overrides`/`information_source_profiles` values for gap (c)'s new world — the
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` precedent requires bespoke, archetype-honest
  content per world, not copy-paste (its own explicit discipline, cited by this ticket's own Related
  Tickets section).
- Do not touch `data/content/world/resources.yaml` speculatively while investigating the
  resource-density world (gap b) — `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s Step 2 precedent
  is to verify `source_region_tags` coverage for any new region combination and flag (not silently
  fix) any gap found, since it is a shared catalog file.
- Do not edit `data/content/world_compositions/{world}.yaml` for any of the 3 new worlds — that
  directory is a stale, diverged mirror per this session's own operator note; only
  `data/worlds/{world}/world.yaml` is authoritative.
- Do not touch `ANCHORED_WORLD_BANDS`/`POPULATION_STABILITY_WORLDS` entries for any of the 9
  existing non-stress worlds — only add new entries for the 3 new worlds (per this ticket's
  Out-of-Scope item 1, mirroring the AGENCY ticket's "do not touch existing worlds' entries" guard).
