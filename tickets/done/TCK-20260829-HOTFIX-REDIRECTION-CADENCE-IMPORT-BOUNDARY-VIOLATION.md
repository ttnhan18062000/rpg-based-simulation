---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION
phase: done
date: 2026-08-29
tags: [engine, architecture]
---

# TCK-20260829-HOTFIX-REDIRECTION-CADENCE-IMPORT-BOUNDARY-VIOLATION

## Title
`src/systems/strategic_systems/redirection.py` gained a module-level `systems -> engine` import
not in the pinned exceptions list, breaking `test_systems_do_not_import_engine_outside_pinned_exceptions`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live during a post-batch double-check review of the `m1-quick-wins` batch (real, direct
`pytest` verification, not trusted from any prior self-report).
`TCK-20260824-TOWN-CENTER-POINTER-FIX` (commit `94e96218`) added `from src.engine.cadence import
SystemCadence` at `src/systems/strategic_systems/redirection.py:11` (module level, used for the
`enforce(..., cadence: SystemCadence = None)` parameter's default-instantiation
`cadence = cadence or SystemCadence()` inside the function body) to give `StrategicRedirectionSystem`
an injectable cadence. This is a genuine, real `systems -> engine` import-boundary violation:
`tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
fails for real (confirmed directly, not assumed -- a naive `pytest` invocation from outside the
worktree can spuriously report this test PASSING because `_iter_py_files`'s relative `src/systems`
path resolves against whatever `cwd` pytest was launched from, silently scanning a different
branch's checkout if run from the wrong directory; always run this test with cwd set to this
worktree). This file already has ONE pinned exception for the same module,
`("src/systems/strategic_systems/redirection.py", 23): ("src.engine.cadence", ("should_run",))`
-- a function-scoped import inside `enforce()`'s own body, not a module-level one. The new
`SystemCadence` import was added at module scope instead of following that same already-accepted,
already-pinned function-scoped pattern for the exact same module.

This slipped past `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own Test phase because that ticket's
scoped pytest command never included `tests/architecture/` -- its own new/modified files were all
under `src/{worldbuilding,systems/strategic_systems,systems/world_systems}/` and `tests/{unit,integration}/`,
not `tests/architecture/`, so the structural test-scope-coverage backstop had no reason to flag it.

## Scope
- **Recommended fix (restructure, not pin)**: since `src/systems/strategic_systems/redirection.py`
  already has `from __future__ import annotations` (line 1, confirmed), the `cadence: SystemCadence`
  parameter annotation is never evaluated at runtime regardless of whether `SystemCadence` is a real
  importable name at module scope -- move the type name into the existing `if TYPE_CHECKING:` block
  (for IDE/mypy support only) and move the real runtime import into the SAME existing function-scoped
  import statement already present inside `enforce()` for `should_run` (i.e.
  `from src.engine.cadence import SystemCadence, should_run`, replacing the current two separate
  imports with one). This keeps the file's real behavior byte-identical, avoids adding a second
  pinned exception, and follows the file's own already-established pattern instead of diverging from
  it -- confirm this compiles and the `enforce()` default-cadence-instantiation behavior is unchanged
  by a real test run before/after.
- **Alternative (only if the restructure proves non-trivial for some reason not yet found)**: add a
  second pinned exception entry for `("src/systems/strategic_systems/redirection.py", 11):
  ("src.engine.cadence", ("SystemCadence",))` in both
  `tests/architecture/test_phase18_import_boundaries.py`'s `_SYSTEMS_ENGINE_PINNED` dict and
  `docs/audits/D14_coupling_depth.md`, with a real rationale -- do not silently choose this path
  over the restructure without documenting why the restructure wasn't viable.
- Confirm `tests/architecture/test_phase18_import_boundaries.py::test_systems_do_not_import_engine_outside_pinned_exceptions`
  passes for real afterward (run with cwd set to the repo worktree, not the main checkout).

## Out of Scope
- Any other pinned-exception entries in `_SYSTEMS_ENGINE_PINNED` -- this ticket is scoped to the
  one new violation found, not a general audit of all 13+ existing pins
- `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own broader scope -- already closed, not reopened by
  this ticket; this is a narrow, self-contained follow-up

## Acceptance Criteria
- [ ] `test_systems_do_not_import_engine_outside_pinned_exceptions` passes for real (verified with
      cwd correctly set to the worktree, not a spurious pass from scanning the wrong branch)
- [ ] Either the restructure lands (preferred, no new pinned exception added) or a new pinned
      exception is added to both the test file and `docs/audits/D14_coupling_depth.md` with a
      documented rationale for why the restructure wasn't chosen
- [ ] `StrategicRedirectionSystem.enforce()`'s real behavior (default-cadence instantiation) is
      unchanged, confirmed by a real test run

## Related Tickets
- TCK-20260824-TOWN-CENTER-POINTER-FIX (where this import was introduced)

## Related Docs
- docs/audits/D14_coupling_depth.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/strategic_systems/redirection.py
- tests/architecture/test_phase18_import_boundaries.py

## Assumptions / Open Questions
None -- self-evident intent, minimal targeted fix (a local-import restructure, or a documented pin
as a fallback).

**New blocking discovery found during execution (2026-08-29)**: after applying the recommended
restructure, the target test still fails -- but for a reason entirely outside this ticket's own
scope. See Implementation Notes below. Not resolvable without either widening this ticket's scope
(explicitly forbidden by the "Out of Scope" section above) or a separate follow-up ticket.

## Implementation Notes
Recommended fix applied exactly as scoped:
- Moved `SystemCadence` into the existing `if TYPE_CHECKING:` block (for annotation-only use;
  `from __future__ import annotations` means it's never evaluated at runtime).
- Deleted the module-level `from src.engine.cadence import SystemCadence` (was line 11).
- Merged the runtime import into `enforce()`'s existing function-scoped import: changed
  `from src.engine.cadence import should_run` to `from src.engine.cadence import SystemCadence,
  should_run` (now at line 25 -- unchanged from before the edit, since removing the module-level
  import and adding one line to the `TYPE_CHECKING` block net to zero line-count change above it).
  `cadence = cadence or SystemCadence()` (the default-cadence-instantiation line) is byte-identical.
- The file's ONE existing pinned exception, `("src/systems/strategic_systems/redirection.py", 23):
  ("src.engine.cadence", ("should_run",))`, was already stale before this ticket touched anything:
  the actual import has always been on line 25, not 23 -- confirmed via `git show 94e96218 --
  src/systems/strategic_systems/intelligence.py` that the SAME originating commit
  (`TCK-20260824-TOWN-CENTER-POINTER-FIX`) shifted line numbers across this file too, without
  updating the pin table. Updated the SAME existing pin entry's key/value in place -- `(redirection.py,
  25): ("src.engine.cadence", ("SystemCadence", "should_run"))` -- in both
  `tests/architecture/test_phase18_import_boundaries.py`'s `_SYSTEMS_ENGINE_PINNED` dict and
  `docs/audits/D14_coupling_depth.md`'s table (line `23` -> `25`). This is an update to the one
  already-accepted pin for this exact import statement, not a second new pinned exception -- no
  behavior change, verified by isolated re-run of the test's own scan logic against just this file
  (clean, zero violations) and by `tests/unit/strategic/test_redirection.py` passing unchanged.

**Blocking discovery (root-caused, not guessed)**: `test_systems_do_not_import_engine_outside_pinned_exceptions`
still FAILS end-to-end, run with cwd correctly set to this worktree -- but now on
`src/systems/strategic_systems/intelligence.py:70` (`src.engine.policy`), a file this ticket never
touches. Root cause: the SAME commit `94e96218` (`TCK-20260824-TOWN-CENTER-POINTER-FIX`) also edited
`intelligence.py` (added an import line near the top, removed/added lines mid-file around its
routine-blocker pass) without updating that file's own 9 pinned-exception line numbers in
`_SYSTEMS_ENGINE_PINNED` (lines 69/75/78/83/664/829/833/905/958 in the dict vs. actual current
70/76/79/84/663/828/832/904/957). This was invisible to `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own
Test phase (never touched `tests/architecture/`, per this ticket's own Request Summary) AND
invisible to this ticket's original investigation, because the test's `assert` fires on the FIRST
violation found per file and `redirection.py`'s NEW, unpinned module-level import was encountered
first in `os.walk` file-iteration order -- masking the pre-existing `intelligence.py` drift entirely
until the `redirection.py` violation was fixed.

Per this ticket's own explicit "Out of Scope" text ("Any other pinned-exception entries in
`_SYSTEMS_ENGINE_PINNED` -- this ticket is scoped to the one new violation found, not a general audit
of all 13+ existing pins" and "not reopening `TCK-20260824-TOWN-CENTER-POINTER-FIX`'s own broader
scope"), `intelligence.py`'s 9 stale pins were NOT touched here. Filed
`tickets/todos/TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT.md` as the follow-up to
correct them (same fix pattern as this ticket's own redirection.py pin correction). This ticket's
own AC #1 ("test passes for real") therefore cannot be satisfied without that follow-up landing
first, or without this ticket's scope being explicitly widened by a human decision -- neither of
which this ticket is authorized to do unilaterally per Gate Integrity.

**Resumption (2026-08-29, same date, later in the day)**: the sibling ticket
`TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT` landed independently (moved to
`tickets/done/`), correcting all 9 stale `intelligence.py` pin keys in the same two shared files
this ticket already touched (`tests/architecture/test_phase18_import_boundaries.py`'s
`_SYSTEMS_ENGINE_PINNED` dict and `docs/audits/D14_coupling_depth.md`'s table), without reverting or
altering this ticket's own already-in-place `redirection.py` pin correction (line 25) in either file.
With both tickets' fixes now present together in the same working tree, this ticket's Test phase was
re-run for real (not trusted from any prior summary) -- see Test Summary below -- and
`test_systems_do_not_import_engine_outside_pinned_exceptions` now passes end-to-end. This ticket's
blocker is cleared; proceeding through post-Test cleanup, Parity (no ledger update required -- see
below), Verify, and Finalize.

**Parity check (behavior_changed=false, but `redirection.py` is a real `src/` path so the skip
condition doesn't apply -- full parity check performed rather than skipped)**: searched
`docs/parity_ledger/strategic_cognition.yaml` for existing entries citing `redirection.py`. Found
`STRAT-260` (added by `TCK-20260824-TOWN-CENTER-POINTER-FIX`), whose `v2_evidence` cites
`StrategicRedirectionSystem.enforce()`'s "Return to Town" fallback and
`nearest_town_tile()`-call behavior by function name only -- no line numbers, so this ticket's
line-25 import restructure doesn't invalidate the citation. Its `test_path`
(`tests/unit/strategic/test_redirection.py::test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`)
was re-confirmed passing in this same Test re-run. No parity ledger update needed --
`git status --porcelain -- docs/parity_ledger/` is empty after this check.

**Security-Review**: not triggered -- ticket tags (`engine`, `architecture`) do not include
`security`, and no `/security-review` skill was flagged during scoping. Phase skipped per the
conditional gate.

**Verify**: static DoD pre-check (`done_checker_static.run_static_precheck`) run for real -- all
applicable conditions PASS, staging-artifact and frontmatter-validation conditions correctly N/A for
hotfix tier. `tools/validate_frontmatter.py` confirms the ticket's own frontmatter is valid.
`READY_TO_CLOSE`.

## Test Summary
**First attempt (blocked)**:
`pytest src/systems/strategic_systems/redirection.py tests/architecture/test_phase18_import_boundaries.py tests/unit/strategic/test_redirection.py -v`
(run with cwd = this worktree): 5 passed, 1 failed.
- PASS: all 4 other `test_phase18_import_boundaries.py` tests, `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort`.
- FAIL: `test_systems_do_not_import_engine_outside_pinned_exceptions` -- on `intelligence.py:70`, unrelated to this ticket's own change (see Implementation Notes).
- Isolated re-check of just `redirection.py` against the test's own scan logic: 0 violations, fully clean.
- `enforce()`'s default-cadence-instantiation behavior (`cadence = cadence or SystemCadence()`) confirmed byte-identical via source inspection and the passing unit test above.

**Resumption re-run (after `TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT` landed)**:
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
src/systems/strategic_systems/redirection.py
tests/architecture/test_phase18_import_boundaries.py
tests/unit/strategic/test_redirection.py -v`, run with `cwd` explicitly set to this worktree
(`.claude/worktrees/docs-build-lastupdate-metadata-overhead`, confirmed via the pytest `rootdir` line
in the run's own output, not assumed): **6 passed, 0 failed**. All 5 `test_phase18_import_boundaries.py`
tests PASS, including `test_systems_do_not_import_engine_outside_pinned_exceptions` (previously
failing on `intelligence.py:70`, now clean because the sibling ticket's pin corrections are present
in the same file). `test_redirection_enforce_targets_nearest_town_tile_not_arbitrary_sort` PASS,
confirming `enforce()`'s behavior is unchanged. Acceptance Criterion #1 is now genuinely met.

## Files Changed
- `src/systems/strategic_systems/redirection.py` -- import restructure (recommended fix; this
  ticket's own change)
- `tests/architecture/test_phase18_import_boundaries.py` -- updated the existing redirection.py pin's
  key (line 23 -> 25, names expanded to include SystemCadence) as this ticket's own change; also
  carries the sibling ticket's 9 independent `intelligence.py` pin-lineno corrections in the same
  file (not this ticket's own work -- see `TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT`)
- `docs/audits/D14_coupling_depth.md` -- updated the corresponding `redirection.py` table row's line
  number (23 -> 25) as this ticket's own change; also carries the sibling ticket's `intelligence.py`
  row correction in the same file

## Completion Summary
DONE. This ticket's own recommended fix (moving `redirection.py`'s `SystemCadence` import into
`TYPE_CHECKING` and merging the runtime import into the existing function-scoped `should_run`
import) is implemented, verified correct, and behavior-unchanged. The ticket was correctly left
BLOCKED at `TESTS_FAILED` when its own fix, applied in isolation, could not make
`test_systems_do_not_import_engine_outside_pinned_exceptions` pass end-to-end -- the failure had
shifted to a pre-existing, unrelated line-number drift in `intelligence.py`'s pins, caused by the
same root-cause commit (`94e96218`) but out of this ticket's explicit scope. Rather than widening
scope or patching around the gate, a separate follow-up ticket
(`TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT`) was filed and has since landed
independently. With that sibling fix present in the same working tree alongside this ticket's own
change, the Test phase was re-run for real and now passes fully (6/6, cwd-verified). Parity ledger
required no update (STRAT-260's citation is function-level, unaffected by the import-location
change). Security-Review not triggered (no `security` tag). Verify: READY_TO_CLOSE (static DoD
pre-check all PASS/NA for hotfix tier). No known material gap remains.
