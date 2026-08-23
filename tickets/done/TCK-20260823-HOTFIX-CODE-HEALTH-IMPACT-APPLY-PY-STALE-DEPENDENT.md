---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT
phase: open
date: 2026-08-23
tags: [testing]
---

# TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT

## Title
Fix stale `src/engine/apply.py`-as-dependent-of-`pipeline.py` assumption in `test_code_health_impact.py`'s real-path smoke tests

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/tools/test_code_health_impact.py::test_real_path_pipeline_includes_kernel_as_dependent` and
`::test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data` both assert
`"src/engine/apply.py" in report["dependents"]` (and in the formatted text) for
`chi.build_impact_report(_REPO_ROOT, "src/engine/pipeline.py")`. Both currently fail: real
`graphify` no longer reports `src/engine/apply.py` as a dependent of `src/engine/pipeline.py`.

Confirmed via direct source inspection (not just the graphify graph): `src/engine/apply.py` does
not import `src/engine/pipeline.py` anywhere (only a docstring mention of the word "pipeline"), and
`src/engine/pipeline.py` does not import `src/engine/apply.py` either — there is no direct import
edge between them in either direction in the current codebase. `src/engine/kernel.py` (which does
import `apply.py`) correctly still appears as a dependent — that half of both tests' assertions
passes. The `apply.py` assumption appears to predate a refactor that removed whatever import chain
used to connect the two files; neither file has been touched by any of this session's tickets (last
real edits: both files last changed in commit `29d78798` "Simulation quality (#20)", 2026-08-14,
well before this session's work began 2026-08-21).

Discovered during the Test phase of `TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR` (2nd ticket of
the codebase-health-observatory-tooling batch) — surfaced only because that ticket's fresh worktree
had no `graphify-out/graph.json` until `graphify update .` built one for the first time; the main
checkout's own possibly-stale cached graph may have been masking this. Confirmed pre-existing and
unrelated to that ticket's own change (it touches no `src/` path; both forbidden-to-touch files
`tools/code_health_impact.py`/`tests/tools/test_code_health_impact.py` were correctly left
untouched, and the failure was reported truthfully rather than routed around).

## Scope
- Investigate the real current dependency relationship (if any, direct or transitive within the
  test's implicit expected depth) between `src/engine/apply.py` and `src/engine/pipeline.py`.
- If no real relationship exists any more: update both tests' assertions to drop the stale
  `apply.py` expectation, replacing it with a currently-real dependent path if the test's intent
  (demonstrating multiple, not just one, dependent surfaces in the formatted/truncated output) still
  needs a second example path.
- If a real relationship does exist (e.g. via a transitive/indirect chain this investigation should
  trace, not assumed away) and `graphify`'s dependent-resolution is itself missing it: that would be
  a `tools/code_health_impact.py` or `graphify` bug, not a test bug — scope changes accordingly and
  flag for design if the fix belongs to a different subsystem entirely.

## Out of Scope
- Any change to `tools/pr_impact_report.py` or its tests (the sibling ticket that discovered this;
  already shipped/shipping independently, not blocked by this ticket).
- Any change to `tools/code_health_impact.py`'s actual dependent-resolution logic unless
  investigation confirms the bug is there rather than in the test's stale assumption.

## Acceptance Criteria
- [x] Root cause determined: stale test assumption vs. real `graphify`/`code_health_impact.py` gap.
- [x] Both affected tests pass again, reflecting the real current dependency graph.
- [x] `pytest tests/tools/test_code_health_impact.py -v` fully passes.

## Related Tickets
- TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR (discovered this during its own Test phase)
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND (original ticket that added these tests)

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent per CLAUDE.md's hotfix convention.

## Related Code Areas
- tests/tools/test_code_health_impact.py
- tools/code_health_impact.py (read-only reference unless investigation proves the bug is here)
- src/engine/apply.py
- src/engine/pipeline.py

## Assumptions / Open Questions
- Whether the main checkout's own `graphify-out/graph.json` (gitignored, per-checkout) already
  reflects this same drift, or whether it happens to still be stale in a way that masks the failure
  there — not verified in this worktree (cannot inspect the main checkout's local state from here).

## Implementation Notes
Root-cause determination was performed by the orchestrator prior to dispatching this implementation
step, and re-verified briefly here rather than re-derived from scratch: `src/engine/apply.py` has no
`import` of `src/engine/pipeline.py` (its only mention of "pipeline" is a docstring reference to an
unrelated contract file), and `src/engine/pipeline.py`'s own import list (grep-confirmed at the top
of the file) does not include `apply.py` either. With `DEFAULT_AFFECTED_DEPTH = 2` in
`tools/code_health_impact.py`, this rules out `apply.py` as a dependent of `pipeline.py` at the depth
the tool resolves. This is a stale test-fixture assumption (Scope's first branch), not a
`tools/code_health_impact.py` or `graphify` bug — `tools/code_health_impact.py` was not touched.

Both real-path smoke tests in `tests/tools/test_code_health_impact.py` asserted
`"src/engine/apply.py" in report["dependents"]` / `in formatted`. Replaced both with
`"src/engine/scenario_checkpoint.py"`, the real second dependent of `pipeline.py` (confirmed via
`chi.build_impact_report()` against the real repo: 176 total dependents, with
`scenario_checkpoint.py` immediately after `kernel.py`). It preserves both tests' original intent —
demonstrating a second, same-subsystem (`src/engine/`) dependent surfaces correctly in both the raw
data and the truncated/sorted formatted output, not just `kernel.py` alone. Added an inline comment
citing this ticket ID next to the docstring-style narrative in
`test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`, explaining why
the example path changed, without deleting the original truncation-window-fix narrative (still
historically accurate).

## Test Summary
- `PYTHONPATH=. .venv/bin/python3 -m pytest tests/tools/test_code_health_impact.py -v` — 24 passed,
  0 failed, including both previously-failing tests
  (`test_real_path_pipeline_includes_kernel_as_dependent` and
  `test_real_path_pipeline_kernel_visible_in_formatted_output_not_just_internal_data`).
- `PYTHONPATH=. .venv/bin/python3 -m pytest tests/tools/ -k "code_health_impact or codebase_health or pr_impact_report" -q`
  — 64 passed, 2430 deselected, no regressions in the broader tools/ scope.

## Files Changed
- tests/tools/test_code_health_impact.py (updated two stale `apply.py` assertions to
  `scenario_checkpoint.py`; added ticket-cited comment explaining the change)
- tickets/inprogress/TCK-20260823-HOTFIX-CODE-HEALTH-IMPACT-APPLY-PY-STALE-DEPENDENT.md (this file —
  status, acceptance criteria, implementation notes, test summary, files changed, completion summary)

`tools/code_health_impact.py` was intentionally NOT modified — investigation confirmed no bug there.

## Completion Summary
Confirmed the pre-supplied root-cause finding (no import edge between `src/engine/apply.py` and
`src/engine/pipeline.py` in either direction, ruling out dependency even at the tool's depth-2
resolution) and fixed the two stale real-path smoke tests in `tests/tools/test_code_health_impact.py`
by swapping the `apply.py` assertion for `scenario_checkpoint.py`, the actual current second
dependent of `pipeline.py`. All 24 tests in the target file pass, and the broader
code-health/codebase-health/pr-impact-report regression scope (64 tests) passes with no regressions.
`tools/code_health_impact.py` was left untouched, as required.
