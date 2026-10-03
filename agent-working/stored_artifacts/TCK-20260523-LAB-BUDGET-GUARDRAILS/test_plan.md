---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-BUDGET-GUARDRAILS
artifact_type: test_plan
tags: [lab, budget, guardrails]
---

# Test Plan - Resource, Storage, and Runtime Guardrails (Milestone 82)

We verify functionality at three levels:
1. **Unit Testing**: Direct estimation and check verification for both standard, high-run-count, high-ticks, and custom-budget scenarios.
2. **Integration / Lifecycle Testing**: Verifying `ScenarioLabOrchestrator` execution bounds:
   - Warnings raise `BudgetWarningError` when confirmation is missing.
   - Blocks raise `BudgetBlockedError` unless bypassed by `force` flag in local dev.
   - Bypasses are correctly logged as audit log events.
   - Blocked runs leave zero directories or manifest records.
   - Budget warnings are successfully saved to reports.
3. **CLI End-To-End Testing**: Confirming new `--profile`, `--force`, and `--confirm` parameters successfully propagate, and that budget exceptions output descriptive stdout/stderr details and exit with specific exit codes.
