---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-DATA-RUNS-CLEANUP-TIMING
artifact_type: test_plan
tags: [ai, workflows, process-improvement]
---

# Test Plan — TCK-20260708-DATA-RUNS-CLEANUP-TIMING

## Regression Surface

All existing coverage for `tools/gate_checks/done_checker_static.py` must keep passing unchanged —
this ticket must not weaken or alter `check_data_runs_clean`'s behavior (Out of Scope).

**Unit:**
- `tests/tools/test_done_checker_static.py` — all 34 existing tests, in particular the four
  `check_data_runs_clean`-specific tests (`test_data_runs_clean_empty_dirs_passes`,
  `test_data_runs_clean_file_before_start_ts_passes`,
  `test_data_runs_clean_file_at_or_after_start_ts_fails_naming_path`,
  `test_data_runs_clean_unparsable_start_ts_flags_any_file`) and the two `run_static_precheck`
  aggregate tests (`test_run_static_precheck_all_pass_eligible`,
  `test_run_static_precheck_surfaces_fail_not_masked`) — these pin the exact PASS/FAIL contract any
  new earlier-checkpoint function must reuse without modification.

**Integration / architecture guard:**
- None currently exist for `.claude/workflows/implement-ticket.js` itself — confirmed via repo-wide
  grep (`grep -rl "implement-ticket.js\|implement_ticket" tests/` → zero hits). There is no workflow-level
  JS test harness in this repo. This is a pre-existing gap, not something this ticket is expected to
  close (see New Tests Required below for how this bounds what's actually testable).

**Arena-combat:** Not applicable — this ticket touches no combat/simulation logic.

## New Tests Required

Because `.claude/workflows/implement-ticket.js` has no test harness (see Regression Surface), the
"add/update tests" AC is only satisfiable for the **new Python function(s)** backing whichever
earlier checkpoint Plan selects — never for the `.js` prompt/orchestration wiring itself, which can
only be verified by re-reading the diff (per AC #1's own wording: "verifiable by diffing the file's
phase prompts before/after," not by a test).

Per acceptance criteria:

1. **Test name:** `test_<new_function>_detects_leftover_artifacts_before_prior_checkpoint`
   (exact name depends on the function Plan introduces, e.g.
   `check_data_runs_clean_or_reuse` / a new `clean_data_runs_early(start_ts, ...)` wrapper).
   - **Category:** unit
   - **Verifies:** given files under `data/runs/`/`reports/release_proof/` with `mtime >= start_ts`
     (simulating Test-phase-generated artifacts not yet cleaned), the new function either (a) removes
     them and a subsequent `check_data_runs_clean(start_ts, ...)` call then returns `PASS`, or (b)
     returns a fail-fast signal — whichever design Plan selects (see investigation.md Risk #2).
   - **Location:** `tests/tools/test_done_checker_static.py` (if the function lives in the same
     module) or a new `tests/tools/test_<new_module>.py` alongside it, following the existing
     `tmp_path` + `os.utime()` fixture pattern already used for `check_data_runs_clean`'s own tests.

2. **Test name:** `test_<new_function>_preserves_files_older_than_start_ts`
   - **Category:** unit
   - **Verifies:** files with `mtime < start_ts` (a concurrent session's or genuinely stale
     prior-session artifacts) are **not** deleted/flagged by the new earlier checkpoint — guards
     against the concurrent-session-safety risk flagged in investigation.md (Risk #3). Mirrors
     `test_data_runs_clean_file_before_start_ts_passes`'s existing pattern exactly.

3. **Test name:** `test_<new_function>_reuses_check_data_runs_clean_definition`
   - **Category:** unit (architecture guard in spirit — pins the "same definition of clean" rule)
   - **Verifies:** the new function's flagging decision agrees with `check_data_runs_clean` given the
     identical fixture inputs (i.e. call both against the same `tmp_path` layout and assert
     equivalent PASS/FAIL outcomes) — enforces that the new checkpoint did not invent a second,
     diverging definition of "clean" (explicitly Out of Scope per the ticket).
   - **Location:** same file as tests 1-2.

4. **Test name:** `test_<new_status>_appears_in_failure_recovery_reference_table` (only if Plan
   introduces a new blocking status rather than pure auto-clean)
   - **Category:** unit / documentation guard
   - **Verifies:** `docs/ai/ticket-lifecycle.md`'s Failure Recovery Reference table contains a row for
     the new status, in the existing 4-column `| Return status | What failed | Fix | Re-run |` shape —
     a simple string-presence assertion against the doc file (mirrors how this repo already treats
     doc/table consistency as a checkable artifact elsewhere, e.g. `validate_frontmatter.py`'s
     checks). If Plan chooses pure auto-clean with no new status, skip this test — the AC's own
     wording ("if a new failure/return status was introduced") makes it conditional.
   - **Location:** `tests/tools/` (new small test file, e.g. `test_ticket_lifecycle_doc.py`) — no
     existing file owns doc-content assertions for `ticket-lifecycle.md`; confirm no such file exists
     before creating a new one (`grep -rl "ticket-lifecycle.md" tests/tools/` — not yet checked,
     verify at implementation time).

## Scoped Pytest Commands

```
pytest tests/tools/test_done_checker_static.py -v
```

If a new sibling module is created instead of extending `done_checker_static.py` directly, add its
test file explicitly:

```
pytest tests/tools/test_done_checker_static.py tests/tools/test_<new_module>.py -v
```

Never `pytest tests/` and never a bare `pytest tests/tools/` (over-broad relative to the change,
per the Testing Rule's scoping requirement) — scope to the exact file(s) touched.

## Anti-Drift Test Guards

- **Existing `check_data_runs_clean` tests must pass unmodified** — any diff to
  `tests/tools/test_done_checker_static.py`'s four `check_data_runs_clean`-specific tests (lines
  135-193) is a signal the ticket has drifted into changing the definition of "clean," which is
  explicitly Out of Scope. If those tests need to change, stop and re-check scope before proceeding.
- **`run_finalize_selfcheck` tests (lines 540-580) must pass unmodified** — guards against
  accidental scope creep into the Finalize self-check / `FINALIZE_INCOMPLETE` path, which is
  explicitly Out of Scope.
- **A concurrent-session-safety test (New Test #2 above) is not optional** — without it, a naive
  implementation of the earlier checkpoint could regress into an unconditional `rm -rf`, silently
  breaking a second in-flight `implement-ticket` run. This is the single highest-risk regression this
  ticket could introduce and must be explicitly guarded, not just implied by code review.
- **No test should assert on `.claude/workflows/implement-ticket.js`'s literal prompt text.** Per
  investigation.md, there is no JS test harness in this repo — any temptation to grep the `.js` file's
  prompt strings inside a pytest test would be testing prose, not behavior, and would be brittle
  against future prompt wording changes. Confirm the AC's own "verifiable by diffing the file's phase
  prompts before/after" language (a manual/PR-review check, not a test) is respected instead.
