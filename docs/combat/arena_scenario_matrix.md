---
status: historical
layer: combat
authority: P2
audience: developer
---

# Arena Scenario Matrix (Milestone 6)

This document defines the core scenarios used to validate the combat and movement overhaul.

## Core 1v1 Scenarios (Scout Group)

| ID | Name | Participant A | Participant B | Map | Expected Pattern |
| --- | --- | --- | --- | --- | --- |
| `1v1-01` | Melee Mirror | Lvl 1 Warrior | Lvl 1 Warrior | Open Field | ~50% Win Rate (Symmetry Check) |
| `1v1-02` | Kiting Check | Lvl 1 Ranger | Lvl 1 Warrior | Open Field | Ranger Win Rate > 70% |
| `1v1-03` | Cage Match | Lvl 1 Ranger | Lvl 1 Warrior | Tight Arena | Warrior Win Rate > 60% |
| `1v1-04` | AoE Blast | Lvl 1 Mage | Lvl 1 Warrior | Open Field | TBD (AoE scaling check) |

## Core 1vMany Scenarios (Swarm Group)

| ID | Name | Elite | Horde | Map | Expected Pattern |
| --- | --- | --- | --- | --- | --- |
| `1vm-01` | Elite Tank | Lvl 10 Tank | 5x Lvl 1 Goblins | Open Field | Elite survives > 80% |
| `1vm-02` | Ranged Swarm | Lvl 5 Warrior | 4x Lvl 1 Ranger Goblins | Restricted Space | Swarm Win Rate > 50% |

## Core Many-vs-Many Scenarios (Frontline Group)

| ID | Name | Faction A | Faction B | Map | Expected Pattern |
| --- | --- | --- | --- | --- | --- |
| `mvm-01` | Phalanx | 3x Melee, 2x Ranged | 5x Melee | Chokepoint | Mixed Group Win Rate > 70% |
| `mvm-02` | Open Skirmish | 5x Mixed | 5x Mixed | Open Field | Resolution under 2000 ticks |

## Scenario Detail Example: `1v1-02` (Kiting Check)
- **Primary Goal**: Ensure the movement model and kiting AI allow a faster ranged unit to successfully evade a slower melee unit in open space.
- **Stop Condition**: `Entity_Dead(A)` or `Entity_Dead(B)` or `Timeout(5000)`.
- **Validation**: If Win Rate < 70%, it suggests ranged kiting is failing (likely due to collision blocking or pathing stall).
