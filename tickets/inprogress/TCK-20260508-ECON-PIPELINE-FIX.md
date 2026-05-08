# TCK-20260508-ECON-PIPELINE-FIX

## Title
Fixing RPG Pipeline Regression Failures (101 Fails)

## Status
INPROGRESS

## Request Summary
The user identified 101 regression failures after Phase E5 pipeline hardening. Investigation revealed that `IntentResult` tracking was missing, `WorldDynamicsSystem` was omitted from orchestration, and `InteractionSystem` channeling logic was decoupled incorrectly.

## Scope
- Record `IntentResult` in `ResourceTransactionSystem`.
- Restore `WorldDynamicsSystem` to `AuthoritativeApplyPipeline`.
- Fix `InteractionSystem` channeling reset logic.
- Audit and fix system method names in `pipeline.py`.

## Out of Scope
- Major architectural changes to systems themselves.
- Performance optimization of the pipeline.

## Acceptance Criteria
- 100% pass rate on `pytest tests -k "not (test_long_run_determinism.py or test_long_run_stability.py)"`.
- `EntityUpdate.intent_results` correctly populated for all resource transfers.
- Hazards, spawns, and decays correctly processed in every tick.

## Related Tickets
- None

## Related Docs
- `architecture.md`
- `AGENTS.md`

## Related Stored Artifacts
- `implementation_plan.md`

## Related Code Areas
- `src/engine/economy.py`
- `src/engine/pipeline.py`
- `src/engine/interaction.py`

## Assumptions / Open Questions
- None at this time.

## Implementation Notes
- `WorldDynamicsSystem` needs an `EntityGenerator`. This will be instantiated in the pipeline using the current state's `next_entity_id`.

## Test Summary
- Pending execution.

## Files Changed
- Pending changes.

## Completion Summary
- Pending completion.
