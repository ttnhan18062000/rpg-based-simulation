# TCK-20260408-FIXGROUPBIAS: Fix Group AI Integration Bias

- **Ticket ID**: TCK-20260408-FIXGROUPBIAS
- **Title**: Fix Group AI Integration Bias
- **Request summary**: Resolve failure in `test_brain_group_behavior_bias` where AI is not applying group coordination biases.
- **Scope**: Update integration test with appropriate entity distances; cleanup instrumentation code.
- **Out of scope**: Performance optimization of GroupSystem.
- **Acceptance criteria**:
    - `test_brain_group_behavior_bias` passes.
    - No debug print statements remain in production code.
- **Related tickets**: Phase 3 Stage 4 tasks in `phase_3_ds_implementation_plan.md`.
- **Status**: INPROGRESS

**Tier:** standard
**Type:** chore
**Priority:** P1
