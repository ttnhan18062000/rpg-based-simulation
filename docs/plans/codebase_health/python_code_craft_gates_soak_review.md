---
status: active
layer: testing
authority: P2
audience: agent
date: 2026-10-04
tags: [delivery, planning]
---

# Python Code Craft: M4 gates soak review (FINAL, window cut short by the early merge)

Ticket `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`. Planned window for the ratchet: 2026-10-03T16:47:13Z (PR #305
merged) to 2026-10-17. **The window was not completed.** The owner merged the flip batch (PR #329, squash `c8c355459`) on
2026-10-05T14:47:13Z, 13 days early, so the measured window is about 2 of the planned 14 days (about 1 day for mypy,
whose window began 2026-10-04T04:59Z). The #329 squash title says "merge on or after 2026-10-18"; that is wrong as
history and is left as is. The "Draft" column below is the 2026-10-04 reading; the "Final" column was measured on
2026-10-05 over the runs that exist (see "Final measurement"). The verdict is therefore about a short window, not the
two weeks the plan asked for. Method: `gh run list` for
`test.yml` runs created since #305's merge; per run, the check-run warning annotations of the `Code health (advisory)`
and `Type check (informational)` jobs (step conclusions are useless here: a `continue-on-error` step reports
`success`). Run logs are not readable from this environment (log hosts blocked), so a finding's identity is taken
from the annotation counts and the PR it ran on, not from the job summary.

## Counts (draft, 2026-10-04 ~14:00Z)

| Measure | Draft | Final |
|---|---|---|
| `test.yml` runs in the window (PR + main pushes) | 69, of which 68 ran the `code-health` job (1 skipped) | 163 runs created 2026-10-03T16:47Z to 2026-10-05T14:47Z (116 pull_request, 45 push, 2 schedule); 162 of them have job rows (2 job-list calls returned HTTP 502 and were not retried) |
| Runs where the ratchet step exited 1 (new/worse violations) | 4: goal-dispatch-impl (PR #291) 3 violations; perf-m1-partial-lift (PR #319) 2 violations on two pushes; `main` after #319 merged, 2 violations | 75 runs reported new/worse violations (53 on 23 pull-request branches, 22 on `main`; the throwaway demo branch excluded). Most are the 27 rows other domains added and the owner accepted (below), which stayed on `main` and so re-failed every later run |
| Runs where the ratchet could not run (exit 2, "could not run" warning) | 0 | 0 for the ratchet. 30 runs showed `mypy-baseline could not run ... exited 3` (the `mypy_gate` exit-code defect, below), 2026-10-05T04:52Z to 14:16Z |
| Runs with new mypy errors / mypy could not run | 0 / 0 (no `mypy-baseline` warning on any `Type check (informational)` job) | 41 / 30 (see the two later sections) |
| Registry reseeds on `main` | 1: #315 added 111 `ast_grep` rows with the rule pack (new tool rows, no existing row reseeded) | 1 (unchanged) |
| mypy-baseline syncs | 0 after the first commit of the baseline | 1, in the flip branch on 2026-10-05 (3 added, 9 dropped) |
| Rows reviewed (`reviewed: true`) / total rows | 27 / 3723 (the 27 accepted violations below; 0 / 3724 before 2026-10-05) | 27 / 3723 |
| Rows tightened or deleted by the flip | 6 tightened, 4 deleted (all paid-off debt, evidence below); then on 2026-10-05 17 more lowered and 2 deleted | 23 lowered and 6 deleted in total |

## Findings and dispositions

1. **PR #291 (`goal-dispatch-impl`): 3 new/worse violations**, then clean at its final head. Disposition: real
   (function-local imports `PLC0415` in `src/ai/goals/scorers.py` and `src/content_semantics/faction.py`, and an
   unsorted import block `I001` in `faction.py`); the author fixed them before merge. This is the ratchet doing its job.
2. **PR #319 (`perf-m1-partial-lift`) and the `main` push after it: 2 violations each**: a new ruff `C901` in
   `src/core/protocol_validator.py` and `ProtocolValidator.validate_result_batch` at complexipy 24 above the ceiling 18.
   Disposition: real. Fixed by perf in #320 (`c049b9d65`); the row for `validate_result_batch` is now "gone" and is
   deleted by this flip. `main` was red on the advisory job between the two merges, which a required check would have
   prevented; this is the argument for fixing before the flip, not a false positive.
3. **False-positive classes found: none** in the measured window (about 2 days). Not confirmed over the planned 14: a rare false positive would not have had time to appear.
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

## Violations other domains added during the window, accepted as reviewed rows (2026-10-05)

`origin/main` at the merge into this branch carried **27 ratchet violations (1 new, 26 worse)** that `src/` PRs of other
domains added while the ratchet was advisory. They are real findings (no false positive: each value was measured on the
changed file at the PR's commit and its parent with ruff, complexipy and the line-count tool, and the delta sits in that PR's
diff). The owner decided on 2026-10-05 to accept all 27 as debt: they are recorded in `codebase/baselines/code_health_exceptions.jsonl`
as **reviewed** rows (`reviewed: true`, value = ceiling = the measurement), in the same commit that tightened the improved rows
and deleted the gone ones. This is the evidence the window was meant to produce: a blocking ratchet would have stopped each of
these PRs at its own CI. The registry schema has no `reason` field, so the reason for each row (the PR and the owning domain) lives
in this table and in `handoffs/handoff_to_rpg.md`; `check` after the commit reads `OK: 0 new, 0 worse`.

| PR | domain | row | before -> after |
|---|---|---|---|
| #328 | architecture / world | `worldgeneration/generator.py` ProceduralCompositionGenerator.generate `complexipy cognitive-complexity` | 62 -> 63 |
| #328 | architecture / world | `worldgeneration/generator.py` ProceduralCompositionGenerator.generate `line_count function-length` | 161 -> 191 |
| #333 | combat | `domains/cooperation/providers.py` PartnerCandidateProvider.get_candidates `line_count function-length` | 92 -> 93 |
| #333 | combat | `engine/combat.py` `ruff I001` | 6 -> 7 |
| #333 | combat | `systems/strategic_systems/intelligence.py` `line_count module-length` | 1788 -> 1798 |
| #333 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem `line_count class-length` | 1634 -> 1639 |
| #333 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem.fused_strategic_pass `line_count function-length` | 394 -> 399 |
| #335 | world | `engine/kernel.py` Kernel `line_count class-length` | 1381 -> 1384 |
| #335 | world | `engine/kernel.py` Kernel.__init__ `line_count function-length` | 302 -> 307 |
| #335 | world | `engine/kernel.py` `line_count module-length` | 1415 -> 1419 |
| #335 | world | `worldgeneration/generator.py` ProceduralCompositionGenerator._assign_region_namespaces `complexipy cognitive-complexity` | new -> 18 |
| #335 | world | `worldgeneration/generator.py` ProceduralCompositionGenerator.generate `line_count function-length` | 191 -> 198 |
| #341 | world | `worldbuilding/compiler.py` WorldCompiler `line_count class-length` | 602 -> 604 |
| #341 | world | `worldbuilding/compiler.py` WorldCompiler.compile `line_count function-length` | 509 -> 511 |
| #342 | combat | `core/state.py` EntityState.to_canonical_dict `complexipy cognitive-complexity` | 27 -> 32 |
| #342 | combat | `core/state.py` EntityState.to_canonical_dict `line_count function-length` | 97 -> 100 |
| #342 | combat | `core/state.py` `line_count module-length` | 1705 -> 1708 |
| #342 | combat | `engine/tactical.py` TacticalDecisionSystem `line_count class-length` | 800 -> 816 |
| #342 | combat | `engine/tactical.py` TacticalDecisionSystem.evaluate_entity_intent `line_count function-length` | 714 -> 720 |
| #342 | combat | `systems/strategic_systems/intelligence.py` `line_count module-length` | 1798 -> 1824 |
| #342 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem `line_count class-length` | 1639 -> 1664 |
| #342 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem.evaluate_strategic_intent `complexipy cognitive-complexity` | 220 -> 233 |
| #342 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem.evaluate_strategic_intent `line_count function-length` | 542 -> 567 |
| #342 | combat | `systems/strategic_systems/work_queue.py` StrategicWorkQueue.build `complexipy cognitive-complexity` | 81 -> 83 |
| #342 | combat | `systems/strategic_systems/work_queue.py` StrategicWorkQueue.build `line_count function-length` | 107 -> 112 |
| #345 | world | `worldbuilding/compiler.py` WorldCompiler `line_count class-length` | 604 -> 607 |
| #345 | world | `worldbuilding/compiler.py` WorldCompiler.compile `line_count function-length` | 511 -> 514 |
| #347 | combat | `engine/executor.py` LocalSequentialExecutor.execute `complexipy cognitive-complexity` | 27 -> 29 |
| #347 | combat | `engine/executor.py` LocalSequentialExecutor.execute `line_count function-length` | 132 -> 138 |
| #347 | combat | `systems/strategic_systems/intelligence.py` `line_count module-length` | 1824 -> 1832 |
| #347 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem `line_count class-length` | 1664 -> 1672 |
| #347 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem.fused_strategic_pass `complexipy cognitive-complexity` | 425 -> 433 |
| #347 | combat | `systems/strategic_systems/intelligence.py` StrategicIntelligenceSystem.fused_strategic_pass `line_count function-length` | 399 -> 407 |
| #347 | combat | `systems/strategic_systems/redirection.py` StrategicRedirectionSystem.enforce `complexipy cognitive-complexity` | 94 -> 102 |
| #347 | combat | `systems/strategic_systems/redirection.py` StrategicRedirectionSystem.enforce `line_count function-length` | 126 -> 134 |

Tightened in the same commit (improved on `main`): `core/dirty.py` `mark_from_update` complexipy 41->39; `campaigns/orchestrator.py` module 1138->1124, class 1016->1002, PLC0415 25->24; `engine/executor.py` PLC0415 20->19; `engine/kernel.py` BLE001 12->11, F821 3->2, I001 19->17, PLC0415 85->83, e3 2->1, `_run_initial_placement_check` 84->83, jscpd 31->30; `engine/legality.py` PLC0415 4->2; `engine/worker_logic.py` PLC0415 4->3; `party.py` I001 3->2; `intake.py` `evaluate_salience` 20->17; `worldassembly/schema.py` jscpd 38->35. Deleted (gone): `systems/social_systems/party.py` F821 and PLC0415. 17 lowered, 2 deleted.

## Mypy errors other domains added during the window (accepted 2026-10-05)

`python3 -m codebase.gates.mypy_gate` on the merged tree found 3 errors not in the baseline: `worldassembly/resolve_io.py:30` no-any-return (#328, architecture / world), `engine/tactical.py:853` arg-type (#342, combat), `systems/strategic_systems/intelligence.py:1823` boredom_delta arg-type (#342, combat; 15 -> 16 call sites). Accepted by the owner as debt and added to `codebase/baselines/mypy_baseline.txt` with `mypy_baseline sync`; the same sync dropped 9 entries that other PRs had fixed (kernel `json` NameError, party `StrategicUpdate` NameError twice, and 6 others). Baseline: 1569 -> 1563 entries. The baseline format has no reason field, so the reasons live here and in `handoffs/handoff_to_rpg.md`.

**A real defect in the gate, found by this:** `mypy-baseline filter` exits with the NUMBER of new errors (capped at 100), but the gate accepted only 0 and 1, so two or more new errors were reported as "mypy-baseline could not run ... exited 3" (exit 2). That is what `main` showed on 58aa22f67 and #351. Fixed in this branch: the gate returns 1 for any number of new errors and 2 only when the tool cannot run (a non-zero filter exit with no `error:` line, e.g. an unparseable baseline); three new tests pin it. Before the flip this only produced a confusing advisory message; after it, a contributor with two errors would have been told the tool was broken.

## Open ideas (follow-ups, not tickets)

- A `reason` field on registry rows (and a reviewed-row command that takes it): this window's 27 accepted rows keep their PR and domain only in this document and `handoffs/handoff_to_rpg.md`. The planner judged the docs enough for a one-off (2026-10-05); revisit if accepting debt becomes routine.

## Final measurement (2026-10-05)

Source: `gh run list --workflow test.yml` for runs created 2026-10-03T16:47:13Z to 2026-10-05T14:47:13Z, then per run the
`Code health` and `Type check` job annotations (warning level) via the check-runs API. Counts are runs, not distinct
findings. The 75 ratchet-failing runs are dominated by the 27 accepted rows persisting on `main`; the 22 `main` runs
and the pull-request runs that inherited them are the same debt seen repeatedly, not 75 independent defects. The
41 mypy runs with new errors are runs that reported `mypy-baseline: N new errors` (N=1 before the 3 accepted errors landed; not
broken down further); the 30
"could not run" runs are the `mypy_gate` exit-code defect, which only produced a misleading advisory message.

## Verdict (final)

Short window, so weak evidence for "no false positives" and strong evidence for "the ratchet and mypy gate catch real
regressions": 0 false positives and 0 ratchet exit-2 runs in about 2 days, 1 real tool defect (`mypy_gate` exit code,
fixed before the flip), and 27 + 3 real violations that other domains added while the gates were advisory.
First-draft verdict follows. No false-positive class and no exit-2 run in the first part of the window; every failing run was a real new or worse
violation, including the 27 that other domains' PRs added to `main` and the owner accepted as reviewed rows on 2026-10-05 (evidence for the flip: the blocking ratchet would have stopped each at its own CI). The flip is on track, subject to the final-day re-measurement and the precondition that `main` is
ratchet-clean and mypy-gate-clean at the flip commit (re-run right before merge).
