---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-GUARDRAILS
artifact_type: plan
tags: [lab, guardrails]
---

# Implementation Plan: Token, Time, and Storage Guardrails with E2E System Tests

We will harden the human-gated simulation workflows by implementing dynamic context budgets, resource/storage/time pre-flight guardrail checks, audit trail logging for all violations, and a full 13-stage E2E integration test suite.

## User Review Required

> [!IMPORTANT]
> **Dynamic Profile Limits:** In CI profiles, limit thresholds are set conservatively (max 20 runs, 5000 ticks, 100MB) to ensure pipelines remain fast and inexpensive.
> **Authoritative Pipeline Parity:** No workflow is allowed to auto-trigger another, preserving human authority and gates between every stage of execution.

## Proposed Changes

### Lab Agent Guardrails

#### [MODIFY] [context.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/context.py)
*   Update `ContextPackBuilder.build_generation_pack` and `build_investigation_pack` to accept and enforce the dynamic `context_budget` config.
*   Enforce a default constraint of `raw_logs_allowed: bool = False`. If False, any attempt to read/serialize raw logs (like `.jsonl` trace files) is strictly blocked and raises a `PermissionError` or returns a warning.

#### [MODIFY] [workflows.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/workflows.py)
*   **Context Budgets parsing**: Integrate the dynamic frontmatter loading via `WorkflowRegistry` in all workflow workflows (e.g. `GenerateSimulationSetupWorkflow`, `PrepareSimulationExecutionWorkflow`, `InvestigateSimulationResultWorkflow`).
*   **Resource Pre-Flight Estimation**: Integrate `LabBudgetGuardrails` in `PrepareSimulationExecutionWorkflow`.
    *   Parse `world.yaml` and `experiment.yaml` from `draft_specs/` using `safe_path_resolution`.
    *   Obtain estimates for: run count, total ticks, entity count, event volume, expected artifact size (MB), expected runtime.
    *   Create a structured `readiness_report.json` and a formatted `readiness_report.md` report inside `preparation/` stage directory.
    *   If check results block/warn, record a `guardrail_violation` event in `LabAuditTrail`.
*   **Analysis Depth Controls**: In `InvestigateSimulationResultWorkflow`, ensure `analysis_depth` constraints are strictly checked, and that deep analysis requires explicit confirmation parameters.

## Verification Plan

### Automated Tests
*   Run the new unit tests: `pytest tests/unit/lab_agent/test_agent_guardrails.py`
*   Run the new E2E integration tests: `pytest tests/integration/lab_agent/test_human_gated_agentic_lab_e2e.py`

### Manual Verification
*   Check that audit logs inside `audit_log.jsonl` record all file operations and guardrail checks correctly.
