# TCK-20260413-STRAT-STRUCTURAL-SECURITY

## Title
Strategic Engine Hardening: Structural Integrity & Uncertainty Verification

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Remediate structural weaknesses in the strategic simulation engine to ensure byte-identical persistence, authoritative traceability, and anti-cheating uncertainty.

## Scope
- [x] Milestone 1: Strategic State Foundation (Snapshot isolation & Update merging)
- [x] Milestone 2: Strategic Appraisal (Traceability & Decision Drivers)
- [x] Milestone 3: Leads, Uncertainty, Blockers (Vague lead anti-cheating & exhaustion)

## Out of Scope
- Performance optimization (Targeted for later sub-projects)
- New strategic features (This is hardening/remediation)

## Acceptance Criteria
- Full snapshot -> world recovery yields identical strategic state.
- `StrategicUpdate` correctly merges identical IDs without record duplication or state jitter.
- `DecisionDriver` structured records are traceable from brain to entity state.
- Vague leads do not resolve exact coordinates until verified by discovery logic.
- Exhausted leads are strictly filtered from future appraisal.

## Related Tickets
- TCK-20260413-STRAT-INFRA-REMEDIATION (Completed)

## Related Docs
- docs/specs/2026-04-13-trust-boundary-remediation-design.md

## Related Code Areas
- `src/core/models/strategy.py`
- `src/core/models/snapshot.py`
- `src/systems/gameplay/action_system.py`
- `src/ai/brain.py`

## Assumptions / Open Questions
- None.

## Implementation Notes
- Hardened structural isolation between live state and decision snapshots.
- Standardized `StrategicUpdate` payload transport to prevent ID collisions.
- Resolved a Pydantic validation error in rumors ingestion.

## Test Summary
- New: `tests/integration/strategy/test_strategic_structural_integrity.py` (4 PASSED)
- Updated: `tests/integration/strategy/test_strategy_observability_consistency.py` (2 PASSED)
- Updated: `tests/integration/strategy/test_knowledge_continuity_stabilization.py` (3 PASSED)
- Full Suite: `pytest tests/integration/strategy/` (28 PASSED)

## Files Changed
- [TCK-20260413-STRAT-STRUCTURAL-SECURITY.md](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260413-STRAT-STRUCTURAL-SECURITY.md)
- [test_strategic_structural_integrity.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_strategic_structural_integrity.py)
- [test_strategy_observability_consistency.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_strategy_observability_consistency.py)
- [test_knowledge_continuity_stabilization.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_knowledge_continuity_stabilization.py)
- [strategic_knowledge_ingestion.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/strategic_knowledge_ingestion.py)

## Completion Summary
Sub-project 2 is complete. The strategic engine is now structurally secure against state corruption across snapshot boundaries and provides authoritative traceability for its reasoning. Lead uncertainty and anti-cheating mechanisms are fully verified.
