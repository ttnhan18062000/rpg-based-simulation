---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
artifact_type: test_plan
tags: [ai, documentation]
---

# Test Plan — TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP

## Step 1 verification (malformed entries)
- `tools/parity_index.py build` succeeds (schema-valid YAML).
- The "fully bare entries" SQL scan (all evidence fields NULL) returns 0 rows, down from 2.
- Existing parity-ledger test suite (`tests/tools/test_parity_index_baseline.py` and any
  `tests/tools/test_parity_*.py`) still passes.
- **Required, not covered by the above**: run `tools/parity_ledger_writer.py::validate_entry()`
  (or equivalent schema check) directly against `docs/parity_ledger/town_resource.yaml`'s full
  entry list after the fix — `build()` does not itself enforce `schema.json`'s `allOf` rules, so
  passing `build` and the bare-entries scan does not prove schema compliance. If `TOWN-040`/
  `TOWN-041` were removed, confirm they no longer appear at all (trivially compliant). If either
  was kept instead, confirm it has a non-null, non-empty `test_path` (mandatory for `priority: P0`
  regardless of `status`) and that `test_path` points at a real, passing test.

## Step 2 verification (absent_file triage)
- Re-run `tools/parity_index.py health` after fixes; `absent_file` count is lower than the
  173 baseline recorded in investigation.md (exact target count depends on how many were real vs.
  false positives — not pre-determined here).
- If `_populate_entry_health()` was changed to check `dashboard-frontend/` as a second root: add a
  test fixture proving it now resolves a real `dashboard-frontend/`-only path, and still correctly
  flags a genuinely absent one (coverage-honesty pattern already used elsewhere in this repo's
  `tests/tools/`, e.g. `test_workflow_meta_conformance.py`'s own docstring convention).

## Step 3 verification (archive)
- `docs/logic_checklist_exhaustive.md` no longer exists at its old path; exists under
  `docs/archive/`, with frontmatter `status: archive` / `authority: P2` / `audience: historical` /
  `layer: guidelines` / `original_date: 2026-05-04` (matching every other `docs/archive/*.md`
  file's convention).
- `docs/REGISTRY.yaml` (regenerated at Finalize) lists the file at its new path with `status:
  archive` — not still showing `status: active` at the old path.
- `grep -rn "logic_checklist_exhaustive"` across the live (non-archive, non-historical-ticket)
  tree returns only the new archive path and legitimately historical references
  (`tickets/done/`, `stored_artifacts/`) — no live script or doc still points at the old path.
  This must include `tools/add_frontmatter_live.py`'s `LOOSE_FILES` entry and
  `docs/plans/engine_future_epics_roadmap.md:43` — both confirmed live during Review as
  additional references investigation.md's original sweep missed.
- `tests/tools/test_add_frontmatter_live.py::test_loose_logic_checklist` still passes against
  whatever `add_frontmatter_live.py` change was made (update the test in step, not after).
- Any script moved to `scripts/archive/` (vs. deleted) still parses as valid Python (no partial
  edit left it broken) even though it's no longer wired to anything.
- All 3 `logic_checklist_exhaustive_v2.md` references no longer dangle: `src/engine/rpg_depth.py`,
  `scripts/certification_long_run.py`, `tests/integration/kernel/test_certification_scenarios.py`
  (investigation.md's original count of 1 was incomplete — confirmed 3 during Review).

## Acceptance-criteria mapping
| Acceptance criterion | Verified by |
|---|---|
| No entry in the ledger has every evidence field empty | Step 1 verification |
| `absent_file` count meaningfully drops from the 173 baseline | Step 2 verification |
| The orphaned checklist system is archived, not just noted | Step 3 verification |
