---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT

Pure file-relocation ticket; no new test coverage is needed. The test plan is a
behavior-preservation check.

## Pre-split baseline

```
pytest tests/integration/lab_agent tests/unit/lab_agent -m "not slow and not extra_slow" \
       --tb=short -q
```
Record pass/fail counts.

## Post-split verification

1. Same command must produce identical pass/fail counts — a directory/file reorganization must
   not change test outcomes.
2. `python3 -c "from src.lab.workflows import GenerateSimulationSetupWorkflow, \
   PrepareSimulationExecutionWorkflow, RegisterSimulationResultWorkflow, \
   CompactSimulationDataWorkflow, InvestigateSimulationResultWorkflow, \
   ProposeSimulationEnhancementsWorkflow, UpdateSimulationKnowledgeWorkflow, \
   RevertSimulationKnowledgeWorkflow, LabKnowledgeRevertError"` — the full flat import surface
   still resolves via the new package's `__init__.py` facade.
3. `grep -rn "from src.lab.workflows import\|import src.lab.workflows" src/ tests/ tools/` —
   confirm no call site needed editing (facade completeness check).
4. `git ls-files src/lab/workflows.py` returns nothing (old flat file actually removed, not left
   alongside the new package).

## Acceptance-criteria mapping

| Acceptance criterion | Verified by |
|---|---|
| `src/lab/workflows.py` no longer exists as a single 2,695-line file | Step 4 |
| Every existing import of the 9 classes still resolves unchanged | Steps 2-3 |
| No test behavior changed | Step 1 |
