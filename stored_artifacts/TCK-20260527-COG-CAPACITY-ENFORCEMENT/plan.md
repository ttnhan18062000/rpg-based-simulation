# Implementation Plan — Capacity Enforcement

We will implement an unconditional capacity enforcement layer that regularly trims entity cognitive capacity limits (projects, leads, concerns, hypotheses) to ensure strict invariants are maintained.

## Proposed Changes

### Component: Strategic Systems

#### [MODIFY] [detour.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/detour.py)
- Enhance `DetourSuggestionSystem.enforce_bandwidth()` (or create `enforce_capacity()`) to handle trimming of `projects`, `leads`, `concerns`, and `hypotheses` unconditionally and return a unified `StrategicUpdate`.
- Sort projects by: current active project first, then remaining projects, and trim to `profile.max_active_projects`.
- Sort hypotheses by confidence descending and trim to `profile.max_hypotheses`.
- Ensure leads and concerns are trimmed strictly based on certainty and urgency.
- Emit a clear `CognitionCapacityTrimmed` trace/log event with trimmed fields, entity ID, counts before/after, and dropped IDs.

#### [MODIFY] [intelligence.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic_systems/intelligence.py)
- Wire `enforce_capacity()` into the unified `fused_strategic_pass()` so it runs unconditionally on every strategic tick for all entities.

## Verification Plan

### Automated Tests
- Create `tests/unit/strategic/test_capacity_enforcement.py` verifying:
  - Idempotency of repeated trims.
  - Active project preservation.
  - Preservation of highest-priority concerns/leads/hypotheses.
  - Verification that overloaded entities are trimmed even with no strategic updates.
