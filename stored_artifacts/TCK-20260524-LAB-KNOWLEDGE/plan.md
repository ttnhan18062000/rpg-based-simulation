---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260524-LAB-KNOWLEDGE
artifact_type: plan
tags: [lab, knowledge]
---

# Implementation Plan - Milestone 102 Update Knowledge Base

## Goal Description
Implement `UpdateSimulationKnowledgeWorkflow` to store approved insights, known issues, rulebook updates, and decision notes in a global, safe, and audited simulation knowledge base structure.

## User Review Required
No breaking changes. The workflow strictly adheres to the Phase 14 specifications.

## Proposed Changes

### RPG Engine Lab Workflows

#### [MODIFY] [workflows.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/workflows.py)
- Create and implement `class UpdateSimulationKnowledgeWorkflow`:
  - **`__init__(workspace_root)`**: Sets up session store and workspace paths.
  - **`run(session_id, request)`**:
    1. Loads the session manifest and transitions to the `KNOWLEDGE_UPDATE` stage.
    2. Resolves target paths and validates safe sandbox limits via `safe_path_resolution`.
    3. Validates inputs:
       - **Generic**: Ingests approved items from the latest enhancement stage (e.g. reading `enhancement/proposed_patches/`, `enhancement/insight_candidates.json`).
       - **Specific**: Uses specified `approved_insights`, `approved_patches`, and `decision_note`.
    4. Enforces strict approval gate rules:
       - Checks for explicit model or request approval markers (e.g. `approval_recorded: true`).
       - If no approval is present or recorded, rejects updates to rules or principles, raising `ValueError`.
    5. Serializes and stores approved insights and known issues under:
       - `data/lab_knowledge/insights/`
       - `data/lab_knowledge/known_issues/`
       - `data/lab_knowledge/rules/`
       - `data/lab_knowledge/principles/`
    6. Appends the decision notes line-by-line to `data/lab_knowledge/decisions/decision_log.jsonl`.
    7. Safeguards against duplicate insight registrations by checking stable identifiers/ids.
    8. Preserves original evidence references in all persistent records.
    9. Returns `{"status": "READY", "report_path": "..."}`.

#### [MODIFY] [__init__.py](file:///home/vboxuser/Work/rpg-based-simulation/src/lab/__init__.py)
- Import and export `UpdateSimulationKnowledgeWorkflow` in `__all__`.

### Integration Tests

#### [NEW] [test_update_simulation_knowledge_workflow.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py)
- Write tests verifying:
  - Approved insights are stored successfully.
  - Known issues are created and stored.
  - Decisions are appended cleanly to `decision_log.jsonl`.
  - Attempts to register unapproved items or update rules without approval markers fail validation.
  - Duplicate insight records are successfully blocked/rejected.
  - Original evidence references are preserved perfectly.

## Verification Plan

### Automated Tests
- Run `pytest tests/integration/lab_agent/test_update_simulation_knowledge_workflow.py`.
- Run `graphify update .` to keep the codebase knowledge graph synchronized.
