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

**`established`, with a scope-level stability caveat.** The surface is resource conservation
(Mechanics Bible ch03 §3 Node Charges, §1 Atomic Conservation; `src/core/conservation.py`; parity
`TOWN-122`). `rpg-feature-planning` (2026-09-30, relaying `world-rule-catalog-design`) said the
`pressure-propagation-economy` epic does not plan to change conservation, harvesting or trade behaviour
per its declared scope, and has no schedule.

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
| 2b | Approved-oracle review | **Not demonstrated** | none | HOLD D-M2. No claim is made about approved-oracle review. |
| 3 | Choose or create a test with a documented pattern | Yes | `tests/unit/resource/test_node_charge_accounting.py` (4 tests), `tests/integration/kernel/test_node_charge_cross_actor.py` (1 test); markers per `docs/testing/test_taxonomy.md` §10; helpers `tests/helpers/{entities,resources}.py` | `marker_check` first flagged a real `level-placement-mismatch` (a `kernel_integration` test under `tests/unit/`); it was fixed by moving the test, and the second run reported 0 findings. |
| 4 | Run the correct local and CI lanes | Yes, with a gap | `outputs/cap4_scoped_local_run.txt` (54 passed, JUnit sha256 `d46b5826c7e7…`, run 2026-09-30T08:53:23Z); `outputs/cap4_scenario_lane_manual_run.txt` (`tests/mechanic_scenarios -m "not slow and not extra_slow"`, 53 passed, 15 s, JUnit `85a946282cbf…`, 08:53:16Z to 08:53:31Z); both at SHA `54a2198f9de928dc1135f3c04d2ba1744aaa08ed` | **CI would not have run the scenario lane for these paths.** `tests/mechanic_scenarios` runs only in the `Perf / cert / arena` job, gated by `PERF_RE` in `.github/workflows/test.yml`. D1's changed paths match none of it, and on PR #265 that job was `skipped`. The gate does match `src/core/`, so a change to `conservation.py` itself would trigger it; a change under `src/economy/` or `src/systems/` would not (F2). The CI rule is untouched (HOLD D-R2). The fast-lane CI run and job conclusions at the final head are recorded in the PR #265 body. |
| 5 | Interpret an injected failure and route it | Yes (drill) | `outputs/cap5_triage_record_DRILL.md`, `inputs/cap5_injected_fault.diff`, `outputs/cap5_new_tests_on_fault.txt`, `outputs/cap5_rerun_isolated.txt` | The fault was injected in a scratch detached worktree (removed, confirmed gone), so nothing was filed and nothing was sent to the feature team. Classified `Product regression` per `regression_policy.md` §13.2 with the full §13.1 record; routing stated as "would route to `rpg-feature-planning` per §13.4". |
| 6 | Report reflects evidence, with a state change after a deliberate invalidation | Yes | `outputs/cap6_before/`, `outputs/cap6_after_junit_dropped/`, `outputs/cap6_after_mutation_record_changed/` (`report.{json,md}`); inputs: `inputs/scoped_junit.xml`, `inputs/scenario_lane_junit.xml`, `inputs/cap6_mutation_record_copy/` | Two invalidations, both on copies. Dropping the scoped JUnit: the D1 unit file's state went from `pass` (4) to `not-run`. A copy of the mutation record with a changed target hash, in a scratch worktree: `fresh` became `stale` with reason `target-changed` (and `worktree_dirty` true). No tracked baseline was edited. |

## Mutation baseline (cited, not changed)

`tests/mutation/baselines/src_core_conservation.json` was recorded 2026-09-29 (177 mutants: 60 killed,
117 survived) with `stale_after` 30 days, so the report marks it stale from 2026-10-30. Its 117 survivors,
including 7 `accepted=False` to `True` mutants, are an **assertion gap in existing tests, not a live
product bug**: production returns `accepted=False` on every path. That gap belongs to
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
| Advisory test-quality checklist (Epic C) | inconclusive | Not exercised: the pilot ran outside `implement-ticket`, so `architecture-reviewer` did not run. |
| Impact report v0 (Epic B) | keep, after two fixes | Found, in the first run, that a conservation change mapped to substrate only with no scenario level, and that a tests-only change named no domain or level. Both fixed in this batch (`TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS`; before/after artifacts under capability 1). Agent and workflow files are still `impact-unknown`, by design of v0. |
| Markers and `marker_check` (Epic B) | keep | Caught a real placement mismatch on the first run. |
| Core-RPG report v0 (Epic A) | keep, after one fix and one documented decision | State changes on invalidation were accurate and reproducible. Fixed: the parity layer reported ledger status counts only, so `TOWN-122`'s new `test_path` was invisible; it now shows P0 entries with and without a `test_path` and lists the P0 ids without one (`TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE`; `outputs/cap6b_parity_test_path_visible_after_fix.json`: `TOWN-122` is listed before, not listed after). Decision, not changed: the file classification stays heuristic (directory and import signals), and declared markers are listed beside it and never override it; the ownership fix above changes the class for tests importing the two dual-owned modules but not this rule. |
| Scenario-lane rule (Epic B, HOLD D-R2) | inconclusive | Not changed. The manual run passed; this report records that CI would not have run it for these paths. |

## Acceptance criteria of the epic

1. Capabilities 1, 2, 3, 4, 5, 6 each have an artifact above; the table lists what each one actually
   demonstrated. Capability 1 fell short in the first run; the shortfalls and their fixes are stated in its row and in item 5.
2. Capability 2b is stated as "not demonstrated"; no claim is made about approved-oracle review.
3. Classification: `established`, on the confirmed real surface with the caveats above.
4. This report records keep / revise / inconclusive per intervention with measurements and a qualitative
   review; it is directional.
5. Capability 1 fell short in the first run (a conservation change mapped to substrate only with no scenario
   level; a tests-only change named no domain or level), and the parity layer did not show a new `test_path`.
   These were recorded as revise items and **fixed in this batch**: economy and substrate ownership for
   `src/core/conservation.py` and `src/core/inventory.py` (justification: ch03 §1 and §2, parity
   TOWN-011/012), declared markers in the impact report, and `test_path` presence in the core-RPG report. The
   before and after capability 1 outputs are both kept as evidence. The heuristic classification of test files
   is a documented decision, not a revise item. The first run is not counted as a pass for capability 1.
