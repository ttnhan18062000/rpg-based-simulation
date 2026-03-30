# Investigation - TCK-20260325-RPG_SIMULATION_REVIEW

## Current State Analysis

### 1. Pathfinding
- **File**: `src/ai/pathfinding.py`.
- **Logic**: Standard A* with a `max_nodes=200` budget.
- **Risk**: High CPU cost for long-range navigation.
- **Fix**: Dijkstra Maps (Flow Fields) for static targets.

### 2. Stamina & Combat
- **File**: `src/actions/combat.py`.
- **Logic**: Flat subtraction damage (`atk - def//2`).
- **Risk**: Zero-damage stalemates.
- **Fix**: Fractional Armor Mitigation `raw / (raw + def*2)`.
- **Exhaustion**: Currently missing debuffs when stamina hits 0.

### 3. Economy & Items
- **File**: `src/core/items.py`.
- **Logic**: Linear item power heuristic. No gold sinks beyond base purchases.
- **Fix**: Exponential enhancement scaling (+1 to +15) with material gates (Iron -> Dust -> Essence).

## Assistant's Independent Review Findings (Deeper Risks)

### 1. Attribute Depth & "Dump Stats"
- **CHA (Charisma)**: Currently underutilized. It should influence **Party Formation Speed** and **Familiarity Gain**. High CHA heroes should naturally acts as "Party Leaders".
- **PER (Perception)**: Should be linked to **Hidden Cache Discovery**. Vision alone is too passive.
- **Luck**: The current scale (0.002) is negligible. It should influence **Loot Rarity Roll** and **Rare Skill Procs** (Miracles).

### 2. The "Level 1 God" Problem (Attribute Scaling)
- **Risk**: Entities can train attributes indefinitely while staying at Level 1.
- **Fix**: Implement a **Soft Cap** where attributes cannot exceed `(Level * 5) + Base`. This forces entities to engage in high-risk leveling/combat to grow their potential.

### 3. Class-Blind Equipment
- **Risk**: `auto_equip_best` uses a generic power score. A Warrior might equip a high-MATK staff over a slightly lower raw-power sword.
- **Fix**: Weighting `_item_power` by `HeroClass` (e.g. Warriors value ATK 3x, Mages value MATK 3x).

### 4. Resting Tiers
- **Risk**: "Field Rest" (Camp Rations) making the Town Inn irrelevant.
- **Fix**: Implement a **Comfort Multiplier**. Town Inns should provide a `Well-Rested` buff (Max HP bonus) that Field Rests cannot provide.

### 5. Long-Term Cognition (Groundhog Day Effect)
- **Risk**: Utility AI is stateless; heroes often get stuck in optimal but repetitive loops (e.g. grinding the same 10 tiles forever).
- **Fix**: Introduce **Life Directives** (Long-term bias) and **Memory Fatigue** (Regional penalties) to force exploration and distinct life stories.

## Risks & Assumptions
- **Cognitive Overhead**: Adding a 7-step pipeline and Softmax selection must not exceed the 50ms tick budget for 1000+ entities.
- **Flow Fields**: Static caching must be invalidated if terrain changes (e.g. fire/ice magic).
- **Armor Math**: Requires retraining the AI to understand "diminishing returns" instead of "immunity".
- **QuadTree Memory**: Refactoring `terrain_memory` is critical to prevent OOM in long-running simulations.
