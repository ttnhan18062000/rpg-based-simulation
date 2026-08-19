---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT

**Planning/scoping only — no implementation.** This describes the target layout and migration
approach for the implementing agent; it does not perform the split.

## Target layout

Convert `src/lab/workflows.py` into a package `src/lab/workflows/`:

```
src/lab/workflows/
  __init__.py                          # re-exports all 9 classes + LabKnowledgeRevertError,
                                        # preserving `from src.lab.workflows import X` exactly
  _path_safety.py                      # safe_path_resolution() moved here (shared, not
                                        # workflow-specific — see investigation.md)
  generate_simulation_setup.py         # GenerateSimulationSetupWorkflow
  prepare_simulation_execution.py      # PrepareSimulationExecutionWorkflow
  register_simulation_result.py        # RegisterSimulationResultWorkflow
  compact_simulation_data.py           # CompactSimulationDataWorkflow
  investigate_simulation_result.py     # InvestigateSimulationResultWorkflow
  propose_simulation_enhancements.py   # ProposeSimulationEnhancementsWorkflow
  update_simulation_knowledge.py       # UpdateSimulationKnowledgeWorkflow
  revert_simulation_knowledge.py       # LabKnowledgeRevertError + RevertSimulationKnowledgeWorkflow
                                        # (kept together — tightly coupled per investigation.md)
```

One file per pipeline stage, named after the milestone's behavior (not `M96.py` etc. — the
milestone numbers are useful in the docstring/investigation trail but not good file names).

## Steps

1. Create the package directory and move each class to its own file, preserving all imports each
   class currently needs (each workflow file will need its own copy of whatever shared imports
   `workflows.py` currently has at module level — check for any *workflow-specific* shared
   private helpers beyond `safe_path_resolution()` before assuming zero others exist).
2. `src/lab/workflows/__init__.py` re-exports all 9 public names so every existing
   `from src.lab.workflows import X` (10 call sites: `src/lab/__init__.py` + 9 test files, per
   investigation.md) continues to work unchanged — zero call-site edits required if the facade is
   complete.
3. Delete the original flat `src/lab/workflows.py`.
4. Run `graphify update .` (files under `src/` changed).
5. Verify per test_plan.md.

## Explicitly out of scope
- Any behavioral change to the 9 workflow classes — pure file relocation.
- Renaming any public class or changing its public API.
- Touching `src/lab/audit.py` beyond its existing import of `safe_path_resolution()` continuing
  to resolve (via the facade or a direct import of the new `_path_safety` module — implementer's
  choice, either is zero-risk).
