---
status: active
layer: combat
authority: P1
audience: developer
---

# Observability Rulebook (Milestone 7)

## 1. Overview
This rulebook defines the authoritative contract for structured runtime observability within the Combat and Movement Overhaul. It specifies the categories of "reasons" that the system must expose when an action is proposed, rejected, or modified.

## 2. Reason Categories

### A. Movement Reasons
| Category | ReasonCode | Metadata Fields | Description |
| :--- | :--- | :--- | :--- |
| **Advancing** | `ADVANCING` | `target: str` | Standard movement following a path. |
| **Occupancy** | `OCCUPANCY_VIOLATION` | `occupant_id: int` | Rejected: The target tile is already occupied. |
| **Pathing** | `NO_PATH` | `target: str` | Rejected/Rest: No valid route exists to the target. |
| **Yielding** | `YIELDING` | `blocker_id: int` | Waiting: Higher priority entity has right-of-way. |
| **Sidestepping** | `SIDESTEPPING` | - | Moving to a cardinal neighbor to avoid a temporary obstacle. |
| **Waiting** | `WAITING` | - | Stay put because the ideal next tile is blocked. |

### B. Combat Reasons
| Category | ReasonCode | Metadata Fields | Description |
| :--- | :--- | :--- | :--- |
| **Range** | `OUT_OF_RANGE` | `max_range: int` | Rejected: Entity is too far from target. |
| **Invalid Target** | `INVALID_TARGET` | - | Rejected: Target no longer exists or is dead. |
| **Interaction** | `INTERACTION_REJECTED`| `sub_reason: str` | Generic rejection from the interaction layer. |
| **Exhaustion** | `EXHAUSTED` | - | Action penalized or prevented due to low stamina. |

### C. Tactical AI Reasons
| Category | ReasonCode | Metadata Fields | Description |
| :--- | :--- | :--- | :--- |
| **Targeting** | `NO_TARGET` | - | AI state has no valid enemy to engage. |
| **Retreat** | `LOW_HP_RETREAT` | `hp_ratio: float` | Moving away from threat due to health threshold. |
| **Kiting** | `KITING` | `enemy_dist: float` | Ranged entity maintaining distance. |
| **Maintenance** | `MAINTAINING_DISTANCE`| - | Staying at current distance to continue firing. |
| **Spacing** | `SPACING` | `ally_id: int` | Moving to avoid stacking with other ranged allies. |

## 3. Implementation Contract
- **Authoritative**: REASONS must be derived from the same logic that makes the decision.
- **Structured**: Reasons should prefer machine-readable keys over free-form prose where possible.
- **Deterministic**: Given the same world state, the side-effect-free evaluator must produce the same reason.
- **Surfaced**: All reasons must be reachable via the `AIDecisionSchema` in the entity inspection API.
