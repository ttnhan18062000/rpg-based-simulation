# AI System: The Cognitive Pipeline

The WorldLoop AI system uses a **Hybrid Architecture** combining **Utility AI** for high-level goal selection and a **State Machine (FSM)** for tactical execution. Following the AOA pivot, the AI is strictly stateless and side-effect-free during its decision cycle.

---

## 1. The 5-Phase Cognitive Pipeline

Every scheduled tick, the `AIBrain` executes an expanded cognitive cycle to bridge long-term strategy with tactical execution.

### Phase 0: Strategic Derivation [NEW]
- **Input**: `MindAspect.strategic` state.
- **Logic**: Process high-level **Projects** to derive the active **Objective**.
- **Locking**: If a project or objective is locked (hysteresis), this phase skip derivation to ensure continuity.
- **Updates**: Refreshes the `active_objective_id` in the strategic state.

### Phase 1: Sensory & Perception
- **Input**: Raw `Snapshot` and `Entity` state.
- **Selective Attention**: Filters visible entities based on "Saliency". Top slots are actively processed.
- **Updates**: Proposes a `PerceptionUpdate` for the `attention_pool`.

### Phase 2: Memory & Appraisal
- **Memory Decay**: Increments `stale_ticks` for entities no longer visible.
- **Emotional Appraisal**: Calculates `panic`, `stuck`, and `dread` based on current surroundings.
- **Updates**: Proposes `PerceptionUpdate` and `MindUpdate`.

### Phase 3: Deliberation (Goal Selection)
- **Strategic Alignment**: Utility scores are now biased by the **Active Objective** (1.5x - 2.0x weight).
- **Utility Scoring**: Candidates evaluated against `GoalScorer` registry.
- **Hysteresis**: Ensures smooth transitions by protecting the current goal unless a significantly better one appears.
- **Updates**: Proposes `MindUpdate` with target `AIState`.

### Phase 4: Output (Proposal)
- **State Handler**: The `StateHandler` (e.g. `CombatHandler`) generates concrete `ActionProposal`.
- **Strategic Persistence**: Handlers can now propose `StrategicUpdate` to mark objective progress.

---

## 2. Strategic Mind Structure

The `MindAspect` has been hardened to support authoritatively persistent goals:

*   **`strategic`**: (The Continuity Stratum)
    *   **Directives**: Canonical motives (Built-in or Quest-driven).
    *   **Projects**: Current long-term commitment (e.g. "Visit Blacksmith").
    *   **Objectives**: The tactical step (e.g. "Navigate to Shop").
*   **`decision`**: Real-time AI goal scores and tactical state.
*   **`perception`**: Threat table and subjective entity/terrain memory.
*   **`narrative`**: Chronological memory log of `InterpretedEvent` records.

---

## 3. Hierarchical Commitment Registry

Strategic reasoning is supported by a registry of projects:

| Project | Kind | Typical Initial Objective |
| :--- | :--- | :--- |
| **Survival** | CORE | `FLEE`, `REST`, or `RECOVER` |
| **Combat** | TACTICAL | `ENGAGE`, `HUNT`, or `BRACE` |
| **Logistics** | SERVICE | `RESTOCK`, `CRAFT`, or `SELL` |
| **Exploration** | WORLD | `EXPLORE_REGION` or `VISIT_POI` |

---

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
