# Ticket TCK-20260410-PH1-STG2-ASPECT-INTEGRATION
## Phase 1 Stage 2: Aspect Integration

### Tier
standard

## Type
chore

## Priority
P1
## Request Summary
Integration of the strategic domain into the entity's mind as a first-class aspect.

### Scope
- [x] Attached `StrategicState` to `MindAspect` in `src/core/aspects/mind.py`.
- [x] Updated model rebuilds and imports.
- [x] Ensured default factories correctly initialize empty strategic domain for all entities.

### Acceptance Criteria
- [x] Entities possess a `mind.strategic` field by default.
- [x] System remains backward compatible with existing AI logic.

### Status
DONE
