---
ticket_id: TCK-20260612-LAB-CONTRACT
phase: investigation
---

# Investigation: Lab Contract

## Compliance ID Map

| ID(s) | File | Description |
|---|---|---|
| SCENARIO-001, 002, 003 | src/lab/schema.py | Lab schemas (LabRunManifest, LabSessionManifest, ExperimentSpec, etc.) |
| SCENARIO-004, 005, 006 | src/lab/validator.py | Scenario/experiment validators (+ sub-rules SCENARIO-REF-001, SCENARIO-LIMIT-001, SCENARIO-SIGNAL-001, SCENARIO-ANOMALY-001) |
| SCENARIO-007, 008, 009 | src/lab/repository.py | ScenarioRepository, ExperimentRepository, LabRunRepository |
| SCENARIO-010 | src/lab/__init__.py | Module init contract |
| SCENARIO-012, 013, 014, 015 | src/lab/orchestrator.py | ScenarioLabOrchestrator workflow contract |
| METAMORPHIC-RULE-001, 002, 003 | src/lab/metamorphic.py | Metamorphic testing rules |
| MUTATION-ENGINE-001, 002, 003 | src/lab/mutation.py | Mutation engine contract |
| MUTATION-ORCHESTRATOR-001, 002, 003 | src/lab/mutation_orchestrator.py | Mutation orchestration contract |
| BALANCE-COMPARE-001, 002, 003 | src/lab/comparison.py | Balance comparison rules |

## Session Lifecycle
States: ACTIVE, WAITING_FOR_USER, COMPLETED, FAILED, ARCHIVED
Stages: GENERATION → EXECUTION_SUPPORT → REGISTRATION → INVESTIGATION → ENHANCEMENT → KNOWLEDGE_UPDATE
Approval gates per stage: PENDING → APPROVED | REJECTED (for generation, execution_support, enhancement)

## Guardrails
- BudgetBlockedError: hard block — run cannot proceed
- BudgetWarningError: soft warning — requires human confirmation
- BudgetEstimation: run_count, total_ticks, expected_entity_count, expected_event_volume, expected_artifact_mb, expected_runtime_minutes
- BudgetCheckResult: status ("OK", "WARNING", "BLOCKED"), warnings list, blocked_reasons list

## Orchestrator
ScenarioLabOrchestrator: loads World+Scenario+Experiment specs → isolated lab run → simulation ticks → post-run analysis → summary
LabSessionStore: sessions stored under data/lab_sessions/ with strict path security guards

## State
Sessions stored in file-based store (not AuthoritativeState). Lab state is shadow state — isolated per session.
