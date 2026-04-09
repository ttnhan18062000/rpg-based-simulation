# Ticket TCK-20260410-PH1-STG5-BOOTSTRAPPING
## Phase 1 Stage 5: Bootstrapping

### Request Summary
Implementation of default strategic orientation seeding during entity generation.

### Scope
- [x] Implemented `_seed_strategic_state` in `src/core/entities/entity_builder.py`.
- [x] Added role-based and archetype-based directive seeding (e.g., GREEDY_SCAVENGER -> Build Wealth).
- [x] Ensured starting entities possess non-empty strategic orientations to drive initial behavior.

### Acceptance Criteria
- [x] Generated entities start with valid directives aligned with their identity.
- [x] No manual bootstrapping is required for basic strategic functionality.

### Status
DONE
