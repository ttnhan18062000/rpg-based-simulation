---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH
artifact_type: investigation
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH

## Current Behavior

### EconomyScorer — event-driven, no durable-state read (Pattern 6 does NOT apply)

`src/simulation_quality/scorers/economy.py::EconomyScorer` (class at L11) listens for 10
`EVENT_TYPES` (L18-31): `resource_harvested`, `item_crafted`, `trade_executed`,
`shop_transaction`, `gold_transferred`, `resource_node_depleted`, `gold_sink_fired`,
`conservation_law_verified`, `conservation_law_violated`, `paid_info_transaction`,
`quest_reward_dispensed`. Every branch (L68-138) reads only `envelope.event_type`/`payload` and
`self.weights[...]` — there is no `AuthoritativeState` field read anywhere in this class. This
confirms the ticket's own open question: **Pattern 6 (`docs/guidelines/design_patterns.md`
"Compile-Time Pillar Activation Pattern") does not apply to ECONOMY.** Pattern 6 fixes a bootstrap
gap where a durable-state field is never constructed by `WorldCompiler.compile()`, so no world
content could ever satisfy the scoring condition. ECONOMY's gap is the opposite shape: the fields
exist and the events *can* fire, they just don't fire enough because too few worlds have enough
merchant/crafting-capable population and building content authored into them. This is pure content
authoring, confirmed against real corpus data below (not assumed).

### Re-verified current ECONOMY grade state (post `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, same day)

Per `docs/simulation_quality/current_state.md` (refreshed today, post-fix): **ECONOMY = 0 S / 1 A /
17 B / 57 C, across 75 anchor entries / 18 worlds.** This supersedes the ticket's own stale framing
("60/72 C … caps at 1/3-of-A regardless of volume") on two counts: (a) the anchor count is 75/18,
not 72/17 (`current_state.md`'s own correction of a meta-key miscounting bug); (b) the ceiling
described in the ticket's Request Summary is fixed — the same 69-event `urban_political` run the
ticket cites as "only reached 0.16" now grades **A at 0.66** (`scoring_weights.yaml` ECONOMY
section: `harvest_active=12.0, crafting_active=16.0, trade_active=12.0`, etc. — a uniform x4 vs.
pre-fix, per the comment block at the top of that YAML section, `M_ECONOMY = ceil((0.5*841)/138)
= 4`). Content-authoring effort will now actually show up in the grade, which is the ticket's own
stated precondition for proceeding.

### The real gap, empirically confirmed (not assumed from the raw C-count)

Cross-referencing `tests/simulation_quality/fixtures/grade_anchors.json` (all 75 entries,
programmatically grouped by world) against `data/calibration/*/quality_report.json` and
`docs/simulation_quality/eval_matrix_results.md` surfaces the real shape of the gap:

- **`gold_sink_fired` is the only ECONOMY event path that fires generically, corpus-wide, with no
  authored economy content at all** (`eval_matrix_results.md` line ~190: "`gold_sink_fired` (the
  only active ECONOMY event path globally) requires `GoldSinkSystem` to detect Gini > 0.7
  (`INFLATION_SPIRAL_GINI_THRESHOLD` in `src/economy/health_monitor.py`)"). This fires from pure
  combat-loot wealth inequality, not real harvest/craft/trade. Confirmed empirically:
  `dungeon_crawl_seed42_1000t` and `sandbox_world_seed42_1000t` — two structurally unrelated worlds
  — produce **byte-identical** `EconomyScorer` output (`raw_score=192.0, event_count=24,
  loop_flags=["inflation_controlled"]`, normalized=0.213, grade B) at `data/calibration/
  dungeon_crawl_seed42_1000t/quality_report.json` and `.../sandbox_world_seed42_1000t/...`. This is
  a generic, content-independent baseline, not a signal of real economic activity — it must not be
  mistaken for "ECONOMY already partially covered" during Plan.
- **Only `urban_political` has ever produced real harvest/craft/trade volume.** Its
  `seed123_1000t` run (69 events, `raw_score=552.0` post-fix, grade A) is the corpus's one
  data point with actual `harvest_active`/`crafting_active`/`trade_active` density. This is because
  `urban_political` is the only world composition that adds the `trading_company_hub` module
  (`data/content/world_modules/trading_company_hub.yaml`) with a **parameterized `merchant_count:
  6`** (`data/worlds/urban_political/world.yaml` L14-18, `module_refs:` format with
  `parameters: {merchant_count: 6}`) on top of `frontier_village_core`.
- **`docs/simulation_quality/eval_matrix_results.md`'s own "Archetype Note"
  (`TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`, ~line 187) and "Zero-Pillar World Confirmation"
  section (~line 1057) name the exact worlds with no merchant NPC / no service building:
  `dungeon_crawl` (combat-only, no settlement module) and, explicitly by name, all five of
  `wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_extended`,
  `frontier_living_world` — "no merchant NPCs, no non-combat cognitive triggers, same archetype
  pattern as `dungeon_crawl`'s documented COGNITION/ECONOMY C." This is corroborating, independent,
  pre-existing evidence (not this ticket's own guess) that the content gap is real, not just an
  artifact of the C-count.
- **However, this doc's "no merchant NPCs" framing needs one caveat, found this session and not
  previously documented anywhere:** all five of those worlds' settlement content
  (`frontier_village_core` and `settled_quarter`, both used across `frontier_living_world`,
  `frontier_extended`, `swamp_border_world`, `highland_traverse`, and `sandbox_world`) reference the
  **same** population, `frontier_village_population`
  (`data/content/entities/populations.yaml` L10-17), which already contains `traveling_merchant: 1`
  and `village_blacksmith: 1` among 13 total members. So it is not literally true that these worlds
  have *zero* merchant/crafter entities — it is that the density is too sparse (1 merchant among 13,
  vs. `urban_political`'s dedicated 6-merchant hub) to generate scoreable volume at the corpus's
  typical 200-500t calibration window. This distinction matters for Plan: the fix is **raising
  merchant/crafting density**, not introducing a wholly new archetype role from nothing — a cheaper,
  lower-risk framing than "add a merchant NPC" implies literally.
- A second, already-defined-but-unused population exists that raises this density directly:
  `merchant_caravan` (`data/content/entities/populations.yaml` L30-35: `traveling_merchant: 2,
  frontier_guard: 2`) — not referenced by any current world composition. Adding it as an
  **additional** `populations:` entry at the composition level (not editing the shared module
  files) is a smaller, more surgical lever than adding a whole `trading_company_hub` module, and
  fits a route/traversal-themed world (e.g. `highland_traverse`, whose description already reads
  "mountain pass and river crossing routes") better than a full trading-hub retrofit would.
- `trading_company_hub` (`data/content/world_modules/trading_company_hub.yaml`) is itself already
  fully defined, tested (via `urban_political`'s own anchors), and parameterizable
  (`merchant_count`, 1-8) — the lowest-risk lever for worlds whose description already reads as
  trade/settlement-heavy (`frontier_living_world`: "mine economy, trade road";
  `frontier_extended`: same base + "trade road"). Adding it to a world currently using the plain
  `modules: [...]` string-list format (all 5 candidate worlds do) requires either accepting its
  `merchant_count` default (3) via the plain list, or switching that one world's file to the
  richer `module_refs:` format (as `urban_political`/`generated_frontier_3_42` already do) if a
  non-default count is wanted — confirmed via `src/worldassembly/schema.py` L17
  (`ModuleRef.parameters: Dict[str, Any]`) and `WorldCompositionSpec` (L21).

### Candidate worlds — confirmed against live `data/worlds/*/world.yaml`, not assumed

| World | Tier | Current ECONOMY | Merchant/craft content today | Verdict |
|---|---|---|---|---|
| `frontier_living_world` | End-to-end | C (200t) | `frontier_village_core` (shop+blacksmith buildings, 1 merchant/1 blacksmith in pop), `old_mine_resource_loop` (iron/crystal/silver nodes) already present; description explicitly "mine economy, trade road" | **Strong candidate** — thematically already an economy world, just under-populated with commerce entities |
| `frontier_extended` | End-to-end | C (200t) | Same base as above + orc/forest modules; largest world (56 entities/10 regions) | **Strong candidate** — same reasoning, more population to work with |
| `swamp_border_world` | End-to-end | C (200t) | `frontier_village_core` present (shop+blacksmith), no dedicated trade module | **Candidate** — plainer frontier-settlement fit for a trading-hub-style addition |
| `highland_traverse` | End-to-end | C (200t) | `settled_quarter` (blacksmith/healer/inn/shop buildings, same sparse `frontier_village_population`) | **Candidate, different shape** — route/traversal theme fits a `merchant_caravan` population addition better than a full trading hub (avoids duplicate shop/blacksmith buildings) |
| `sandbox_world` | End-to-end | C (200t)/B (1000t, generic gold-sink baseline) | `frontier_village_core` only | Considered, lower priority — this is the dev/calibration base world, not named in the ticket's target list and not one of the doc's explicitly-flagged 5 |
| `generated_frontier_3_42` | End-to-end | C (200t)/B (1000t, generic) | Procedurally generated, already uses `module_refs:`, includes `old_mine_resource_loop` but no trade hub | Viable but lower priority — procedurally generated content is regenerated by tooling, riskier to hand-edit durably |
| `dungeon_crawl` | End-to-end | C→B (1000t, generic gold-sink) | None — 7 combat/creature archetype groups only, explicitly documented "no merchant NPC, no service buildings" | **Rejected** — same structural reasoning `TCK-20260710-SIMQ-DEPTH-SOCIAL` used to reject it for SOCIAL (no settlement/civilian module); forcing a merchant NPC into a pure dungeon-crawl archetype is a thematic mismatch, not a content-authoring fix |
| `wilderness_survival` | End-to-end | C | No settlement-adjacent module at all (`forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter`) | **Rejected** — same "no settlement module" reasoning INFORMATION already used to skip this world; adding commerce content here is closer to inventing a new archetype than authoring into an existing one |
| `crowded_frontier`, `resource_dense_basin`, `frontier_marches` | Stress | C | N/A | **Out of scope** — Stress-tier worlds must stay content-inert per `corpus_tier_taxonomy.md`'s tier-purity discipline; `resource_dense_basin`'s name is a false lead (it fills a *node-density* stress gap, not an economy-activity one — its own anchor is already confirmed stable C, `eval_matrix_results.md` line 1387) |
| `unit_*`, `hero_guild_routing`, `simq_routing_test` | Unit/Regression | C/B | N/A | **Out of scope** — Unit-tier isolation worlds and the `simq_routing_test` calibration fixture must stay single-mechanic/minimal per tier discipline |
| `urban_political` | Regression/baseline | A (richest run) | Already has `trading_company_hub`, `merchant_count: 6` | **Out of scope** — already the corpus's ECONOMY reference case; Regression/baseline tier is "do not touch" unless deliberately promoted, and it needs no more content |

**Recommended 3 candidates: `frontier_living_world`, `frontier_extended`, `swamp_border_world`** —
all three share the identical `frontier_village_core` baseline, are thematically economy-flavored
already (two explicitly describe "trade road"/"mine economy"), and the lowest-risk, most
precedented lever (add `trading_company_hub` to the composition's `modules:` list, mirroring
`urban_political`'s own already-proven pattern) applies cleanly to all three without inventing new
module content. `highland_traverse` is a plausible 4th/alternate pick using a different, smaller
lever (`merchant_caravan` population addition) if Plan wants a fourth data point or if one of the
three primary candidates turns out unsuitable on closer probe.

## Mechanics / Engine Constraints

- `docs/mechanics/03_economic_laws.md` §5 (Industry: Crafting & Conversion) — governs the actual
  gather→craft→sell chain any new merchant/blacksmith content must respect (recipe materials, gold
  cost, atomic conservation). Any newly-authored content must resolve through the existing
  authoritative economy pipeline (`src/engine/economy.py`, `src/systems/economy_systems/`) — this
  ticket authors world/population data, not new economy logic.
- `docs/simulation_quality/quality_scoring_contract.md` §4.4/§4.8 — the `normalized_score` formula
  and the "weights are config, never scorer literals" rule; not touched by this ticket (out of
  scope, owned by the sibling ceiling-fix ticket). §5 ECONOMY defines the 10 scored event types this
  investigation already cross-checked against `EconomyScorer.EVENT_TYPES`.
- `src/economy/health_monitor.py` — `EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD = 0.7`
  (L22) is the sole gate for `gold_sink_fired`, the corpus's generic baseline signal. Confirmed
  out of scope per the ticket's own Out of Scope section — do not touch this constant. Adding real
  merchant/trade population changes the Gini distribution as a side effect (more entities holding
  and moving gold), which could shift how often `gold_sink_fired` fires — a second-order effect to
  watch during recalibration, not a reason to touch the threshold itself.
- `docs/guidelines/design_patterns.md` Pattern 6 — confirmed **not applicable** (see Current
  Behavior above); cited here only to close the ticket's own open question with evidence.

## Parity Ledger Overlap

| ID | File | Status | Relevance |
|---|---|---|---|
| `INFRA-242` | `infrastructure.yaml` | verified, P1 | `EconomyScorer` event-type coverage — this ticket does not change scorer logic or event-type coverage, only world content volume; entry should remain accurate as-is, but its `v2_evidence` could optionally cite the new worlds' event counts as further corroboration once measured. |
| `SIMQ-CALIBRATED-001` | `infrastructure.yaml` | verified, P1 | Already updated by the sibling ceiling-fix ticket to describe ECONOMY's weights as "empirically tuned." This ticket's content-authoring work does not change weights again, but should be cross-checked (not necessarily edited) once new anchors land, since it's the general "calibration progressively operational" record. |
| `TOWN-174`/neighboring `RESOURCE_DEPLETED`/`RESOURCE_RECOVERED` entries | `town_resource.yaml` (~L1835-1856) | verified, P1 | `support_boundary` on the `RESOURCE_DEPLETED` entry explicitly documents the "archetype-blocked in dungeon_crawl" case (no harvesting-capable entity, node exists as dressing only) — directly relevant precedent for why `dungeon_crawl`/`wilderness_survival` are rejected candidates here, not silently reused without citation. |
| Crafting-chain entries (`town_resource.yaml` ~L1819-1831) | `town_resource.yaml` | verified, P1 | "Crafting recipe catalog has ≥25 entries... complete gather→craft chain: iron_ore → steel..." — the recipe substrate this ticket's new content would exercise already exists and is tested; no recipe-catalog change is anticipated. |

**No P0 entries identified in this scope.** All entries above are P1 and `verified` — none strictly
block this ticket, but per the Authoritative Mechanics Rule, `INFRA-242` and/or a new/extended
entry should get a `v2_evidence` update once the new worlds' real ECONOMY event counts are measured
and anchored, in the same session as the content-authoring work (mirroring how
`TCK-20260710-SIMQ-DEPTH-SOCIAL` extended `SOC-007` rather than leaving the ledger silently stale).

## Prior Work

- **`TCK-20260713-SIMQ-SCORE-CEILING-FIX`** (`stored_artifacts/`, this ticket's hard dependency) —
  raised ECONOMY's positive weights x4; its own Anti-Drift Hazards section explicitly names this
  ticket ("Do not author new content into any world — that is
  `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`... A natural but wrong instinct... is to add
  harvest/craft/trade events to worlds — that is out of scope here") confirming the two tickets'
  boundary is already correctly drawn and non-overlapping.
- **`TCK-20260710-SIMQ-DEPTH-SOCIAL`** (`tickets/done/`) — the closest playbook precedent: same
  "investigate candidates against live world.yaml/population-trigger conditions, don't trust the
  roadmap doc, reject structurally-blocked worlds (no settlement module → `dungeon_crawl` rejected
  for SOCIAL, same reasoning this investigation applies to ECONOMY), recalibrate 3 seeds, full
  regression sweep, file any newly-discovered engine bug separately" shape. That ticket's SOCIAL
  mechanism (`ENABLE_SOCIAL_COOPERATION` flag) is *not* analogous to ECONOMY's mechanism
  (pure content volume, no flag at all) — worth not over-fitting the playbook's mechanics, only its
  process discipline.
- **`TCK-20260710-SIMQ-DEPTH-FACTION`/`-INFORMATION`** (`tickets/done/`) — established the
  composition-level (not module-level) content-authoring discipline this investigation's
  recommendation follows: author new content (`trading_company_hub` module reference,
  `merchant_caravan` population) at each target world's own `data/worlds/<world>/world.yaml`, never
  by editing the shared `frontier_village_core`/`settled_quarter` module files those tickets found
  are reused by 5+ worlds each.
- **`TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`** (referenced in `eval_matrix_results.md`, not
  independently confirmed to have a `stored_artifacts/` folder under this exact name in this
  checkout) — the original finding that ECONOMY=C is archetype-correct for `dungeon_crawl`, and the
  origin of the "no merchant NPC, no service buildings" diagnostic this investigation reuses and
  extends to the other 4 named worlds.
- `docs/simulation_quality/eval_matrix_results.md`'s "Zero-Pillar World Confirmation" section
  (~L1046-1060) is the single most load-bearing piece of prior evidence for this investigation —
  it independently (pre-dating this ticket) names the exact 5 candidate-pool worlds and the reason
  each is currently ECONOMY=C, which this investigation corroborates and refines (the
  `frontier_village_population` density caveat above) rather than merely re-citing.

## Risks and Open Questions

1. **Blocking for Plan, not resolved here:** exact final world count (3 vs. 4) and exact per-world
   lever (`trading_company_hub` module addition vs. `merchant_caravan` population addition vs. a
   `merchant_count` parameter override requiring a `modules:` → `module_refs:` format migration for
   that one file). This investigation narrows the space but does not commit — Plan should run a
   live probe (mirroring `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s discipline of confirming trigger
   conditions empirically before locking the candidate list) on at least `frontier_living_world`
   before finalizing all 3.
2. **Not yet empirically confirmed: does adding `trading_company_hub` at default `merchant_count: 3`
   (via the plain `modules:` list, no format migration) produce enough volume to move the grade, or
   is `urban_political`'s `merchant_count: 6` override load-bearing for its A grade?** The
   67% jump in event count needed (69 events at count=6) vs. an unknown count-3 yield is not
   derivable from static content alone — this requires an actual calibration run per candidate
   world during Plan/Implement, not an assumption here.
3. **Second-order Gini/gold-sink interaction, flagged but not resolved.** Adding merchant density
   changes the wealth distribution the `EconomyHealthMonitor` samples every 100 ticks
   (`WINDOW_SIZE=100`). It's plausible (not confirmed) that a richer merchant economy actually
   *reduces* how often the generic `gold_sink_fired`/`inflation_controlled` baseline fires (by
   smoothing the Gini coefficient down from combat-loot-driven inequality), which could partially
   offset the gain from new `harvest_active`/`trade_active` events. This must be measured during
   recalibration, not assumed away.
4. **Cross-pillar side-effect risk, explicitly flagged by the ticket itself and by precedent.**
   `TCK-20260710-SIMQ-DEPTH-SOCIAL` found adding a new active phase/content can shift NARRATIVE
   and PROGRESSION by ±1 band as a legitimate downstream effect (new entities/objects perturb
   quest/XP event counts), and `TCK-20260710-SIMQ-DEPTH-INFORMATION` found a COGNITION side-effect
   from an ostensibly INFORMATION-only change. Adding new population (merchants) or a new module
   (trading hub, with its own quest_definitions) to `frontier_living_world`/`frontier_extended`/
   `swamp_border_world` is very likely to add new NARRATIVE quest activity and new PROGRESSION XP
   events as a side effect (each module ships its own `quest_definitions`) — the full regression
   sweep (AC 2) must not be skipped or narrowed to ECONOMY-only.
5. **`highland_traverse`'s alternate lever (`merchant_caravan` population) is untested as a
   composition-level addition — need to confirm the schema actually supports adding an ad-hoc
   `populations:` entry at the world-composition level (not just via a module) before committing to
   it in Plan.** Not verified in this investigation; flagged as an implementation-phase check.
6. **Not blocking, but worth noting for Plan:** none of the 3 recommended candidates currently use
   the `module_refs:` format — all use the plain `modules: [...]` string list. If Plan wants a
   non-default `merchant_count`, one or more of these files needs a small format migration
   (string list → `module_refs:` list of objects), which is a slightly larger diff than a one-line
   module-ID append. Using the module's default (`merchant_count: 3`) avoids this migration
   entirely and may be sufficient — Plan should decide based on the probe data from Open Question 2.

## Anti-Drift Hazards

- **Do not touch `config/simulation_quality/scoring_weights.yaml` or `grade_thresholds.yaml`** —
  that lever belongs entirely to `TCK-20260713-SIMQ-SCORE-CEILING-FIX`, already landed. This
  ticket's job is content only.
- **Do not touch `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD`** — explicit
  ticket Out of Scope; any temptation to "help" ECONOMY by lowering the Gini gate instead of
  authoring content is scope creep into a different, deliberately-untouched mechanism.
- **Do not edit the shared module files** (`frontier_village_core.yaml`, `settled_quarter.yaml`,
  `old_mine_resource_loop.yaml`) to add merchant density directly — each is referenced by
  multiple worlds (`frontier_village_core` alone by 5+: `frontier_living_world`, `frontier_extended`,
  `swamp_border_world`, `sandbox_world`, `urban_political`); editing it would silently perturb every
  world that references it, defeating "0 unattributed regressions." Author at the composition level
  (`data/worlds/<world>/world.yaml`) only, exactly as the FACTION/INFORMATION depth waves did.
- **Do not touch `urban_political`** — it is Regression/baseline tier, "do not touch" by
  `corpus_tier_taxonomy.md`'s own policy, and it is not one of this ticket's candidates; it is the
  reference case being matched, not a target.
- **Do not add economy content to any Stress/Unit/Regression-tier world**
  (`crowded_frontier`, `resource_dense_basin`, `frontier_marches`, any `unit_*` world,
  `hero_guild_routing`, `simq_routing_test`) — explicit tier-purity requirement restated in the
  ticket's own Related Docs section. `resource_dense_basin`'s name is a specific, easy-to-fall-into
  trap here (it sounds economy-relevant but its stress-tier purpose is node *density*, not
  activated harvesting behavior — its own anchor is already confirmed stable C).
- **Do not force merchant/crafting content into `dungeon_crawl` or `wilderness_survival`** just
  because a "no merchant NPC" note happens to describe them too — both lack any settlement module
  at all, and both were already investigated-and-rejected for an analogous reason (SOCIAL/
  `dungeon_crawl`, INFORMATION/`wilderness_survival`) by prior depth-wave tickets. Re-opening either
  is exactly the kind of "re-litigating a closed DA ruling" the project's Hard Rules warn against.
- **Full regression sweep must not be narrowed to ECONOMY's own anchor columns.** Per the
  cross-pillar side-effect history (SOCIAL→NARRATIVE/PROGRESSION, INFORMATION→COGNITION), new
  module/population content in 3 worlds is likely to move at least one adjacent pillar's grade by
  design (new quest_definitions, new XP-earning entities) — this must be attributed and documented,
  not silently absorbed into `grade_anchors.json`, and not treated as a failure to "fix."
- **Do not conflate the generic `gold_sink_fired`/`inflation_controlled` baseline (byte-identical
  across unrelated worlds at long tick counts) with real content-driven ECONOMY activity** when
  evaluating whether a candidate world "already has some economy signal." A B grade at 1000t+ from
  this generic path is not evidence the content gap is smaller than it looks.
