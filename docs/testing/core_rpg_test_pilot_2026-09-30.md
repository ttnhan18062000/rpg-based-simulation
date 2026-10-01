---
status: active
layer: testing
authority: P2
audience: agent
tags: [testing]
---

# Core-RPG test pilot report (2026-09-30)

Report for `TCK-20260929-EPIC-CORE-RPG-TEST-PILOT` (roadmap `docs/plans/test_architecture/roadmap.md` §3, §6). One
exercise, D1 (`TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING`), on a real surface. It is a workflow
demonstration, not a feature proof portfolio, and it is directional: it makes no causal claim. Evidence
files are in `stored_artifacts/TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING/pilot/`
(`inputs/`, `outputs/`; paths below are relative to it).

## Result

**`established` for the component demonstrations on a real surface (D1), with a scope-level stability caveat. Addendum 2026-10-01: the real `implement-ticket` pipeline has now run to DONE on a second, behaviour-owned ticket (capability 7, below), with five orchestrator interventions listed there, so "pipeline validation" is demonstrated only with those caveats. CI scenario execution is recorded in the CI note under capability 7 and is not claimed until CI has run.** The surface is resource conservation
(Mechanics Bible ch03 §3 Node Charges, §1 Atomic Conservation; `src/core/conservation.py`; parity
`TOWN-122`). `rpg-feature-planning` (2026-09-30, relaying `world-rule-catalog-design`) said the
`pressure-propagation-economy` epic does not plan to change conservation, harvesting or trade behaviour
per its declared scope, and has no schedule.

## What ran where

| Question | Answer |
|---|---|
| What ran locally | The 5 new tests plus the scoped unit set (54 passed), the manual `tests/mechanic_scenarios` run (53 passed), the report, impact report and `marker_check` runs, the injected-fault drill in a scratch worktree, and the report invalidations (capabilities 1, 3, 4, 5, 6). |
| What ran in CI | PR #265's ordinary fast lanes. The `Perf / cert / arena` job, the only job that runs `tests/mechanic_scenarios`, was **skipped**, so no scenario test ran in CI for this pilot. |
| Did the real `implement-ticket` Workflow pipeline run | **For D1: no.** D1 was hand-orchestrated, so the `architecture-reviewer` checklist, the `done-checker` test-plan field check (it did not exist then) and per-phase cost were not exercised. **For the second exercise (capability 7): yes, via the `/implement-ticket` skill** (the JS executed phase by phase with real phase agents), not via the native `Workflow` tool, which cannot parse `implement-ticket.js` (see capability 7). |
| What this establishes | That the component pieces (impact report, markers and check, test plan fields, triage procedure, report states) work on a real surface. |
| What it does not establish | D1 alone does not establish end-to-end pipeline behaviour or that CI runs scenario tests for such a change. Capability 7 adds one real pipeline run; CI scenario execution is recorded only from a real CI run. |

**Caveats that apply to every capability below:**
1. That confirmation is a scope-level read of the epic's tickets and summaries, not a line-by-line audit.
2. `origin/new_feature_planning` is the only remote branch with a diff on `src/core/conservation.py`.
   It is not live: last commit 2026-07-02, its PR #19 merged 2026-07-02, and the diff is only the branch
   lagging `main`. No open PR touches the file.
3. Not the authoritative-write boundary; no `src/` file was edited.

## Capabilities demonstrated

| # | Capability | Demonstrated | Artifact | Caveat next to it |
|---|---|---|---|---|
| 1 | Identify impacted domains and levels | **Yes, after two fixes made in this batch** | Before the fixes: `outputs/cap1_impact_d1_actual_paths_before_fix.{md,json}` and `outputs/cap1_impact_whatif_with_conservation_change_before_fix.md`. After: `outputs/cap1_impact_d1_actual_paths.{md,json}` and `outputs/cap1_impact_whatif_with_conservation_change.md` (a labelled what-if: D1's paths plus a change to `src/core/conservation.py`) | **First run (before fix), two shortfalls.** (i) For D1's own paths (two changed tests and a ledger file) the report returned tests, files and lanes but **empty Domains and Levels**. (ii) The what-if mapped `src/core/conservation.py` to **`substrate` only**, with levels `unit` and `kernel_integration` and **no `mechanic_scenario`**, although conservation is the ch03 economic law (this is the known "economy code lives in `src/core`" trap; `src.core` is a substrate root and the scenario level needs a non-substrate owner). So a real change to the economy's central law got no economy domain and no scenario recommendation, and the pilot's own tests declare `domain("economy")`. **After the fixes** (`TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS`): the what-if names `economy` and `substrate` and recommends `mechanic_scenario`; D1's changed tests contribute their declared domains and levels as `declared-marker` reasons. It also surfaced a real dependency in both runs: `tests/tools/test_parity_index_baseline.py` and 2 other tests read the changed ledger file, and were run. |
| 2 | Test plan citing the oracle source | Yes | `stored_artifacts/<D1>/test_plan.md` (Proof Plan: ch03 §3 and §1, `TOWN-122`) | The ledger entry had `test_path: null`, so the plan cites the oracle document and the parity id, not an existing proof. |
| 2b | Approved-oracle review | **Not demonstrated** | none | D-M2 was approved on 2026-09-30 (advisory, text only), after this pilot ran; the step was not exercised. No claim is made about approved-oracle review. |
| 3 | Choose or create a test with a documented pattern | Yes | `tests/unit/resource/test_node_charge_accounting.py` (4 tests), `tests/integration/kernel/test_node_charge_cross_actor.py` (1 test); markers per `docs/testing/test_taxonomy.md` §10; helpers `tests/helpers/{entities,resources}.py` | `marker_check` first flagged a real `level-placement-mismatch` (a `kernel_integration` test under `tests/unit/`); it was fixed by moving the test, and the second run reported 0 findings. |
| 4 | Run the correct local and CI lanes | Yes, with a gap | `outputs/cap4_scoped_local_run.txt` (54 passed, JUnit sha256 `d46b5826c7e7…`, run 2026-09-30T08:53:23Z); `outputs/cap4_scenario_lane_manual_run.txt` (`tests/mechanic_scenarios -m "not slow and not extra_slow"`, 53 passed, 15 s, JUnit `85a946282cbf…`, 08:53:16Z to 08:53:31Z); both at SHA `54a2198f9de928dc1135f3c04d2ba1744aaa08ed` | **CI would not have run the scenario lane for these paths.** `tests/mechanic_scenarios` runs only in the `Perf / cert / arena` job, gated by `PERF_RE` in `.github/workflows/test.yml`. D1's changed paths match none of it, and on PR #265 that job was `skipped`. The gate does match `src/core/`, so a change to `conservation.py` itself would trigger it; a change under `src/economy/` or `src/systems/` would not (F2). The CI rule is untouched (HOLD D-R2). The fast-lane CI run and job conclusions at the final head are recorded in the PR #265 body. |
| 5 | Interpret an injected failure and route it | Yes (drill) | `outputs/cap5_triage_record_DRILL.md`, `inputs/cap5_injected_fault.diff`, `outputs/cap5_new_tests_on_fault.txt`, `outputs/cap5_rerun_isolated.txt` | The fault was injected in a scratch detached worktree (removed, confirmed gone), so nothing was filed and nothing was sent to the feature team. Classified `Product regression` per `regression_policy.md` §13.2 with the full §13.1 record; routing stated as "would route to `rpg-feature-planning` per §13.4". |
| 6 | Report reflects evidence, with a state change after a deliberate invalidation | Yes | `outputs/cap6_before/`, `outputs/cap6_after_junit_dropped/`, `outputs/cap6_after_mutation_record_changed/` (`report.{json,md}`); inputs: `inputs/scoped_junit.xml`, `inputs/scenario_lane_junit.xml`, `inputs/cap6_mutation_record_copy/` | Two invalidations, both on copies. Dropping the scoped JUnit: the D1 unit file's state went from `pass` (4) to `not-run` (renamed `not-in-supplied-runs` in report schema_version 2, 2026-09-30; the stored artifacts keep the original label). A copy of the mutation record with a changed target hash, in a scratch worktree: `fresh` became `stale` with reason `target-changed` (and `worktree_dirty` true; that key was renamed `scanned_inputs_dirty` in schema_version 2 and covers only the inputs the report scans, not the whole repository; stored artifacts keep the original key). No tracked baseline was edited. |
| 7 | Real `implement-ticket` pipeline; per-phase cost; `architecture-reviewer` checklist; `done-checker` field check | **Demonstrated, with five orchestrator interventions listed below** | `stored_artifacts/TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP/` (investigation, plan, test_plan); the run's events in `agent-monitoring/data/2026-W40/conservation-rejection-path-assertions.{events,runs}.jsonl`; `tests/mutation/reruns/src_core_conservation_rerun.json` | Ticket: `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` (rpg-implementer (2)'s, test-only, standard tier). The run reached DONE after two earlier paused passes. See "Capability 7 detail" below for interventions, cost, what was and was not exercised, and environment facts. |

## Capability 7 detail (added 2026-10-01)

**Route.** The native `Workflow` tool rejected `implement-ticket` before any agent ran (`Script parse error: Unexpected token (182:78)`: a raw backtick inside a template literal at `.claude/workflows/implement-ticket.js:182`; `tests/tools/test_workflow_runtime_acorn_parse.py` pins `implement-ticket.js` as not parsing). That is a separate fact and is not the result of this exercise. The run used the `/implement-ticket` skill, which executes the same JS phase by phase with real phase agents (`ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`, `implementer`, `doc-updater`, `test-scoper`, `done-checker`, plus a finalizer) and the orchestrator-run gate checks.

**Outcome.** DONE: tests only, `src/` unchanged (empty `git diff origin/main -- src/`). Two new test files, 60 new tests, a scoped run of 906 passed and 1 skipped. A two-pass mutmut 2.5.1 re-run (private scratch install): pass 1 on the baseline's own 8 files reproduced 177 / 60 / 117 (positive control); pass 2 on those 8 plus the 2 new files gave 177 / 143 killed / 34 survived, all 22 `accepted=False` to `True` flip survivors killed. The record is `tests/mutation/reruns/src_core_conservation_rerun.json`, outside the baseline glob; the baseline is not refreshed and the core-RPG report cannot see the re-run. The before and after test sets differ, and the record names three existing end-to-end `TARGET_LOCKED` tests outside the selection so no artifact reads "survived" as "untested". No kill rate or equivalence claim is made.

**Orchestrator interventions (each one is an intervention, not part of "the pipeline ran"):**
1. **User stop after pass 1.** The planner wrote `## Unresolved Questions (decide before the implementer runs; ...)` under three genuine owner decisions. The static gate `plan_gate_static.py` matches only the bare heading, so it returned "no unresolved questions" and the JS would have continued. The user, reading the plan, chose to stop. The run record's `NEEDS_HUMAN_INPUT` status is the orchestrator's pause, not the gate's verdict (draft hotfix `TCK-20260930-PLAN-GATE-HEADING-SUFFIX-FALSE-NEGATIVE`).
2. **`todos_source_path` passed to Finalize and Verify by hand.** On a resumed run `scope_ticket_relocate.py` returns an empty `todos_source_path` (`already_in_inprogress`), so the JS's Finalize would not delete the `tickets/todos/` copy and the Verify prompt would not declare it as an expected duplicate.
3. **`record_events.py` re-run with `ts` set.** The JS pushes the Parity-skipped event with a null timestamp, and the writer rejected the batch (`missing fields ['ts']`). The first write failed atomically; the re-run set the timestamp.
4. **Verdict string normalized by hand.** The Architecture-Verify agent returned `APPROVED (no confirmed real violations)`. The JS compares the exact string (`archVerify.verdict !== 'APPROVED'`), so **strictly the gate would have stopped there**. The orchestrator treated it as `APPROVED`. This is not presented as a pass.
5. **An added sentence in the Architecture-Verify prompt** asking whether the agent ran a test-quality checklist, which the workflow script does not contain. The checklist is wired into `.claude/agents/architecture-reviewer.md`, so it should run unprompted, but this run only shows that it runs when asked.
Also: the three paused or resumed passes themselves, and the owner's decisions between them (recorded in the ticket), were manual. The shadow reviewer (below) ran as the JS specifies.

**What was and was not exercised.**
- Test-plan Proof Plan fields: the real `investigator` produced them in all three passes, and the `done-checker` advisory (agent-working PR #268) ran at Verify and reported `OK ... all mandatory Proof Plan fields present`. The same check was run afterwards, by hand, on D1's stored `test_plan.md` and also reported OK. So the fields are present on two tickets, with D1 checked after the fact and not inside a pipeline.
- Test-quality checklist: it ran at Architecture-Verify on the two changed test files and reported no findings, **but only with intervention 5**. A clean diff also shows nothing about detection. The unprompted case is still unexercised.
- The planner caught two existing end-to-end `TARGET_LOCKED` tests that the investigator missed, and the investigator corrected the ticket's premise ("seven" named survivors were in fact 22).
- Architecture-Review, Document-Update, Test and Verify all passed without needing a re-run; Parity was skipped (no `src/`, behaviour unchanged, no P0 intersection).

**Cost profile (data, not a verdict).** `tool_call_count` and `cost_proxy_score` per phase come from the monitoring records, not agent self-report.

| Pass | Phases | tool calls, total |
|---|---|---|
| 1 (paused after Plan by the user) | Scope 7 / 52.6, Investigate 16 / 58.0, Plan 10 / 60.4 | 33 |
| 2 (paused at Plan by the gate) | Scope 6 / 51.7, Investigate 16 / 59.0, Plan 9 / 53.0 | 31 |
| 3 (to DONE) | Scope 5 / 56.1, Investigate 14 / 57.3, Plan 9 / 54.5, Review 5 / 56.7, Implement 42 / 1133.7, Document-Update 6 / 57.3, Architecture-Verify 4 / 55.0, Test 6 / 146.4, Parity 0 / 0 (skipped), Verify 6 / 55.5, Finalize 11 / 66.7 | 108 |

All three passes: 172 tool calls (33 + 31 + 108). A tests-only standard-tier ticket cost 108 tool calls across 11 phases in the final pass, with Implement dominated by about 15 minutes of mutmut (404 s and 530 s). The two earlier passes show what the owner questions cost in agent work. The numbers are one run and say nothing about other tickets.

**Environment facts.** `SHADOW_CONTEXT_PACKET_ENABLED=1` was set in this environment (the default is off), so the shadow context-packet step ran and wrote retrieval events. The shadow candidate reviewer (`claude-fable-5-1`, advisory) ran at Architecture-Verify because its sampling window was open (`SHADOW_REVIEWER_LOGGING_ENABLED` unset, on by default); it also approved and never affects the gate.

**Pipeline findings from this run** (filed by agent-working, not by this report): the native-runtime parse failure (folded into `TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION`); the plan-gate heading false negative (above); a resume losing `todos_source_path`; a null-`ts` event rejected by `record_events.py`; a verdict string not enforced as an enum.

**CI note.** Filled in from this PR's own CI run, recorded in a final small commit: see the section below once present.

## Mutation baseline (cited, not changed)

`tests/mutation/baselines/src_core_conservation.json` was recorded 2026-09-29 (177 mutants: 60 killed,
117 survived) with `stale_after` 30 days, so the report marks it stale from 2026-10-30. Its 117 survivors,
including 7 `accepted=False` to `True` mutants, survived **under the baseline's selected test set**. They are not a live
product bug (production returns `accepted=False` on every path), and this report does not claim a repo-wide assertion gap or that the survivors are equivalent mutants. The rejection-path gap in the selected tests belongs to
`TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` (owned by `rpg-feature-planning`, not merged),
which this pilot does not implement. D1 targets only the `NODE` charge-accounting mutants at
`src/core/conservation.py` lines 82-91, so any re-run of the baseline will show kills on those lines that
belong to this pilot's tests, not to that ticket's fix. The pilot makes no claim about a mutation-score
change: the drill fault was also caught by an existing test
(`tests/unit/resource/test_harvest_channeling.py`), so a survivor in the baseline reflects that
baseline's own selected test set, not an absence of coverage in the repository.

## Per-intervention review (directional; keep / revise / inconclusive)

| Intervention | Verdict | Measurement and qualitative review |
|---|---|---|
| Proof Plan fields in `test_plan.md` (Epic C) | keep | Filled in one pass for 4 acceptance criteria; the oracle-source field forced finding that `TOWN-122` had no proof path at all. Cost: **inconclusive**. The run was hand-orchestrated, so no per-phase `tool_call_count` exists to compare. |
| §13 triage procedure (Epic C) | keep | Fit the injected fault without adaptation; the "Unknown is the default" rule was not needed. One added lesson for §13.1: record which test set a mutation baseline used, because the drill fault was caught by a test the baseline did not select. |
| Advisory test-quality checklist (Epic C) | inconclusive for D1; partially demonstrated by capability 7 | D1 ran outside `implement-ticket`, so the checklist did not run there. In capability 7 it ran, but only because of an added prompt sentence (intervention 5), and on a clean diff, so detection is still not shown. |
| Impact report v0 (Epic B) | keep, after two fixes | Found, in the first run, that a conservation change mapped to substrate only with no scenario level, and that a tests-only change named no domain or level. Both fixed in this batch (`TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS`; before/after artifacts under capability 1). Agent and workflow files are still `impact-unknown`, by design of v0. |
| Markers and `marker_check` (Epic B) | keep | Caught a real placement mismatch on the first run. |
| Core-RPG report v0 (Epic A) | keep, after one fix and one documented decision | State changes on invalidation were accurate and reproducible. Fixed: the parity layer reported ledger status counts only, so `TOWN-122`'s new `test_path` was invisible; it now shows P0 entries with and without a `test_path` and lists the P0 ids without one (`TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE`; `outputs/cap6b_parity_test_path_visible_after_fix.json`: `TOWN-122` is listed before, not listed after). Decision, not changed: the file classification stays heuristic (directory and import signals), and declared markers are listed beside it and never override it; the ownership fix above changes the class for tests importing the two dual-owned modules but not this rule. |
| Scenario-lane rule (Epic B, D-R2) | inconclusive | D-R2 was approved 2026-09-30 and the job is implemented, but it had not run in CI for this pilot. Not changed by the pilot. The manual run passed; this report records that CI would not have run it for these paths. |

## Acceptance criteria of the epic

1. Capabilities 1, 2, 3, 4, 5, 6 each have an artifact above; the table lists what each one actually
   demonstrated. Capability 1 fell short in the first run; the shortfalls and their fixes are stated in its row and in item 5.
2. Capability 2b is stated as "not demonstrated"; no claim is made about approved-oracle review.
3. Classification: `established` for the component demonstrations on the confirmed real surface, with the caveats above. Capability 7 (2026-10-01) adds one real pipeline run with five recorded orchestrator interventions; the checklist part is only partially demonstrated, and CI scenario execution is recorded from CI. Epic D stays open until the reviewer closes it.
4. This report records keep / revise / inconclusive per intervention with measurements and a qualitative
   review; it is directional.
5. Capability 1 fell short in the first run (a conservation change mapped to substrate only with no scenario
   level; a tests-only change named no domain or level), and the parity layer did not show a new `test_path`.
   These were recorded as revise items and **fixed in this batch**: economy and substrate ownership for
   `src/core/conservation.py` and `src/core/inventory.py` (justification: ch03 §1 and §2, parity
   TOWN-011/012), declared markers in the impact report, and `test_path` presence in the core-RPG report. The
   before and after capability 1 outputs are both kept as evidence. The heuristic classification of test files
   is a documented decision, not a revise item. The first run is not counted as a pass for capability 1.
