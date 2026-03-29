# Design Patterns & Extension Guide

Technical documentation for the OOP design patterns used in the simulation engine and how to extend each system.

---

## Overview

The engine uses five core patterns to maintain extensibility and the Open/Closed Principle. Each system can be extended by adding new classes and registering them — without modifying existing code.

---

## 1. Goal Evaluation — Plugin Pattern

**Location:** `src/ai/goals/`

### Pattern

Each AI goal is a self-contained `GoalScorer` subclass. The `GoalEvaluator` iterates all registered scorers without knowing their internals. New goals are added by creating a class and registering it — zero changes to existing code.

```
GoalScorer (ABC)
├── CombatGoal      → AIState.HUNT
├── FleeGoal        → AIState.FLEE
├── ExploreGoal     → AIState.WANDER
├── LootGoal        → AIState.LOOTING
├── TradeGoal       → AIState.VISIT_SHOP
├── RestGoal        → AIState.RESTING_IN_TOWN
├── CraftGoal       → AIState.VISIT_BLACKSMITH
├── SocialGoal      → AIState.VISIT_GUILD
└── GuardGoal       → AIState.GUARD_CAMP
```

### Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `GoalScorer` | `goals/base.py` | ABC: `name`, `target_state`, `score(ctx)` |
| `GoalScore` | `goals/base.py` | Dataclass: `(goal, score, target_state)` |
| `GoalEvaluator` | `goals/base.py` | `evaluate(ctx)` → sorted scores, `select(scores, rng)` → winner |
| `GOAL_REGISTRY` | `goals/base.py` | Module-level list of registered `GoalScorer` instances |
| `register_goal()` | `goals/base.py` | Append a scorer to the registry |

### How to Add a New Goal

1. Create a `GoalScorer` subclass:

```python
class QuestGoal(GoalScorer):
    @property
    def name(self) -> str:
        return "quest"

    @property
    def target_state(self) -> AIState:
        return AIState.QUEST  # add to enums.py first

    def score(self, ctx: AIContext) -> float:
        if not ctx.actor.active_quest:
            return 0.0
        return 0.6
```

2. Register in `goals/registry.py`:

```python
register_goal(QuestGoal())
```

3. Add a `StateHandler` in `ai/states.py` for the new state.

### Design Decisions

- **Classes over functions:** Allow properties (`name`, `target_state`), inheritance, and cached state across ticks.
- **Global registry:** Simple. For testing, clear and re-register. For mods, call `register_goal()`.

---

## 2. Damage Calculation — Strategy Pattern

**Location:** `src/actions/damage.py`

### Pattern

Each damage type is a `DamageCalculator` subclass that resolves ATK/DEF power, attribute multipliers, and training actions. Combat code calls `get_damage_calculator(damage_type)` and uses the returned `DamageContext` — no if/else branching.

```
DamageCalculator (ABC)
├── PhysicalDamageCalculator  (ATK vs DEF, STR/VIT scaling)
└── MagicalDamageCalculator   (MATK vs MDEF, SPI/WIS scaling)
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `DamageCalculator` | ABC: `damage_type`, `resolve(attacker, defender) -> DamageContext` |
| `DamageContext` | Dataclass: `atk_power`, `def_power`, `atk_mult`, `def_mult`, `train_action` |
| `DAMAGE_CALCULATORS` | Registry dict: `DamageType -> DamageCalculator` |
| `get_damage_calculator()` | Lookup with physical fallback |

### How to Add a New Damage Type

1. Add enum value in `src/core/enums.py`
2. Create a `DamageCalculator` subclass
3. Register: `DAMAGE_CALCULATORS[DamageType.TRUE] = TrueDamageCalculator()`

### Design Decisions

- **Classes over config dicts:** Classes can override complex logic (e.g., HYBRID damage splitting PHY/MAG).
- **`DamageContext` dataclass:** Decouples resolution from application. Combat code only sees the context.

---

## 3. Entity Construction — Builder Pattern

**Location:** `src/core/entity_builder.py`

### Pattern

The `EntityBuilder` provides a fluent API for constructing `Entity` instances. All spawn sites (hero, goblin, race-specific) use the same builder, eliminating code duplication.

### Usage

```python
hero = (
    EntityBuilder(rng, eid, tick=0)
    .kind("hero")
    .at(pos)
    .home(town_center)
    .faction(Faction.HERO_GUILD)
    .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3)
    .with_randomized_stats()
    .with_hero_class(HeroClass.WARRIOR)
    .with_race_skills("hero")
    .with_class_skills(HeroClass.WARRIOR, level=1)
    .with_inventory(max_slots=20, max_weight=100, weapon="iron_sword")
    .with_starting_items(["small_hp_potion"] * 3)
    .with_home_storage(max_slots=30)
    .with_traits(race_prefix="hero")
    .build()
)
```

### Key Methods

| Category | Methods |
|----------|---------|
| **Identity** | `kind()`, `at()`, `home()`, `ai_state()`, `faction()`, `tier()` |
| **Stats** | `with_base_stats()`, `with_randomized_stats()` |
| **Attributes** | `with_hero_class()`, `with_mob_attributes()`, `with_race_attributes()` |
| **Skills** | `with_race_skills()`, `with_class_skills()` |
| **Inventory** | `with_inventory()`, `with_existing_inventory()`, `with_equipment()`, `with_starting_items()` |
| **Storage** | `with_home_storage()` |
| **Traits** | `with_traits()` |
| **Build** | `build()` → `Entity` (calls `recalc_derived_stats`) |

### Design Decisions

- **Builder over Factory:** Handles combinatorial explosion of optional features without parameter explosion.
- **`with_existing_inventory()`:** Allows generator to build complex inventories externally while still using the builder for everything else.

---

## 4. Trait Aggregation — Typed Dataclasses

**Location:** `src/core/traits.py`

### Pattern

Trait aggregation uses **typed dataclasses** instead of `dict[str, float]` for type safety, autocomplete, and compile-time error detection.

| Dataclass | Purpose | Default Strategy |
|-----------|---------|-----------------|
| `UtilityBonus` | Additive modifiers for goal scoring | All fields start at `0.0` |
| `TraitStatModifiers` | Passive stat modifiers | Multipliers at `1.0`, additive at `0.0` |

### Usage

```python
bonus = aggregate_trait_utility(entity.traits)
score += bonus.combat  # typed access, IDE autocomplete

mods = aggregate_trait_stats(entity.traits)
effective_atk = base_atk * mods.atk_mult
```

### How to Add a New Trait Effect

1. Add the field to the appropriate dataclass
2. Update the aggregation function to sum the new field
3. Add the field to `TraitDef` and populate in trait definitions

---

## 5. AI State Machine — Strategy Pattern

**Location:** `src/ai/states.py`

### Pattern

Each AI state is a `StateHandler` subclass registered in `STATE_HANDLERS`. The `AIBrain` looks up the handler for the entity's current state and delegates execution.

```python
STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    # ... 18 total states
}
```

### How to Add a New AI State

1. Add the enum value in `src/core/enums.py`
2. Create a `StateHandler` subclass in `src/ai/states.py`
3. Register it in `STATE_HANDLERS`
4. (Optional) Create a `GoalScorer` that maps to the new state

---

## 6. Pattern Summary

| Pattern | Location | Open/Closed Principle |
|---------|----------|----------------------|
| **Plugin** (Goal Scorers) | `ai/goals/` | Add goal = add class + register. No existing code modified. |
| **Strategy** (Damage Calc) | `actions/damage.py` | Add damage type = add subclass + register. No if/else. |
| **Strategy** (State Handlers) | `ai/states.py` | Add AI state = add handler + register. |
| **Builder** (Entity) | `core/entity_builder.py` | Fluent API absorbs new features without parameter explosion. |
| **Typed Dataclass** (Traits) | `core/traits.py` | Type-safe aggregation. Add field = add to dataclass + aggregator. |

---

## 7. Metadata API — Shared Schemas

**Location:** `src/core/` (shared models), `src/api/routes/metadata.py` (endpoints), `frontend/src/types/metadata.ts`, `frontend/src/contexts/MetadataContext.tsx`

### Shared Pydantic Dataclasses (Single Source of Truth)

Core game definitions are **pydantic dataclasses** (`pydantic.dataclasses.dataclass`) used by both the engine and the API:

| Model | File | Used By |
|-------|------|---------|
| `ItemTemplate` | `core/items.py` | Game engine (IntEnum fields), API (serializes enums as strings) |
| `SkillDef` | `core/classes.py` | Game engine (skill execution), API (skill metadata) |
| `ClassDef` | `core/classes.py` | Game engine (class assignment), API (class views) |
| `BreakthroughDef` | `core/classes.py` | Game engine (promotion logic), API (breakthrough data) |
| `TraitDef` | `core/traits.py` | Game engine (trait effects), API (trait list) |

Enum fields use `Annotated[EnumType, PlainSerializer(...)]` so they remain IntEnums at runtime but serialize as lowercase strings (e.g., `ItemType.WEAPON` → `"weapon"`).

Mutable runtime types (`SkillInstance`, `TreasureChest`, `Building`, etc.) stay as stdlib `dataclass`.

### Endpoints

| Endpoint | Returns | Backend Source |
|----------|---------|---------------|
| `GET /metadata/enums` | Materials, AI states, tiers, rarities, item types, damage types, elements, entity roles, factions, entity kinds | `core/enums.py`, `core/faction.py` |
| `GET /metadata/items` | All item templates — serialized directly from core `ItemTemplate` | `core/items.py` → `ITEM_REGISTRY` |
| `GET /metadata/classes` | Class views, skills, breakthroughs, scaling grades, mastery tiers, race skills | `core/classes.py` |
| `GET /metadata/traits` | All trait defs — serialized directly from core `TraitDef` | `core/traits.py` → `TRAIT_DEFS` |
| `GET /metadata/attributes` | Attribute keys, labels, descriptions | Defined in route (9 core attributes) |
| `GET /metadata/buildings` | Building type names and descriptions | Defined in route |
| `GET /metadata/resources` | Resource node types per terrain | `core/resource_nodes.py` → `TERRAIN_RESOURCES` |
| `GET /metadata/recipes` | Crafting recipes with materials and output | `core/buildings.py` → `RECIPES` |

### Frontend Architecture

```
MetadataProvider (wraps App)
  └─ fetches all 8 endpoints in parallel on mount
  └─ builds derived lookup maps (itemMap, classMap, traitMap, etc.)
  └─ provides GameMetadata via React context

useMetadata() hook
  └─ used by InspectPanel, ClassHallPanel, BuildingPanel, LootPanel, etc.
  └─ returns typed GameMetadata with both raw data and lookup maps
```

### How to Add New Metadata

1. Define the pydantic dataclass in `src/core/` with `Annotated` serializers for any enum fields
2. Add a thin endpoint in `src/api/routes/metadata.py` that serializes via `TypeAdapter`
3. Add the TypeScript type in `frontend/src/types/metadata.ts`
4. Add the fetch call in `MetadataContext.tsx` and extend `GameMetadata`
5. Use `useMetadata()` in components that need the data

### Design Decisions

- **Shared schemas** — core pydantic dataclasses are the single source of truth for both engine and API
- **Annotated enum serializers** — `Annotated[ItemType, PlainSerializer(...)]` keeps IntEnum for game logic, strings for JSON
- **Colors stay in frontend** — visual presentation is a UI concern, not game data
- **Multiple small endpoints** — each endpoint is independently cacheable and focused
- **Derived lookup maps** — `itemMap`, `classMap`, `traitMap` etc. are built once on load for O(1) access

---

## 8. File Map (Refactored Modules)

```
src/
├── core/
│   ├── entity_builder.py     # Builder pattern — fluent Entity construction
│   ├── traits.py             # TraitDef, UtilityBonus, TraitStatModifiers
│   ├── classes.py            # ClassDef, SkillDef, BreakthroughDef, registries
│   ├── items.py              # ItemTemplate, ITEM_REGISTRY
│   ├── buildings.py          # Recipe, RECIPES, building logic
│   ├── resource_nodes.py     # TERRAIN_RESOURCES
│   ├── faction.py            # Faction enum, FactionRegistry
│   └── enums.py              # DamageType, Element, TraitType, AIState
├── api/
│   └── routes/
│       ├── metadata.py       # 8 metadata endpoints (Pydantic schemas + handlers)
│       └── __init__.py       # Router registration (includes metadata_router)
├── actions/
│   ├── combat.py             # CombatAction (uses DamageCalculator strategy)
│   └── damage.py             # DamageCalculator ABC + subclasses + registry
├── ai/
│   ├── brain.py              # AIBrain (hybrid: GoalEvaluator + StateHandler)
│   ├── goal_evaluator.py     # Backward-compat shim → ai/goals/
│   └── goals/
│       ├── __init__.py       # Package init, auto-registers all goals
│       ├── base.py           # GoalScorer ABC, GoalScore, GoalEvaluator, GOAL_REGISTRY
│       ├── scorers.py        # 9 built-in GoalScorer subclasses
│       └── registry.py       # register_all_goals() — idempotent registration
└── systems/
    └── generator.py          # EntityGenerator (uses EntityBuilder)

frontend/src/
├── types/
│   ├── api.ts                # Simulation state types (Entity, Building, etc.)
│   └── metadata.ts           # Metadata response types (GameMetadata, ClassEntry, etc.)
├── contexts/
│   └── MetadataContext.tsx    # MetadataProvider + useMetadata() hook
├── constants/
│   └── colors.ts             # Visual-only: tile/kind/state/rarity colors, CELL_SIZE
├── components/
│   ├── InspectPanel.tsx       # Entity inspector (uses useMetadata for items/classes/traits)
│   ├── ClassHallPanel.tsx     # Class browser (uses useMetadata for class/skill data)
│   ├── BuildingPanel.tsx      # Building details (uses useMetadata for items/recipes)
│   └── LootPanel.tsx          # Loot display (uses useMetadata for item info)
└── hooks/
    └── useCanvas.ts           # Canvas rendering (visual colors only)
```
