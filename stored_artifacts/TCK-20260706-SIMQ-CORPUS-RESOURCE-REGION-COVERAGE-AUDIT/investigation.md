---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT
artifact_type: investigation
tags: [simulation-quality, world, resource-registry, corpus]
---

# Investigation — TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT

## Current Behavior

### 1. Root mechanism (unchanged from parent ticket, re-verified live)

`ResourceOpportunityProvider.get_opportunities()` (`src/world/providers/resources.py:69`) gates
purely on:

```python
if current_region in res_def.source_region_tags:
```

`res_def` comes from `ResourceRegistry.get(node.kind)` (`src/world/providers/resources.py:65`) — a
lookup keyed **only by resource kind**, never by node instance or placement. `ResourceNodeState`
(`src/core/state.py:905-918`) has no region field — only `id`, `kind`, `position`, charges, etc.
`source_region_tags` per kind is computed once at bootstrap by
`CatalogToResourceRegistryAdapter.adapt()` (`src/core/registries.py:397-501`), precedence:
1. `res.metadata["source_region_tags"]` if present (explicit additive override — the mechanism
   `stone_outcrop`, `wood_node`/`herb_patch` (hometown fix), and `iron_vein`/`frost_shard_cluster`
   (mountain_pass_zone fix) already use).
2. Else `res.metadata["preferred_biomes"]` (note: **not** the top-level `preferred_biomes` field —
   `ResourceDefinition.preferred_biomes` at `src/content/schema.py:241` is a sibling Pydantic field,
   not nested under `metadata`, and `extra="forbid"` on `CatalogBaseDefinition` means it is never
   silently promoted — branch 2 only fires if a YAML author explicitly nests it under `metadata:`).
3. Else a hardcoded `legacy_id` keyword heuristic covering exactly 5 kinds
   (`node_wood`→`near_forest`, `node_herb`→`(near_forest, moon_cave)`, `node_iron`→`old_mine`,
   `node_resin`→`moon_cave`, `node_flower`→`near_forest`); everything else (`crystal_outcrop`,
   `silver_vein`, `venom_nest`, `spirit_wisp`, `ember_core_cluster`) resolves to `()`.

### 2. Live-reverified corpus audit (AC item 1) — corpus has GROWN since the parent table was written

The parent investigation's table covered 10 worlds (+ `resource_dense_basin` added later = 11). The
corpus now has **17** worlds with `resolved/world.resolved.yaml` — 6 new worlds were authored after
the parent audit: `crowded_frontier`, `frontier_marches`, `hero_guild_routing`,
`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`. This ticket's AC1 requires
re-verifying "the table above live," and the live-verified table below supersedes it — it is not
merely a re-confirmation, it is a materially larger corpus.

Live-ran `CatalogRepository("data/content").load_all()` → `CatalogToResourceRegistryAdapter.adapt()`
(current, unmodified) to compute the real global covered-tag set:
`{frontier_village, hometown, moon_cave, mountain_pass_zone, near_forest, old_mine}`. Then parsed
every `data/worlds/*/resolved/world.resolved.yaml`'s `entities[].spawn_region` /
`entities[].role` (note: population entries — not `identity`/`navigation` nested fields; see Gaps
below) against that set:

| world | uncovered spawn regions (all roles) | uncovered (hero-role) |
|---|---|---|
| crowded_frontier | bandit_road, goblin_camp, orc_stronghold | none |
| dungeon_crawl | bandit_road, goblin_camp, haunted_battlefield | (no heroes) |
| frontier_extended | bandit_road, goblin_camp, haunted_battlefield, orc_stronghold, sacred_grove, wolf_den | (no heroes) |
| frontier_living_world | bandit_road, goblin_camp, haunted_battlefield, wolf_den | (no heroes) |
| frontier_marches | bandit_road, goblin_camp, haunted_battlefield, orc_stronghold, swamp_border_territory, wolf_den | none |
| generated_frontier_3_42 | bandit_road, goblin_camp, orc_stronghold | (no heroes) |
| hero_guild_routing | goblin_camp, haunted_battlefield | none |
| highland_traverse | wolf_den | (no heroes) |
| resource_dense_basin | orc_stronghold | (no heroes) |
| sandbox_world | wolf_den | (no heroes) |
| simq_routing_test | goblin_camp | none |
| swamp_border_world | swamp_border_territory, wolf_den | (no heroes) |
| unit_faction_tension | wolf_den | (no heroes) |
| unit_information_source | (none) | none |
| unit_selfmodel_pilot | (none) | none |
| urban_political | bandit_road, trading_hometown | none |
| wilderness_survival | haunted_battlefield, wolf_den | (no heroes) |

**Key correction vs. the parent table: `hometown` no longer appears anywhere.** This confirms
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s fix (adding `hometown` to
`wood_node`/`herb_patch`'s `source_region_tags`) landed and is corpus-wide effective, including for
all 6 new worlds. Every hero-role entity in the corpus (7 worlds have hero-role population:
`crowded_frontier`, `frontier_marches`, `hero_guild_routing`, `simq_routing_test`,
`unit_information_source`, `unit_selfmodel_pilot`, `urban_political`) spawns exclusively in
`hometown` — confirmed by direct enumeration — so **zero hero-role entities are affected by any
remaining gap today**. Only `simq_routing_test` and `hero_guild_routing` run with
`ENABLE_ADVENTURE_ROUTING: "ON"` (`config/simulation_quality/profiles/*.yaml`); both are fully
covered.

Distinct uncovered regions across the corpus, deduplicated: `bandit_road`, `goblin_camp`,
`haunted_battlefield`, `orc_stronghold`, `sacred_grove`, `swamp_border_territory`, `wolf_den`,
`trading_hometown`.

### 3. Per-region disposition trace (whether a resource node is physically placed there or not)

Traced every `data/content/world_modules/*.yaml`'s `resources:` (flat kind→count, placed in the
module's first-declared region) and `resource_recipes:` (explicit `region:` field) against the
resolved worlds' actual `resources[].region` output:

| region | node(s) physically placed there? | placing module | kind(s) | tag-gap class |
|---|---|---|---|---|
| `orc_stronghold` | **yes** | `orc_clan_territory` | `iron_vein`, `wood_node` | (a) tag-gap |
| `sacred_grove` | **yes** | `forest_warden_grove` | `healing_flower_patch`, `spirit_wisp` | (a) tag-gap |
| `swamp_border_territory` | **yes** | `sunken_swamp_border` | `wood_node`, `herb_patch` | (a) tag-gap |
| `haunted_battlefield` | **yes, in worlds using `undead_battlefield`** (`frontier_extended`, `wilderness_survival`) — **no** in worlds using only `ruins_mystery_quest` (`dungeon_crawl`, `hero_guild_routing`, `frontier_marches`) | `undead_battlefield` | `spirit_wisp` | (a) tag-gap where placed; (c) no-content where not |
| `trading_hometown` | **yes** | `trading_company_hub` (namespace `trading`, region-id-prefixing confirmed at `src/worldassembly/resolver.py:335`: `prefix = f"{ref.namespace}_"` remaps module region id `hometown`→`trading_hometown`) | `iron_vein` | (a) tag-gap |
| `bandit_road` | **no** — neither `scalable_bandit_camp.yaml` nor `bandit_road_trade_pressure.yaml` declares any `resources:`/`resource_recipes:` | — | — | (c) no-content, candidate intentional-gap |
| `goblin_camp` | **no** — `goblin_camp_conflict.yaml` declares no `resources:`/`resource_recipes:` | — | — | (c) no-content, candidate intentional-gap |
| `wolf_den` | **no** — `wolf_den_near_forest.yaml` declares `resources: {wood_node:8, herb_patch:6, healing_flower_patch:3}` but its **first-declared region is `near_forest`**, and the compiler places the module's flat `resources:` dict entirely in that first region (confirmed live: `wolf_den_near_forest__wood_node_0` etc. all resolve `region: near_forest` in every world that uses this module — `sandbox_world`, `wilderness_survival` checked directly) — `wolf_den` itself receives **zero** resource nodes from any module, corpus-wide | — | — | (c) no-content, candidate intentional-gap |

**Strong evidence for 4 of the 5 tag-gap regions (`orc_stronghold` is the exception):** the affected
resource kind's own top-level `preferred_biomes` field (a sibling of `metadata`, authored
independently) already names the placing module's `biomes:` value:
- `spirit_wisp`: `preferred_biomes: ["sacred_grove", "haunted_battlefield"]` — **both** of its two
  gap regions are literally named in its own catalog entry (`data/content/world/resources.yaml:91-97`)
  — yet it has no `metadata.source_region_tags` override and no `legacy_id` heuristic branch, so it
  resolves to `()` today (confirmed live). This is the clearest authoring-intent-vs-gating mismatch
  found in this audit.
- `healing_flower_patch`: `preferred_biomes: ["near_forest", "sacred_grove"]`
  (`resources.yaml:46-52`) — names `sacred_grove` directly, but again no `metadata` override exists,
  so it falls to the `node_flower`→`("near_forest",)`-only heuristic branch, silently dropping
  `sacred_grove`.
- `herb_patch`: `preferred_biomes: ["near_forest", "sunken_swamp"]` (`resources.yaml:35-43`) — names
  `sunken_swamp`, which matches `sunken_swamp_border.yaml`'s `biomes: ["sunken_swamp"]` exactly (a
  **biome** name, not the module's actual **region id** `swamp_border_territory` — the two are
  distinct fields, biome≠region-id, confirmed by reading the module file directly). `herb_patch`
  already has an explicit `metadata.source_region_tags` override (`["near_forest", "moon_cave",
  "hometown"]`, branch 1), so branch 2 (`preferred_biomes`) never even gets consulted for it — the
  mismatch is structural, not just missing data.
- `orc_stronghold`: **no** matching evidence. Neither `wood_node`'s (`["frontier_village",
  "near_forest"]`) nor `iron_vein`'s (`["old_mine"]`) `preferred_biomes` mentions `orc_stronghold` or
  `orc_clan_territory.yaml`'s biome (`orc_territory`). This region's coverage gap is genuinely
  underspecified — no self-evident authoring intent exists either way, unlike the other three.
- `trading_hometown`: `iron_vein`'s `preferred_biomes` (`["old_mine"]`) does not mention hometown/
  trading either; however, `trading_company_hub.yaml`'s explicit `resource_recipes: [{resource_type:
  iron_vein, region: "hometown"}]` is direct compile-time placement evidence, and this world (`urban_
  political`) was already the subject of `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`
  for its plain-`hometown` half — this ticket's Out of Scope explicitly excludes that ticket's
  `hometown` rows but `trading_hometown` (the namespaced variant) is a **distinct** region id not
  covered by that prior fix, and is in-scope here.

### 4. Non-hero opportunity-consumer trace (AC item 2)

Searched all callers of `ResourceOpportunityProvider.get_opportunities()`
(`grep -rn "get_opportunities" src/`):
1. `src/domains/adventure/phase.py:100` (`AdventureDecisionPhase.apply()`) — hero-role only
   (`e.identity.role == EntityRole.HERO`, `phase.py:75`). Already covered by the parent ticket.
2. `src/testing/scenario_runner.py:93` — dev/test scenario tooling under `src/testing/`, not part of
   the authoritative kernel pipeline; always seeds its own fixed `node_wood`/synthetic state, not
   corpus-world-driven.

No other pipeline phase, tactical AI, economic AI, or quest system calls `get_opportunities()`
directly. However, `src/town/guild.py`'s `GuildAction.visit()` (lines 49-72) **independently
reimplements the same `region_id in res_def.source_region_tags` matching** (explicitly documented in
its own comment as mirroring `resources.py:60-66`) to compute a `scarcity` signal feeding
`QuestPressureProfile`/`QuestGenerator.generate_quests()` — this is role-agnostic (`GuildAction.visit
(entity, state)` takes no role filter). This is parity-ledger-tracked at **STRAT-244**
(`docs/parity_ledger/strategic_cognition.yaml`, `verified`, P1,
`v2_evidence` cites `src/town/guild.py::GuildAction.visit()` directly).

**But `GuildAction.visit()` is not currently wired into any dispatched pipeline phase** — confirmed by
`grep -rln "GuildAction" .` returning only `src/town/guild.py` (definition), `src/quests/generator.py`
(a docstring mention), and `tests/unit/world/test_guild_pipeline.py` (direct unit-test invocation with
a hardcoded `hero`-kind entity). No `ActionIntent` kind, dispatcher registry, or pipeline phase calls
`GuildAction.visit()` anywhere in `src/engine/` or `src/domains/`. **Conclusion: today, in live
simulation runs, no non-hero system is affected by these region/tag gaps** — the only two live
callers of the gating check are hero-only (`AdventureDecisionPhase`) or dev tooling
(`scenario_runner.py`). `GuildAction`'s scarcity computation is a **latent** consumer: if/when it is
ever wired into a dispatched action, it would silently report `scarcity = 0.0` (not "unknown data" —
literally treated as "fully abundant", `src/town/guild.py:72`: `scarcity = (1.0 - sum(ratios)/len
(ratios)) if ratios else 0.0`) for any entity in an uncovered region, feeding
`QuestGenerator`'s pressure-weighted template selection incorrectly. Worth flagging in the doc
disposition as a secondary, currently-dormant risk of the same root mechanism — not something this
ticket needs to fix (`GuildAction` wiring is out of scope; no dispatcher change is authorized).

## Mechanics / Engine Constraints

- No `docs/mechanics/` chapter formalizes `source_region_tags`/opportunity gating as a law — this is
  content-catalog/engine-adapter implementation detail, not a Mechanics Bible formula. Confirmed by
  grep across `docs/mechanics/03_economic_laws.md` and `docs/mechanics/adventure_routing_contract.md`
  (only the latter references `gather_resource` at all, purely as a route-family enum entry, `line
  50/88/206` — no gating-mechanism language).
- `docs/mechanics/adventure_routing_contract.md` defines the `defer_with_reason` fallback contract
  this gap class interacts with for hero-role entities — already fully resolved corpus-wide per §2
  above, out of this ticket's remaining live-risk scope.
- Per the Authoritative Mechanics Rule (CLAUDE.md), any option (a)/(b) content fix here is a
  catalog/content change, not a code or mechanics-law change — consistent with how `stone_outcrop`
  and the `hometown`/`mountain_pass_zone` precedents were classified ("Bug Fix" divergence class).

## Parity Ledger Overlap

- **TOWN-188** (`docs/parity_ledger/town_resource.yaml`, `verified`, P1,
  `test_path: tests/unit/core/test_registry_bridge.py; tests/unit/strategic/test_opportunities.py`) —
  documents the `hometown` fix. Not modified by this ticket (out of scope, already closed).
- **TOWN-183** (`docs/parity_ledger/town_resource.yaml:2029`, `verified`, P1) — `urban_political`
  node-count assertion, scoped to count not gating coverage. Unaffected by any option (a) fix here
  (additive tag change doesn't change node counts).
- **STRAT-225** (`docs/parity_ledger/strategic_cognition.yaml`, `verified`, P0,
  `test_path: tests/perf/test_phase3_adventure_decision_budget.py::test_phase3_adventure_decision_perf_budget`)
  — documents `AdventureDecisionPhase` calling `get_opportunities()`. **P0** — if any fix touches
  `resources.py` or `registries.py` (it should not; the recommended fix is catalog-file-only), this
  entry's test must still pass.
  **No new entry needed** unless registries.py/resources.py source is touched (recommended path
  avoids this).
- **STRAT-244** (`docs/parity_ledger/strategic_cognition.yaml`, `verified`, P1,
  `test_path: tests/unit/quest/test_quest_generation.py::test_quest_generation_favors_hunt_under_high_trauma;
  ...::test_quest_generation_favors_gather_under_high_scarcity`) — documents `GuildAction.visit()`'s
  scarcity computation, the latent non-hero consumer identified in §4. Not modified by this ticket
  unless the disposition doc explicitly calls out the dormant `GuildAction` risk (recommended: yes,
  as a note, no test change needed since `GuildAction` isn't live-dispatched).
- **No entry currently exists** for `orc_stronghold`/`sacred_grove`/`swamp_border_territory`/
  `haunted_battlefield`/`trading_hometown`/`bandit_road`/`goblin_camp`/`wolf_den` coverage
  specifically — if Plan/Implementation applies option (a) fixes, new `town_resource.yaml` entries
  (or an addendum to TOWN-188) are required, following the `hometown` precedent's format exactly.
  None of these are P0 (this whole area is P1/P2 by precedent), so no `test_path` is a hard blocker,
  but each new entry should still cite a passing regression test per repo convention.

## Prior Work

- `stored_artifacts/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP/investigation.md` §3/§4 —
  established the `metadata.source_region_tags` additive-override fix pattern and performed the first
  version of this corpus audit (10+1 worlds). §3's rejected option (c) is this ticket's architecture
  question (see Risks below for the recommendation).
- `stored_artifacts/TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP/investigation.md` —
  confirms `urban_political`'s plain-`hometown` row is closed and permanently dormant (AGENCY=C by
  design, `ENABLE_ADVENTURE_ROUTING=OFF`). Does **not** cover `trading_hometown` (a distinct
  namespaced region id) — that row is genuinely still open and in this ticket's scope.
- `tickets/done/TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP.md` + `docs/guidelines/
  intentional_divergences.md` §2.26 — established the `metadata.source_region_tags` override
  mechanism originally, for `stone_outcrop`/`frontier_village`.
- `docs/guidelines/intentional_divergences.md` §2.27 "Hometown Resource-Opportunity Gating Fix" — the
  exact entry-format precedent to follow for this ticket's option (a) fixes and option (c) dispositions.
- `docs/simulation_quality/eval_matrix_results.md` (lines ~993-1012, ~1076-1094) — already documents
  the `mountain_pass_zone` gap (since fixed, confirmed live — `iron_vein`/`frost_shard_cluster` both
  now carry `mountain_pass_zone` in `metadata.source_region_tags`) and the `orc_stronghold` gap
  (still open) as "recommended follow-up" — this ticket is that follow-up.
- `tests/unit/strategic/test_opportunities.py` — already contains
  `test_resource_opportunities_orc_stronghold_tag_gap` (asserts **zero** opportunities today,
  deliberately, with an explicit docstring: "If this assertion starts failing, the tag gap has been
  closed and this test should be rewritten to assert coverage") and
  `test_resource_opportunities_mountain_pass_zone_iron_vein`/`_frost_shard_cluster` (the already-fixed
  positive-coverage pair, showing the exact test-rewrite pattern to follow when `orc_stronghold` is
  fixed).

## Risks and Open Questions

- **OQ-1 (blocks Scope item 2's per-region "hazard-region intentionality" decision, per the ticket's
  own Assumptions section) — is `bandit_road`/`goblin_camp`/`wolf_den` (0 nodes placed, no
  `preferred_biomes` evidence either way) an intentional design choice ("hazard/combat regions don't
  forage") or an authoring oversight?** This investigation found no code or doc evidence settling this
  either way — no resource kind's `preferred_biomes` names any of these three regions, unlike the 4
  tag-gap regions where `preferred_biomes` provides a strong intent signal. This is a genuine open
  question the Plan phase (or a human) must resolve per-region, not assume; recommend defaulting to
  option (c) (explicit accepted-gap documentation) for these three unless someone identifies specific
  gameplay intent to author new content.
- **OQ-2 — `orc_stronghold`'s tag-gap fix (add `orc_stronghold` to `wood_node` and/or `iron_vein`'s
  `source_region_tags`) has no `preferred_biomes` self-evidence**, unlike the other 3 tag-gap regions.
  It is still recommended as option (a) because a resource node **is** physically placed there
  (matching the `hometown` precedent's root-cause shape exactly), but Plan should note this is a
  slightly weaker evidentiary case than `sacred_grove`/`swamp_border_territory`/`haunted_battlefield`.
- **Region-aware `ResourceNodeState` architecture recommendation (Scope item 2's required
  adopt/defer/reject call):** **Recommend DEFER**, not adopt-now, not reject. Rationale: the pattern
  has now recurred in 5+ distinct regions across the growing corpus (evidence this ticket adds to the
  parent's finding), which argues the bug class is real and structural, not a one-off — but per the
  parent investigation's §3(c) analysis, implementing it requires a durable-state schema change to
  `ResourceNodeState` (a frozen, `slots=True` dataclass at `src/core/state.py:904-918`) plus touching
  the compiler, `ResourceOpportunityProvider`, `GuildAction.visit()`'s parallel scarcity computation,
  and every test constructing `ResourceNodeState`/mocking `ResourceRegistry` (dozens of call sites
  across `tests/unit/strategic/`, `tests/unit/core/`, `tests/integration/`) — the additive
  `metadata.source_region_tags` fix continues to fully resolve every case found so far (4 of 5
  tag-gaps have strong `preferred_biomes` self-evidence) with zero blast radius. Reject is too strong
  given the recurrence rate; adopt-now is unjustified given the additive fix's continued sufficiency.
  Not reject outright — flag for re-evaluation if a 6th+ occurrence surfaces where the additive fix
  genuinely cannot express the needed distinction (e.g. two worlds wanting the *same* kind covered
  in one region but not another — not yet observed).
- **This ticket's Related Docs cites `docs/guidelines/intentional_divergences.md`** (matches the
  actual file); CLAUDE.md's Authoritative Mechanics Rule section instead names
  `docs/guidelines/v2_intentional_divergences.md` — that file **does not exist**
  (`find docs -iname "*intentional_diverg*"` returns only the non-`v2_`-prefixed file). This is a
  pre-existing naming inconsistency in CLAUDE.md, not something introduced by this ticket; flagging so
  Plan does not get blocked trying to locate a `v2_`-prefixed file that isn't there. Use the actual
  file, `docs/guidelines/intentional_divergences.md` (matches this ticket's own Related Docs entry and
  every prior precedent's citation, §2.26/§2.27).

## Anti-Drift Hazards

- **Any `source_region_tags` fix must be additive** (`["existing", ..., "new_region"]`), never a
  replacement — a bare `["orc_stronghold"]` on `wood_node` would silently break every world relying on
  `wood_node`'s `near_forest`/`hometown` coverage (`frontier_extended`, `frontier_living_world`,
  `generated_frontier_3_42`, `sandbox_world`, `swamp_border_world`, `wilderness_survival`,
  `crowded_frontier`, `frontier_marches`, and more). This exact hazard is already called out in the
  `hometown` precedent (§3 of that investigation) — same risk, same mitigation.
- **Do not touch `ResourceNodeState`, the compiler, or `ResourceOpportunityProvider`'s gating logic**
  — Scope explicitly excludes implementing the region-aware architecture change; only
  `data/content/world/resources.yaml` (`metadata.source_region_tags`) should change for any option
  (a) fix, mirroring every prior precedent (`stone_outcrop`, `hometown`, `mountain_pass_zone`).
- **`test_resource_opportunities_orc_stronghold_tag_gap`
  (`tests/unit/strategic/test_opportunities.py:232`) currently asserts ZERO opportunities on
  purpose.** If `orc_stronghold` is fixed via option (a), this test MUST be rewritten to assert
  positive coverage (its own docstring says so explicitly) — leaving it as-is after a fix would be a
  false-negative regression test masking the fix, not confirming it. Same applies to any other
  region-specific "expected zero" test if that region's disposition changes to option (a)/(b).
- **Do not conflate `trading_hometown` with the already-closed plain-`hometown` row** — they are
  distinct region ids (confirmed via `src/worldassembly/resolver.py:335`'s namespace-prefixing), and
  `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`'s Out-of-Scope only covers the
  hero-role/plain-`hometown` finding, not this namespaced variant.
- **`GuildAction.visit()` is unwired dead code today** — do not "fix" its scarcity computation as part
  of this ticket's option (a)/(b) work; it isn't reachable from any live pipeline path, so a fix there
  would be scope creep with no observable effect and risks conflicting with a future ticket that
  formally wires it in.
- **`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`, `crowded_frontier`,
  `frontier_marches`, `hero_guild_routing`** were not part of the parent investigation's audited
  corpus at all — any Plan/Implementation step that re-derives "the 10/11-world list" from the parent
  doc instead of live-globbing `data/worlds/*/resolved/world.resolved.yaml` will silently miss 6
  worlds and under-scope the fix/decision set.
- **`preferred_biomes` is not consulted unless nested under `metadata:`** — a naive fix attempt that
  edits `resources.yaml`'s top-level `preferred_biomes` list (rather than adding/extending
  `metadata.source_region_tags`) will have **zero effect** on gating behavior; this is the exact
  structural trap the herb_patch/healing_flower_patch/spirit_wisp evidence above depends on
  recognizing.

## Gaps Found

- All files listed in the ticket's "Related Code Areas" exist and were read directly; no gaps there.
- The ticket's own uncovered-region table is **stale** relative to the current corpus (6 new worlds
  added since it was written) — not an error in the ticket, but Scope item 1 ("re-verify... live")
  anticipated exactly this kind of drift; §2 above is the corrected table.
