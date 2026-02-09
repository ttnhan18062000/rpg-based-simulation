# Design Patterns & Extension Guide

This document describes the OOP design patterns used in the RPG simulation engine and how to extend each system.

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

1. Create a new `GoalScorer` subclass (in `goals/scorers.py` or a new file):

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
        return 0.6  # high priority when quest is active
```

2. Register it in `goals/registry.py`:

```python
from src.ai.goals.scorers import QuestGoal

def register_all_goals() -> None:
    # ... existing goals ...
    register_goal(QuestGoal())
```

3. Add the corresponding `StateHandler` in `ai/states.py` for `AIState.QUEST`.

### Design Decisions

- **Why not a dict of functions?** Classes allow properties (`name`, `target_state`), inheritance, and state (e.g., a goal could cache expensive calculations across ticks).
- **Why a global registry?** Simplicity. For testing, clear and re-register. For mods, just call `register_goal()`.

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

1. Add the enum value in `src/core/enums.py`:

```python
class DamageType:
    PHYSICAL = 0
    MAGICAL = 1
    TRUE = 2      # new: ignores defense
```

2. Create the calculator in `src/actions/damage.py`:

```python
class TrueDamageCalculator(DamageCalculator):
    @property
    def damage_type(self) -> int:
        return DamageType.TRUE

    def resolve(self, attacker, defender):
        return DamageContext(
            atk_power=attacker.effective_atk(),
            def_power=0,        # ignores defense
            atk_mult=1.0,
            def_mult=1.0,
            train_action="attack",
        )
```

3. Register it:

```python
DAMAGE_CALCULATORS[DamageType.TRUE] = TrueDamageCalculator()
```

### Design Decisions

- **Why not a config dict?** Classes can override complex logic (e.g., HYBRID damage that splits PHY/MAG). A flat config can't express that.
- **`DamageContext` dataclass**: Decouples resolution from application. Combat code only sees the context, not the calculator internals.

---

## 3. Entity Construction — Builder Pattern

**Location:** `src/core/entity_builder.py`

### Pattern

The `EntityBuilder` provides a fluent API for constructing `Entity` instances. All spawn sites (hero, goblin, race-specific) use the same builder, eliminating code duplication.

### Usage

```python
# Hero spawn
hero = (
    EntityBuilder(rng, eid, tick=0)
    .kind("hero")
    .at(pos)
    .home(town_center)
    .faction(Faction.HERO_GUILD)
    .with_base_stats(hp=50, atk=10, def_=3, spd=10)
    .with_randomized_stats()
    .with_hero_class(HeroClass.WARRIOR)
    .with_race_skills("hero")
    .with_class_skills(HeroClass.WARRIOR, level=1)
    .with_inventory(max_slots=20, weapon="iron_sword")
    .with_starting_items(["small_hp_potion"] * 3)
    .with_traits(race_prefix="hero")
    .build()
)

# Mob spawn (generator)
goblin = (
    EntityBuilder(rng, eid, tick=tick)
    .kind("goblin")
    .at(pos)
    .faction(Faction.GOBLIN_HORDE)
    .tier(tier)
    .with_base_stats(hp=base_hp, atk=base_atk, ...)
    .with_existing_inventory(pre_built_inv)
    .with_mob_attributes(attr_base, tier)
    .with_race_skills("goblin")
    .with_traits(race_prefix="goblin")
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
| **Traits** | `with_traits()` |
| **Build** | `build()` → `Entity` |

### How to Add a New Entity Type

1. Define its stats, attributes, and skills.
2. Chain the builder with the appropriate methods.
3. For complex inventory, build it externally and pass via `with_existing_inventory()`.

### Design Decisions

- **Why Builder over Factory?** The builder's fluent API handles the combinatorial explosion of optional features (class, skills, traits, inventory) without a parameter explosion.
- **`with_existing_inventory()`**: Allows the generator to build complex tier/race-specific inventories externally while still using the builder for everything else.

---

## 4. Trait Aggregation — Typed Dataclasses

**Location:** `src/core/traits.py`

### Pattern

Trait aggregation uses **typed dataclasses** instead of `dict[str, float]` for type safety, autocomplete, and compile-time error detection.

| Dataclass | Purpose | Default Strategy |
|-----------|---------|-----------------|
| `UtilityBonus` | Additive modifiers for goal scoring | All fields start at `0.0` |
| `TraitStatModifiers` | Passive stat modifiers | Multipliers start at `1.0`, additive at `0.0` |

### Usage

```python
from src.core.traits import aggregate_trait_utility, aggregate_trait_stats

# Typed access — IDE autocomplete works
bonus = aggregate_trait_utility(entity.traits)
score += bonus.combat  # not bonus.get("combat", 0.0)

mods = aggregate_trait_stats(entity.traits)
effective_atk = base_atk * mods.atk_mult  # not mods.get("atk_mult", 1.0)
```

### How to Add a New Trait Effect

1. Add the field to the appropriate dataclass:

```python
@dataclass(slots=True)
class UtilityBonus:
    # ... existing fields ...
    quest: float = 0.0  # new goal bonus
```

2. Update `aggregate_trait_utility()` to sum the new field.
3. Add the corresponding field to `TraitDef` and populate it in trait definitions.

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
    # ...
}
```

### How to Add a New AI State

1. Add the enum value in `src/core/enums.py`.
2. Create a `StateHandler` subclass in `src/ai/states.py`.
3. Register it in `STATE_HANDLERS`.
4. (Optional) Create a `GoalScorer` subclass that maps to the new state.

---

## 6. File Map (Refactored Modules)

```
src/
├── core/
│   ├── entity_builder.py     # Builder pattern — fluent Entity construction
│   ├── traits.py             # TraitDef, UtilityBonus, TraitStatModifiers
│   └── enums.py              # DamageType, Element, TraitType, AIState
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
```

---

## 7. Pattern Summary

| Pattern | Location | Open/Closed Principle |
|---------|----------|----------------------|
| **Plugin** (Goal Scorers) | `ai/goals/` | Add goal = add class + register. No existing code modified. |
| **Strategy** (Damage Calc) | `actions/damage.py` | Add damage type = add subclass + register. No if/else. |
| **Strategy** (State Handlers) | `ai/states.py` | Add AI state = add handler + register. |
| **Builder** (Entity) | `core/entity_builder.py` | Fluent API absorbs new entity features without parameter explosion. |
| **Typed Dataclass** (Traits) | `core/traits.py` | Type-safe aggregation. Add field = add to dataclass + aggregator. |
