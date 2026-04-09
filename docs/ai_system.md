# AI System: The Cognitive Pipeline

The WorldLoop AI system uses a **Hybrid Architecture** combining **Utility AI** for high-level goal selection and a **State Machine (FSM)** for tactical execution. Following the AOA pivot, the AI is strictly stateless and side-effect-free during its decision cycle.

---

## 1. The 4-Phase Cognitive Pipeline

Every time an entity is scheduled to act, the `AIBrain.decide()` method executes a structured four-phase pipeline:

### Phase 1: Sensory & Perception
- **Input**: Raw `Snapshot` and `Entity` state.
- **Selective Attention**: The brain filters all visible entities based on "Saliency" (Distance × Hostility × Tier). Only the top `max_attention_slots` (default 5) are actively processed.
- **Updates**: Proposes a `PerceptionUpdate` to set the `attention_pool` and `pos_history`.

### Phase 2: Memory & Appraisal
- **Memory Decay**: Entities in memory that are no longer visible have their `stale_ticks` incremented. If they cross a threshold (15-30 ticks), they are forgotten.
- **Emotional Appraisal**: 
  - **Stuck Detection**: High `stuck` spike if position hasn't changed in 5 ticks.
  - **Region Dread**: Sentiment-based `panic` increase if current region has high trauma history.
  - **Survival appraisal**: `panic` increase if HP < flee threshold.
- **Updates**: Proposes `PerceptionUpdate` (memory changes) and `MindUpdate` (emotional shifts).

### Phase 3: Deliberation (Planning)
- **Utility Scoring**: Each registered `GoalScorer` (Combat, Flee, Loot, etc.) evaluates the current context and returns a score (0.0 - 1.0+).
- **Boredom/Hysteresis**: 
  - Recent goals receive a **Boredom Multiplier** (0.8x) to prevent repetitive loops.
  - The current active goal receives a **1.25x Hysteresis boost** to prevent "state-shivering" between equally scored options.
- **Selection**: A temperature-controlled **Softmax** picks the winning goal from the top 3 candidates.
- **Updates**: Proposes `MindUpdate` with new goal scores and the target `AIState`.

### Phase 4: Output (Proposal)
- **State Handler**: The `StateHandler` for the selected `AIState` (e.g., `CombatHandler`) generates a concrete `ActionProposal` (ATTACK, MOVE, etc.).
- **Tactical Hints**: The brain injects "Hints" (e.g., `skirmish=True` for ranged classes) into the context to flavor the handler's output.
- **Final Return**: Returns the `tuple[AIState, ActionProposal]` to the engine.

---

## 2. Nested Mind Structure

The `MindAspect` is decomposed into typed sub-models to ensure the API can reliably serve data for UI introspection.

- **`decision`**: Tracks `goal_scores`, `boredom_multipliers`, and `consecutive_idle_ticks`.
- **`perception`**: Stores `threat_table`, `entity_memory` (short-term), and `terrain_memory`.
- **`emotion`**: Real-time floats for `panic`, `stuck`, `bravery`, and long-term `mood`.
- **`navigation`**: Stores `cached_path` (A*) and `pos_history`.
- **`narrative`**: A `memory_log` of typed records (`CombatNarrative`, `LootNarrative`, `DiscoveryNarrative`).

---

## 3. Utility Goal Registry

| Goal | target_state | Primary Logic |
| :--- | :--- | :--- |
| **COMBAT** | HUNT | Proximity to highest threat/nearest enemy. |
| **FLEE** | FLEE | HP ratio < flee threshold (default 30%). |
| **LOOT** | LOOTING | Presence of ground loot within vision range. |
| **TRADE** | VISIT_SHOP | Bag > 80% full or has high-value gold pouches. |
| **REST** | RESTING_IN_TOWN | Low HP/Stamina + proximity to safe zone. |
| **CRAFT** | VISIT_BLACKSMITH | Has materials + gold for learned recipes. |
| **GUARD** | GUARD_CAMP | (Mobs only) Protector of home territory. |

---

## 4. State Handlers (Tactical Execution)

The FSM handlers implement the "How" for each state.

- **CombatHandler**: Handles skill selection (Melee vs. AoE vs. Kiting).
- **WanderHandler**: Implements frontier exploration and leash enforcement.
- **TownHandlers**: Orchestrate complex service interactions (Buying potions, upgrading equipment).
- **Navigation Logic**:
  - **Manhattan Dist ≤ 2**: Greedy movement for performance.
  - **Manhattan Dist > 2**: A* Pathfinding with terrain cost integration.

---

## 5. Statelessness & Side-Effects

**CRITICAL**: The `AIBrain` and all `StateHandler` objects must be **side-effect-free**. They must NOT:
1.  Mutate `actor` or `snapshot` fields.
2.  Perform direct I/O.
3.  Access global mutable state.

All desired changes must be expressed as `IntentUpdate` records within the returned `ActionProposal`. The `ActionSystem` resolution phase is the only place where these updates are actually applied to the world state.
