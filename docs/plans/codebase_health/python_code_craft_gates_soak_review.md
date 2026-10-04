---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-04
tags: [delivery, planning]
---

# Python Code Craft: M4 gates soak review (DRAFT, finalize after 2026-10-17)

Ticket `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`. Window for the ratchet: 2026-10-03T16:47:13Z (PR #305 merged) to
2026-10-17. **This is a draft written on 2026-10-04 from the first ~12 hours of the window; every count below is
re-measured on the final day and the "Final" column filled in before the flip PR merges.** Method: `gh run list` for
`test.yml` runs created since #305's merge; per run, the check-run warning annotations of the `Code health (advisory)`
and `Type check (informational)` jobs (step conclusions are useless here: a `continue-on-error` step reports
`success`). Run logs are not readable from this environment (log hosts blocked), so a finding's identity is taken
from the annotation counts and the PR it ran on, not from the job summary.

## Counts (draft, 2026-10-04 ~14:00Z)

| Measure | Draft | Final |
|---|---|---|
| `test.yml` runs in the window (PR + main pushes) | 69, of which 68 ran the `code-health` job (1 skipped) | |
| Runs where the ratchet step exited 1 (new/worse violations) | 4: goal-dispatch-impl (PR #291) 3 violations; perf-m1-partial-lift (PR #319) 2 violations on two pushes; `main` after #319 merged, 2 violations | |
| Runs where the ratchet could not run (exit 2, "could not run" warning) | 0 | |
| Runs with new mypy errors / mypy could not run | 0 / 0 (no `mypy-baseline` warning on any `Type check (informational)` job) | |
| Registry reseeds on `main` | 1: #315 added 111 `ast_grep` rows with the rule pack (new tool rows, no existing row reseeded) | |
| mypy-baseline syncs | 0 after the first commit of the baseline | |
| Rows reviewed (`reviewed: true`) / total rows | 0 / 3724 | |
| Rows tightened or deleted by the flip | 6 tightened, 4 deleted (all paid-off debt, evidence below) | |

## Findings and dispositions

1. **PR #291 (`goal-dispatch-impl`): 3 new/worse violations**, then clean at its final head. Disposition: real
   (function-local imports `PLC0415` in `src/ai/goals/scorers.py` and `src/content_semantics/faction.py`, and an
   unsorted import block `I001` in `faction.py`); the author fixed them before merge. This is the ratchet doing its job.
2. **PR #319 (`perf-m1-partial-lift`) and the `main` push after it: 2 violations each**: a new ruff `C901` in
   `src/core/protocol_validator.py` and `ProtocolValidator.validate_result_batch` at complexipy 24 above the ceiling 18.
   Disposition: real. Fixed by perf in #320 (`c049b9d65`); the row for `validate_result_batch` is now "gone" and is
   deleted by this flip. `main` was red on the advisory job between the two merges, which a required check would have
   prevented; this is the argument for fixing before the flip, not a false positive.
3. **False-positive classes found: none so far.** To confirm at the end of the window.
4. **Tool noise:** the `Node.js 20 is deprecated` annotation on 68 runs (`actions/setup-node@v4`); a one-off
   `setup-uv` cache-reservation warning on one `Type check` run. Neither changes a result.

## Deferred SARIF live proof (TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK)

PR #291 is a same-repository PR that edits `src/`. At commit `65731e0c9` the code-scanning check run `ruff`
(app `github-advanced-security`) reported **failure, "4 new alerts including 4 errors"**; its annotations are
`src/ai/goals/scorers.py:105` and `:106` and `src/content_semantics/faction.py:78` (twice: `PLC0415` and `I001`). All
three files are in the PR's diff, and the 4 alerts are the 3 ratchet units of finding 1 (the two `scorers.py` lines
are one `PLC0415` group). At the final head `c659d67a7` the `ruff`, `complexipy` and `ast-grep` check runs all report
success, "No new alerts in code changed by this pull request". So the PR showed exactly its own new findings, and the
alerts cleared when they were fixed. These are standalone check runs; `tools/delivery/pr_status.py` does not see them,
so read them with `gh pr checks` or the check-runs API. **Verdict: proof obtained.** (Confirm no later PR contradicts
it by the end of the window.)

## The mypy window is one day shorter than the ratchet's

The mypy gate (`codebase/gates/mypy_gate.py`) and `codebase/baselines/mypy_baseline.txt` first reached `main` inside
PR #313 (merged 2026-10-04T04:59:04Z), so mypy's advisory window runs 2026-10-04T04:59Z to 2026-10-18T04:59Z, not to
2026-10-17. Decision 8.18 merges the batch on or after 2026-10-18, so merging after 05:00Z on 2026-10-18 gives mypy its
full 14 days as well. Reported to codebase-planner on 2026-10-04.

## Live demos and the Ubuntu 26 pre-check

Run links (throwaway draft PR #331, based on the #329 branch, never merged; job-level results read from check-run step conclusions and annotations; a run shows "cancelled" overall when the next push superseded it):
- Step 1, clean, `Code health` and `Type check` on `ubuntu-26.04` (701bf7c8f): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37210551134 , both jobs passed.
- Step 2, one new ruff finding plus one new mypy error in `src/core/zz_demo_violation.py` (b1bd27209): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37210796539 , `Code health` failed at the `Code health ratchet` step (`::error::code-health: 2 new/worse violations`), `Type check` failed at the `mypy` step (`::error::mypy-baseline: 1 new errors`).
- Step 3, top-level package `src/zz_flip_demo` with no registry row (20386ff93): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37211037495 , `Code health` failed only at `Package registry` (the ratchet step passed); in `Tools · a–e`, `test_committed_registry_loads_and_is_schema_valid_and_complete` failed with `[completeness] tracked top-level package has no row: src/zz_flip_demo`.
- Step 4, the row added (ec6afd47e): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213113973 , `Code health` (both steps) and `Tools · a–e` passed.
- Step 5, one silent `except OSError: pass` in `src/core/zz_demo_e3.py` (e3ee1784e): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213577739 , `Code health` failed at the `Code health ratchet` step (`::error::code-health: 1 new/worse violations`; the single finding is `ast_grep e3-silent-except`); `Type check` passed.

**Ubuntu 26 pre-check:** step 1 set `runs-on: ubuntu-26.04` for `code-health` and `typecheck` on the throwaway branch only (the label is listed as generally available by the runner-images announcement, actions/runner-images issue 14748; `ubuntu-latest` begins migrating on 2026-10-19). Both jobs ran with that label and passed with no skip note and no error; nothing changed in PR #329.

Side effect of the demo, not of the flip: adding any `src/` file bumps `tests/unit/tools/test_mechanism_registry_completeness_check.py::test_wider_scope_numbers_pinned` (`scope_files == 296`), so `Unit · infra / observability` failed on steps 2 and 5 of the demo; a real PR that adds a `src/` module must update that pin (testing / mechanism-registry owner).

## Decision: jscpd may fail to run without failing the check

`scan.run_scan` raised `ToolUnavailableError` for any non-zero `npx` exit, which `check` turned into exit 2. With the
step blocking, an npm registry blip would fail a required check for a tool that is report-only by decision 16. The
planner approved (2026-10-04) a separate `SKIPPABLE_TOOLS = {jscpd}` (never derived from `REPORT_ONLY_TOOLS`, with
`SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS` pinned by a test): a jscpd that cannot run is "not measured", noted in the
summary and as a `::warning::`, its registry rows are left out of the comparison (never "gone"), and `seed`/`tighten`
never skip. Exit 2 stays for ruff, complexipy, line counts, ast-grep and every registry error.

## Rows tightened or deleted (evidence: `check` on `origin/main` 053f459e4)

Tightened: `engine/legality.py` I001 3->2 and PLC0415 5->4; `perf/scenarios.py` F401 4->1 and I001 2->1;
`LongRunStabilityHarness.execute_run` complexipy 50->47; `LegalityServiceV2` class-length 596->584.
Deleted: `ProtocolValidator.validate_result_batch` complexipy; `engine/checkpoint.py` I001; `perf/scenarios.py` PLC0415;
`build_metropolis_state` function-length. After `tighten --yes`: `OK: 0 new, 0 worse, 0 improved, 0 gone, 3724 unchanged`.

## Verdict (draft)

No false-positive class and no exit-2 run in the first part of the window; every failing run was a real new or worse
violation. The flip is on track, subject to the final-day re-measurement and the precondition that `main` is
ratchet-clean and mypy-gate-clean at the flip commit (re-run right before merge).
