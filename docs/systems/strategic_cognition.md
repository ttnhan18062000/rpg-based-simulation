---
status: active
layer: systems
authority: P1
audience: developer
---

# Strategic Cognition: The Mind's Hierarchy

> [!NOTE]
> **Compliance Status**: This system is 90% certified. See the [Gap Analysis](../compliance/gap_analysis.md) for known issues regarding hardcoded interruption thresholds and missing sovereignty transitions.

The Strategic Cognition system provides the simulation with **Long-Term Continuity**. It ensures that entities don't just react to their immediate surroundings, but follow persistent, motive-driven "projects" across hundreds of ticks.

---

## 1. The Strategy Hierarchy

An entity's mind is structured in three layers of abstraction:

### A. Directives (Motives)
The highest level of abstraction. Directives represent the entity's core drives or global quests.
- **Example**: `Build Wealth`, `Protect Faction`, `Seek Vengeance`.
- **Function**: They serve as the "North Star" for project selection.

### B. Projects (Commitments)
Medium-term commitments with defined success and failure conditions.
- **Example**: `Visit Blacksmith`, `Clear Goblin Camp`, `Flee to Town`.
- **Function**: Projects maintain behavioral hysteresis. Once an entity starts a project, it is "locked" into that behavior until the project is completed, significantly interrupted, or timed out.

### C. Objectives (Tactical Tasks)
Concrete, world-space tasks derived from the active project.
- **Example**: `Navigate to (32, 10)`, `Engage Entity 55`, `Wait for Cooldown`.
- **Function**: Objectives are the interface between the Strategic mind and the Tactical AI Brain.

---

## 2. The Derivation Cycle

Strategic reasoning happens during the Cognitive Pipeline's **Strategic Derivation** stage:

1.  **Project Selection**: If no project is active, the brain evaluates available opportunities (from the `StrategicWorldIntegrationSystem`) and personal directives to pick a new Project.
2.  **Objective Derivation**: The active Project is passed to a `ProjectDerivationService` which analyzes the world state to pick the correct next `Objective`.
3.  **Hysteresis Locking**: Projects and Objectives can be **Locked**. A locked objective prevents the AI from "jittering" between goals even if a higher utility one momentarily appears (e.g., stopping a walk to a shop just to pick up a single gold coin).

---

## 3. Interruption & Reprioritization

Life in the simulation is dangerous. The strategy system supports graceful **Interruption**:

- **Emergency Interrupt**: High-priority concerns (like `Hero Near Death`) can interrupt the current project.
- **Suspension**: The old project is saved as `interrupted_project_id`.
- **Resumption**: Once the emergency is cleared (e.g., the hero heals), the strategy system can automatically resume the previous project, maintaining narrative continuity.

---

## 4. Observability: The Cognition Graph

To debug strategic reasoning, the engine exports **Cognition Graphs** (`cognition_e[id].json`):

*   **Nodes**: Represent Directives, Projects, Objectives, and Concerns.
*   **Edges**: Represent relationships like `pursuing`, `interrupted_by`, `has_objective`.

You can visualize these using the `tools/viz_strategy.html` utility to see a character's "Mind Map" in real-time.

---

## 5. Persistence & AOA Safety

Strategic state is stored in the `StrategicState` model within the `MindAspect`. To ensure determinism and AOA (Authoritative Observable Atomic) compliance:
- Mutations ONLY happen during the Cognitive Pipeline's **Resolution** stage, via the `ActionSystem`.
- High-level strategic choices are recorded in the `DecisionLog` for replayability.
- The `freeze()` mechanism ensures that strategic choices during a tick are isolated from other concurrent workers.

---

## 6. Structural Explainability: Decision Drivers

To prevent the AI from being a "black box," the strategy system surfaces **Decision Drivers**. These are explicit reasons for strategic shifts, committed authoritatively to the entity's state.

- **`recent_drivers`**: A list of `DecisionDriver` objects stored in the `StrategicState`.
- **Labels**: Standardized labels like `STRATEGIC_SWITCH`, `STRATEGIC_RESUME`, `STRATEGIC_KEEP`.
- **Transparency**: Each driver includes a human-readable `description` and a `weight`, allowing the `AIPresenter` to explain exactly why a project was abandoned or resumed.
- **Traceability**: These drivers are visible in the API via the `StrategicStateSchema` and can be inspected in the UI to debug "jitter" or illogical project shifts.
