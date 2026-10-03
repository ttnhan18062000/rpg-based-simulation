# Investigation: TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG
# ECONOMY / COGNITION Zero-Activation in dungeon_crawl

**Date:** 2026-07-02
**Phase:** Investigation (seq 2)
**Status:** Complete — archetype decision reached

---

## Current Behavior

### Calibration data (confirmed via `data/calibration/*/quality_scores.jsonl`)

| World / Ticks | ECONOMY event_type | count | COGNITION event_type | count |
|---|---|---|---|---|
| sandbox_world_seed42_1000t | gold_sink_fired | 72 | decision_divergence_detected | 21 |
| sandbox_world_seed42_2000t | gold_sink_fired | 48 | decision_divergence_detected | 16 |
| urban_political_seed42_1000t | gold_sink_fired | 48 | (none) | 0 |
| urban_political_seed123_1000t | gold_sink_fired | 92 | decision_divergence_detected | 14 |
| simq_routing_test_seed123_500t | (none) | 0 | decision_divergence_detected | 3 |
| **dungeon_crawl (all seeds, all tick counts)** | **(none)** | **0** | **(none)** | **0** |

dungeon_crawl produces zero ECONOMY and COGNITION score records at 200t, 500t, 1000t, and 2000t across seeds 42, 123, and 456.

### Event types that would need to fire for non-zero ECONOMY

Per `src/simulation_quality/scorers/economy.py` `EconomyScorer.EVENT_TYPES`:
- `resource_harvested`, `item_crafted`, `trade_executed`, `shop_transaction` — all calibration_hits=0 globally (not yet implemented in engine as active behaviors)
- `gold_sink_fired` — the ONLY economy event firing in any calibration run
- `quest_reward_dispensed`, `gold_transferred`, `resource_node_depleted`, `conservation_law_verified` — all calibration_hits=0 globally

### Event types that would need to fire for non-zero COGNITION

Per `src/simulation_quality/scorers/cognition.py` `CognitionScorer.EVENT_TYPES`:
- `decision_divergence_detected` — the ONLY cognition event firing in calibration (sandbox/urban/routing_test only)
- `belief_updated`, `self_model_updated`, `lead_certainty_changed`, `strategic_goal_changed`, `knowledge_default_fallback` — all calibration_hits=0 globally

---

## Root Cause: WHY ECONOMY is Zero in dungeon_crawl

### Mechanism: gold_sink_fired requires INFLATION_SPIRAL Gini threshold

The `gold_sink_fired` event path (the only active ECONOMY path) is:

```
EconomyHealthMonitor.sample()           # src/economy/health_monitor.py L56
  → gini_coefficient > 0.7             # INFLATION_SPIRAL_GINI_THRESHOLD
GoldSinkSystem.apply()                  # src/engine/gold_sink.py L51
  → ResourceTransferIntent (REPAIR_FEE / SERVICE_FEE / TAX)
  → resolved by ResourceTransactionSystem
  → event_extractor emits gold_sink_fired
  → EconomyScorer.score() records ScoreRecord
```

This fires only at WINDOW_SIZE=100 tick boundaries AND only when the entity population's gold Gini coefficient exceeds 0.7 (`src/economy/health_monitor.py:22`).

### Why dungeon_crawl never reaches Gini > 0.7

dungeon_crawl entities (`data/worlds/dungeon_crawl/resolved/world.resolved.yaml`):

| Entity group | count | archetype_id | role | spawn_region |
|---|---|---|---|---|
| goblin_raiding_party_goblin_scout | 2 | goblin_scout | scout | goblin_camp |
| goblin_raiding_party_goblin_raider | 4 | goblin_raider | raider | goblin_camp |
| goblin_raiding_party_goblin_archer | 2 | goblin_archer | scout | goblin_camp |
| goblin_raiding_party_goblin_warlord | 1 | goblin_warlord | leader | goblin_camp |
| old_mine_spider_cluster_cave_spider | 5 | cave_spider | predator_hunter | old_mine |
| undead_battlefield_patrol_undead_sentinel | 6 | undead_sentinel | sentinel | haunted_battlefield |
| pop_0 (bandit scouts) | 12 | (not set) | scout | bandit_road |

Total: ~32 entities, all pure combat/creature archetypes. `behavioral_profile` is `None` for every entity in the resolved spec.

- Non-humanoid entities (`cave_spider`, `undead_sentinel`) carry no gold by archetype design
- Humanoid combat entities (goblins, bandits) accumulate gold only through symmetric combat looting — the distribution stays near-uniform
- sandbox_world's `traveling_merchant` (archetype_id=traveling_merchant, role=merchant) + service buildings (shop, blacksmith, inn, town_hall, healer_hut in `hometown`) create gold inequality: merchants accumulate far more gold through transactions than worker entities → Gini crosses 0.7 → gold_sink_fired
- dungeon_crawl has no merchant NPC, no service buildings; its only building is `mine_entrance` (region: old_mine) — not a service building

### Why other ECONOMY events cannot fire

- `resource_harvested`: 3 resource nodes exist (iron_vein, crystal_outcrop, silver_vein in old_mine region). However, no entity has a harvesting behavioral profile. cave_spider is `predator_hunter`; entities with `goblin_*` or `bandit_scout` archetypes are combat-oriented. No entity is assigned to harvest resource nodes. `resource_harvested` calibration_hits=0 globally across all worlds.
- `trade_executed` / `shop_transaction`: no merchant entity (traveling_merchant archetype absent), no shop/blacksmith/inn/town_hall building exists in dungeon_crawl. These events require an active trade or shop interaction between economic NPCs or entities with gold reserves.
- `quest_reward_dispensed`: Quest definitions exist (`mine_fetch_ore`, `goblin_hunt_warlord`, etc.) but no entity has a quest-taking behavioral profile. `required_participant_tags` for most quests is `['humanoid', 'opportunistic']` — goblin entities in dungeon_crawl are not configured as quest participants.

---

## Root Cause: WHY COGNITION is Zero in dungeon_crawl

### Mechanism: decision_divergence_detected requires non-survival project context

Per `docs/simulation_quality/event_type_coverage.md` §1.1, `decision_divergence_detected` fires when:
```
DANGER concern urgency > 0.7 AND entity is on a non-survival project
```
(implemented in `event_extractor.py`)

In sandbox_world, `village_worker`, `frontier_guard`, and `traveling_merchant` entities run economic/exploration projects. When a DANGER concern spikes during these non-combat tasks, the divergence condition fires.

In dungeon_crawl, all entities are permanently in combat/survival mode (goblin raiders, spiders, undead sentinels, bandit scouts). Their active project is always survival-classified. The "non-survival project" condition is **never met**, so `decision_divergence_detected` never fires.

### Why other COGNITION events cannot fire

- `belief_updated`: Requires strategic lead tracking (entity has a lead that gets updated). Combat archetype entities do not have the strategic cognition system active — they have no leads to update. `belief_updated` calibration_hits=0 globally.
- `self_model_updated`: Requires `self_model_bundle_set` on entity update. Combat archetypes do not generate self-model bundles. `self_model_updated` calibration_hits=0 globally.
- `lead_certainty_changed`: Requires a strategic lead with certainty state. Combat entities don't pursue investigation leads. `lead_certainty_changed` calibration_hits=0 globally.
- `strategic_goal_changed`: Requires StrategicObjectiveChanged or StrategicConcernRaised engine events (via `_TRANSLATE_SIMPLE`). Combat entities don't maintain strategic objectives in the architecture sense. Calibration_hits=0 globally.
- `knowledge_default_fallback`: Requires `StrategicLeadExhausted`. No leads to exhaust. Calibration_hits=0 globally.

---

## Archetype Analysis: What Is dungeon_crawl Designed For?

### Entity composition
All 7 entity groups are adversarial combat creatures or wilderness threats:
- Goblin faction: raiding party composition (scout, raider, archer, warlord) — classic combat encounter set
- Spider cluster: predator_hunter role — pure ecological threat
- Undead patrol: sentinel role — static guardian archetype
- Bandit company: scout role — territorial threat

No economic agents, no strategic reasoners, no knowledge-gathering entities.

### World infrastructure
- 1 building: `mine_entrance` (region: old_mine) — dungeon entry point, not a service building
- 3 resource nodes: iron_vein, crystal_outcrop, silver_vein (all in old_mine) — exist as world dressing and potential quest targets; no entity harvests them
- 16 factions, 4 regions — faction structure supports FACTION pillar events (territory, tension, war) but none fire because the feature flag is off globally for non-cooperation pillars
- 0 populations — dungeon_crawl uses explicit named entity groups rather than emergent population generation

### What dungeon_crawl does activate
Per eval_matrix_results.md and calibration data:
- **COMBAT**: A at 500t and 1000t (highest-scoring pillar)
- **WORLD**: B (hazard events, trauma) — the combat ecosystem drives world dynamics
- **PROGRESSION**: A at 500t and 1000t (XP/level progression from combat)
- COMBAT + WORLD + PROGRESSION = the three pillars this archetype is built around

### Comparison: sandbox_world
sandbox_world activates ECONOMY via merchant/worker gold inequality (Gini > 0.7) and COGNITION via worker/guard entities doing non-survival projects. Its infrastructure (5 service buildings, economic NPC roles) creates the conditions dungeon_crawl intentionally lacks.

---

## Design Decision: DA (Archetype-Intentional)

**Decision: DA — dungeon_crawl ECONOMY=C and COGNITION=C are archetype-correct.**

### Rationale

1. **Entity composition is unambiguously combat-only**: Every entity in dungeon_crawl is a combat/creature archetype with no economic or cognitive behavioral profile. This is not an oversight — it is the defining characteristic of this world type.

2. **Infrastructure confirms intent**: The only building is a mine entrance (dungeon access). No service buildings, no merchant NPCs, no craft stations. The 3 resource nodes exist but are never harvested — they are world dressing for a dungeon aesthetic, not functional economic infrastructure.

3. **ECONOMY=C is mechanically impossible to fix without changing the archetype**: `gold_sink_fired` requires Gini > 0.7, which requires an economic agent (merchant/worker) accumulating disproportionate gold. Adding such an entity to dungeon_crawl would change its fundamental character from a combat dungeon to a dungeon-with-town.

4. **COGNITION=C is mechanically impossible without enabling strategic cognition on combat entities**: `decision_divergence_detected` requires a non-survival project context, which combat entities never enter. Adding strategic cognition profiles to goblins/spiders/undead would change them from creature archetypes to strategic agents — a category error.

5. **The C grades are stable and deterministic**: All 3 seeds × all 4 tick counts show ECONOMY=C, COGNITION=C. eval_matrix_results.md already records this correctly. The grades represent the correct absence of economic and cognitive simulation layers in a combat-arena world.

6. **Archetype boundary is meaningful for evaluation**: Having a world type that only activates COMBAT/WORLD/PROGRESSION allows the eval matrix to distinguish "pillar not applicable to this archetype" from "pillar broken in this world". This is a feature, not a deficiency.

**No world spec change is needed.**

---

## If DB Were Chosen: Minimal World Spec Extension (Not Recommended)

This section is documented for completeness; the decision is DA.

To activate ECONOMY, the minimum viable change would be adding:
- 1 `traveling_merchant` entity (archetype_id=traveling_merchant, role=merchant, spawn_region=any) — creates gold inequality → Gini > 0.7 → gold_sink_fired
- OR 1 shop/blacksmith service building — enables trade interactions

To activate COGNITION, the minimum viable change would be:
- Enable `ENABLE_ADVENTURE_ROUTING=ON` in the dungeon_crawl simulation profile — enables `decision_divergence_detected` via `AdventureDecisionPhase` (at the cost of making dungeon_crawl entities use routing logic designed for exploration, not dungeon crawling)
- OR add 1 non-combat entity with a non-survival project profile (e.g., a lore_scholar NPC doing investigation)

Both changes would compromise the archetype's combat-arena identity and are not recommended.

---

## Parity Ledger Overlap

### `docs/parity_ledger/town_resource.yaml`

The resource harvesting entries (lines ~107, 118, 128) cover `loot/harvest` mechanics. These are applicable to economic worlds. No specific dungeon_crawl exclusion is documented — it should be added as a scope note to relevant harvest and gold_sink entries.

**Affected entries:**
- Gold sink / GoldSinkSystem entries (lines ~1943-1972): add scope note: "Applies when INFLATION_SPIRAL fires; archetype-blocked in dungeon_crawl (no gold-accumulating economic agents)"
- Harvest entries (lines ~1835-1844): add scope note: "Requires entity with harvesting behavioral profile; archetype-blocked in dungeon_crawl"

### `docs/parity_ledger/strategic_cognition.yaml`

Cognition capacity entries (lines ~49-390, 676, 2123-2473) document bounded cognition mechanics. These apply to entities with strategic cognition profiles. Combat archetypes in dungeon_crawl have no such profiles.

**Affected entries:**
- decision_divergence_detected entry (if present): add scope note: "Requires non-survival active project; archetype-blocked in dungeon_crawl (all entities survival-mode only)"
- belief_updated / self_model_updated entries: add scope note: "Requires strategic cognition profile; archetype-blocked in combat-only entities"

### `docs/simulation_quality/eval_matrix_results.md`

Already records dungeon_crawl ECONOMY=C, COGNITION=C correctly. Needs explicit archetype-intent annotation in the stability analysis section (currently describes combat/world stability but does not explicitly label economy/cognition C as archetype-correct).

---

## Risks and Open Questions

**R1 — `pop_0` ambiguity**: Entity group `pop_0` (12 entities, role=scout, faction=bandit_company, spawn_region=bandit_road) has no archetype_id set. It is labeled `pop_0` as if generated from a population module, but behaves identically to named combat entities. If `pop_0` ever gets an economic profile applied, gold accumulation could change. Low risk: the bandit_scout archetype has no economic profile defined.

**R2 — `mine_fetch_ore` quest activation**: The `mine_fetch_ore` quest definition (tags: `['resource', 'economy']`, required_participant_tags: `[]`) has empty participant tag requirements. Theoretically any entity could become a participant. If the quest system is ever activated in dungeon_crawl (e.g., by a future scenario mode), `quest_reward_dispensed` could fire. This would be the only ECONOMY event achievable without world spec changes.

**R3 — Gini threshold sensitivity**: The INFLATION_SPIRAL threshold is 0.7. If combat loot creates even minor gold inequality (e.g., warlord loots more than scouts), Gini could theoretically approach this threshold at very long runs (2000t+). Current calibration shows 0 events even at 2000t, so this is not a near-term risk. Monitor if loot mechanics change.

**R4 — `ruins_first_contact` quest** (required_participant_tags: `['undead']`, required_location_tags: `['ruins']`): undead_sentinel entities exist in dungeon_crawl. If a ruins region had the right tags and the quest system activated, undead could theoretically participate. Not a quality metric risk but a design observation.

---

## Anti-Drift Hazards

**AH1 — New entity types added to dungeon_crawl**: If a future ticket adds a merchant or worker NPC to dungeon_crawl (e.g., for a "dungeon town" variant), ECONOMY will start firing and the C grade anchors will be incorrect. Ticket implementer must update `grade_anchors.json` and re-run calibration.

**AH2 — GoldSinkSystem threshold change**: If `INFLATION_SPIRAL_GINI_THRESHOLD` (`src/economy/health_monitor.py:22`) is lowered below the natural Gini of dungeon_crawl combat loot distribution (estimated ~0.3-0.5 based on symmetric looting), dungeon_crawl would start generating `gold_sink_fired` events. Current threshold (0.7) is well above this.

**AH3 — ENABLE_ADVENTURE_ROUTING enabled globally**: If adventure routing is turned on by default (it currently defaults OFF), `decision_divergence_detected` would fire for any entity doing non-survival projects. dungeon_crawl entities are always in survival mode, so this risk is low — but monitor if routing logic changes what counts as "survival".

**AH4 — Behavioral profile templates applied to combat archetypes**: If a future refactor applies a default behavioral_profile to all entities (including combat archetypes), the cognition system could activate for dungeon_crawl entities unexpectedly.

**AH5 — eval_matrix_results.md auto-grade annotation drift**: The DA decision must be explicitly documented in eval_matrix_results.md. Without it, a future agent may see ECONOMY=C for dungeon_crawl and incorrectly classify it as a bug rather than an archetype feature.
