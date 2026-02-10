# Epic 03: Day/Night Cycle & Weather System

## Summary

Introduce a time-of-day cycle and dynamic weather that affect gameplay mechanics, AI behavior, visibility, and combat. The world gains a natural rhythm that drives entity behavior patterns and creates strategic variety.

Inspired by: Minecraft day/night mob spawning, Don't Starve survival pressure, Breath of the Wild weather effects, Dwarf Fortress seasonal cycles.

---

## Motivation

- The simulation currently has no concept of time beyond ticks — no day/night, no seasons
- Day/night creates natural activity cycles: explore by day, defend by night
- Weather adds environmental variety and strategic depth (rain reduces vision, storm boosts lightning damage)
- `Domain.WEATHER` already exists in the RNG enum but is unused
- Aligns with "realistic RPG simulation" — real worlds have day/night and weather

---

## Features

### F1: Day/Night Cycle
- Configurable tick-based cycle: e.g. 200 ticks = 1 full day (100 day + 100 night)
- `WorldState.time_of_day` enum: `DAWN`, `DAY`, `DUSK`, `NIGHT`
- Time exposed via API and displayed in the frontend header
- **Extensibility:** Time phases defined as data (`TimePhase` dataclass with duration, light_level, modifiers)

### F2: Visibility Effects
- **Day:** Full vision range
- **Night:** Vision range reduced by ~40% for all entities
- **Dawn/Dusk:** Gradual transition (vision range interpolated)
- PER attribute mitigates night vision penalty
- Certain traits (Keen-Eyed) reduce penalty further
- **Extensibility:** Vision modifiers defined per `TimePhase`, not hard-coded

### F3: Enemy Behavior Changes
- **Night:** Increased mob spawn rates, more aggressive behavior (lower flee thresholds)
- **Night:** Elite enemies more likely to roam outside their territory
- **Day:** Normal spawn rates, standard behavior
- Camp guards more alert at night (larger alert radius)
- **Extensibility:** Behavior modifiers attached to `TimePhase` data

### F4: Weather System
- Weather types: `CLEAR`, `RAIN`, `STORM`, `FOG`, `SANDSTORM` (desert only), `BLIZZARD` (mountain only)
- Weather changes periodically using `Domain.WEATHER` RNG
- Each weather type applies global or terrain-specific modifiers
- `WorldState.current_weather` tracked and exposed via API

### F5: Weather Effects

| Weather | Vision | Combat | Movement | Special |
|---------|--------|--------|----------|---------|
| Clear | Normal | Normal | Normal | — |
| Rain | -20% | -10% fire damage | -10% SPD on FLOOR | Extinguishes fire DoTs |
| Storm | -30% | +20% lightning damage | -15% SPD | Random lightning strikes (area damage) |
| Fog | -50% | Normal | Normal | Stealth bonus (+20% evasion) |
| Sandstorm | -40% (desert) | -15% accuracy | -20% SPD (desert) | Desert-only |
| Blizzard | -40% (mountain) | +20% ice damage | -25% SPD (mountain) | Mountain-only |

- **Extensibility:** `WeatherDef` dataclass with vision_mult, damage_mods, speed_mult, terrain_filter — new weather = new data

### F6: AI Weather Awareness
- Heroes consider weather when evaluating goals (avoid exploring in storms, prefer rest in bad weather)
- `WeatherBonus` trait modifiers — some traits thrive in bad weather (Resilient ignores SPD penalty)
- Enemies more/less active based on weather + time combination
- **Extensibility:** Weather influence on goal scoring via `WeatherUtilityBonus` typed dataclass

### F7: Frontend Visualization
- Canvas overlay tint changes with time of day (warm yellow → blue-dark → warm orange)
- Weather particles: rain drops, fog layer, storm flashes, sand particles
- Header shows current time phase icon + weather icon
- Minimap reflects lighting changes

---

## Design Principles

- Day/night and weather are properties of `WorldState`, not separate systems
- Effects flow through existing `StatusEffect` system or modifier multipliers
- All weather transitions deterministic via `Domain.WEATHER`
- Weather effects are data-driven — adding new weather = registering a `WeatherDef`
- No gameplay-breaking penalties — weather creates variety, not frustration

---

## Dependencies

- `Domain.WEATHER` (already exists in enums)
- Status effect system (already exists)
- Trait system for weather-related bonuses (already exists)
- Vision range system (already exists)

---

## Estimated Scope

- Backend: ~8 files new/modified
- Frontend: ~5 files modified (overlay, header, particles)
- Config: Time cycle length, weather transition frequency, effect magnitudes
