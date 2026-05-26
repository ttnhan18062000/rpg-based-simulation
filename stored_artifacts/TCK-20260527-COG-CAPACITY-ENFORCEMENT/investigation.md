# Investigation — Capacity Enforcement

## Current Implementation Analysis
- Capacity limits for `leads` and `concerns` are currently enforced via `DetourSuggestionSystem.enforce_bandwidth()`.
- Trimming occurs during active strategic updates, but not on a standalone/unconditional cadence.
- Trimming of `projects` and `hypotheses` is not implemented in `enforce_bandwidth()`.
- Trimming is partially reactive, meaning a passive entity with stale excess state might bypass enforcement.

## Proposed Strategy
1. **Unconditional Enforcement Phase**: Create a `CapacityEnforcementPhase` inside `StrategicIntelligenceSystem.fused_strategic_pass()` that runs unconditionally on every strategic tick for all entities.
2. **Idempotence**: The trimming operation must be deterministic and stable:
   - Projects: Sort non-active projects, keep current active project at the top, and trim to `profile.max_active_projects`.
   - Leads: Sort by certainty descending, keeping the top N (`profile.max_leads`).
   - Concerns: Sort by urgency descending, keeping the top N (`profile.max_concerns`).
   - Hypotheses: Sort by confidence descending, keeping the top N (`profile.max_hypotheses`).
3. **Observability**: When trimming occurs, emit a clear log trace event capturing counts before and after, the dropped IDs, and the field trimmed.
