---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT

## Origin
Item 1 of `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`: `src/lab/workflows.py` (2,695
lines) is the single largest file in `src/`. Extracted into its own standalone ticket once
concretely investigated, matching the pattern used for this epic tree's other items. Investigated
via AST structural parsing (class/function signatures + docstrings + line spans only, no full
file reads) plus targeted `grep` for cross-file usage — no implementation performed, per explicit
instruction; a separate agent implements.

## Structure (verified via AST parse, not manual reading)

`src/lab/workflows.py`, 2695 lines, contains exactly:

| Symbol | Lines | Span | Purpose (from docstring) |
|---|---|---|---|
| `safe_path_resolution()` | 14 | L72-85 | Shared helper: blocks path-traversal outside a base dir |
| `GenerateSimulationSetupWorkflow` | 507 | L87-593 | M96: draft world/scenario/experiment configs from user intent |
| `PrepareSimulationExecutionWorkflow` | 270 | L596-865 | M97: resolves draft specs, validates safety, creates launcher scripts |
| `RegisterSimulationResultWorkflow` | 246 | L868-1113 | M98: registers/catalogs a completed manual sweep run |
| `CompactSimulationDataWorkflow` | 453 | L1116-1568 | M99: converts heavy raw run folders + child reports |
| `InvestigateSimulationResultWorkflow` | 489 | L1571-2059 | M100: analyzes registered/compacted results |
| `ProposeSimulationEnhancementsWorkflow` | 260 | L2062-2321 | M101: ingests investigation scorecard, constructs proposals |
| `UpdateSimulationKnowledgeWorkflow` | 258 | L2324-2581 | M102: stores approved insights/rule updates/decisions |
| `LabKnowledgeRevertError(Exception)` | 3 | L2584-2586 | Error type for `RevertSimulationKnowledgeWorkflow` |
| `RevertSimulationKnowledgeWorkflow` | 104 | L2589-2692 | Reverts the most recent knowledge sync for a session |

8 milestone-numbered workflow classes (M96-M102, plus the companion Revert workflow) forming a
sequential pipeline: Generate → Prepare → Register → Compact → Investigate → Propose → Update →
(Revert). Each is independently sized (104-507 lines) and self-contained — no shared base class,
no cross-class inheritance. This is a "9 sequential pipeline stages living in one file" situation,
not a single god-class — confirms D24's original characterization ("cohesive theme, each class a
legitimate ~250-400 line pipeline stage — a mild file-organization smell, not a god-class").

## Cross-file usage (verified via `grep`, not full reads)

10 files import from `src.lab.workflows`:
- `src/lab/__init__.py` — re-exports (needs to keep working after the split)
- 9 test files under `tests/integration/lab_agent/` and `tests/unit/lab_agent/`, each importing
  1-2 specific classes by name (e.g. `from src.lab.workflows import CompactSimulationDataWorkflow,
  InvestigateSimulationResultWorkflow`)

No file imports the module as a whole (`import src.lab.workflows`) or relies on two classes being
defined in the same file beyond importing them together in one `import` statement — trivially
preserved by a facade re-export.

**Correction (Review, 2026-08-19):** `safe_path_resolution()` is defined independently in TWO
places, not shared as one function used by 3 files. `src/lab/audit.py:9-25` has its own,
separately-written `safe_path_resolution()` with a different signature
(`target_path_str: str` vs. `workflows.py`'s `target_path: str | Path`) and different error
message text (`"Path traversal detected: ..."` vs. `workflows.py`'s `"Path traversal blocked:
..."`) — `audit.py` does NOT import from `workflows.py`; grep confirms no `from src.lab.workflows
import` anywhere in `audit.py`. The two are historical duplicates that happen to share a name,
not one genuinely shared helper. `workflows.py`'s own copy is used by itself and by
`tests/unit/lab_agent/test_agent_guardrails.py` (which imports it from `src.lab.workflows`) — 2
real usage sites, not 3. `audit.py`'s copy is untouched by this ticket (see plan.md's Out of
Scope) — moving `workflows.py`'s copy to its own module does not affect `audit.py` at all, and
consolidating the two duplicates into one is explicitly NOT this ticket's scope (would be a real
behavior change: different exception message text reaching callers/logs).

## Related
- `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC` (item 1 extracted from here)
- `docs/audits/D24_codebase_health_observatory.md` §D, §F (original source finding)
