---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260326-NARRATIVE
artifact_type: investigation
tags: [narrative]
---

# Investigation: Narrative Memory System

## Current State

### Existing Memory Infrastructure
| Component | Location | What It Does |
|:---|:---|:---|
| `memory_log` | `mind.py:18` | `list[dict]` — stores `{tick, type, desc, impact}` entries |
| GLORY recording | `action_system.py:330` | Records kill events with +5 impact (+50 for bosses) |
| TRAUMA recording | `action_system.py:362` | Records ally death witness with -10 impact |
| GLORY reading | `calamity_evolution.py:35` | Sums GLORY impact for world boss evolution |
| `memory_locations` | `mind.py:38` | Region sentiment (-1 to +1) — already influences exploration |
| `grudges` | `mind.py:37` | Per-entity animosity — already influences targeting |

### What's Missing
1. **No SURVIVAL memories**: Entity nearly dies but survives — this should create a lasting impression.
2. **No DISCOVERY memories**: Entering a new region for the first time — should encourage exploration.
3. **Memory never influences goal scoring**: `MemoryModifier` doesn't exist. GLORY/TRAUMA are stored but only read by `calamity_evolution.py`.
4. **No memory decay**: `memory_log` grows unbounded. Over 50k ticks, this could be 1000s of entries.

## Design: 3 New Components

### Component 1: New Memory Event Types
- **SURVIVAL**: Recorded in `combat.py` when an entity survives a combat round with `hp_ratio < 0.2`.
  - Impact: -3.0 (traumatic but less than watching an ally die)
  - Only once per combat encounter (use a flag `last_survival_tick`)
- **DISCOVERY**: Recorded in `brain.py` or `action_system.py` when entity enters a region not in `memory_locations`.
  - Impact: +2.0 (mild positive)

### Component 2: MemoryModifier (GoalScorer Bias)
New `ScoreModifier` in `base.py`:
```python
class MemoryModifier(ScoreModifier):
    def modify(self, score, ctx):
        glory = ctx.actor.mind.total_glory()
        trauma = ctx.actor.mind.total_trauma()
        if score.goal == "combat":
            score.score *= 1 + glory / 100
        elif score.goal == "flee":
            score.score *= 1 + abs(trauma) / 100
        elif score.goal == "explore":
            discovery_count = sum(1 for m in ctx.actor.mind.memory_log if m["type"] == "DISCOVERY")
            score.score *= 1 + discovery_count / 20
```

### Component 3: Memory Decay
In `_memory_appraisal_phase` of `brain.py`:
- If `len(memory_log) > 50`, sort by `abs(impact)` and keep top 50.
- This naturally preserves the most significant memories.

## Risks
- **Performance**: `total_glory()` / `total_trauma()` iterate the list each tick. Mitigation: cache values in MindAspect, invalidate when memory_log changes.
  - Simpler approach: compute lazily but accept O(N) where N ≤ 50 (capped).
