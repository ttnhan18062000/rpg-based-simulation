---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-08-30
---

# Progression Domain Contract

**Source:** `src/domains/progression/` (phase.py, ledger.py, generator.py, resolver.py, selector.py, gaps.py, possession.py, interpretation.py, schema.py)  
**Pipeline phase:** the Progression Conversion stage (`ProgressionConversionPhase`)  
**Authoritative status:** Tick orchestration domain — manages reward ledger tracking and conversion decisions. Level-up mechanics, stat recalculation, and skill unlocks live in `src/progression/leveling.py`, NOT here.

---

## Critical Architectural Split

**If you are searching for "how leveling works", go to `src/progression/leveling.py` — not this domain.**

The progression subsystem is intentionally split across two locations:

| Location | Responsibility |
|---|---|
| `src/domains/progression/` | Tick orchestration, reward ledger tracking, possession evaluation, conversion option generation and selection |
| `src/progression/leveling.py` | **Authoritative level-up mechanics**: XP threshold formula, level cap, AP grants per level, skill unlock thresholds, stat derivation, 6-phase stat recalc order |
| `src/progression/skills.py` | Skill mechanics and skill application |
| `src/progression/breakthroughs.py` | Breakthrough system — bonus application implemented; granting mechanic not yet wired into gameplay |

`ProgressionConversionPhase` reads the entity's current level but **never calls `leveling.py`** directly. Level-up processing runs separately via the engine's authoritative apply path after all domain phases have emitted their updates.

---

## Purpose

Each tick, for every active living entity, `ProgressionConversionPhase` evaluates what the entity should do with its recently-earned rewards (XP, gold, items). It works through a 6-step pipeline: understand current possessions → identify growth gaps → interpret recent rewards → generate conversion options → select the best option → resolve to a typed intent. The resulting `EntityUpdate` is merged back into the tick's `StateUpdate` for authoritative application.

---

## Engine Phase

**Progression Conversion stage — `ProgressionConversionPhase.execute(state, update)`**

Eligibility check per entity:

| Criterion | Check |
|---|---|
| Active | `entity.lifecycle.active = True` |
| Alive | `entity.combat.alive = True` |
| Feature flag | `state.progression_conversion_enabled` (default: True) |

Entities failing either lifecycle check are skipped. The phase accepts an incoming `StateUpdate` (from earlier phases) and returns a merged `StateUpdate` — it does not produce a fresh one.

---

## What It Owns

- The **reward ledger**: `RewardLedgerComponent` stored in `entity.identity.properties["reward_ledger"]`; tracks up to 20 entries of recent XP, gold, and item rewards
- **Possession understanding**: a per-tick evaluation of what the entity currently holds and what state it is in
- **Growth gap evaluation**: what equipment, skills, or capabilities the entity is missing relative to its class doctrine
- **Conversion option generation and selection**: which of up to 10 typed options (EQUIP_ITEM, REPAIR_GEAR, SELL_LOOT, CRAFT_ITEM, ALLOCATE_AP, ASK_ITEM_USE, SAVE_FOR_LATER) best serves the entity this tick
- **Debug trace property**: `last_progression_decision` written to `entity.identity.properties`,
  stored as a plain JSON-serializable dict (`dataclasses.asdict(decision)`), never the raw
  `ProgressionDecisionResult` dataclass — `CanonicalStateHasher.to_canonical_json()`
  (`src/engine/checkpoint.py`) serializes `entity.identity.properties` via plain `json.dumps()`
  with no custom encoder, so a raw dataclass there crashes `Kernel`'s persistence phase (fixed by
  `TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH`; regression test:
  `tests/unit/domains/progression/test_progression_decision_canonical_hash.py`)

---

## What It Reads

From the entity under evaluation:

| Field | Purpose |
|---|---|
| `entity.identity.properties["reward_ledger"]` | Recent reward entries (XP/gold/items) — initialized to empty `RewardLedgerComponent` if absent |
| `entity.inventory` | Current items held, equipped gear, unspent AP |
| `entity.identity.level` | Current level (read; never written by this domain) |
| `entity.identity.unspent_ap` | Available ability points to spend |
| `entity.cognition.motivation.doctrine` | Class doctrine — used by `GrowthGapEvaluator` to assess what the entity should have |
| `entity.cognition.motivation.role_fit_preference` | Role preference — assessed via `RoleFitEvaluator` (motivation domain) |

From world state:

| Field | Purpose |
|---|---|
| `state` (general) | Context for option generation (available vendors, crafting stations, current tick) |
| Current project (via `entity.strategic`) | Informs what equipment is useful — gear aligned with active route families scores higher |

---

## The 6-Step Pipeline

`ProgressionConversionPhase.execute()` runs all six steps sequentially per entity:

### Step 1 — Possession Understanding (`PossessionUnderstandingService.evaluate`)

Evaluates the entity's current inventory and equipment state. Outputs a possession snapshot: what is equipped, what is unequipped, what is sellable loot, what is damaged. Materials needed for the entity's known recipes are identified via a `RecipeRegistry`-backed lookup (`src/core/registries.py::RecipeRegistry`, per TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE) rather than a fixed item list. `entity.identity.known_recipes` is populated in production via `BlacksmithSystem.enforce()`'s wholesale-learn step (`src/engine/blacksmith.py`), which as of that ticket reads the same `registries.py::RecipeRegistry` catalog this lookup and the live `REQUEST_CRAFT` crafting-execution path (`src/engine/intent/action_intent.py`) both read — so an organically-learned recipe id is genuinely reachable here. See `docs/parity_ledger/progression.yaml`'s `PROG-123` entry for status and test evidence.

### Step 2 — Growth Gap Evaluation (`GrowthGapEvaluator.evaluate`)

Compares the possession snapshot against class doctrine and role-fit preference. Identifies gaps: missing weapon type, underleveled armor, missing key skill, missing recipe material, unspent AP. The gap record prioritizes which conversion options are most relevant this tick.

### Step 3 — Reward Interpretation (`RewardInterpretationService.interpret`)

Parses the `RewardLedgerComponent` to surface actionable reward signals: unspent XP, unspent gold, unconsumed item rewards. Marks entries as consumed once processed. Returns an interpretation record consumed by option generation.

### Step 4 — Option Generation (`ConversionOptionGenerator.generate`)

Generates up to 10 scored `ConversionOption` records based on the interpretation and gap records. The full option type set:

| Option type | Condition |
|---|---|
| `EQUIP_ITEM` | Unequipped item present that fills a gap |
| `CRAFT_ITEM` | Crafting gap identified and materials available |
| `REPAIR_GEAR` | Equipped item is damaged below threshold |
| `SELL_LOOT` | Sellable loot present and gold gap exists |
| `ASK_ITEM_USE` | Usable consumable held and relevant need identified |
| `ALLOCATE_AP` | Unspent AP available and skill gap identified |
| `SAVE_FOR_LATER` | Default fallback — always generated at minimum score |

### Step 5 — Decision Selection (`ConversionDecisionService.select`)

Selects the highest-scoring `ConversionOption` from the generated list. `SAVE_FOR_LATER` is the guaranteed fallback if no higher-scoring option is generated.

### Step 6 — Intent Resolution (`ConversionIntentResolver.resolve`)

Maps the selected `ConversionOption` to a typed `EntityUpdate`. The resolved update is merged with any existing entity update from prior phases. A debug trace property `last_progression_decision` is written for observability — as a plain dict (`asdict(decision)`), not the raw `ProgressionDecisionResult` dataclass, so it survives `CanonicalStateHasher`'s canonical-hash pass. Do not write the raw dataclass back into `property_updates` here; that reintroduces the `TypeError: Object of type ProgressionDecisionResult is not JSON serializable` crash fixed in `TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH`.

---

## Reward Ledger

`RewardLedgerComponent` is stored in `entity.identity.properties["reward_ledger"]`.

| Field | Value |
|---|---|
| Storage key | `entity.identity.properties["reward_ledger"]` |
| Max entries | 20 (oldest entries trimmed when exceeded) |
| Entry fields | `tick`, `kind` (xp/gold/item), `subject`, `quantity`, `source`, `consumed_by_plan` |
| Trimming | When >20 entries: `all_entries[-20:]` — newest 20 retained |

`RewardLedgerService` (in `ledger.py`) provides `record_entry()` and `mark_consumed()` — both return new immutable `RewardLedgerComponent` instances; the ledger itself is never mutated in place.

---

## What It May Mutate (Via Intent Only)

All mutations are expressed as typed updates inside `EntityUpdate`, never applied directly by the domain.

| Intent type | Effect |
|---|---|
| `EquipmentUpdate` | Equip or unequip an item from inventory |
| `TaskUpdate` | Queue a craft or repair task |
| `ResourceTransferIntent` | Sell or trade items for gold |
| `IdentityUpdate(unspent_ap_delta=-1)` | Spend one AP toward a skill or stat |

The `StateUpdate` returned by `execute()` carries these per-entity updates for authoritative application downstream.

---

## What It Must NOT Mutate

- **Level**: `entity.identity.level` is read-only from this domain. Level increments belong to `src/progression/leveling.py` applied via the engine's authoritative apply path.
- **Derived stats**: HP, ATK, DEF, and other computed attributes. Stat recalculation runs inside `leveling.py` after level changes, not here.
- **Skill levels**: Skill unlock and advancement are owned by `src/progression/skills.py`.
- **World state**: regions, resource nodes, ecology.
- **Other entities**: no cross-entity writes.

---

## Progression Mechanics Reference: `src/progression/leveling.py`

For agents implementing or investigating level-up behaviour, the authoritative mechanics are:

| Mechanic | Value / Formula |
|---|---|
| XP threshold formula | `int(100 * level ** 1.5)` — VERIFIED v2: `xp_threshold_formula` |
| Level cap | 99 — VERIFIED v2: `level_cap_enforced` |
| AP granted per level | +5 unspent AP per level-up |
| Skill unlock thresholds | Levels 2, 5, 10 |
| Stat recalc order | 6-phase recalculation sequence inside `recalculate_combat_stats()` |
| DEF formula | `base_def + int(vitality × 0.3) + gear_def` |

`ProgressionConversionPhase` does NOT call `LevelingService` — it reads `entity.identity.level` as a reference value only. The authoritative level-up apply path is separate from domain phase execution.

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Motivation** | `GrowthGapEvaluator` calls `RoleFitEvaluator` (motivation domain) to assess equipment and skill fit against class doctrine; doctrine tags inform which gaps are prioritized |
| **Adventure** | The entity's current project (set by the adventure domain's Adventure Decision stage) informs which equipment and skills are relevant this tick — gear aligned with the active route family scores higher in option generation |
| **`src/progression/leveling.py`** | Authoritative level-up mechanics; runs separately via the engine apply path — this domain does NOT call it |
| **`src/progression/skills.py`** | Skill mechanics consumed when `ALLOCATE_AP` options reference skill targets |
| **`src/progression/breakthroughs.py`** | Breakthrough system — `apply_bonuses()` implemented and wired into `get_effective_stats()`; see `docs/mechanics/attribute_progression_contract.md` Breakthroughs section |

---

## Test Protection

Primary test targets:

```
grep -r "ProgressionConversionPhase\|ConversionOptionGenerator\|reward_ledger\|ConversionIntentResolver\|RewardLedgerService\|GrowthGapEvaluator" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| Entity with no reward_ledger → initializes to empty, no crash | Yes |
| Ledger trimming: >20 entries → newest 20 retained | Yes |
| SAVE_FOR_LATER always generated as minimum-score fallback | Yes |
| ALLOCATE_AP option: unspent AP consumed via IdentityUpdate delta=-1 | Yes |
| Inactive or dead entity → skipped, no update emitted | Yes |
| feature_flag = False → phase returns update unchanged | Yes |
| Possession understanding correctly identifies damaged gear | Yes |
| Level is never written by this domain (no IdentityUpdate.level field set) | Yes |

---

## Extension Rules

**To add a new conversion option type:**
1. Add the value to `ConversionKind` in `schema.py`.
2. Implement a scoring heuristic and generation condition in `ConversionOptionGenerator.generate()`.
3. Add an intent mapping case in `ConversionIntentResolver.resolve()`.
4. Add tests: generation condition, score ordering, intent output, SAVE_FOR_LATER still generated as fallback.

**To change level-up mechanics:**
Edit `src/progression/leveling.py` — not this domain. Update the parity ledger entry in `docs/parity_ledger/progression.yaml` in the same session.

**To add a new reward kind (beyond xp/gold/item):**
Extend `RewardEntry.kind` in `schema.py`, update `RewardInterpretationService.interpret()` to handle it, update `RewardLedgerService.record_entry()` if new fields are needed, and add tests.

**Never add level-up logic to this domain.** The split between `src/domains/progression/` (decisions) and `src/progression/leveling.py` (mechanics) is load-bearing — it ensures level-up is applied once, atomically, via the authoritative path, not re-derived per phase.
