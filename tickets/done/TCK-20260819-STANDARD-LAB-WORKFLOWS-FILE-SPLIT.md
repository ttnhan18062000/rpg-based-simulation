---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT

## Title
Split src/lab/workflows.py (2,695 lines, 9 pipeline-stage classes) into one file per workflow

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
`src/lab/workflows.py` is the single largest file in `src/` (2,695 lines) — item 1 of
`TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`, extracted into its own ticket once concretely
investigated. AST-level structural parsing (no full-file read) confirms it holds 8
milestone-numbered (M96-M102 + Revert), independently-sized (104-507 line) workflow classes
forming a sequential pipeline (Generate → Prepare → Register → Compact → Investigate → Propose →
Update → Revert) plus one shared helper function — a "9 stages in one file" organization smell,
not a god-class. Mechanical, low-risk split.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Convert `src/lab/workflows.py` into a `src/lab/workflows/` package, one file per class (see
  plan.md for exact target layout).
- `src/lab/workflows/__init__.py` re-exports every class so all 10 existing import sites
  (`src/lab/__init__.py` + 9 test files) continue to work unchanged.
- Move the shared `safe_path_resolution()` helper to its own module (used by `src/lab/audit.py`
  too, not workflow-specific).
- Delete the original flat file once the package fully replaces it.

## Out of Scope
- Any behavioral change to the 9 workflow classes.
- Renaming any public class or changing its public API.

## Acceptance Criteria
- [x] `src/lab/workflows.py` no longer exists as a single 2,695-line file.
- [x] Every existing import of the 9 classes (10 call sites) still resolves unchanged — zero
      call-site edits required.
- [x] Pre-split and post-split `tests/integration/lab_agent` + `tests/unit/lab_agent` pass/fail
      counts match exactly.

## Related Tickets
- TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC (item 1 extracted from here; epic remains open
  for its other 2 items — pipeline.py/tactical.py coverage verification, tests/helpers/
  under-utilization; item 2, the observability/mining/ naming investigation, was resolved
  directly within the epic itself rather than spun into a separate ticket — see that epic's
  Status update)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§D, §F — original source finding)
- docs/plans/codebase_navigability_hygiene_epic.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT/

## Related Code Areas
- src/lab/workflows.py
- src/lab/__init__.py
- src/lab/audit.py
- tests/integration/lab_agent/, tests/unit/lab_agent/

## Assumptions / Open Questions
- Whether any workflow class has a module-level import or private helper beyond
  `safe_path_resolution()` that's shared with another workflow class (not just imported from
  elsewhere) wasn't fully ruled out — investigation.md's AST parse covers class/function
  signatures, not full import-statement bodies; a final check before splitting is prudent.

## Implementation Notes
Converted `src/lab/workflows.py` (2,695 lines) into a `src/lab/workflows/` package following
plan.md's target layout exactly: one file per class (`generate_simulation_setup.py`,
`prepare_simulation_execution.py`, `register_simulation_result.py`, `compact_simulation_data.py`,
`investigate_simulation_result.py`, `propose_simulation_enhancements.py`,
`update_simulation_knowledge.py`, `revert_simulation_knowledge.py` holding both
`LabKnowledgeRevertError` and `RevertSimulationKnowledgeWorkflow`), plus `_path_safety.py` holding
the relocated `safe_path_resolution()` helper. Each class's code, docstrings, and comments were
copied verbatim — zero logic changes.

Per-file imports were derived from a full manual + grep-based usage audit of the original file's
top-level import block (not guessed), so each new file carries exactly the shared imports its
class actually uses:
- Two module-level imports in the original file were dead code (never referenced anywhere in the
  file body): `import re`, and `LabSessionError`/`LabSessionManifest` from `src.lab.session`.
  Also dead: `BudgetBlockedError`, `BudgetWarningError`, `BudgetEstimation` from
  `src.lab.guardrails`. None of these were carried into any split file — omitting an import that
  nothing references is not a behavior change (pure relocation still holds; nothing in the module
  graph observably depended on these dead names being importable from `src.lab.workflows`, and the
  facade re-export list — the actual compatibility surface — never included them either).
- `CompactSimulationDataWorkflow` does not use `LabAuditTrail` anywhere in its body (verified by
  grep across its exact line range) — `compact_simulation_data.py` correctly omits that import;
  earlier per-class grep in investigation.md did not go this deep, so this is a finding made
  during implementation, not previously documented.
- The two documented redundant `from src.lab.audit import LabAuditTrail` local imports inside
  `UpdateSimulationKnowledgeWorkflow.run()` and `RevertSimulationKnowledgeWorkflow.run()` were
  preserved exactly as-is (both the module-level top import AND the redundant function-local
  re-import), per the plan's explicit instruction not to "clean up" this redundancy.
- `RevertSimulationKnowledgeWorkflow` does not call `safe_path_resolution()` (confirmed by grep) —
  matches the ticket's list of 6 classes that use it (Prepare, Register, Compact, Investigate,
  Propose, Update); Generate and Revert do not, and `revert_simulation_knowledge.py` correctly has
  no import from `_path_safety`.

**Plan deviation (necessary, not optional):** `staging_artifacts/.../plan.md` step 2 says the
`__init__.py` facade re-exports "all 9 public names" (the 9 classes + `LabKnowledgeRevertError`).
During implementation I found a 10th real import site not covered by that list:
`tests/unit/lab_agent/test_agent_guardrails.py` line 24-29 does
`from src.lab.workflows import (PrepareSimulationExecutionWorkflow,
InvestigateSimulationResultWorkflow, GenerateSimulationSetupWorkflow, safe_path_resolution)` —
i.e. it imports `safe_path_resolution` directly from `src.lab.workflows`, not just the 9 classes.
investigation.md's Review correction paragraph already flagged that this test file imports
`safe_path_resolution` "from `src.lab.workflows`", but plan.md's step 2 facade list did not carry
that forward into the explicit re-export list. Without adding it, this real call site would break
and the ticket's own acceptance criterion ("zero call-site edits required") would fail. I added
`safe_path_resolution` to `src/lab/workflows/__init__.py`'s imports and `__all__` (re-exported
from the new `_path_safety` module) to keep this real, pre-existing import working unchanged. This
is documented in staging_artifacts's plan.md "Deviations" section below.

Updated `docs/parity_ledger/infrastructure.yaml`: re-grepped the whole file for
`src/lab/workflows.py` citations (4 line matches total, confirming investigation.md's count of
2 entries) and updated the `v2_evidence` field of both `INFRA-225` and `INFRA-261` to cite the new
per-class file paths. Left the `text` field of `INFRA-225` (which also happens to mention
`src/lab/workflows.py` descriptively) untouched, per the plan's explicit "only the path citation
text [in v2_evidence]" scope guard — `status`/`priority`/`test_path` were not touched on either
entry. Confirmed the file still parses as valid YAML after the edit.

Ran `graphify update .` — no code-graph topology changes were detected (pure AST-level file
relocation, same symbols/edges under new file paths).

Deleted the original flat `src/lab/workflows.py` from disk. `src/lab/audit.py` was left
byte-for-byte untouched (confirmed via `git diff --stat` showing no changes), per the plan's
explicit out-of-scope note that its independently-written duplicate `safe_path_resolution()` is
not touched by this ticket.

## Test Summary
Ran `.venv/bin/python3 -m pytest tests/unit/lab_agent tests/integration/lab_agent -m "not slow and
not extra_slow" --tb=short -q` twice: once against the split package (post-split), then used
`git stash push -u -- src/lab/workflows.py src/lab/workflows/` to restore the original flat file
and get a true pre-split baseline from the same working tree, then `git stash pop` to restore the
split.

- **Pre-split baseline**: 95 passed, 0 failed.
- **Post-split**: 95 passed, 0 failed.
- Counts match exactly — no test behavior changed.

Also verified:
- `.venv/bin/python3 -c "from src.lab.workflows import <all 9 names>"` — succeeds.
- `.venv/bin/python3 -c "from src.lab.workflows import (PrepareSimulationExecutionWorkflow,
  InvestigateSimulationResultWorkflow, GenerateSimulationSetupWorkflow,
  safe_path_resolution)"` (the exact import statement from
  `test_agent_guardrails.py`) — succeeds.
- `import src.lab` (the package `__init__.py` that also imports from `src.lab.workflows`) —
  succeeds.
- `grep -rn "from src.lab.workflows import\|import src.lab.workflows" src/ tests/ tools/` — found
  all 10 real call sites (`src/lab/__init__.py` + 9 test files), none required editing.
- `ls src/lab/workflows.py` — confirms no such file (removed, not left alongside the package).
- `git ls-files src/lab/workflows.py` still lists the path because the deletion is unstaged
  (working-tree delete, not yet `git add`/committed) — this is expected pre-commit state, not a
  leftover flat file; `ls` on disk confirms the file itself is gone.
- `.venv/bin/python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
  — parses without error after the `v2_evidence` edits.

## Files Changed
- `src/lab/workflows.py` — deleted (was the flat 2,695-line module).
- `src/lab/workflows/__init__.py` — new; facade re-exporting the 9 public names +
  `safe_path_resolution`.
- `src/lab/workflows/_path_safety.py` — new; `safe_path_resolution()` relocated here.
- `src/lab/workflows/generate_simulation_setup.py` — new; `GenerateSimulationSetupWorkflow`.
- `src/lab/workflows/prepare_simulation_execution.py` — new; `PrepareSimulationExecutionWorkflow`.
- `src/lab/workflows/register_simulation_result.py` — new; `RegisterSimulationResultWorkflow`.
- `src/lab/workflows/compact_simulation_data.py` — new; `CompactSimulationDataWorkflow`.
- `src/lab/workflows/investigate_simulation_result.py` — new; `InvestigateSimulationResultWorkflow`.
- `src/lab/workflows/propose_simulation_enhancements.py` — new; `ProposeSimulationEnhancementsWorkflow`.
- `src/lab/workflows/update_simulation_knowledge.py` — new; `UpdateSimulationKnowledgeWorkflow`.
- `src/lab/workflows/revert_simulation_knowledge.py` — new; `LabKnowledgeRevertError` +
  `RevertSimulationKnowledgeWorkflow`.
- `docs/parity_ledger/infrastructure.yaml` — `v2_evidence` path citations updated for `INFRA-225`
  and `INFRA-261` (no status/priority/test_path changes).
- `docs/ai/agents_dir_disposition.md` — Document-Update phase: updated a live citation of
  `src/lab/workflows.py` (evidence for the `WorkflowRegistry` dead-code determination) to
  `src/lab/workflows/`.
- `docs/ai/workflows.md` — Document-Update phase: updated the `update-knowledge-store` section's
  citation of `RevertSimulationKnowledgeWorkflow.run()`'s location to
  `src/lab/workflows/revert_simulation_knowledge.py`.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — Document-Update phase: updated the
  "Follow-Up Clarification Map" table's real-code reference from `src/lab/workflows.py` to
  `src/lab/workflows/`.
- `staging_artifacts/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT/plan.md` — Deviations section
  appended during this run (documents the `safe_path_resolution` facade addition described above).
  Pre-existing modifications to this file from the prior review-fix cycle (2 review rounds noted
  in the task brief) were already present in the working tree before this session started.
- `staging_artifacts/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT/investigation.md` — already
  modified in the working tree from the prior review-fix cycle before this session started (no
  further edits made by this implementation session).
- `staging_artifacts/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT/test_plan.md` — read for
  verification steps; no edits made (content required no changes).
- `tickets/inprogress/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT.md` — this file; Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary
  updated.
- `graphify-out/` — refreshed by `graphify update .` (no topology changes detected; run recorded
  for traceability).

## Completion Summary
Implemented the approved plan exactly: `src/lab/workflows.py` was split into a `src/lab/workflows/`
package with one file per pipeline-stage class plus a shared `_path_safety.py` module, and
`__init__.py` re-exports the full original public surface (9 classes + `LabKnowledgeRevertError`,
plus `safe_path_resolution` — a real 10th name needed by an existing test import that the plan's
facade list had not explicitly enumerated). The original flat file was deleted. All 10 real
call sites resolve unchanged with zero edits. Pre-split and post-split
`tests/unit/lab_agent` + `tests/integration/lab_agent` runs both pass 95/95 with identical counts,
confirming zero behavior change. `docs/parity_ledger/infrastructure.yaml`'s two affected
`v2_evidence` entries (`INFRA-225`, `INFRA-261`) were updated to the new per-class paths, and
`graphify update .` was run (no topology changes). Implementation, Test, and Parity-ledger work for
this ticket is complete; remaining pipeline phases (Test-scope sign-off, Parity phase gate, Verify,
Finalize/move-to-done) are left for those dedicated agents to run independently.
