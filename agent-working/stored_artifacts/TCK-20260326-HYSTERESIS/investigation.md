---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260326-HYSTERESIS
artifact_type: investigation
tags: [hysteresis]
---

# Investigation: Goal Hysteresis & Anti-Oscillation

## Current Architecture

### Decision Flow
```
AIBrain.decide()
  ├─ Phase 1: Sensory/Perception → AIContext
  ├─ Phase 2: Memory/Appraisal → Emotion updates
  ├─ Phase 3: Deliberation → GoalEvaluator.evaluate() → select()
  └─ Phase 4: Finalization → StateHandler.handle() → ActionProposal
```

### Existing Anti-Oscillation Mechanisms
| Mechanism | Location | Effect | Strength |
|:---|:---|:---|:---|
| `HysteresisModifier` | `base.py:148` | 1.25x boost to current goal | Weak (25% easily overcome) |
| `BoredomModifier` | `base.py:96` | 0.8x penalty each selection | Moderate (punishes repeated goals) |
| `_DECISION_STATES` | `brain.py:57` | Skip re-eval in execution states | Strong but narrow scope |
| `FatigueModifier` | `base.py:211` | Region-based penalty | Anti-grind, not anti-oscillation |

### Root Cause: Score Boundary Crossings
When an entity is near a decision boundary (e.g., HP at 30%), competing goals produce nearly identical scores. The softmax selection then becomes a coin flip each tick.

**Example — Combat↔Flee at HP 29%:**
```
Tick N:   combat=0.45, flee=0.42  → Combat wins (hysteresis boosts it to 0.56)
HP drops to 28%:
Tick N+1: combat=0.35, flee=0.82  → Flee wins (panic +200% swing)
HP heals to 30% (potion):
Tick N+2: combat=0.50, flee=0.30  → Combat wins again
```

## Proposed Solution: 3-Layer Anti-Oscillation

### Layer 1: Minimum Commitment (Goal Lock)
- Track `goal_committed_at_tick` and `min_commitment_ticks` (default: 3).
- Entity cannot re-evaluate goals until `current_tick - goal_committed_at_tick >= min_commitment_ticks`.
- **Escape hatch**: Critical events (HP < 15%, enemy adjacent) can override the lock.

### Layer 2: Cooldown Penalty
- Track `goal_cooldowns: dict[str, int]` — maps goal name to tick when cooldown expires.
- When a goal is abandoned, apply a cooldown of `cooldown_ticks` (default: 5).
- During cooldown, the goal score is multiplied by 0.5 (halved).

### Layer 3: Threshold Deadbands
- Modify `FleeGoal.score()` to use different thresholds for entering vs exiting.
- Enter flee: HP < 30%. Exit flee (stop fleeing): HP > 50%.
- This prevents the "healing oscillation" where a single HP potion flips the decision.

## Risks & Assumptions
- **Responsiveness trade-off**: Minimum commitment could make entities feel "sluggish" if set too high.
  - Mitigation: Keep `min_commitment_ticks` low (3-5) and allow critical overrides.
- **Boredom interaction**: Boredom modifier already penalizes repeated goals. Cooldown penalty must not stack too aggressively.
  - Mitigation: Cooldown and boredom operate on different axes (time vs repetition).
