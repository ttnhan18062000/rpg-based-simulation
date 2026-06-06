# TCK-20260331-RUNTIME-INTEGRITY: Restore Runtime Integrity & AOA Convergence

## Description
This ticket addresses the first priority of the `final_implementation_plan.md`. It aims to eliminate legacy entity/mind/stats access patterns, enforce decision-phase purity in AI handlers, and wire the presenter layer into the API. This is critical for resolving the "split-brain" state of the codebase.

## Scope
- **Legacy Purge**: Remove all `.stats` and flat `.mind.ai_state` call sites across systems and AI.
- **AI Purity**: Refactor shop/crafting/interaction handlers to emit `ActionProposal` or deferred updates instead of direct mutation.
- **Inline Worker Fix**: Ensure `WorldLoop` uses snapshot entities for inline AI execution.
- **Presenter Integration**: Replace direct entity serialization in API routes with `EntityPresenter`.
- **Snapshot Hardening**: Implement basic immutability checks or documentation alignment.

## Acceptance Criteria
- [x] No occurrences of `.stats.` remain in `src/`.
- [x] No occurrences of `.mind.ai_state` remain in `src/`.
- [ ] `AIBrain.decide()` and its handlers do not mutate input entities.
- [ ] `GET /api/v1/state` and `/api/v1/stats` use `EntityPresenter`.
- [ ] All 748+ tests pass.
- [ ] Deterministic replay remains consistent.

## Related Tickets
- [TCK-20260330-CORE-STABILIZATION](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260330-CORE-STABILIZATION.md) (Superseded/Extended)

## Status
INPROGRESS

**Tier:** standard
**Type:** chore
**Priority:** P1
