# TCK-20260410-STRAT-REFACTOR: Strategic Consistency and Authoritative Closure

**Request Summary**: Execute [Improvement Phase 1] from `thinking_implementation_improvement.md`. Reconcile `StrategicUpdate` schema to support blockers, eliminate live-mutation shortcuts in `SocialStateApplicator` and `BeliefService`, and harden strategic snapshot isolation.

**Scope**:
- [MODIFY] `src/core/models/strategy.py`: Add canonical blockers.
- [MODIFY] `src/actions/base.py`: Add blocker operations to `StrategicUpdate`.
- [MODIFY] `src/ai/beliefs.py`: Functional refactor of `BeliefService`.
- [MODIFY] `src/core/logic/social_state_applicator.py`: Functional refactor of interpreted consequences.
- [MODIFY] `src/systems/gameplay/action_system.py`: Update authoritative application orchestration.
- [NEW] `tests/test_strategic_consistency.py`: AOA purity and snapshot isolation validation.

**Out of Scope**:
- Adding new strategic behaviors (e.g., party coordination).
- Improving strategic reasoning performance.

**Acceptance Criteria**:
- All strategic producers emit valid `StrategicUpdate` shapes (including blockers).
- No cognition paths directly mutate live strategic or belief state.
- `tests/test_strategic_consistency.py` passes with 100% success.
- Snapshot isolation for nested strategy structures is verified.

**Related Tickets**:
- TCK-20260410-PHASE-2-ALIGNMENT (Ref)
- TCK-20260410-PH5-STRATEGIC-CONSEQUENCES (Ref)

**Current Status**: DONE

## Implementation Summary
- **Schema Reconciliation**: Added `blockers_add_or_update` and `blockers_remove` to `StrategicUpdate`. Resolved Pydantic model definition issues via `model_rebuild` namespace enrichment.
- **Authoritative Refactor**:
    - Converted `BeliefService.decay_stale_beliefs` to return `PerceptionUpdate`.
    - Converted `SocialStateApplicator` to return batches of `IntentUpdate`.
    - Integrated these results into the `ActionSystem` orchestration loop.
- **Verification**: Implemented a new integration test suite `tests/test_strategic_consistency.py` which proves snapshot isolation and authoritative application integrity.

## Changed Files
- `src/core/models/strategy.py`
- `src/core/logic/social_state_applicator.py`
- `src/core/logic/turning_points.py`
- `src/systems/gameplay/action_system.py`
- `src/ai/brain.py`
- `src/actions/base.py`
- `tests/test_strategic_consistency.py`

**Tier:** standard
**Type:** chore
**Priority:** P1
