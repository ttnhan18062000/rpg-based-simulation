# Investigation — TCK-20260613-DOC-MECHANICS-SUBCONTRACTS

**Date:** 2026-06-13
**Status:** Complete

---

## 1. Resource Conservation

### Authoritative module
`src/core/conservation.py` — `ResourceTransactionResolver.resolve()`
Cross-referenced with: `src/systems/economy_systems/crafting.py`, `src/systems/economy_systems/loot.py`, `src/systems/economy_systems/chests.py`, `src/systems/economy_systems/market.py`

### Atomic Law — exact sequence

The resolver enforces conservation in this fixed order:

1. **Idempotency gate** — if `intent.transaction_id` is in `state.processed_transaction_ids`, immediately reject with `IDEMPOTENCY_VIOLATION`. No further checks run.
2. **Destination capacity check** — `InventoryService.can_add_items_with_removals(inventory, items_add, items_remove)`. This accounts for simultaneous removals so that a swap or craft does not over-count slots. Runs before source validation for every `source_kind`.
3. **Source existence / stock check** — the specific guard depends on `source_kind`:
   - `NODE`: node must exist in `state.resource_nodes`; remaining charges > 0 (accounting for `node_overrides` from same-tick sliding updates and `reservations` dict for concurrent actors)
   - `GROUND_ITEM`: item must exist in `state.ground_items`; not reserved by another actor
   - `CORPSE`: corpse must exist in `state.corpses`; not reserved
   - `CRAFTING`: entity must own all materials; gold >= `gold_cost`; capacity check already done
   - `SHOP_BUY`: building functional, has stock, entity has gold
   - `SHOP_SELL`: building functional, has liquidity (gold), entity has items
   - `HOME_STORAGE`: on withdraw — storage has items; on deposit — storage has capacity AND entity has items
4. **Atomicity** — on success, a single `TransactionResult` is returned that bundles all updates (`inventory_update`, `node_update` / `ground_item_remove` / `corpse_remove` / `building_update` / `home_storage_update`). The apply path commits all fields together. On failure, `TransactionResult(accepted=False, reason=<ReasonCode>)` is returned and nothing is mutated.

### Failure codes (structured, not strings)

| Code | Condition |
|---|---|
| `IDEMPOTENCY_VIOLATION` | Duplicate transaction_id |
| `INVENTORY_FULL` | Destination slot or weight capacity exceeded |
| `TARGET_INVALID` | Node / building does not exist or not functional |
| `SOURCE_DEPLETED` | Node charges <= 0 |
| `SOURCE_MISSING` | Ground item / corpse not found |
| `TARGET_LOCKED` | Source reserved by another actor this tick |
| `INSUFFICIENT_GOLD` | Entity gold < cost |
| `INSUFFICIENT_RESOURCES` | Entity missing recipe materials or sell items |
| `OUT_OF_STOCK` | Building has no stock of requested item |
| `LIQUIDITY_EXHAUSTED` | Building lacks gold to pay sell price |
| `INSUFFICIENT_CAPACITY` | Home storage full on deposit |
| `UNKNOWN_SOURCE_KIND` | Unrecognised `source_kind` string |
| `ACTION_EXHAUSTION` | Gold short for TOWN_SERVICE/TAX or home storage item missing |

### State that must not change on failure

On any non-`accepted` result: source item/node/corpse is not touched, entity inventory is not changed, building inventory is not changed, home storage is not changed. This is enforced structurally — the authoritative `apply` path only processes updates from an `accepted=True` result.

### Loot vs regular node distinction

In `resolve()`, both `NODE` kinds share one code path. The distinction is the `charges_delta`:
- **Regular node** (e.g. `iron_vein`): `delta = -1` → exactly one charge consumed per harvest.
- **Loot node** (e.g. `treasure_chest`): `delta = -node.remaining_charges` → all remaining charges consumed in one interaction (fully consumed on first success).
This is determined by `node.kind == "LOOT"` at line 91.

### Home storage rules

- Capacity: 32 slots / 200.0 kg (double inventory).
- Only accessible when entity physically present at home coordinates (enforced at the strategic/interaction layer, not in `conservation.py` itself).
- Withdraw path: storage must hold at least the requested quantity of each item.
- Deposit path: storage must have capacity AND entity must own the items.
- Transfer is symmetric: `inventory_update` adds items entity gains / removes items entity gives; `home_storage_update` does the inverse.
- Security (only owner can access) enforced upstream: the resolver receives `entity.id` as the storage key.

### Crafting atomicity

CraftingSystem (`src/systems/economy_systems/crafting.py`) runs 7 sequential gate checks before emitting an `InventoryUpdate`:
1. Recipe known in `RecipeRegistry`
2. Entity has `recipe_id` in `identity.known_recipes`
3. Entity role matches `recipe.required_role` (if set)
4. All material quantities present in inventory
5. Gold >= `recipe.gold_cost`
6. Capacity for output (slot count, stacking exemption if item already present)
7. If all pass: emit `InventoryUpdate(items_remove=materials, items_add=[result_item], gold_delta=-recipe.gold_cost)`

The conservation path (`source_kind="CRAFTING"`) re-checks materials, gold, and capacity atomically. Materials are removed and product added in the same `InventoryUpdate`.

### Market pricing (dynamic)

`DynamicPriceService.calculate_buy_price()`:
- `multiplier = 1.0 + global_salience` (salience 0.0–2.0)
- Hard cap: `multiplier = min(multiplier, 3.0)` (Fair Trade Law)
- `final_price = max(1, int(base_value * multiplier))`

`DynamicPriceService.calculate_sell_price()`:
- `max(1, int(base_value * 0.5))` — always 50%, no salience modifier.

`MarketSystem.calculate_price()` applies additional region and building modifiers:
- `final = base_val * region_mod * building_mod * type_bias`
- `type_bias = 1.2` (buy) or `0.8` (sell)
- `return max(1, int(final))`

### Concurrent actor protection

The resolver accepts an optional `reservations` dict (`Dict[tuple[str, str|int], int]`). Before committing a NODE, GROUND_ITEM, CORPSE, QUEST, CHEST, or RECRUIT source, the resolver checks `reservations.get((source_kind, source_id), 0)`. If > 0, the second actor receives `TARGET_LOCKED`. This is the mechanism preventing duplication when two actors complete the same loot target in the same tick (TOWN-121 through TOWN-125).

---

## 2. Adventure Routing

### Authoritative modules
- `src/domains/adventure/generator.py` — `AdventureRouteGenerator.generate()`
- `src/domains/adventure/scoring.py` — `AdventureRouteScorer.score()`
- `src/domains/adventure/resolver.py` — `ObjectiveIntentResolver.resolve()`
- `src/domains/adventure/schema.py` — `RouteFamily`, `AdventureRouteOption`, `AdventureDecisionResult`

### Route family taxonomy

All families are defined in `RouteFamily` (str enum):

| Family | Value | Meaning |
|---|---|---|
| `RECOVER` | `"recover"` | Rest, healing, equipment repair |
| `BUY_UPGRADE` | `"buy_upgrade"` | Purchase from shop |
| `CRAFT_UPGRADE` | `"craft_upgrade"` | Blacksmith crafting |
| `TRAIN_SKILL` | `"train_skill"` | Class hall training |
| `TAKE_EASY_QUEST` | `"take_easy_quest"` | Low-risk quest |
| `HUNT_WEAK_ENEMY` | `"hunt_weak_enemy"` | Combat for resources |
| `GATHER_RESOURCE` | `"gather_resource"` | Harvest resource node |
| `SELL_LOOT_FOR_GOLD` | `"sell_loot_for_gold"` | Sell to shop |
| `ASK_INFORMATION` | `"ask_information"` | Information gathering |
| `SCOUT_LOCATION` | `"scout_location"` | Exploration |
| `FORM_PARTY` | `"form_party"` | Social grouping |
| `RETURN_TOWN` | `"return_town"` | Travel back to settlement |
| `DEFER_WITH_REASON` | `"defer_with_reason"` | Fallback when no options |

### Opportunity inputs

`AdventureRouteGenerator.generate()` receives `opportunities: Sequence[Opportunity]` from `src/world/providers/resources.py`. Each `Opportunity` has:
- `kind` — maps to `RouteFamily` via `kind_map`: `gather_resource→GATHER_RESOURCE`, `buy_item→BUY_UPGRADE`, `craft_item→CRAFT_UPGRADE`, `repair_gear→RECOVER`, `ask_information→ASK_INFORMATION`, `rest_inn→RECOVER`
- `confidence` — float 0–1, copied to `AdventureRouteOption.confidence`
- `estimated_reward` — divided by 100 to produce `expected_benefit`
- `estimated_risk` — copied to `expected_risk`
- `requirements` — list of requirement objects (see blockers below)
- `id`, `subject` — for tracing

### Blocker conditions

Checked inside the generator's opportunity loop:
- `req.kind == "has_gold"`: if `entity.inventory.gold < req.quantity` → blocker `f"insufficient_gold:{shortfall}"`
- `req.kind == "has_item"`: if item quantity in inventory < `req.quantity` → blocker `f"missing_item:{req.subject}:{shortfall}"`

Routes with any blocker still appear in the candidate set but receive a massive penalty in scoring (`blocker_penalty = 2.0`).

Structural defaults are added without blocker checking:
- `low_health` or `healing` need → forced `RECOVER` route at confidence 0.9
- `weak_weapon` or `equipment_improvement` need, no BUY/CRAFT already present → `ASK_INFORMATION` at confidence 0.8

### Fallback

If `opts` is empty after all processing: one `DEFER_WITH_REASON` route is appended with `score=0.01`, `confidence=1.0`, `expected_benefit=0.0`. This guarantees a non-empty candidate set.

**Cap:** `opts[:25]` — hard maximum of 25 candidates to prevent evaluation blowup.

### Scoring formula

`AdventureRouteScorer.score()` computes:

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```

Components:
1. **urgency** — max urgency value of active needs matching the route's family (from `entity.self_model.needs.active_needs` dict, via `family_needs` lookup table)
2. **benefit** — `route.expected_benefit` directly
3. **personality_bias** — up to +0.25 based on matching trait:
   - RECOVER → `caution * 0.25`
   - GATHER_RESOURCE / SELL_LOOT_FOR_GOLD / TAKE_EASY_QUEST → `greed * 0.25`
   - ASK_INFORMATION / SCOUT_LOCATION → `curiosity * 0.25`
   - CRAFT_UPGRADE / GATHER_RESOURCE → `industry * 0.25` (note: GATHER_RESOURCE matches both greed and industry; last match wins in if/elif chain — only `industry` applies since GATHER_RESOURCE appears in the `elif` branch, not the greed branch — this is a known quirk)
   - FORM_PARTY → `sociability * 0.25`
4. **confidence_bonus** — `route.confidence * 0.15`
5. **risk_penalty** — `route.expected_risk * risk_multiplier * 0.5`
   - `risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)`
6. **blocker_penalty** — `2.0` if any blocker present, else `0.0`

Final: `round(max(0.0, final_score), 4)`

### Trait normalisation

`get_trait()` normalises trait values:
- If value > 1.0: divide by 100 (handles percentage-scale storage)
- `caution` is derived: `max(0.0, min(1.0, 1.0 - bravery))`
- `curiosity` is derived from `entity.identity.properties["curiosity"]` or `attributes.intelligence / 10.0` if > 1.0

### Selection algorithm

`AdventureRouteScorer.score()` is called for each candidate, returning an updated `AdventureRouteOption` with `score` set. The caller (the service layer, not documented in these modules) selects the highest-scoring candidate.

### Trace events

`AdventureDecisionResult.trace` is a `Dict[str, Any]` — the service populates it with evaluation metrics for debugging. Exact trace keys are set by the service layer (not in generator/scorer). The `reason` field on each `AdventureRouteOption` provides human-readable source context.

### Objective resolution

`ObjectiveIntentResolver.resolve()` maps `ObjectiveKind` → `ActionIntent.kind`:

| ObjectiveKind | ActionIntent kind |
|---|---|
| `REACH_SERVICE` | `MOVE_TO` |
| `BUY_ITEM` | `BUY_ITEM` |
| `ACQUIRE_ITEM` | `REQUEST_CRAFT` |
| `REACH_LOCATION` | `MOVE_TO` |
| `ACCEPT_QUEST` | `ACCEPT_QUEST` |
| `DEFEAT_ENEMY` | `ATTACK_TARGET` |
| `REACH_RESOURCE` | `MOVE_TO` |
| `HARVEST_RESOURCE` | `HARVEST_RESOURCE` |
| `ASK_INFORMATION` | `ASK_INFORMATION` |
| `RETURN_TOWN` | `RETURN_TOWN` |
| default | `MOVE_TO` |

Default fallback kind before any match: `"DEFER"`.

---

## 3. Damage Formula

### Authoritative modules
- `src/engine/combat.py` — `CombatResolutionSystem`
- `src/engine/combat_rewards.py` — `CombatRewardClassificationService`
- `src/engine/rpg_depth.py` — `StaminaService.get_exhaustion_multiplier()` (called in tactical multiplier path)

### Base damage formula

```python
# Fractional Armor Mitigation
atk = float(attacker.combat.atk) * atk_mult
dfn = float(defender.combat.def_stat) * def_mult
raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))
damage = max(1, raw_damage)
```

- Minimum damage: 1 (enforced by `max(1, raw_damage)`)
- Rounding: `int()` truncates before the minimum clamp

### Tactical modifier evaluation order (`_get_tactical_multipliers`)

Modifiers stack additively on `atk_mult` and `def_mult`, except multiplicative entries which are noted:

1. **High Ground** (`check_high_ground`): `atk_mult += 0.20`
2. **Flanking** (`check_flanking` returns `is_flanked, is_surrounded`):
   - Flanked: `atk_mult += 0.15`
   - Surrounded: `atk_mult += 0.25`
3. **Cover** (`check_cover`): `def_mult += 0.30`
4. **Frozen/Shatter** (`defender.identity.properties.get("status_frozen")`): `atk_mult *= 1.50` (multiplicative)
5. **Sleep Exhaustion** (`attacker.biological.sleep_debt > 80.0`): `atk_mult *= 0.80` (multiplicative)
6. **Stamina Exhaustion** (`StaminaService.get_exhaustion_multiplier(attacker.stamina)`): `atk_mult *= exhaust_mult` (multiplicative, only if < 1.0)
7. **Bond Synergy** (first adjacent ally with `familiarity > 0.5`): `atk_mult += 0.10`

Additive modifiers apply before multiplicative ones in the execution order above, so application order matters. Shatter, Sleep Exhaustion, and Stamina Exhaustion can compound.

### Modifier sources table

| Modifier | Type | Value | Source check |
|---|---|---|---|
| High Ground | additive ATK | +0.20 | Attacker elevation > defender elevation |
| Flanking | additive ATK | +0.15 | Defender's focus direction |
| Surrounded | additive ATK | +0.25 | Multiple enemies adjacent to defender |
| Cover | additive DEF | +0.30 | Defender adjacent to cover relative to attacker |
| Shatter (Frozen) | multiplicative ATK | ×1.50 | `status_frozen` property on defender |
| Sleep Exhaustion | multiplicative ATK | ×0.80 | Attacker `sleep_debt > 80.0` |
| Stamina Exhaustion | multiplicative ATK | ×exhaust_mult | `StaminaService` (< 1.0 only) |
| Bond Synergy | additive ATK | +0.10 | Adjacent ally with `familiarity > 0.5` |

### Durability decay

`_get_durability_decay()` — applied to both attacker and defender on every resolved hit:
- **Attacker**: `MAIN_HAND` slot: `-1.0` durability (only if slot occupied)
- **Defender**: `TORSO`, `LEGS`, `HEAD` slots: `-0.5` durability each (only if slot occupied)
- Broken equipment (durability <= 0) provides zero stat bonuses (enforced in `LevelingService.recalculate_combat_stats()`)

### Wound infliction

`_get_wound_infliction()`:
- Threshold: `damage > defender.combat.max_hp * 0.25` (note: source uses 0.25 not 0.40 from chapter doc — **divergence from chapter 01 which states 40%**; source 0.25 is authoritative per ticket assumptions)
- Only inflicted if `alive=True` (target survived the hit)
- Wound fields: `kind` (SLASH if attacker is HERO, CRUSH otherwise), `severity = damage / max_hp`, `atk_penalty = 5.0`, `def_penalty = 5.0`
- Permanent scars: 30% of original wound penalty — stated in chapter 01, not yet traced to a source function in the investigated modules

### Kill rewards

`CombatRewardClassificationService.classify_defeated_target()`:
1. First tries faction relation projection via `FactionSemanticsService.is_hostile_compat()` with `combat_engaged=True` context
2. If hostile by faction: `xp_multiplier=10`, `gold_multiplier=5`, not rebirth eligible
3. Fallback to `EntityRole`:
   - `MONSTER`: xp×10, gold×5, not rebirth eligible
   - `HERO`: xp×20, gold×50, rebirth eligible
   - other: xp×0, gold×0

**XP grant**: `xp_gain = defender.identity.evolution_level * classification.xp_multiplier`
**Gold grant**: `gold_gain = defender.identity.evolution_level * classification.gold_multiplier`

Hero rebirth check:
- `defender.lifecycle.generation < 4` → `generation_delta = 1`, `outcome = "REBIRTH"`
- `generation >= 4` → `is_permadeath_set = True`, `outcome = "PERMADEATH"`

### Death threshold

HP <= 0 triggers kill/defeat. There is no explicit minimum HP floor in `resolve_attack` — the check is `if new_hp <= 0`. The `alive` flag drives all subsequent reward and lifecycle logic.

### AoE splash

`resolve_aoe_attack()`:
- Primary target: full formula damage
- Splash victims (enemy faction, within radius, with LOS from target_pos): `splash_damage = attacker.combat.atk // 2`, minimum 1
- Friendly fire: faction-matched entities skipped

---

## 4. Attribute Progression

### Authoritative modules
- `src/progression/leveling.py` — `LevelingService`
- `src/progression/skills.py` — `SkillScalingService`
- `src/progression/breakthroughs.py` — `BreakthroughService`
- `src/progression/evolution.py` — entity evolution on level cap

### XP gain sources

XP is granted via `ResourceTransferIntent(source_kind="COMBAT", xp_reward=...)` → `conservation.py` path → `IdentityUpdate(evolution_points_delta=xp_reward)`.

Sources identified:
- **Monster kill**: `LVL * 10` XP
- **Hero kill**: `LVL * 20` XP
- **Quest reward**: `evolution_points_delta` on `QUEST` source kind
- Combat rewards are traceable via `trace["REWARD_SOURCE"]` in `CombatUpdate`

XP is accumulated in `identity.evolution_points` (`IdentityComponent.evolution_points`).

### Level threshold formula

```python
# From LevelingService.get_xp_required(level)
# VERIFIED v2: xp_threshold_formula
XP_required_to_reach_next_level = int(100 * (level ** 1.5))
```

Examples:
- Level 1 → 2: 100 XP
- Level 2 → 3: 283 XP
- Level 5 → 6: 1118 XP
- Level 10 → 11: 3162 XP
- Level 98 → 99: 969,440 XP (approximate)

Edge case: `level <= 0` returns 100.

### Level-up execution (`_execute_level_up`)

1. `new_level = identity.evolution_level + 1`
2. `rem_xp = total_xp - cost` (carry over excess XP — note: does not chain level-ups in one call)
3. `ap_gain = 5` (always +5 AP per level)
4. Skill unlocks: level 2 → `power_strike`; level 5 → `swift_reflexes`; level 10 → `fireball`
5. Returns `IdentityUpdate(evolution_level_set=new_level, evolution_points_delta=..., unspent_ap_delta=5, learned_skills=unlocked)`

### Level cap

`current_level >= 99` → XP is still accumulated (`evolution_points_delta=xp_gain`) but no level-up fires. Capped by `VERIFIED v2: level_cap_enforced`.

### Attribute point allocation

`unspent_ap_delta += 5` per level. AP allocation mechanics (spending AP on attributes) are in the apply path — gated by: available points (`PROG-067`), valid attribute name (`PROG-068`), aptitude multiplier (`PROG-069`), attribute cap of 99 (`PROG-070`).

### Derived stat recalculation order

`LevelingService.recalculate_combat_stats()` — triggered whenever attributes or equipment change:

1. **Base from attributes:**
   - `max_hp = base_hp + (vitality * 2) + int(endurance * 0.5)`
   - `atk = base_atk + int(strength * 0.5)`
   - `def_stat = base_def + int(vitality * 0.3)`
   - `evasion = base_evasion + (agility * 0.001)`
   - `atk_range = 1` (default)

2. **Equipment bonuses** (only non-broken slots, `durability > 0`):
   - `atk += item.properties["atk_bonus"]`
   - `def_stat += item.properties["def_bonus"]`
   - `max_hp += item.properties["hp_bonus"]`
   - `evasion += item.properties["evasion_bonus"]`
   - `atk_range` overridden by MAIN_HAND weapon `"range"` property
   - `total_weight` accumulated for movement cost

3. **Passive skill bonuses:**
   - Only `SkillKind.PASSIVE` skills apply here
   - `swift_reflexes`: `evasion += skill.power`
   - Other passives added as new skills registered

4. **Trait bonuses:**
   - `"Tough"`: `max_hp += 20`
   - `"Quick"`: `evasion += 0.02`
   - `"Strong"`: `atk += 3`

5. **Movement cost:**
   - `move_cost = max(5.0, 10.0 + (total_weight / 5.0) - (agility * 0.1))`

6. **Tactical role derivation (with hysteresis):**
   - Scores: VANGUARD=strength, SKIRMISHER=agility, PROTECTOR=vitality
   - New role = max score
   - Hysteresis: only switch if `new_role_score > current_role_score + 5`

### Biological pressure interaction with progression

Biological pressures affect combat stats but not XP accumulation:
- `sleep_debt > 80.0` → `atk_mult *= 0.80` (in combat only, not on base stats)
- Hunger at 100.0 → starvation (5 damage/tick) — no stat reduction on leveling
- Stamina exhaustion → `exhaust_mult < 1.0` applied to atk in combat

### Skill advancement (SkillScalingService)

Active skill power scaling:
- `PHYSICAL`: `skill.power * (1.0 + attributes.strength * 0.02)`
- `MAGICAL`: `skill.power * (1.0 + attributes.intelligence * 0.03)`
- `ELEMENTAL`: `skill.power * (1.0 + attributes.spirit * 0.025 + attributes.wisdom * 0.01)`

Passive skill bonus (swift_reflexes): `skill.power * (1.0 + attributes.agility * 0.01)`

### Breakthroughs

`BreakthroughService.REGISTRY` defines 3 breakthroughs:
- `iron_will`: +2 spirit, +2 wisdom
- `fleet_foot`: +3 agility, +0.05 flat evasion
- `titan_grip`: +4 strength

`apply_bonuses()` is a placeholder — full synergy logic not yet implemented (Phase 8 placeholder comment in source).

---

## Notable Discrepancies Found

1. **Wound threshold divergence**: Chapter 01 states `damage >= max_hp * 0.40`. Source code `combat.py` uses `damage > max_hp * 0.25`. The source is authoritative per ticket assumptions. This divergence must be noted in the sub-contract doc and flagged for parity ledger update.

2. **GATHER_RESOURCE personality bias quirk**: In `scoring.py`, GATHER_RESOURCE appears in both the greed branch and the industry branch of the personality_bias if/elif chain. Because `elif` is used, only the first matching branch applies. GATHER_RESOURCE hits the greed branch first (`elif route.family in (RouteFamily.GATHER_RESOURCE, RouteFamily.SELL_LOOT_FOR_GOLD, RouteFamily.TAKE_EASY_QUEST)`). The industry `elif` branch also lists CRAFT_UPGRADE and GATHER_RESOURCE — but GATHER_RESOURCE never reaches it. This is a code-level quirk worth documenting but not correcting here (documentation ticket only).

3. **Adventure routing and combat rewards**: XP reward formula differs between AoE kills (hardcoded ×10/×5 inside `resolve_aoe_attack`) and the classification service path used in `resolve_attack`/`resolve_skill_usage`. AoE bypasses faction relation projection.
