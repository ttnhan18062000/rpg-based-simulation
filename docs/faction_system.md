# Faction System

Technical documentation for the faction, territory intrusion, and status effect systems.

---

## Overview

Every entity in the simulation belongs to a **Faction**. Relationships between factions determine who is an enemy, ally, or neutral. Each faction can own a territory tile type, and entering hostile territory has consequences: stat debuffs and alerts to nearby defenders.

The system is **data-driven** — adding new factions, changing alliances, or adjusting territory debuffs requires only registry configuration, not code changes in AI, combat, or movement logic.

**Primary files**: `src/core/faction.py`, `src/core/effects.py`, `src/core/models.py`

---

## Faction Identity

Defined in `src/core/faction.py` as an `IntEnum`:

```python
class Faction(IntEnum):
    HERO_GUILD = 0
    GOBLIN_HORDE = 1
    # Future: UNDEAD = 2, BEAST = 3, BANDIT = 4, ...
```

Entities receive their faction at creation time via the `faction` field on `Entity`. The `FactionRegistry` maps entity `kind` strings to factions:

| Kind | Faction |
|------|---------|
| `hero` | HERO_GUILD |
| `goblin` | GOBLIN_HORDE |
| `goblin_scout` | GOBLIN_HORDE |
| `goblin_warrior` | GOBLIN_HORDE |
| `goblin_chief` | GOBLIN_HORDE |

---

## Faction Relations

Relations between factions are stored as `FactionRelation` values:

```python
class FactionRelation(IntEnum):
    ALLIED = 0     # Will not attack; may cooperate
    NEUTRAL = 1    # Ignore each other (unless provoked)
    HOSTILE = 2    # Attack on sight
```

### Default Relations

| Faction A | Faction B | Relation |
|-----------|-----------|----------|
| HERO_GUILD | GOBLIN_HORDE | HOSTILE |
| Same | Same | ALLIED (implicit) |

### Querying Relations

```python
reg = FactionRegistry.default()
reg.is_hostile(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)  # True
reg.is_allied(Faction.HERO_GUILD, Faction.HERO_GUILD)      # True
reg.relation(Faction.HERO_GUILD, Faction.GOBLIN_HORDE)     # FactionRelation.HOSTILE
```

---

## Territory System

Each faction owns a tile type via `TerritoryInfo`:

```python
@dataclass(frozen=True, slots=True)
class TerritoryInfo:
    tile: Material          # The Material that is this faction's territory
    atk_debuff: float       # Multiplier applied to intruder ATK (e.g. 0.7 = 30% reduction)
    def_debuff: float       # Multiplier applied to intruder DEF
    spd_debuff: float       # Multiplier applied to intruder SPD
    alert_radius: int       # How far the intrusion alert propagates
```

### Default Territories

| Faction | Tile | ATK Debuff | DEF Debuff | SPD Debuff | Alert Radius |
|---------|------|-----------|-----------|-----------|-------------|
| HERO_GUILD | TOWN | 0.6× | 0.6× | 0.8× | 6 |
| GOBLIN_HORDE | CAMP | 0.7× | 0.7× | 0.85× | 6 |

### Territory Queries

```python
reg.owns_tile(Faction.HERO_GUILD, Material.TOWN)        # True
reg.tile_owner(Material.CAMP)                             # Faction.GOBLIN_HORDE
reg.is_home_territory(Faction.HERO_GUILD, Material.TOWN) # True
reg.is_enemy_territory(Faction.HERO_GUILD, Material.CAMP) # True
```

---

## Territory Intrusion

When an entity steps on a hostile faction's territory tile, the `WorldLoop._process_territory_effects()` method triggers two consequences:

### 1. Stat Debuff

A `StatusEffect` of type `TERRITORY_DEBUFF` is applied to the intruder:

- ATK, DEF, SPD are multiplied by the territory's debuff values
- The debuff is **refreshed** every tick while the entity remains on hostile territory
- The debuff is **removed immediately** when the entity leaves hostile territory
- Duration is configurable via `SimulationConfig.territory_debuff_duration` (default: 3 ticks)

Debuffs flow through `Entity.effective_atk()`, `effective_def()`, `effective_spd()` automatically. Combat and movement code requires zero special-case logic.

### 2. Alert Propagation

All same-faction defenders within the territory's `alert_radius` of the intruder are switched to `AIState.ALERT`:

- Only affects entities not already in `COMBAT`, `HUNT`, `ALERT`, or `FLEE` states
- The `AlertHandler` in `ai/states.py` causes alerted entities to seek and engage the intruder
- If no enemy is visible after the alert, defenders return to `GUARD_CAMP` or retreat home

### 3. Town Aura

The TOWN territory has an additional mechanic: **aura damage**. Hostile entities standing on TOWN tiles lose `town_aura_damage` (default: 2) HP every tick, applied in `WorldLoop._heal_home_entities()`.

This prevents enemies from camping the hero's respawn point. Enemies can still enter town to fight a weakened hero, but the steady HP drain forces them to retreat before long. The AI responds to this pressure:

- **WanderHandler**: enemies in town retreat when below 60% HP or no target visible
- **HuntHandler**: enemies abort hunts in town at 60% HP
- **CombatHandler**: enemies disengage from combat in town at 50% HP (higher than normal 30% flee threshold)

### 4. Town Passive Heal

Heroes in town regenerate `town_passive_heal` (default: 1) HP per tick even when **not** in `RESTING_IN_TOWN` state (e.g. while wandering, hunting, or in combat stance). This heal is **blocked when an adjacent hostile entity is in melee range**, so enemies can still pressure a low-HP hero — they just can't prevent all healing indefinitely.

Heroes in `RESTING_IN_TOWN` state heal at the faster `hero_heal_per_tick` (default: 3) rate, also blocked by adjacent hostiles.

### Movement Rules

Territory tiles (TOWN, CAMP) are **passable for all factions**. The old hardcoded restrictions (heroes blocked from camps, goblins blocked from towns) have been removed. The consequence of trespassing is debuffs, aura damage, and combat, not movement blocking.

---

## Status Effect System

Defined in `src/core/effects.py`, `StatusEffect` is a generic system for temporary stat modifiers.

### StatusEffect Fields

| Field | Type | Description |
|-------|------|-------------|
| `effect_type` | EffectType | Category (TERRITORY_DEBUFF, POISON, etc.) |
| `remaining_ticks` | int | Duration; 0 = permanent until removed |
| `source` | str | Human-readable origin (e.g. "goblin_horde_territory") |
| `atk_mult` | float | ATK multiplier (1.0 = neutral) |
| `def_mult` | float | DEF multiplier |
| `spd_mult` | float | SPD multiplier |
| `crit_mult` | float | Crit rate multiplier |
| `evasion_mult` | float | Evasion multiplier |
| `hp_per_tick` | int | Flat HP change per tick (positive = regen, negative = DoT) |

### EffectType Enum

```python
class EffectType(IntEnum):
    TERRITORY_DEBUFF = 0    # Stat penalty for hostile territory
    TERRITORY_BUFF = 1      # Stat bonus for home territory
    POISON = 2              # DoT (future)
    BERSERK = 3             # ATK up, DEF down (future)
    SHIELD = 4              # Temporary DEF boost (future)
    HASTE = 5               # SPD boost (future)
    SLOW = 6                # SPD penalty (future)
```

### Factory Helpers

```python
from src.core.effects import territory_debuff, territory_buff

# Create a territory intrusion debuff
debuff = territory_debuff(atk_mult=0.7, def_mult=0.7, spd_mult=0.85, duration=3, source="camp")

# Create a home territory buff
buff = territory_buff(atk_mult=1.1, def_mult=1.1, duration=3, source="town")
```

### Effect Lifecycle

1. **Applied**: `WorldLoop._process_territory_effects()` adds/refreshes effects each tick
2. **Ticked**: `WorldLoop._tick_effects()` decrements `remaining_ticks` each tick
3. **Expired**: Effects with `remaining_ticks < 0` are pruned automatically
4. **Queried**: `Entity.effective_*()` methods aggregate all active effect multipliers

### Entity Integration

```python
entity.has_effect(EffectType.TERRITORY_DEBUFF)     # Check if debuffed
entity.remove_effects_by_type(EffectType.POISON)   # Remove all poison effects
entity._effect_mult("atk_mult")                     # Aggregate ATK multiplier from all effects
```

---

## AI Integration

### AIContext

All AI state handlers receive an `AIContext` dataclass that includes the `FactionRegistry`:

```python
@dataclass(slots=True)
class AIContext:
    actor: Entity
    snapshot: Snapshot
    config: SimulationConfig
    rng: DeterministicRNG
    faction_reg: FactionRegistry
```

### Faction-Aware Perception

`Perception` methods accept an optional `FactionRegistry` for faction-based enemy/ally detection:

```python
Perception.nearest_enemy(actor, visible, faction_reg)    # Returns closest hostile entity
Perception.nearest_ally(actor, visible, faction_reg)      # Returns closest allied entity
Perception.is_on_enemy_territory(actor, snapshot, reg)    # True if on hostile tile
Perception.is_on_home_territory(actor, snapshot, reg)     # True if on own faction's tile
```

### Class-Based State Handlers

State handlers are classes implementing `StateHandler.handle(ctx: AIContext)`, registered in `STATE_HANDLERS`:

```python
STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    AIState.FLEE: FleeHandler(),
    AIState.RETURN_TO_TOWN: ReturnToTownHandler(),
    AIState.RESTING_IN_TOWN: RestingInTownHandler(),
    AIState.RETURN_TO_CAMP: ReturnToCampHandler(),
    AIState.GUARD_CAMP: GuardCampHandler(),
    AIState.LOOTING: LootingHandler(),
    AIState.ALERT: AlertHandler(),
}
```

Adding a new state requires: (1) add to `AIState` enum, (2) create a handler class, (3) register in the dict.

### Goals & Territory Awareness

Entity goals (displayed in the Inspect Panel) now include territory context:
- "Trespassing on enemy territory — stat debuff active!"
- "Weakened by hostile territory"
- "Intruder detected! Engage the threat!"

---

## Extending the System

### Adding a New Faction

```python
# 1. Extend the enum
class Faction(IntEnum):
    HERO_GUILD = 0
    GOBLIN_HORDE = 1
    UNDEAD = 2          # NEW

# 2. Register in FactionRegistry.default()
reg.set_relation(Faction.UNDEAD, Faction.HERO_GUILD, FactionRelation.HOSTILE)
reg.set_relation(Faction.UNDEAD, Faction.GOBLIN_HORDE, FactionRelation.NEUTRAL)
reg.set_territory(Faction.UNDEAD, TerritoryInfo(
    tile=Material.GRAVEYARD,   # (would need new Material)
    atk_debuff=0.5,
    def_debuff=0.5,
    spd_debuff=0.7,
    alert_radius=8,
))
reg.register_kind("skeleton", Faction.UNDEAD)
reg.register_kind("lich", Faction.UNDEAD)
```

No changes to AI handlers, combat logic, or movement code.

### Adding a New Status Effect

```python
# 1. Add to EffectType enum
class EffectType(IntEnum):
    ...
    POISON = 2

# 2. Create a factory
def poison_effect(damage: int = 3, duration: int = 5) -> StatusEffect:
    return StatusEffect(
        effect_type=EffectType.POISON,
        remaining_ticks=duration,
        source="poison_attack",
        hp_per_tick=-damage,
    )

# 3. Apply in combat or ability code
entity.effects.append(poison_effect())
```

### Adding a New AI State

```python
# 1. Add to AIState enum
class AIState(IntEnum):
    ...
    PATROL = 11

# 2. Create handler class
class PatrolHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        # Custom patrol logic
        ...

# 3. Register
STATE_HANDLERS[AIState.PATROL] = PatrolHandler()
```

---

## Configuration

Territory-related settings in `SimulationConfig`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `territory_debuff_duration` | 3 | Ticks the debuff lasts after leaving hostile territory |
| `territory_alert_radius` | 6 | How far intrusion alert propagates to defenders |
| `town_aura_damage` | 2 | HP lost per tick by hostile entities on TOWN tiles |
| `town_passive_heal` | 1 | HP regained per tick by heroes in town (even outside rest) |
| `hero_heal_per_tick` | 3 | HP regained per tick by heroes in RESTING_IN_TOWN state |
| `sanctuary_radius` | 5 | Buffer zone radius around town center |

Territory-specific debuff multipliers are configured in `TerritoryInfo` within `FactionRegistry.default()`.
