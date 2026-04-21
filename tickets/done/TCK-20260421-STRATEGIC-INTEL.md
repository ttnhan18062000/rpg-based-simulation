# TCK-20260421-STRATEGIC-INTEL

## Title
Strategic Resource Intelligence and Blocker/Lead Recovery

## Status
INPROGRESS

## Request Summary
Recover the strategic feedback layer necessary for the RPG progression loop in V2. This involves emitting blockers (material/gold) and leads (hints) based on town and resource outcomes.

## Scope
- Define `StrategicComponent` in V2 state.
- Implement `BlockerState` and `LeadState` models.
- Implement `StrategicIntelligenceSystem` to generate blockers/leads.
- Integrate blockers into the progression loop (influencing entity targets).
- Add parity and contract tests for strategic outputs.

## Out of Scope
- Full project systems or long-horizon planning.
- Social AI or broad concern graphs.
- Reputation scaling (if not strictly needed for blockers).

## Acceptance Criteria
- Supported blockers (material/gold) are emitted explicitly.
- Supported hints/leads are emitted explicitly.
- Strategic outputs influence next-step behavior in the progression loop.
- 100% parity with V1 for supported strategic cases.
- All new systems are hardened with contract tests.

## Related Tickets
- TCK-20260421-TOWN-RESOLUTION (Milestone 2)

## Related Docs
- `resource_phase5_implementation_milestone_3.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src_v2/core/strategic.py` (New)
- `src_v2/systems/strategic.py` (New)
- `src_v2/core/state.py`
- `src_v2/core/updates.py`
- `src_v2/engine/apply.py`

## Assumptions / Open Questions
- Should blockers live in `IdentityComponent` or a new `StrategicComponent`? (Assuming new component for modularity).
- How much of V1's `LeadRecord` complexity is needed? (Assuming simplified version for Phase 5).

## Implementation Notes
- Focus on material blockers from crafting failures.
- Focus on gold blockers from shop visits or lack thereof.

## Test Summary
- None yet.

## Files Changed
- None yet.

## Completion Summary
- None yet.
