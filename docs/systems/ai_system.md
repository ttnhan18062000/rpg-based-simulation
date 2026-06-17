---
status: active
layer: systems
authority: P1
audience: developer
---

# AI System: The Cognitive Pipeline (v2)

Following the **Resource-Safe Engineering** model, the AI system is strictly decoupled from the authoritative world state. Deliberation occurs in background workers using read-only snapshots, and the results are returned as authoritative `ActionResults`.

---

## 1. The Cognitive Cycle

Every AI worker executes a single, deterministic cognitive cycle during the **PACKETIZATION** phase of the kernel. This cycle bridges long-term strategy with tactical execution.

### Strategic Appraisal
- **Input**: `MindAspect.strategic` state.
- **Logic**: Evaluates the current **Project** (e.g., "Clear Bandit Camp") to derive the active **Objective** (e.g., "Attack Leader").
- **Hysteresis**: Ensures goal continuity by protecting the current objective from low-impact fluctuations.

### Sensory Filtering & Perception
- **Input**: `WorkerPacket` and local viewport.
- **Selective Attention**: Filters the visible world into a prioritized "Attention Pool" based on **Saliency** (distance, threat level, faction).
- **Perception Update**: Proposes updates to the entity's subjective `perception` memory.

### Emotional Appraisal
- **Logic**: Derives real-time emotional states (`panic`, `bravery`, `dread`) from the attention pool and recent narrative memory.
- **Grudges**: Identifies "Nemeses" in the current viewport to bias targeting.

### Deliberation (Goal Scoring)
- **Input**: Utility AI Scorers + Personality Traits.
- **Scoring**: Candidates are evaluated against the `GoalRegistry`. Utility scores are heavily biased by the active **Strategic Objective**.
- **Pick**: Selection of the winning `AIState` (e.g., `HUNT`, `FLEE`, `GATHER`).

### Output (Action Proposal)
- **Logic**: The mapping of the chosen state to a concrete `ActionProposal` via the `StateHandler`.
- **Result Generation**: Produces a `WorkerResult` containing the tactical proposal and any proposed updates to the entity's mental state.

---

## 2. Strategic Mind Hierarchy

The `MindAspect` is the permanent authoritative store for an entity's strategic history:

*   **`strategic`**: Continuity layer. Stores `Directives` (motives), `Projects` (medium-term), and `Objectives` (immediate).
*   **`perception`**: Threat table and subjective terrain/entity memory.
*   **`emotion`**: Persistent grudges and emotional baseline.
*   **`narrative`**: Log of high-impact events (Trauma, Glory).

---

## 3. Stateless Execution Law

**CRITICAL**: All AI deliberation must be **Stateless and Side-Effect-Free**.
- Workers receive a `WorkerPacket` (a shallow-cloned view restricted to local context).
- Workers must NOT attempt to mutate any world reference.
- All intended changes must be expressed as a `WorkerResult`.

This law ensures that the simulation can be parallelized safely and that AI logic never accidentally leaks into the authoritative resolution phase.

---

## 4. Tactical Handlers

State handlers translate "Intent" into "Action":
- **CombatHandler**: Handles skill priority and kiting distance.
- **WanderHandler**: Manages frontier traversal and leashing.
- **RestockHandler**: Orchestrates town service visits based on economic need.

> [!TIP]
> Use the `Cognition Visualizer` (`tools/viz_strategy.html`) to audit hierarchical AI decisions in real-time.
