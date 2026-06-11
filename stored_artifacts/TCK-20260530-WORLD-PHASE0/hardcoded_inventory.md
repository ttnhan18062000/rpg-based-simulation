---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [world, phase0]
---

# Hardcoded Semantic Assumptions Inventory

This document serves as an exhaustive semantic inventory of hardcoded assumptions currently embedded within `src/` as compiled in RPG-Based Simulation Phase 0.

---

## 1. Worldbuilding Compiler & Recipe Mapping

### 1.1 Faction Enum Mapper
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L43-L52)
- **Function/Class**: `get_faction_enum`
- **Current Behavior**: Compares the capitalized input string against `"HERO"`, `"GUILD"`, `"VILLAGE"`, `"MONSTER"`, `"HORDE"`, `"HOSTILE"`, `"COUNCIL"`, `"TOWN"`. Maps them hardcoded to `Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, `Faction.TOWN_COUNCIL`, with a default fallback to `Faction.NEUTRAL`.
- **Why Hardcoded**: Bootstrapping initial specifications string-to-enum mappers.
- **Migration Target**: Catalog-backed `src/content_semantics` matching schema ids to `legacy_engine_bucket`.
- **Risk Level**: High (direct schema breakage if faction names change).
- **Blocking Phase**: Blocks Phase 2 and Phase 5.

### 1.2 EntityRole Enum Mapper
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L25-L40)
- **Function/Class**: `get_role_enum`
- **Current Behavior**: Scans role string for keywords: `"HERO"` -> `EntityRole.HERO`, `"SHOP"`/`"STORE"` -> `EntityRole.SHOPKEEPER`, `"MONSTER"` -> `EntityRole.MONSTER`, `"CITIZEN"`/`"CIVILIAN"` -> `EntityRole.CITIZEN`, `"WORKER"`/`"PEASANT"` -> `EntityRole.WORKER`, `"GUARD"` -> `EntityRole.GUARD`. Fallback to `EntityRole.CITIZEN`.
- **Why Hardcoded**: Bootstrapping roles from text specs.
- **Migration Target**: Catalog-backed `src/content_semantics` resolving from `RoleDefinition.legacy_engine_role`.
- **Risk Level**: High (rigid string containment matching).
- **Blocking Phase**: Blocks Phase 2 and Phase 5.

### 1.3 Entity Defaults (HP, Attack, Readiness)
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L213-L220)
- **Function/Class**: `WorldCompiler.compile` (entity compilation loop)
- **Current Behavior**:
  - `hp` / `max_hp` = `100`
  - `atk` = `10`
  - `attack_range` = `1`
  - `readiness` = `100.0`
- **Why Hardcoded**: Hardcoded initial stats before recipe profiles were available.
- **Migration Target**: Resolved via `CompileProfileResolver` checking explicit recipe `stats_profile` or role defaults.
- **Risk Level**: Medium.
- **Blocking Phase**: Blocks Phase 3.

### 1.4 Faction Starting Vault Gold Defaults
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L136-L143)
- **Function/Class**: `WorldCompiler.compile` (faction compilation loop)
- **Current Behavior**: Hardcodes starting gold value `1000.0` inside `global_resources` for `Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, `Faction.TOWN_COUNCIL` or any custom dynamic faction identifier.
- **Why Hardcoded**: Basic initialization configuration.
- **Migration Target**: Resolved via `CompileProfileResolver` mapping faction catalog starting gold definitions.
- **Risk Level**: Low.
- **Blocking Phase**: Blocks Phase 3.

### 1.5 Resource Node Durability Default
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L163)
- **Function/Class**: `WorldCompiler.compile` (resource compilation loop)
- **Current Behavior**: Sets `required_ticks = 10` for every spawned resource node.
- **Why Hardcoded**: Basic initialization configuration.
- **Migration Target**: Resolved via `CompileProfileResolver` checking catalog default resource tick cost.
- **Risk Level**: Low.
- **Blocking Phase**: Blocks Phase 3.

### 1.6 Building Integrity Defaults
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L184-L185)
- **Function/Class**: `WorldCompiler.compile` (building compilation loop)
- **Current Behavior**: Sets `hp = 500` and `max_hp = 500` for all buildings.
- **Why Hardcoded**: Standard building properties initialization.
- **Migration Target**: Resolved via `CompileProfileResolver` using default building properties catalog mapping.
- **Risk Level**: Low.
- **Blocking Phase**: Blocks Phase 3.

### 1.7 Region Faction Ownership Default
- **File Path**: [compiler.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/compiler.py#L128)
- **Function/Class**: `WorldCompiler.compile` (region compilation loop)
- **Current Behavior**: Assigns `owner_faction_id = Faction.HERO_GUILD` if region type is `"town"`, else `None`.
- **Why Hardcoded**: Basic gameplay rule mapping (towns belong to heroes).
- **Migration Target**: Default semantic rules mapping in `src/content_semantics`.
- **Risk Level**: Low.
- **Blocking Phase**: Blocks Phase 2/3.

### 1.8 Recipe dead fields
- **File Path**: [recipe.py](file:///home/vboxuser/Work/rpg-based-simulation/src/worldbuilding/recipe.py#L39-L41,L60)
- **Function/Class**: `PopulationRecipeSpec` / `BuildingRecipeSpec`
- **Current Behavior**: Declares fields `stats_profile`, `inventory_profile`, `cognition_profile`, `service_profile` but never resolves or compiles them (they are completely dead).
- **Why Hardcoded**: Placeholder stubs.
- **Migration Target**: Clean implementation consuming them through the new Phase 3 `CompileProfileResolver`.
- **Risk Level**: High (causes schema drift if they remain unused).
- **Blocking Phase**: Blocks Phase 3.

---

## 2. Runtime Simulation Direct Faction Dependencies

### 2.1 World Dynamics Regional Influence Faction Shifts
- **File Path**: [world_dynamics.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/world_dynamics.py#L74-L79)
- **Function/Class**: `WorldDynamicsSystem.resolve_dynamics`
- **Current Behavior**: Hardcodes direct comparisons:
  - If influence >= 100, assigns owner to `Faction.HERO_GUILD`.
  - If influence <= -100, assigns owner to `Faction.MONSTER_HORDE`.
- **Why Hardcoded**: Hardcoded core gameplay loops (Hero vs Monster territory shifts).
- **Migration Target**: Abstract through `src/content_semantics` faction hostiles/liberators query APIs.
- **Risk Level**: High.
- **Blocking Phase**: Blocks Phase 9 / Future runtime dynamic expansion.

### 2.2 Faction Influence Death Penalty/Bonus Evaluator
- **File Path**: [influence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/influence.py#L33-L40)
- **Function/Class**: `FactionInfluenceService.process_influence_shift`
- **Current Behavior**:
  - If dying entity's faction is `Faction.HERO_GUILD`, influence shifts negative.
  - If dying entity's faction is `Faction.MONSTER_HORDE`, influence shifts positive.
  - Otherwise ignored.
- **Why Hardcoded**: Simple binary faction struggle.
- **Migration Target**: Check faction category alignment (e.g. Hostile vs Defender) retrieved from the catalog semantics.
- **Risk Level**: High.
- **Blocking Phase**: Blocks Phase 9.

### 2.3 Environmental Aura of Despair Faction Protection
- **File Path**: [environment.py](file:///home/vboxuser/Work/rpg-based-simulation/src/world/environment.py#L70)
- **Function/Class**: `EnvironmentService.get_aura_multipliers`
- **Current Behavior**: Directly checks `if entity.identity.faction == Faction.HERO_GUILD` before checking nearby monster strongholds and applying the Aura of Despair debuff.
- **Why Hardcoded**: Mapped specifically to harm hero units.
- **Migration Target**: Abstract through a faction semantics check (e.g. check if faction has a specific defensive role or hostile alignment).
- **Risk Level**: Medium.
- **Blocking Phase**: Blocks Phase 9.
