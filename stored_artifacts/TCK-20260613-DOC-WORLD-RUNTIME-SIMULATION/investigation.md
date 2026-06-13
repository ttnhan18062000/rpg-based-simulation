# Investigation — TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION

Date: 2026-06-13
Status: Complete

---

## src/world/ Directory Listing

```
src/world/
├── boss.py
├── calamity.py
├── camp.py
├── consequences.py
├── ecology.py
├── environment.py
├── influence.py
├── motivation/
│   └── pressure_resolver.py
├── perception/
│   └── gate.py
├── providers/
│   ├── __init__.py
│   ├── information.py
│   ├── requirements.py
│   ├── resources.py
│   └── services.py
├── raid.py
├── region_threat_classifier.py
├── regional_sovereignty.py
├── regions.py
├── spawn.py
├── spawn_config.py
├── threat.py
└── transformation.py
```

All 5 investigation topics map to the expected file locations named in the ticket. No unexpected file locations found.

---

## Topic 1: Ecology and Calamity

### Ecology — `src/world/ecology.py`

Class: `ResourceEcologyService`

**What it does each tick:** runs only every `ECOLOGY_INTERVAL = 200` ticks. On a qualifying tick, it:
1. Counts existing resource nodes per region by querying `LegalityServiceV2.get_region_for_position()`.
2. Computes a target node count for each region: `target = int((area / 40_000) * (1 + region.stability))`, minimum 1.
3. If current count is below target, rolls a 50% seeding chance using the deterministic RNG (`Domain.SPAWN`).
4. On success, creates a `ResourceNodeState` at a random position within the region bounds. Node kind is determined by region biome: FOREST → WOOD, MOUNTAIN → IRON, others → STONE.
5. Returns a `StateUpdate(nodes_add=[...], next_node_id_set=...)`.

**No explicit depletion handling in ecology.py itself** — depleted nodes (remaining_charges → 0) are simply not counted in the cap and fall below threshold, naturally triggering re-seeding on the next ecology tick.

**No compliance ID header** in ecology.py — compliance IDs for ecology are embedded in calamity.py and the world_dynamics parity ledger.

### Calamity — `src/world/calamity.py`

Compliance IDs: `SUB-006, WORLD-023, WORLD-024, WORLD-025, WORLD-026, WORLD-027, WORLD-028, WORLD-063`

Class: `CalamityService`

**Constants:**
- `MATURITY_INTERVAL = 1000` ticks — maturity advances by 1 per interval
- `CALAMITY_MIN_INTERVAL = 2000` ticks — minimum gap between calamities
- `CALAMITY_RANDOM_CHANCE = 0.005` — defined but not currently wired (note: random chance path is present as a constant but the spawn check uses `CALAMITY_FORCE_INTERVAL` only)
- `CALAMITY_FORCE_INTERVAL = 5000` ticks — guaranteed spawn if min interval passed

**Calamity trigger logic (`process_world_dynamics`):**
1. If `tick % MATURITY_INTERVAL == 0 and tick > 0`: increment `state.maturity`.
2. If `tick - state.last_calamity_tick >= CALAMITY_MIN_INTERVAL` AND `tick % CALAMITY_FORCE_INTERVAL == 0 and tick > 0`: set `should_spawn = True`.
3. If `should_spawn`: find region with highest `calamity_intensity > 0.3`, spawn a `world_boss` of `difficulty_tier=4` at its center. Update `last_calamity_tick`.

**Calamity consequences (`apply_calamity_consequences`):**
- Called after entity deaths. If a hero dies in a region with `hazard_level > 0.5`, increases `calamity_intensity` by `+0.05` (capped at 1.0) via `WorldUpdate`.

**Key gap noted:** The `CALAMITY_RANDOM_CHANCE = 0.005` constant is defined but the random check path is not implemented in `process_world_dynamics` — only the forced interval path is active. This is a known partial implementation worth documenting.

**environment.py** (`EnvironmentService`) handles the runtime effect of calamity intensity:
- Hazard drain formula: `int(hazard_level * (1.0 + calamity_intensity) * 10.0)`
- `MIASMA` modifier multiplies drain by 1.5
- Weather effects: STORM/RAIN reduce perception; SNOW/BLIZZARD slow movement and increase stamina drain
- Stronghold aura: −30% move speed, −20% readiness regen for heroes within Manhattan distance < 12

---

## Topic 2: Threat and Consequences

### Threat — `src/world/threat.py`

Class: `ThreatService`

Two distinct threat axes tracked per region:
1. **`trauma_score`** — long-term danger score, decays slowly (`THREAT_DECAY_RATE = 0.01` per tick) only when the region is peaceful (no active world boss AND `retaliation_pressure < 5.0`)
2. **`retaliation_pressure`** — short-term combat pressure, always cools at `PRESSURE_COOLING_RATE = 0.1` per tick; increases by `+1.0` per monster kill via `record_kill()`

**Peaceful state definition:** no `world_boss` entity alive anywhere in the world AND region's `retaliation_pressure < 5.0`.

**Threat decay:** `trauma_delta = -0.01` per tick during peaceful state. Trauma can only decrease through natural decay or via consequence events (e.g., boss death: -20, camp clearing: -10).

### Region Threat Classifier — `src/world/region_threat_classifier.py`

Class: `RegionThreatClassifier`

This is a **read-only perspective-based classification service**, not a tick-level updater. It classifies a region's danger label from a faction's point of view using `RelationProjectionService`.

**Output labels:** `"safe" | "neutral" | "contested" | "threatened" | "hostile" | "unknown"`

**Classification path:**
1. If no faction data: returns `"unknown"`.
2. If entity has a perspective entry in catalog: uses `RelationProjectionService.project_relation()` for each controlling and population faction. Priority ladder: enemy → hostile; threat controller + enemy pop → hostile; threat controller alone → threatened; ally controller + enemy pop → contested; ally alone → safe.
3. Legacy fallback: bucket-based alignment check (MONSTER_HORDE = hostile, HERO_GUILD = safe, mixed = contested/neutral).

**This is consumed by entity navigation and goal scoring** — it is not a world-state mutator.

### Consequences — `src/world/consequences.py`

Compliance ID: `WORLD-006`

Class: `RegionalConsequenceService`

**`process_recovery()`** (called each tick):
- Local scars: severity decays by `scar.recovery_rate` per tick; scars below `0.01` severity are removed.
- Regional state: `trauma_score -= 0.0005` per tick (baseline recovery), `stability += 0.0001` per tick (baseline recovery). Both clamped.

**`create_battlefield_scar()`**: severity = `min(1.0, 0.2 + level * 0.02)`, recovery_rate = 0.0005.
**`create_raid_scar()`**: severity = 0.8, recovery_rate = 0.0002 (slower recovery for raid damage).

### Influence and Conquest — `src/world/influence.py`

Class: `FactionInfluenceService`

**Constants:**
- `DEATH_INFLUENCE_SHIFT = 5.0` — influence delta per kill
- `CONQUEST_THRESHOLD = -50.0` — influence level triggering monster conquest
- `LIBERATION_THRESHOLD = 50.0` — influence level triggering liberation

**Process:**
- Per recent death: if entity faction is "protector" (hero/town), influence shifts -5.0; if "invader" (monster), influence shifts +5.0. Influence clamped to [-100, +100].
- Conquest check: if no current owner and new_influence ≤ -50 → set owner to `MONSTER_HORDE`, spawn a stronghold entity at region center.
- Liberation check: if owner is monster faction and new_influence ≥ 50 → clear owner (sentinel -1), remove stronghold entity from region.

### Transformation — `src/world/transformation.py`

Class: `TransformationService`

Region type-shifts based on trauma_score and calamity_intensity thresholds. Evaluated deterministically via `get_potential_transformation()` and applied via `apply_transformation()`.

**Transformation table (degradation paths):**
- FOREST → BURNT_FOREST at trauma ≥ 50
- FOREST → WASTELAND at trauma ≥ 100 AND calamity_intensity ≥ 0.5
- PLAINS → DESERT at trauma ≥ 80
- PLAINS → WASTELAND at trauma ≥ 150
- MOUNTAIN → VOLCANIC at calamity_intensity ≥ 0.8
- MOUNTAIN → FROZEN_PEAKS if `FROST` modifier is active

**Recovery paths:**
- BURNT_FOREST → FOREST if trauma < 10
- DESERT → PLAINS if trauma < 20 AND stability > 0.5
- WASTELAND → PLAINS if trauma < 30 AND calamity_intensity < 0.1

**Selection rule:** when multiple transformations are eligible, the one with the most requirements (most complex) is chosen first.

---

## Topic 3: Raid Boss and Camp Systems

### Raid — `src/world/raid.py`

Compliance IDs: `WORLD-032, WORLD-033, WORLD-034`

Class: `RaidService`

**Constants:**
- `RAID_INTERVAL_DAYS = 5` (= 500 ticks at 100 ticks/day)
- `TICKS_PER_DAY = 100`
- `RAID_BASE_SIZE = 3`
- `SANCTUARY_RADIUS = 15`

**Trigger:** `tick % 500 == 0 and tick != 0`.

**Raid assembly:**
- Raid size = `RAID_BASE_SIZE + state.maturity` (scales with world age).
- Spawn position: deterministic RNG angle at distance `SANCTUARY_RADIUS + 10 = 25` from (0,0).
- Each raider is spawned as `"goblin_raider"` at `difficulty_tier=4` with navigation target forced to `(0,0)` (town center).
- Raiders are scattered in a 3×N grid around the base spawn point to avoid overlap.

**No explicit raid lifecycle/resolution tracking** — raids are a spawn event. Resolution is handled by combat system when raiders reach and engage the town.

### Boss — `src/world/boss.py`

Compliance IDs: `WORLD-035, WORLD-036, WORLD-037`

Class: `BossService`

**Spawn conditions (both must be true):**
- `state.maturity >= 50.0` (BOSS_SPAWN_THRESHOLD)
- `region.trauma_score >= 20.0`

**Idempotency guarantee:** at most one active living boss per "home region". Boss ownership is resolved via:
1. `identity.properties["boss_region_id"]` (set at spawn)
2. `strategic.home_region_id`
3. Fallback: current position region

**Boss entity properties:**
- Kind: `"world_boss"` (spawned as `"ancient_sentinel"` at `difficulty_tier=5`, then retyped)
- Properties: `boss_region_id`, `boss_spawn_tick` stored in `identity.properties`
- Inventory: one `ancient_core` item
- Town/sanctuary exclusion: if region center is within |cx| < 20 and |cy| < 20, spawn position is offset to ±25.

**Boss death resolution (`resolve_boss_death`):**
- Regional trauma reduced by -20.0 via WorldUpdate.
- High-tier loot and title/fame rewards are handled externally by LootSystem/QuestResolution (noted in code comments).

### Camp — `src/world/camp.py`

Compliance IDs: `WORLD-030, WORLD-031`

Class: `CampService`

**Constants:**
- `MATURITY_PER_TICK = 0.05`
- `RAID_MATURITY_THRESHOLD = 80.0`
- `CAMP_SPAWN_INTERVAL = 30` ticks

**Camp lifecycle:**
1. **Maturity growth:** +0.05/tick per active camp. Accelerated to ×1.5 if region trauma > 50.
2. **Monster spawn (every 30 ticks):** counts monsters within radius 10 of camp. Cap = `max(2, int(maturity / 10))`. Spawns one monster if below cap. Monster kind: `"goblin_warrior"` or `"orc_warrior"` based on camp kind. Difficulty tier = `int(maturity / 20) + 1`.
3. **Raid trigger:** when maturity ≥ 80 AND last raid was ≥ 500 ticks ago, triggers a raid and costs -20.0 maturity.

**Camp clearing (`resolve_camp_clearing`):**
- Sets camp `active = False`.
- Applies `trauma_delta = -10.0` to the containing region.

### Spawn — `src/world/spawn.py` and `src/world/spawn_config.py`

Class: `SpawnService`

**Spawn interval:** every `50` ticks.

**Density formula:** `target = max(2, int((area / 10_000) * BASE_MONSTER_DENSITY * (1.0 + hazard_level)))` where `BASE_MONSTER_DENSITY = 2.0`.

**Spawn pools (from spawn_config.py):**
- FOREST: `["goblin", "wolf", "bear"]`
- PLAINS: `["slime", "bandit"]`
- MOUNTAIN: `["harpy", "golem"]`

**Difficulty zones (distance from town center (0,0)):**
- ≤80: tier 1
- ≤150: tier 2
- ≤220: tier 3
- >220: tier 4

**Difficulty multipliers (from spawn_config.py):**
- Tier 1: HP×1.0, ATK×1.0, DEF×1.0, XP×1.0, gold×1.0, level 1–3
- Tier 2: HP×1.5, ATK×1.3, DEF×1.2, XP×1.5, gold×1.5, level 3–6
- Tier 3: HP×2.5, ATK×2.0, DEF×1.8, XP×3.0, gold×2.5, level 5–10
- Tier 4: HP×4.0, ATK×3.0, DEF×2.5, XP×5.0, gold×4.0, level 8–15

One monster is spawned per region per qualifying tick (not bulk fill). RNG domain: `Domain.SPAWN`.

---

## Topic 4: Opportunity Providers

### Provider Architecture

`src/world/providers/` contains four state-free provider classes that generate typed `Opportunity` objects. All providers share a `PerformanceBudgets` guard (max 500 total calls, budget tracked across `requirements.py`).

`Opportunity` (defined in `resources.py`):
```
id: str
kind: str  # "gather_resource" | "buy_item" | "craft_item" | "repair_gear" | "ask_information" | "rest_inn"
target_id: str
subject: str
estimated_reward: float
estimated_risk: float
requirements: Tuple[Requirement, ...]
confidence: float
```

### Provider 1: `ResourceOpportunityProvider` (resources.py)

Generates `"gather_resource"` opportunities from active resource nodes in the entity's current region. Filters by:
- Node has `remaining_charges > 0`
- Node's `res_def.source_region_tags` matches entity's region_id
- Reward boosted to 50.0 if resource matches an active material blocker (vs 10.0 base)
- Reward scaled by depletion: `reward *= (0.5 + 0.5 * remaining_charges/max_charges)`
- Requirements: `inventory_space(1)`, `near_service(region)`, `has_item(required_tool)` if tool needed
- Capped at top-5 by reward

### Provider 2: `ServiceOpportunityProvider` (services.py)

Generates service opportunities for town buildings. Affordance-based dispatch:
- `"craft"` affordance → `"craft_item"` opportunities per recipe in RecipeRegistry; reward 90.0 if active material blocker, else 30.0
- `"repair"` affordance + entity has equipment with durability < 50 → `"repair_gear"` at reward 80.0
- `"ask_info"` affordance + active material blocker → `"ask_information"` per blocker subject at reward 70.0
- `"buy"` affordance → `"buy_item"` (small_potion) at reward 40.0 if hp < 40, else 10.0
- `"rest"` affordance + sleep_debt > 40 or hunger > 40 → `"rest_inn"` at reward = sleep_debt value
- Capped at top-5 by reward

### Provider 3: `GuideInformationProvider` / `BlacksmithInformationProvider` / `GuildInformationProvider` (information.py)

These are query-response providers (not opportunity generators):
- `GuideInformationProvider.query()`: handles `"material_source"` queries. Special case: `"moon_resin"` returns a `APPROXIMATE` lead to `"north_ruin"` at certainty 0.55 (cost 10 gold). Normal resources looked up via ResourceRegistry.
- `BlacksmithInformationProvider.query()`: handles `"recipe_requirements"` queries via RecipeRegistry.
- `GuildInformationProvider.query()`: handles `"regional_danger"` queries (currently returns mock data: rating 2.0, enemy archetypes wolf/goblin).

### Provider 4: `RequirementEvaluator` (requirements.py)

Pure evaluator for `Requirement` objects. Supported kinds: `has_gold`, `has_item`, `inventory_space`, `knows_fact`, `near_service`, `target_alive`, `recipe_known`. Each returns a `RequirementResult(passed, blocker_kind, suggested_resolution_tags)`. Budget ceiling: 1000 evaluations per session.

### Perception Gate — `src/world/perception/gate.py`

Class: `PerceptionGate`

**Design:** read-only, deterministic, data-driven from catalog sense profiles. Used upstream of relation projection — gates raw detection capability only.

**Sense channels → target signals:**
- vision → visibility
- hearing → noise
- smell → scent
- magic_sense → magic_signal
- life_sense → life_signal
- vibration → vibration
- social_reading → social_signal

**Detection formula per channel:** `score = sense_strength * signal_strength * distance_factor * terrain_mod * (0.5 + alertness * 0.5)`. Channel contributes to detection if score ≥ 0.2 (`_PERCEPTION_THRESHOLD`).

**Distance factor:** `max(0.05, 1.0 - distance * 0.02)` (linear falloff, min 0.05).

**Profile resolution:** reads from `entity.identity.properties["sense_profile_id"]`. Falls back to `_BASELINE_SENSE` (vision=medium, hearing=medium, smell=low, magic_sense=none, social_reading=medium) if no profile.

**Output:** `PerceptionResult(perceived: bool, confidence: float, signals_used: List[str], profile_source: str)`.

### Motivation Pressure Resolver — `src/world/motivation/pressure_resolver.py`

Class: `MotivationPressureResolver`

**Design:** read-only, deterministic, data-driven from catalog `need_profile` and `drive_profile` definitions.

**Output:** `MotivationPressureSet` with 8 normalised pressures (0.0–1.0):
`hunger_pressure, safety_pressure, territory_pressure, duty_pressure, wealth_pressure, curiosity_pressure, aggression_pressure, purpose_pressure`

**Merge rule:** `max(need_value, drive_value)` per dimension, clamped to 1.0.

**Level mapping (shared with PerceptionGate):**
`very_high=1.0, high=0.9, medium_high=0.75, medium=0.6, low_medium=0.45, low=0.3, very_low=0.1, none=0.0`

**Source field:** `"need_and_drive_profile" | "need_profile_only" | "drive_profile_only" | "no_profile"`.

---

## Topic 5: Regional Sovereignty Runtime

### `src/world/regional_sovereignty.py`

Class: `RegionalSovereigntyService`

**This is the runtime sovereignty enforcement layer**, distinct from the worldbuilding declaration in `docs/mechanics/06_worldbuilding_foundation.md` and `docs/mechanics/regional_sovereignty.md`.

**Taxation (`process_taxation`):** every `TAX_INTERVAL = 100` ticks.
- Per owned region: heroes pay `TAX_RATE_ENTITY = 2.0` gold (deducted via `ResourceTransferIntent` tagged "TAX"). Functional buildings pay `TAX_RATE_BUILDING = 10.0` gold. Collected into faction gold resource key `faction_{owner_faction_id}_gold`.

**Sovereignty debuffs (`apply_sovereignty_debuffs`):**
- Applied to heroes in monster-owned regions. Intended effects: ATK×0.8, DEF×0.8, SPD×0.9 (constants `CONQUERED_ATK_DEF_MOD = 0.8`, `CONQUERED_SPD_MOD = 0.9`).
- **Implementation note:** the debuff application in `apply_sovereignty_debuffs` returns an `EntityUpdate` but does not currently populate any specific field — the code has a comment that the debuff must be handled by the combat system stat recalculation in the apply path. This is a known partial state.

**Border enforcement:** `regional_sovereignty.py` does not directly enforce movement blocking at borders. Entity routing checks `RegionThreatClassifier` labels before choosing destinations; combat encounters in hostile regions deter cross-region movement. No explicit "denied entry" gate exists in the current source.

### `src/world/regions.py`

Compliance IDs: `SUB-275 through SUB-279, WORLD-038, WORLD-041, WORLD-043, WORLD-052–059`

Class: `RegionService`

**`find_region_at(pos)`:** first tries exact bounds containment (`xmin ≤ px ≤ xmax and ymin ≤ py ≤ ymax`); falls back to nearest-center (Voronoi-like) if no bounds match. Compliance ID WORLD-056 confirms this behavior.

**`get_difficulty_tier_at(pos)`:** distance-based lookup into `DIFFICULTY_ZONES` from `spawn_config.py`.

---

## Compliance ID Cross-Reference

| File | Compliance IDs |
|---|---|
| calamity.py | SUB-006, WORLD-023–028, WORLD-063 |
| consequences.py | WORLD-006 |
| raid.py | WORLD-032, WORLD-033, WORLD-034 |
| boss.py | WORLD-035, WORLD-036, WORLD-037 |
| camp.py | WORLD-030, WORLD-031 |
| spawn_config.py | SOC-026–041, TOWN-072, TOWN-078, WORLD-042, WORLD-048, WORLD-049 |
| regions.py | SUB-275–279, WORLD-038, WORLD-041, WORLD-043, WORLD-052–059 |
| ecology.py | (no header — covered under WORLD-023 parent) |
| threat.py | (no header) |
| influence.py | (no header) |
| transformation.py | (no header — WORLD-062 in parity ledger) |
| environment.py | (no header — WORLD-029, WORLD-060, WORLD-061 in parity ledger) |
| regional_sovereignty.py | (no header) |

---

## Key Gaps / Implementation Notes for Doc Writers

1. **Ecology.py has no compliance ID header** — it is covered implicitly under calamity maturity tracking and the WORLD-023 parity entry. The doc should note ecology runs on Domain.SPAWN RNG.
2. **CALAMITY_RANDOM_CHANCE = 0.005** is defined but not wired in the current spawn trigger — only the forced interval path fires. Document the constants as-is; note the random path is inactive.
3. **Sovereignty debuff is declared but not fully wired** — the EntityUpdate from `apply_sovereignty_debuffs` does not yet populate debuff fields. The doc should accurately describe the intended behavior (ATK×0.8, DEF×0.8, SPD×0.9) and note the apply-path dependency.
4. **No explicit border gate** — sovereignty does not block movement at runtime; it operates through taxation and debuffs. Routing decisions that avoid hostile regions are made by the threat classifier (read-only). This should be clearly stated in the sovereignty runtime contract.
5. **Camp raid integration is partial** — `camp.py` calls `RaidService.check_for_raid()` at the camp threshold but does not redirect raiders to camp-origin positions (code comment says "For now, we just mark the last_raid_tick"). Document current behavior accurately.
6. **Information providers include mock data** — `GuildInformationProvider` returns hardcoded danger rating 2.0; this is a known Phase 1 stub.
