---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260709-REGISTRY-REGEN-ON-CLOSE
artifact_type: test_plan
tags: [observability, testing]
---

# Test Plan — TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Regression Surface

Existing tests that must keep passing, grouped by domain:

**Unit — `tools/gate_checks/done_checker_static.py` (the module new functions will most likely live in):**
- `tests/tools/test_done_checker_static.py` — all existing tests, in particular:
  - `test_run_finalize_selfcheck_all_pass` (line 659) — currently asserts `len(results) == 3`. **This assertion will need updating if the new self-check is folded into `run_finalize_selfcheck` as a 4th condition** (see investigation.md Risk #1 — an open design decision, not to be assumed). If instead implemented as a wholly separate function/check, this test is unaffected and stays a pure regression guard.
  - `test_run_finalize_selfcheck_surfaces_incomplete_stored_artifacts`, `test_run_finalize_selfcheck_zero_rows_fails`, `test_run_finalize_selfcheck_duplicate_rows_fails` (lines 668-699) — must continue passing unchanged regardless of which design is chosen; they assert on `migration_complete`/`working_log_exactly_one_row`, not the new condition.
  - `test_check_monitoring_write_recorded_*` (lines 714-771) — regression guard for the non-blocking-warning pattern, useful as a direct behavioral reference if the new self-check follows that shape instead.
  - `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` (line 305) — precedent showing new blocking statuses get pinned into `docs/ai/ticket-lifecycle.md`'s status vocabulary table; if this ticket introduces a new blocking status, an equivalent doc-presence test should be added (see New Tests Required).

**Unit — `tools/generate_registry.py` (must not be modified per Out of Scope, but its behavior is the dependency under test):**
- `tests/tools/test_generate_registry.py` — all 9 test classes (`TestDocEntryGeneration`, `TestTicketEntryGeneration`, `TestArtifactJoin`, `TestSortOrder`, `TestTitleExtraction`, `TestRelatedCodeAreas`, `TestYAMLOutput`, `TestRealDocsTree`, `TestEdgeCases`) must pass unchanged — confirms this ticket did not touch `generate_registry.py` internals.

**Integration / workflow-tooling:**
- No pytest coverage exists for `.claude/workflows/implement-ticket.js` itself (confirmed — no `.test.js` file references it, no JS test runner configured in this repo). Any new orchestrator logic added directly in that file (the `bash()`/JS glue, as opposed to the Python functions it calls) is **not directly testable by pytest** — its correctness is verified only by (a) unit tests on the Python functions it calls via `python3 -c "..."`, and (b) an actual `implement-ticket` dry-run/manual trace. This is a pre-existing gap in this repo's test architecture, not something this ticket is expected to close.

**Doc validation (touched by AC #4's CLAUDE.md edit):**
- `python3 tools/validate_frontmatter.py CLAUDE.md` (or whatever the project's convention is for validating root-level docs — confirm via `tools/validate_frontmatter.py --help` if CLAUDE.md is in scope for that validator; if not, a plain read-through diff review is the check) — must still pass after the "After Work" section edit.

## New Tests Required

Per acceptance criteria, mapped 1:1:

1. **AC #1 — regen invoked unconditionally on every ticket close, all tiers including hotfix**
   - Test name: `test_regenerate_registry_invoked_for_hotfix_tier` (or equivalent, matching whatever function name the implementer gives the new regen wrapper — e.g. `regenerate_docs_registry`)
   - Category: unit
   - Verifies: the new function/check runs (and produces a result) regardless of a `tier == "hotfix"` argument — mirrors `check_monitoring_write_recorded`'s own `test_check_monitoring_write_recorded_applies_under_hotfix_tier` (line 753), which documents that function's deliberate lack of a `tier` parameter for exactly this "including hotfix" Hard-Rule reason. If the new function *does* take a `tier` parameter, this test must prove it has no hotfix-skip branch.
   - Location: `tests/tools/test_done_checker_static.py`

2. **AC #2 — nonzero tool exit is a non-blocking warning, never blocks ticket close**
   - Test name: `test_registry_regen_nonzero_exit_does_not_raise` / `test_registry_regen_reports_warning_on_nonzero_exit`
   - Category: unit
   - Verifies: when `generate_registry()` (or the subprocess wrapping it) would exit non-zero (simulate via a `tmp_path` docs tree with one file missing frontmatter — same fixture shape as `tests/tools/test_generate_registry.py`'s existing `TestDocEntryGeneration`/`TestEdgeCases` missing-frontmatter fixtures), the new wrapper function returns a non-fatal status/tuple (e.g. `("WARN", ...)`) rather than raising or returning a hard `"FAIL"` that would propagate to `FINALIZE_INCOMPLETE`.
   - Location: `tests/tools/test_done_checker_static.py`

3. **AC #3 — self-check confirms the regenerated `docs/REGISTRY.yaml` contains an entry for the closing `ticket_id` before Finalize completes**
   - Test name: `test_registry_entry_present_for_ticket_passes` / `test_registry_entry_missing_for_ticket_fails_naming_it`
   - Category: unit
   - Verifies: given a `docs/REGISTRY.yaml` (or freshly regenerated in-memory/on-disk equivalent under `tmp_path`) that does/does not contain a `ticket_id: <tid>` entry, the check returns PASS/FAIL correctly, with the ticket_id named in the FAIL evidence (matching this file's own established evidence-naming convention, e.g. `check_ticket_location`'s `"Expected ticket file not found at {path}"`).
   - **Also required**: whichever way the blocking/non-blocking design question (investigation.md Risk #1) is resolved:
     - If folded into `run_finalize_selfcheck` (4th condition): update `test_run_finalize_selfcheck_all_pass` to `len(results) == 4`, and add a new `test_run_finalize_selfcheck_surfaces_missing_registry_entry` test analogous to `test_run_finalize_selfcheck_surfaces_incomplete_stored_artifacts` (line 668).
     - If a separate, non-blocking check (mirroring `check_monitoring_write_recorded`): add `test_registry_entry_check_never_flips_status_from_done`-style coverage at the orchestrator-return level (best captured as a manual dry-run trace, since `implement-ticket.js` has no pytest harness — see Regression Surface note above).
   - Location: `tests/tools/test_done_checker_static.py`

4. **AC #4 — CLAUDE.md's "After Work" section documents the new unconditional trigger + `git add docs/REGISTRY.yaml` staging step**
   - Test name: `test_claude_md_documents_registry_regen_trigger` (only if this repo's convention is to pin doc-text assertions the way `test_data_runs_clean_status_appears_in_failure_recovery_reference_table` (line 305) pins `"DATA_RUNS_CLEAN_FAILED"` into `docs/ai/ticket-lifecycle.md`)
   - Category: unit (doc-content regression guard)
   - Verifies: `CLAUDE.md`'s text contains both the unconditional-regen statement and the `git add docs/REGISTRY.yaml` staging instruction, so a future edit to CLAUDE.md cannot silently drop this without a test failure — same "documentation regression guard" precedent already established for `DATA_RUNS_CLEAN_FAILED`.
   - Location: `tests/tools/test_done_checker_static.py` (co-located with the precedent test) or a new `tests/tools/test_claude_md_content.py` if one does not already exist — check for an existing doc-content test file before creating a new one.

5. **Ordering guard (not a literal AC line but directly required by investigation.md's Critical ordering constraint)**
   - Test name: `test_registry_regen_check_runs_after_ticket_moved_to_done`
   - Category: unit / architecture guard
   - Verifies: the self-check function, given a scaffolded `tmp_path` repo where the ticket is still in `tickets/inprogress/` (not yet moved) and `docs/REGISTRY.yaml` was regenerated in that state, correctly reports the entry as **absent** (FAIL) — proving the check would have caught a call-site-ordering regression (e.g., someone later moves the regen call to run before the Finalize `agent()`'s move step) rather than silently passing.
   - Location: `tests/tools/test_done_checker_static.py`

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_generate_registry.py -v --tb=short
```

If the CLAUDE.md-content test lands in a new file:
```
python3 -m pytest tests/tools/test_done_checker_static.py tests/tools/test_generate_registry.py tests/tools/test_claude_md_content.py -v --tb=short
```

Never run bare `pytest tests/` — scope is `tests/tools/` only; this ticket touches no `src/` code and no simulation-domain tests.

## Anti-Drift Test Guards

- **`test_run_static_precheck_all_pass_eligible`/`test_run_static_precheck_surfaces_fail_not_masked`** (Part A, pre-Finalize, lines 479-500) must remain untouched and passing — this ticket's self-check is inherently post-Finalize (the registry entry cannot exist until the ticket is in `tickets/done/`), so any accidental edit that pulls the new check into Part A instead of Part B is a scope violation this suite would catch by shape mismatch (`run_static_precheck`'s fixed 5-condition list growing unexpectedly).
- **All 9 `tests/tools/test_generate_registry.py` classes passing with zero diff** is the guard against `generate_registry.py` internals being touched — this ticket's Out of Scope explicitly forbids modifying `_SKIP_DOC_SUBDIRS` or any other internals; a passing, unmodified test file is the cheapest proof of that boundary.
- **No new CI-gate/`--check` flag tests should appear in this diff** — those belong to `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`; if a new test file or test class exercising a `--check` flag shows up in this ticket's diff, that is scope creep into the sibling ticket and should be rejected at Architecture-Verify.
- **`test_check_monitoring_write_recorded_applies_under_hotfix_tier`** (line 753) stays as the reference "including hotfix, no tier-skip branch" pattern — the new AC #1 test (New Tests Required #1) should assert the same property using the same fixture shape, not a divergent one, so the two Hard-Rule-driven "must apply under hotfix" checks in this file read consistently to a future maintainer.
- **Deliberately do not add a test asserting a specific numeric entry count** in `docs/REGISTRY.yaml` or in any doc text — `TCK-20260709-REGISTRY-COUNT-STALE-DOCS` (this session) just removed exactly this kind of baked-in count because it goes stale; a new test that re-introduces a hardcoded count assertion (e.g. "registry has N entries") would immediately regress that fix's intent.
