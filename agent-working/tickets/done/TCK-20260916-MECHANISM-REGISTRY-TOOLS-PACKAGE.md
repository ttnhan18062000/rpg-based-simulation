---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE

## Title
Move the 14 mechanism-registry tools out of flat `tools/` into `tools/mechanism_registry/`

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
User's ask: the 14 tools this epic added all sit flat in `tools/`. Scope them into a subfolder,
following the precedent `tools/gate_checks/` already sets (a real package, 22 modules). Do it
inside the still-open PR (#209), not after merge, since these tools are new in this PR — moving
them now means `main` never sees the flat layout.

## Scope
1. Move all 14 files into `tools/mechanism_registry/`:
   `generate_mechanism_charts.py`, `generate_mechanism_priority_view.py`,
   `generate_mechanism_registry_html.py`, `generate_mechanism_registry_view.py`,
   `generate_mechanism_verification_view.py`, `mechanism_atlas_card_mapping.py`,
   `mechanism_atlas_regenerate.py`, `mechanism_capabilities_card_mapping.py`,
   `mechanism_capabilities_regenerate.py`, `mechanism_capabilities_tier.py`,
   `mechanism_registry.py`, `mechanism_registry_completeness_check.py`,
   `mechanism_registry_graphify_check.py`, `mechanism_wiring_map_classdef.py`.
2. Resolve the one naming collision: a module and a package cannot both be named
   `mechanism_registry`. `mechanism_registry.py` becomes `registry.py` inside the package;
   `__init__.py` re-exports its public names so `from tools.mechanism_registry import X` (already
   the widely-used import shape across the test suite and sibling modules) keeps working without
   churn.
3. Fix every internal cross-import (the `sys.path.insert(0, tools/)` + bare-name pattern used so
   these scripts remain directly runnable, not just importable) and every `_REPO_ROOT` calculation
   (one directory deeper now).
4. Update every citation repo-wide: `Makefile` targets, test imports (9 test files), any open
   ticket/doc referencing the old flat paths. Grep repo-wide after the move and confirm zero
   remain outside historical `tickets/done/`/`stored_artifacts/` records, which are frozen
   snapshots by convention and not retroactively rewritten.

## Out of Scope
- Renaming individual module basenames beyond the one required collision
  (`mechanism_registry.py` → `registry.py`) — every other file keeps its original name, only its
  parent path changes. Lower risk than also renaming basenames, and not requested.
- Retroactively editing already-closed tickets/stored_artifacts that cite the old flat paths —
  those are frozen historical records by this repo's own standing convention.
- Claims-as-tests phase 1 or either of the two newly-filed detector tickets — this ticket only
  clears the path for a 15th tool to land inside the package instead of the flat directory.

## Acceptance Criteria
1. All 14 files live under `tools/mechanism_registry/`; nothing named `mechanism_*`/
   `generate_mechanism_*` remains directly in `tools/`.
2. `from tools.mechanism_registry import X` (the pre-existing import shape) still resolves for
   every name it resolved before the move.
3. Every direct-script invocation (`python3 tools/mechanism_registry/<file>.py`, including via
   `make` targets) still works — verified by the existing `test_make_target_*`/
   `test_makefile_wires_*` tests, which invoke these as real subprocesses.
4. A repo-wide grep for every old flat path returns zero hits outside `tickets/done/`/
   `stored_artifacts/`.
5. Full scoped suite passes, including with `graphify-out/` genuinely moved aside and restored.

## Related Tickets
- `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`,
  `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — both updated to propose their new
  tool inside `tools/mechanism_registry/`, not the flat directory, so a 15th tool doesn't recreate
  the problem this ticket just fixed.
- `TCK-20260904` (parity ledger `test_path` drift repair) — cited by peer as the precedent for what
  stale path citations cost when left alone; the motivation for the repo-wide grep-and-confirm
  step here.

## Related Docs
None new.

## Related Stored Artifacts
None — hotfix tier, self-evident intent (a mechanical file move plus import fixes) captured in
this ticket.

## Related Code Areas
- `tools/mechanism_registry/` (new package, 14 modules + `__init__.py`)
- `Makefile`
- `tests/unit/tools/test_mechanism_*.py` (9 files, import paths updated)
- `docs/brainstorm/mechanisms.yaml` (2 comment references updated)
- `tickets/todos/TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT.md` (1 reference updated,
  pre-existing unrelated open ticket)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
The `sys.path.insert(0, str(_REPO_ROOT / "tools"))` + bare `from mechanism_registry import X`
pattern (used by 6 of the 14 files to stay directly runnable as scripts, since a relative import
like `from .registry import X` breaks under direct `__main__` execution) was repointed to
`sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))` with the import target
renamed only where the target module itself was renamed (`mechanism_registry` → `registry`); the
other cross-imports (`mechanism_atlas_card_mapping`, `mechanism_capabilities_card_mapping`,
`mechanism_capabilities_tier`) kept their existing bare names since those files were not renamed.

Every file's `_REPO_ROOT = Path(__file__).resolve().parent.parent` became `.parent.parent.parent`
— one more directory level between the file and the repo root now that files live at
`tools/mechanism_registry/<file>.py` instead of `tools/<file>.py`.

The repo-wide grep-and-confirm step (AC #4) found exactly two live (non-historical) files still
citing old paths: `docs/brainstorm/mechanisms.yaml` (2 header-comment references) and the
pre-existing, unrelated, still-open `TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT.md`
(1 reference) — both fixed. `docs/REGISTRY.yaml` also matched but is fully generated and
regenerates clean automatically; not hand-edited.

## Test Summary
170 tests passing in the scoped suite (`tests/unit/tools/`,
`tests/unit/engine/test_capability_registry.py`, `tests/mechanic_scenarios/`), both with
`graphify-out/` present and with it genuinely moved aside and restored. No test content changed —
only import paths.

## Files Changed
- `tools/mechanism_registry/` — new package: 13 moved files + `registry.py` (renamed from
  `mechanism_registry.py`) + new `__init__.py`
- `Makefile` — 11 target paths updated
- `tests/unit/tools/test_mechanism_registry.py`,
  `test_mechanism_registry_completeness_check.py`, `test_mechanism_priority_derivation.py`,
  `test_mechanism_registry_view.py`, `test_mechanism_capabilities_tier.py`,
  `test_mechanism_registry_html.py`, `test_mechanism_registry_graphify_check.py`,
  `test_mechanism_artifact_convergence.py`, `test_mechanism_atlas_regenerate.py`,
  `test_mechanism_capabilities_regenerate.py`, `test_mechanism_wiring_map_classdef.py` — import
  paths updated
- `docs/brainstorm/mechanisms.yaml` — 2 header-comment path references updated
- `tickets/todos/TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT.md` — 1 reference updated
- `tickets/todos/TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION.md`,
  `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION.md` — proposed new-tool paths updated
  to live inside the package

## Completion Summary
Closed. All 14 tools moved into `tools/mechanism_registry/`, matching the `tools/gate_checks/`
precedent. The one naming collision (`mechanism_registry.py` vs. the new package name) resolved by
renaming the module to `registry.py` and re-exporting its public names from `__init__.py`, so the
already-widely-used `from tools.mechanism_registry import X` import shape needed zero churn across
the test suite. Every other file kept its original basename — only its parent path changed,
minimizing rename risk. A repo-wide grep confirmed zero stale citations remain outside frozen
historical ticket/stored-artifact records. Both newly-filed detector tickets already point their
proposed 15th tool at the new package location.
