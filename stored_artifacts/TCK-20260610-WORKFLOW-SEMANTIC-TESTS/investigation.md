---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260610-WORKFLOW-SEMANTIC-TESTS
artifact_type: investigation
tags: [workflow, semantic, tests]
---

# Investigation: TCK-20260610-WORKFLOW-SEMANTIC-TESTS

## Findings

Per-workflow integration test files exist under `tests/integration/lab_agent/`. The unit test directory `tests/unit/lab_agent/` has general infra tests (audit_trail, approval_gate, guardrails) but no per-workflow semantic tests.

**PrepareSimulationExecution**: existing test checks `rpg-lab run` in script but not the exact experiment path. `execution_readiness_report.json` has `storage_estimate.run_count` — matchable against `len(seeds)` from the generated experiment YAML.

**RegisterSimulationResult**: `result_integrity_report.json` contains `completed_run_count`, `failed_run_count`, `run_count` from the manifest. `artifact_index.json` is a list of `{relative_path, size_bytes}` entries.

**InvestigateSimulationResult**: existing `test_investigation_light_depth` already checks `critical_issues[0]["rule_name"] == "HardLawViolationRule"` — covers the "known anomaly → expected type" AC. Missing: healthy run → zero critical issues.

**ProposeSimulationEnhancements**: only CRITICAL issues produce `KnownIssues` patches. WARNING issues produce no KnownIssues patch. The `mock_workspace_warning_only` fixture can write `issue_backlog.json` directly, bypassing the full pipeline, because Propose reads it independently.
