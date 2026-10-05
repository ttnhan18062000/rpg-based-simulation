---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-04
tags: [delivery, planning]
---

# Python Code Craft — Gates Flip Ticket Brief (M4 flip + both M5 flips)

Scoping brief for the codebase implementer. Lands as `docs/plans/codebase_health/python_code_craft_gates_flip_ticket_brief.md`
in the batch's planning commit. The binding plan is `docs/plans/codebase_health/python_code_craft_roadmap.md`
(decisions 8.5, 8.10, 8.13; M4 and M5 rows in Section 7).

**Owner decisions 2026-10-04 (record as roadmap 8.18 and 8.19):**
- **8.18 One flip batch.** The M4 flip (soak ends 2026-10-17) and both M5 flips (soaks end 2026-10-18) ship in one
  branch and one PR, merged **on or after 2026-10-18**: one announcement to the other planners, one branch-protection
  change.
- **8.19 SARIF stays advisory.** The `code-health-sarif` job is changed-line feedback only. It exits 0 on findings by
  design, skips fork PRs, and the ratchet already blocks new violations. Its `continue-on-error` stays permanently; it
  is not one of the gates the flip makes blocking.

**Schedule change (owner, 2026-10-04, "go on with your recommendation" = prepare now, merge on 10-18):** work
starts now, not 2026-10-17. Unchanged: the merge is **on or after 2026-10-18** (8.18), and each soak review covers its
full window, so the soak reviews are drafted now and finalized after the window ends (2026-10-17 for ticket 1,
2026-10-18 for tickets 2 and 3). The PR stays open until then. Live demos and the ruleset change come at the end, each
with the owner's yes. The tickets may move to `inprogress/` now.
**Precondition update:** the #319 debt in `src/core/protocol_validator.py` was fixed by perf in PR #320 (`c049b9d65`).
Re-run the ratchet and the mypy gate on fresh `origin/main` anyway, now and again right before merge.

**Handoff docs ride in this PR (owner, 2026-10-04: no standalone handoff PRs).** In the planning commit, add to
`docs/plans/codebase_health/handoffs/` (pattern of #322's three files; a new dated section in each existing file):
- **agent-working:** `docs/guides/agent_working_path_map.md` is prefix-only, so frozen citations of the old snapshot
  history path resolve to a missing file. Ask for a per-file entry mapping the old path to
  `codebase/reports/codebase_health_history.jsonl` (moved in #326).
- **rpg:** (a) two M7 move ideas from the cycle re-check: take the world CLI out of `worldbuilding` (closes the world*
  cycles); move `GeneticProfile` into `core` (the only real `core`->`systems` edge, `core/state.py:24`). Ideas only,
  `src/` stays frozen. (b) the phase19 decision testing asked for (import-linter condition 3): are `kernel.py`'s
  function-local observability imports (lines 149/304/305/316/1241; re-check on main) allowed with a reason, or
  violations needing an engine ticket?
- **testing:** this PR is the flip PR; it honours their #322 constraints (tagged, PERF_RE pin, scenario lane stays
  non-required).
The owner relays the open PR to the other-machine sessions.

## Batch

Branch `python-code-craft-gates-flip` (fresh from `origin/main`). Tickets, in order:

1. `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING` (folder `todos/python-code-craft-gates/`): ratchet + mypy blocking.
2. `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING` (folder `todos/python-code-craft-structure/`): depends on 1
   (the job-level `continue-on-error` must already be gone, or removing the step's does nothing).
3. `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING` (same folder): depends on 1 (removes `ast_grep` from the report-only
   set that ticket 1 creates).

(`TCK-20261004-CODE-HEALTH-IMPACT-TESTS-LOCAL-ENV` and `TCK-20261004-CODEBASE-HEALTH-HISTORY-MOVE`, once
planned here, shipped early in PR #326, `a6d2e54f9`, 2026-10-04.)

**Constraints from testing's reply on #322 (2026-10-04, `test-architecture-reviewer`):**
- Tag `test-architecture-reviewer` on the flip PR.
- The scenario lane's routing regex (`PERF_RE` in `.github/workflows/test.yml`) is pinned by
  `tests/unit/tools/test_scenario_lane_paths.py` against `tools/test_architecture/scenario_lane_paths.py`. Any
  job-list or path-filter edit keeps them in sync. Run that test before pushing.
- The scenario lane stays non-required: the flip must not make it required as a side effect, and the ruleset change
  names only `Code health` and `Type check`.

**Planning-commit addition:** update `TCK-20261004-IMPORT-LINTER-ADOPTION` (in `todos/python-code-craft-structure/`)
with testing's agreement and its four conditions (#322 comment, 2026-10-04):
1. a class E test is retired only in or after the PR that makes its replacement contract a required check;
2. parity is shown per retired test (the injected violation, and the contract failing on it);
3. phase19 `test_hot_path_does_not_import_heavy_analyzers` is an expectation change, not a retirement: the
   engine/observability owner first decides whether `kernel.py`'s function-local imports at 149/304/305/316/1241 are
   allowed (allowlist with a reason) or violations (an engine ticket);
4. the blind spots and the stale allowlist are covered by contracts. The `or True` assert
   (`tests/unit/observability/test_decision_trace.py:376`) is testing's, not one of the eight.
The ticket stays BLOCKED on the owner's yes and on condition 3's decision (routed to rpg in a later handoff).

Closing 1 closes `TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC` (children 1–6 done) and moves `python-code-craft-gates/`
to done. `IMPORT-LINTER-ADOPTION` stays in `python-code-craft-structure/`, so that folder stays open.

## Planning commit (first commit of the branch, before any code)

- This brief, at its `docs/plans/codebase_health/` path.
- Append `.claude/handover/next-batch/src_package_structure_audit_cycles_addendum.md` to
  `docs/plans/codebase_health/src_package_structure_audit.md` as its "Addendum 2026-10-04" section. Re-run its scan
  on the batch's base commit first and update the numbers if `src/` changed.
- Roadmap Section 7: M6 row and Order line gain "done 2026-10-04 (PR #318)"; M5 row drops the follow-ups #318
  delivered (ast-grep SARIF and snapshot, `exemplar_modules`); add an **M5 soaks** line under the M4 soak line:
  start 2026-10-04 (PR #315 merged 2026-10-04T06:26:43Z), end 2026-10-18. Section 8 gains 8.18 and 8.19.
- Both M5 flip tickets: write those soak dates into Assumptions (they were never written at the #315 merge).
- `AST-GREP-RULE-PACK-FLIP-BLOCKING`: delete the scope bullet "Decide whether the SARIF changed-line feedback should
  include `ast_grep`". #318 (`TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT`) already did it; under 8.19 nothing more is needed.
- `CODE-HEALTH-GATES-FLIP-BLOCKING`: rewrite scope per "Ticket 1" below (the SARIF and report-only changes); its
  acceptance criterion "The three gates fail a PR..." becomes "The ratchet and mypy gates fail...".
- Move the three tickets to `agent-working/tickets/inprogress/` with Status INPROGRESS when work starts (now, per
  the schedule change above); the soak reviews are finalized only after their windows end.

## Constraints for every ticket

- No file under `src/` in the merged diff (decision 8.7). The live demos below touch `src/` only on throwaway
  branches that are never merged.
- No threshold, tool version, or existing registry row changes, except rows the soak review shows are false positives,
  each listed with its reason.
- Tests that pin CI or the Makefile may be edited (decision 8.11); the testing planner gets an outbox note.
- Heavy local runs go one at a time under `systemd-run --user --scope -p MemoryMax=2G`; use `.venv/bin/python3`.
- Before pushing, run the repo-wide guard tests (`tests/tools/test_*guard*.py`), `tests/static`, `tests/codebase`,
  and compare total pass/skip counts with main's latest run.

## Facts measured 2026-10-04 (planner, on `main` at 474ebdcc)

- **The ratchet has no report-only set.** `codebase/health/__main__.py::_cmd_check` returns `1 if result.failed`, and
  `ratchet.compare` treats every tool alike. jscpd and `ast_grep` findings fail the check today; only the step's
  `continue-on-error` hides it. Removing `continue-on-error` alone would make jscpd and ast-grep block, which goes
  against the owner's decisions (jscpd report-only, ast-grep has its own soak).
- `codebase/gates/sarif_feedback.py` runs ruff, complexipy **and ast-grep** (since #318), exits 0 on findings and
  2 only when a tool, its SARIF, or the registry cannot be used.
- `.github/workflows/test.yml`: `code-health` job has job-level `continue-on-error: true` (a backstop for setup
  failures), step `Code health ratchet` has its own, step `Package registry` has its own. The job is named
  `"Code health (advisory)"`, the typecheck job `"Type check (informational)"`. Step `mypy` runs
  `python3 -m codebase.gates.mypy_gate` with `continue-on-error: true` (gate already returns 1 new / 2 cannot run).
- `Makefile` `typecheck-py` ends in `|| true`.
- `docs/parity_ledger/infrastructure.yaml` INFRA-TYPE-001 says "advisory ... continue-on-error until the soak ends".
- Tests that mention advisory status (check each, edit only what pins advisory behavior): `tests/codebase/`
  `test_mypy_gate.py`, `test_typecheck_gate_configured.py`, `test_code_health_ci_summary.py`,
  `test_package_registry.py`, `test_ci_code_health_sarif.py`, `test_code_health_sarif_feedback.py`,
  `test_edit_ratchet_hook.py`; `tests/static/test_ci_uv_install.py`, `test_ci_step_summary_reporting.py`.
- Docs that describe the soak: `docs/guidelines/agent_working_environment.md` ("Reading code-health results on a PR
  (advisory soak)"), `docs/guidelines/python_code_standard.md` Enforcement cells, the CI comments above each job.

## Ticket 1 — CODE-HEALTH-GATES-FLIP-BLOCKING

1. **Soak review** (`docs/plans/codebase_health/python_code_craft_gates_soak_review.md`): window 2026-10-03 → 10-17.
   From the `code-health` and `typecheck` job summaries of every PR and main push in the window (`gh run list`,
   `gh run view --log` or check-run annotations if logs are blocked): runs, runs with exit 1 / exit 2, each new or
   worse finding and its disposition (real / false positive / tool noise), reseeds and mypy-baseline syncs (from git
   log of the two baseline files), reviewed-row count. Also the deferred SARIF live proof: did a same-repository PR
   that touched `src/` show exactly its new findings in code scanning? A false-positive class found here is fixed
   before the flip, or the flip stops and the planner is told.
   **SARIF live proof candidate (found by the planner):** PR #291 (rpg, same repository, edits `src/`). The
   code-scanning check run `ruff` (app `github-advanced-security`) reported failure, "4 new alerts including 4
   errors", at commit `65731e0c9`, then success at the final head `c659d67a7`. Confirm that those 4 were the PR's own
   new findings and cite this as the deferred proof. Note: those check runs are standalone check runs.
   `tools/delivery/pr_status.py` does not see them (rpg's #322 reply; fix on PR #316), so read them with `gh pr checks`
   or the check-runs API.
   **Hard precondition: `main` is ratchet-clean and mypy-gate-clean at the flip commit.** The ratchet reads all of
   `src/`, so a new or worse finding already on `main` fails every domain's PR once blocking. Run
   `python3 -m codebase.health check` and the mypy gate on fresh `origin/main` immediately before the PR, again
   right before merge. Each finding is fixed by the owning domain, or grandfathered as a reviewed registry row with
   that domain's stated reason, recorded in the soak review. Never reseed silently to clear it. Known on 2026-10-04:
   PR #319 (perf, cf7cbcb08) left `src/core/protocol_validator.py` with a new ruff C901 (line 41) and
   `ProtocolValidator.validate_result_batch` complexipy 24 > ceiling 18; perf-planner was asked to fix it or give a
   reason (see the handover note for the answer). The same run showed one improved row (`execute_run` 47 < 50) and one
   gone row (`checkpoint.py` I001): tighten or delete them in the batch, as the ratchet suggests.
2. **Report-only set in the ratchet.** A named constant (e.g. `REPORT_ONLY_TOOLS = frozenset({"jscpd", "ast_grep"})`
   in `codebase/health/ratchet.py`) and `check` exits 1 only for new/worse findings of other tools; report-only
   findings still appear in the report and summary, labelled report-only. No CLI flag: the set is policy, in code,
   with a test per side (a new jscpd and a new ast_grep finding → exit 0 and listed; a new ruff finding → exit 1).
   Exit 2 (cannot run) is unchanged and still covers every tool, jscpd included.
   **Open for the implementer to confirm, then tell the planner:** whether an `npx`/jscpd failure should still exit 2
   once blocking. If it makes the required check flaky on network, propose an exit-2 exemption for report-only tools
   before writing it.
3. **CI:** remove `continue-on-error` from the `Code health ratchet` step and from the `mypy` step. Keep the
   job-level one on `code-health` only if the owner wants a setup-failure backstop; default **remove** it (a broken
   setup must not read as a pass for a required check), and say so in the PR. `Package registry` keeps its step-level
   one until ticket 2. Rename jobs `"Code health (advisory)"` → `"Code health"` and `"Type check (informational)"` →
   `"Type check"`, then update the test pins. **The renamed names are what branch protection lists.** Rewrite the CI
   comments. SARIF job: untouched except its comment ("advisory permanently, decision 8.19").
4. **Makefile:** drop `|| true` from `typecheck-py`; fix the `##` help text of `typecheck-py` and of `code-health` (it names the old job and says "never fails the PR").
5. **Docs/ledger:** INFRA-TYPE-001 text and `v2_evidence`; environment guide section retitled and rewritten (blocking
   for ruff/complexipy/line counts/mypy; report-only jscpd and, until ticket 3, ast-grep; SARIF advisory);
   standard's Enforcement cells where they say "advisory".
6. **Live demo (owner-authorized pushes only):** two throwaway draft PRs from scratch branches, never merged, closed
   after the runs: (a) adds one new ruff violation and one new mypy error in a `src/` file → `Code health` and
   `Type check` fail; (b) a no-`src/` change → both pass. Record run links in the ticket. Ask the owner before the
   first push of each.
7. **Owner action:** mark `Code health` and `Type check` required in the `main` ruleset. Record the date and who did it.

## Ticket 2 — PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING

As filed, plus: soak window 2026-10-04 → 10-18 (review can only be complete on 10-18). Remove the `Package registry`
step's `continue-on-error`. Add the completeness assertion to the real-repo test in
`tests/codebase/test_package_registry.py`, which turns a lane-blocking test into a second enforcement point. That is
intended at the flip and is the reason it waited (review-checklist rule: a live-repo completeness test in a blocking
lane makes the rule blocking). Live demo: draft PR adding an empty top-level `src/<name>/` package with no row → fails;
with a row → passes. Required check: already covered by `Code health` (same job); record that no separate setting is needed.

## Ticket 3 — AST-GREP-RULE-PACK-FLIP-BLOCKING

As filed minus the SARIF bullet. Soak window 2026-10-04 → 10-18; per-rule false positives for N3, N4, E3. Remove
`ast_grep` from `REPORT_ONLY_TOOLS` (jscpd stays). Flip the test from ticket 1 that pinned ast_grep as report-only.
Live demo: a draft PR adding one bare `except: pass` (E3) in a `src/` file → `Code health` fails. Docs: environment
guide and standard N3/N4/E3 Enforcement cells.

## Announcement (planner, before work starts)

When the batch starts (2026-10-17), codebase-planner tells every planner (live: perf-planner, asset-planner;
outbox: rpg-planner, testing-planner, agent-working-planner) the merge date. From that date a PR that edits `src/`
fails on a new ruff/complexipy/line-count/mypy/ast-grep (N3, N4, E3) finding or a new top-level `src/` package
without a registry row. `make code-health` and `make typecheck-py` reproduce it locally.

## Out of scope

`src/` edits; import-linter adoption; jscpd blocking; tightening ceilings; SARIF blocking; M7.
