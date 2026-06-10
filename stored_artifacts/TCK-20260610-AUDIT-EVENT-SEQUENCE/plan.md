# Plan: TCK-20260610-AUDIT-EVENT-SEQUENCE

## Approach

1. Add `workflow_started`/`workflow_completed` to 4 workflows in `src/lab/workflows.py`:
   - GenerateSimulationSetupWorkflow — after initial session save
   - PrepareSimulationExecutionWorkflow — after session save; completed + manual_boundary_declared before final return
   - RegisterSimulationResultWorkflow — after session save; completed before final return
   - ProposeSimulationEnhancementsWorkflow — after manifest load; completed before final return

2. `manual_boundary_declared` emitted at end of PrepareSimulationExecution after `workflow_completed` — signals the human handoff point.

3. In `test_human_gated_agentic_lab_e2e.py`:
   - Make the approved `UpdateSimulationKnowledge` run unconditional (not gated on proposals_list)
   - Replace weak 4-line audit check with gap-tolerant 13-checkpoint ordered sequence scan

## Sequence (actual emit order)
1. workflow_started: GenerateSimulationSetup
2. workflow_completed: GenerateSimulationSetup
3. workflow_started: PrepareSimulationExecution
4. workflow_completed: PrepareSimulationExecution
5. manual_boundary_declared
6. workflow_started: RegisterSimulationResult
7. workflow_completed: RegisterSimulationResult
8. workflow_started: ProposeSimulationEnhancements
9. workflow_completed: ProposeSimulationEnhancements
10. workflow_started: UpdateSimulationKnowledge  (note: before approval_required, not after)
11. approval_required
12. approval_recorded
13. workflow_completed: UpdateSimulationKnowledge
