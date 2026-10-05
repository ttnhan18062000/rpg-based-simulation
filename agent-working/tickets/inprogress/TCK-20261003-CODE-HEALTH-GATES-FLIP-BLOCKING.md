---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Title
M4f: After the two-week soak, make the code-health ratchet, SARIF step and mypy baseline block new violations

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Decision 8.5/8.10: advisory for a two-week soak, then blocking for new violations only. Owner decision 2026-10-03: mypy flips together with the ratchet; jscpd stays report-only. BLOCKED until the soak end date, which TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB records here.

## Scope
- Soak review first (`docs/plans/codebase_health/python_code_craft_gates_soak_review.md`; window 2026-10-03 to 2026-10-17, drafted now, finalized after the window): runs, exit-1 and exit-2 runs, each new or worse finding and its disposition, reseeds and mypy-baseline syncs, reviewed-row count, and the deferred SARIF live proof (PR #291, `ruff` check run at `65731e0c9` "4 new alerts", success at `c659d67a7`)
- Precondition: `main` ratchet-clean and mypy-gate-clean at the flip commit; re-run now and right before merge. **Updated 2026-10-05 (owner decision):** `origin/main` carried 27 violations (1 new, 26 worse) added by other domains' PRs during the soak (#328, #333, #335, #341, #342, #345, #347); this branch records them as reviewed baseline rows and tightens 17 improved / deletes 2 gone rows (`check` after: `OK: 0 new, 0 worse`; table in `python_code_craft_gates_soak_review.md`, list for rpg in `handoff_to_rpg.md`). Mypy had the same problem: 3 new errors (`resolve_io.py:30` #328, `tactical.py:853` #342, `intelligence.py:1823` #342) are added to the baseline as accepted debt (1569 -> 1563 entries after the sync also dropped 9 fixed ones). **Gate wording bug found and fixed here:** `mypy-baseline filter` exits with the number of new errors, so `mypy_gate` reported 2+ new errors as "could not run" (exit 2); it now returns 1 for any number and 2 only when the tool cannot run (3 tests in `tests/codebase/test_mypy_gate.py`). That wording was also what main's advisory job showed (`-m mypy_baseline exited 3`). So on merge day the precondition expects only violations NEWER than that commit: anything `check` reports on the merged tree is a PR that landed after 2026-10-05, to be fixed by its owner or recorded the same way with the owner's yes, never silently reseeded. Clean on `origin/main` 053f459e4 (2026-10-04)
- Ratchet: a named `REPORT_ONLY_TOOLS = frozenset({"jscpd", "ast_grep"})` in `codebase/health/ratchet.py`; `check` exits 1 only for new/worse findings of other tools; report-only findings stay in the report and summary, labelled report-only. A separate `SKIPPABLE_TOOLS = frozenset({"jscpd"})` (network/npx dependency, `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`): if jscpd cannot run it is skipped as "not measured" (never "gone"), with a summary line and a warning annotation; exit 2 stays for every other tool and for registry errors (planner decision 2026-10-04)
- Tighten the 6 improved rows and delete the 4 gone rows on the branch base; the check then reports 0 improved, 0 gone
- CI: remove `continue-on-error` from the `Code health ratchet` step, the `mypy` step and the `code-health` job (default: remove the job-level backstop; a broken setup must not read as a pass for a required check); `Package registry` keeps its step-level one until its own flip; rename the jobs "Code health" and "Type check"; rewrite the CI comments; the SARIF job is untouched except its comment ("advisory permanently, decision 8.19")
- Remove `|| true` from the `make typecheck-py` recipe and fix the `##` help text of `typecheck-py` and `code-health`
- Update INFRA-TYPE-001 text and `v2_evidence`, the environment guide section, the standard's Enforcement cells and the tests that pin advisory status
- Live demos (owner-authorized pushes only, throwaway draft PRs, never merged): (a) one new ruff violation and one new mypy error in a `src/` file fail `Code health` and `Type check`; (b) a no-`src/` change passes both
- Ruleset change (owner action; record date and who), **only in one sitting on 2026-10-18 at or after 05:00Z, never before #329's workflow is on `main`**: `main`'s workflow still names the jobs `Code health (advisory)` and `Type check (informational)`, so requiring `Code health` and `Type check` earlier would leave every other open or new PR waiting forever on "Expected". Order: (1) fresh `origin/main` precondition re-run (ratchet including ast_grep, `packages validate`, `mypy_gate`); (2) push the closure commit to #329, CI green; (3) the owner adds exactly two required checks in the `main` ruleset, `Code health` and `Type check`, and nothing else (not the scenario lane, not the SARIF job); (4) `gh pr checks 329 --required` lists both, recorded here as the proof; (5) merge #329 (`--admin`, `--match-head-commit`, owner's yes). Steps 3 to 5 within minutes. After the merge, PRs already open show the new required checks as "Expected" until their next push or a re-run (the `pull_request` run used the merge ref from when it ran); the announcement tells the other planners to re-run or update their branch.

## Out of Scope
- Any file under src/
- Gating jscpd or line-count beyond what the ratchet already does (jscpd report-only)
- Raising strictness or tightening ceilings

## Acceptance Criteria
- [ ] Soak review written with dates, counts and dispositions
- [ ] The ratchet and mypy gates fail a PR that introduces a new violation and pass one that does not (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
- TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
- TCK-20261003-MYPY-BASELINE-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-001)

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tests/codebase/test_typecheck_gate_configured.py

## Assumptions / Open Questions
- **Explicit step (done in `TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE`, the next codebase batch): the real soak start (the merge date of PR #305) and end (start + 14 days) are written into this ticket, the epic and roadmap Section 7.**
- Soak start: 2026-10-03 (PR #305, the PR that carries the advisory CI job, merged 2026-10-03T16:47:13Z). Soak end: 2026-10-17 (start + 14 days)
- Blocking gates affect every domain that edits src/; announce the date to other planners before flipping

## Implementation Notes
- Policy in code (`codebase/health/ratchet.py`): `REPORT_ONLY_TOOLS = {jscpd, ast_grep}` and a separate `SKIPPABLE_TOOLS = {jscpd}`, pinned `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`. `RatchetResult.failed` keeps its meaning (edit hook and staged ratchet); `blocking_failed` is what `check` exits 1 on.
- **Decision (planner, 2026-10-04): jscpd is exempt from exit 2.** `scan.run_scan(..., skippable=)` returns the tools that could not run; `check` skips them ("not measured", never "gone": their rows are left out of the comparison), writes a summary line and a `::warning::`, and exits 0/1 from the other tools. Reason: with the step blocking, an npm registry or `npx --yes` failure would fail a required check for a tool that is report-only by decision 16. Exit 2 stays for ruff, complexipy, line_count, ast_grep and any registry error. `check --from DIR`, `seed` and `tighten` never skip, so a partial scan can never delete jscpd rows or reseed from one.
- Annotations on `check` and `mypy_gate` changed from `::warning::` to `::error::` (they now fail a required check); the skip note stays a `::warning::`.
- CI: no `continue-on-error` on the `code-health` job, the `Code health ratchet` step or the `mypy` step (a broken setup must not read as a pass for a required check). **Kept on purpose:** the "Paths this PR changed" step (it truncates `/tmp/changed.txt` first and a failed diff only changes summary ordering) and `Package registry` (until its own flip). Jobs renamed `Code health` and `Type check`. The workflow has no path filter and neither job has an `if:`, so a required check cannot hang in "expected".
- Hang backstops (planner review): `_run(..., timeout=)`, passed only by jscpd (`JSCPD_TIMEOUT_S = 300`); a timeout is a skip. `timeout-minutes: 20` on `code-health` and `10` on `typecheck` (measured max 183 s and 96 s over 40 runs of 2026-10-03/04).
- Registry: `tighten --yes` after reading the list: 6 rows lowered, 4 deleted (see the soak review); `check` then reports `0 improved, 0 gone`.
- Precondition measured 2026-10-04 on `origin/main` 053f459e4: `check` exit 0 and `mypy_gate` exit 0. To be repeated right before merge.
- Live demo (owner chose option B, one throwaway draft PR with successive pushes; steps 1 and 2 are this ticket's):
  Run links (throwaway draft PR #331, based on the #329 branch, never merged; job-level results read from check-run step conclusions and annotations; a run shows "cancelled" overall when the next push superseded it):
  - Step 1, clean, `Code health` and `Type check` on `ubuntu-26.04` (701bf7c8f): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37210551134 , both jobs passed.
  - Step 2, one new ruff finding plus one new mypy error in `src/core/zz_demo_violation.py` (b1bd27209): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37210796539 , `Code health` failed at the `Code health ratchet` step (`::error::code-health: 2 new/worse violations`), `Type check` failed at the `mypy` step (`::error::mypy-baseline: 1 new errors`).
  - Step 3, top-level package `src/zz_flip_demo` with no registry row (20386ff93): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37211037495 , `Code health` failed only at `Package registry` (the ratchet step passed); in `Tools · a–e`, `test_committed_registry_loads_and_is_schema_valid_and_complete` failed with `[completeness] tracked top-level package has no row: src/zz_flip_demo`.
  - Step 4, the row added (ec6afd47e): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213113973 , `Code health` (both steps) and `Tools · a–e` passed.
  - Step 5, one silent `except OSError: pass` in `src/core/zz_demo_e3.py` (e3ee1784e): https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/37213577739 , `Code health` failed at the `Code health ratchet` step (`::error::code-health: 1 new/worse violations`; the single finding is `ast_grep e3-silent-except`); `Type check` passed.
- Ubuntu 26 pre-check: step 1's jobs ran with the label `ubuntu-26.04` (listed as generally available by the runner-images announcement, actions/runner-images issue 14748, whose `ubuntu-latest` migration begins 2026-10-19) and passed; nothing changed in the PR.
- Side effect of the demo, not of the flip: adding any `src/` file bumps `tests/unit/tools/test_mechanism_registry_completeness_check.py::test_wider_scope_numbers_pinned` (an exact `scope_files` count; 296 at #331's runs, main has since moved it), so `Unit · infra / observability` failed on steps 2 and 5 of the demo; a real PR that adds a `src/` module must update that pin (testing / mechanism-registry owner).
- Authorization record: each demo push followed a direct owner yes (AskUserQuestion). For step 3 the push command ran after the yes, but its output was lost in a session interruption; the retried command reported "Everything up-to-date", so the push had already happened. That the first execution of the same command did it is an inference, not something the record shows.
- The mypy gate first reached `main` in PR #313 (2026-10-04T04:59Z), so its window ends 2026-10-18T04:59Z; the merge is on or after 2026-10-18 05:00Z.

## Test Summary
- Two `tests/codebase` tests fail on this machine only (a 60 s test budget, identical on clean `main`, green in CI): `tests/codebase/test_codebase_health_baseline.py::test_make_target_runs_successfully_with_plausible_values` and `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end`. Tracked by `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT` (`agent-working/tickets/todos/`); not a result of this flip.

## Files Changed

## Completion Summary
