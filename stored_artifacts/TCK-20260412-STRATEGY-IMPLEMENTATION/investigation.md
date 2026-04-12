# Investigation Notes - TCK-20260412-STRATEGY-IMPLEMENTATION

## Problem Statement
Implement the Strategic Cognition Layer (Milestones 0-7) to provide multi-tick continuity and deterministic reasoning for entities.

## Findings

### 1. Lack of Strategic Stratum
- Entities were purely tactical, leading to "short-termism" where projects (e.g., getting food, traveling to town) were interrupted by minor tactical score changes.
- **Solution**: Implemented `StrategicState` as a persistent domain in `MindAspect`.

### 2. Determinism Drift
- Previous attempts at strategy relied on ephemeral flags that weren't captured in snapshots.
- **Solution**: Integrated all strategic updates into the `ActionSystem` authoritative application path.

### 3. Observability
- Testing "thinking" was difficult because brain states were private and opaque.
- **Solution**: Created `CognitionGraphExporter` to produce machine-readable snapshots of an entity's strategic reasoning.

## Conclusion
The architecture is now properly stratified into Tactical (next tick) and Strategic (multi-tick) layers. This satisfies the requirements for complex, narrative-driven entity behavior.
