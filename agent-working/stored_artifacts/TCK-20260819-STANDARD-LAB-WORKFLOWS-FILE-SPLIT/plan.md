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
   private helpers beyond `safe_path_resolution()` before assuming zero others exist). Two
   `run()` methods (`UpdateSimulationKnowledgeWorkflow.run()` at L2341,
   `RevertSimulationKnowledgeWorkflow.run()` at L2609) contain a function-local `from
   src.lab.audit import LabAuditTrail`, redundant with the top-level import — this travels with
   the method body verbatim; do not "clean up" the redundancy as an uninstructed side change.
2. `src/lab/workflows/__init__.py` re-exports all 9 public names so every existing
   `from src.lab.workflows import X` (10 call sites: `src/lab/__init__.py` + 9 test files, per
   investigation.md — all confirmed at Review to be the plain `from src.lab.workflows import
   X[, Y, ...]` form, no `import ... as` or wildcard forms) continues to work unchanged — zero
   call-site edits required if the facade is complete.
3. Delete the original flat `src/lab/workflows.py`.
4. Update `docs/parity_ledger/infrastructure.yaml`'s `v2_evidence` path citations that reference
   `src/lab/workflows.py` (e.g. `INFRA-225`, and any entry citing
   `src/lab/workflows.py::RevertSimulationKnowledgeWorkflow` or
   `src/lab/workflows.py::UpdateSimulationKnowledgeWorkflow.run()`) to the new per-class file
   paths (e.g. `src/lab/workflows/revert_simulation_knowledge.py::RevertSimulationKnowledgeWorkflow`)
   — grep the file for every `src/lab/workflows.py` citation at implementation time, don't assume
   the 2 examples found at Review are exhaustive. Do NOT change `status`/`priority`/`test_path`,
   only the path citation text.
5. Run `graphify update .` (files under `src/` changed).
6. Verify per test_plan.md.

## Out of Scope (addendum from Review)
- **Do not touch or consolidate `src/lab/audit.py`'s local `safe_path_resolution()` definition.**
  It is an independently-written duplicate (different signature, different error message text),
  not an import from `workflows.py` — see investigation.md's Review correction. Moving
  `workflows.py`'s own copy to `_path_safety.py` does not affect `audit.py` in any way; leave
  `audit.py` byte-for-byte untouched. Consolidating the two duplicates into one shared function
  would be a real behavior change (different exception message text reaching callers/logs) and is
  explicitly not this ticket's scope.

## Explicitly out of scope
- Any behavioral change to the 9 workflow classes — pure file relocation.
- Renaming any public class or changing its public API.
- Touching `src/lab/audit.py` beyond its existing import of `safe_path_resolution()` continuing
  to resolve (via the facade or a direct import of the new `_path_safety` module — implementer's
  choice, either is zero-risk).

## Unresolved Questions

- Whether any workflow class has a module-level import or private helper beyond
  `safe_path_resolution()` that's shared with another workflow class (not just imported from
  elsewhere) wasn't fully ruled out by investigation.md's AST-signature-level parse (class/function
  signatures + docstrings + line spans only, not full import-statement bodies). Step 1 explicitly
  requires the implementer to check for this before assuming each class's imports are fully
  self-contained — not pre-judged here, since the AST pass that would answer it definitively wasn't
  performed as part of this investigation (deliberately, per the ticket's "investigation only, no
  implementation" scope).

## Deviations (recorded during Implement)

- **Step 2's facade list was incomplete by one name.** Step 2 says the `__init__.py` facade
  re-exports "all 9 public names" (the 9 classes + `LabKnowledgeRevertError`). During
  implementation, `tests/unit/lab_agent/test_agent_guardrails.py` (lines 24-29) was found to do
  `from src.lab.workflows import (PrepareSimulationExecutionWorkflow,
  InvestigateSimulationResultWorkflow, GenerateSimulationSetupWorkflow, safe_path_resolution)` —
  i.e. it imports `safe_path_resolution` directly from `src.lab.workflows`, not only the 9 class
  names. investigation.md's Review-correction paragraph had already surfaced that this test file
  imports `safe_path_resolution` "from `src.lab.workflows`," but that detail did not get carried
  into this plan's explicit Step 2 re-export list. Leaving it out would have broken this real,
  pre-existing call site and violated the ticket's own "zero call-site edits required" acceptance
  criterion. The implementer added `safe_path_resolution` to `src/lab/workflows/__init__.py`'s
  imports and `__all__` (re-exported from the new `_path_safety` module) alongside the 9 planned
  names. This is a necessary completion of Step 2's intent (preserve every existing
  `from src.lab.workflows import X` call site unchanged), not a scope change — no new behavior was
  introduced, one additional already-existing name was added to the re-export surface.
- **`CompactSimulationDataWorkflow` does not use `LabAuditTrail`.** Confirmed by grep across its
  exact line range (L1116-1568 in the original file) — unlike the other 7 workflow classes, it
  never instantiates or calls `LabAuditTrail`. `compact_simulation_data.py` correctly omits that
  import. This wasn't called out explicitly in investigation.md (which only inventoried class
  signatures, not full import usage per class) but doesn't contradict it either — it's a finding
  made during the implementer's own per-file import audit, consistent with Step 1's instruction to
  check what each class's imports actually are rather than assume uniformity.
