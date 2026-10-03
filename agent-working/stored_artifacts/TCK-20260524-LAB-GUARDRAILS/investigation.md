---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-GUARDRAILS
artifact_type: investigation
tags: [lab, guardrails]
---

# Investigation: Token, Time, and Storage Guardrails

## Context budget guardrails
The `ContextPackBuilder` constructs context packs for generation and investigation. To satisfy M104:
- Context budgets must be loaded dynamically from the workflow frontmatter contracts (parsed via `WorkflowRegistry`).
- If `context_budget` specifies:
  - `max_known_issues`: default to 10.
  - `max_previous_runs`: default to 5.
  - `max_evidence_packs`: default to 10 (or 3 for investigation).
  - `max_raw_windows`: default to 3.
  - `raw_logs_allowed`: default to false.
- In `ContextPackBuilder.build_investigation_pack`, we must enforce a complete ban on raw logs (e.g. `simulation_events.jsonl`) unless `raw_logs_allowed` is explicitly enabled. This is already partially true, but we will make it explicit and block any text extraction of raw log files.

## Time and Storage Estimation
- In `PrepareSimulationExecutionWorkflow`, before execution setup is finalized, we must estimate:
  - Run count: seeds count * repeat count.
  - Total ticks: run count * ticks.
  - Entity count: sum of counts from world spec.
  - Event volume: total ticks * expected entity count * observability multiplier.
  - Expected artifact size (MB): formula: `(entities * ticks * 0.0001) + (resources * ticks * 0.00005)`.
  - Retention cost / expected runtime.
- We must output a **readiness report** (`readiness_report.json` and `readiness_report.md` inside `preparation` stage directory) that incorporates these estimates.
- If the estimated run count, total ticks, or expected artifact size exceeds profile limits (e.g. CI limit of 20 runs, 5000 ticks, 100MB; local limit of 100 runs, 100000 ticks, 2000MB), we must trigger a guardrail warning or block.
- Violations (warnings/blocks) must be logged into `LabAuditTrail` inside the session's log file as a `blocked_action` or `guardrail_violation` event.

## Investigation Depth Options
- `light`: Only process top 3 issues.
- `standard`: Process top 10 issues.
- `deep`: Support deep analysis requiring explicit parameters or configuration, ensuring we still do not ingest full raw timelines unless authorized.

## E2E Integration Test Architecture
The integration test `tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py` must run a simulated loop covering:
1. `GenerateSimulationSetup` (produces drafts, runs duplication checks).
2. Manually register approval.
3. `PrepareSimulationExecution` (estimates budget, creates readiness report).
4. Simulate execution by writing miniature run reports, summary files, and simulated logs in a mock `lab_runs/` directory.
5. `RegisterSimulationResult` (ingests files, validates checksums).
6. `CompactSimulationData` (prunes raw event files, compresses metrics).
7. `InvestigateSimulationResult` (computes anomalies across depths).
8. `ProposeSimulationEnhancements` (generates patches).
9. Manually register approval.
10. `UpdateSimulationKnowledge` (synchronizes to knowledge store).
11. Assertions verifying the exact safety checkpoints and audit trail compliance throughout the chain.
