---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION

## Title
Epic B — Test structure and selection: level conventions and metadata, scenario tests on relevant PRs, and a first impact report

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Agents can't tell which test level, harness or placement fits a change, or which tests and lanes a
change affects:

- `docs/testing/test_taxonomy.md` describes legacy-parity markers, several of them unused (0 uses of
  `legacy_characterization` and `intentional_divergence`);
- no test declares a domain or level;
- mechanic scenario tests are skipped on PRs that touch only several core-RPG paths (`PERF_RE` in
  `.github/workflows/test.yml`);
- test selection relies on per-ticket agent grep.

Roadmap: `docs/plans/test_architecture/roadmap.md` §3.

## Scope

**Decision record (2026-09-30).** D-R2 is approved with changes (roadmap §11); its HOLD is lifted. Approval does not close this epic: part 2 is in progress and criterion 4 is open.

1. **Conventions** (ungated):
   - rewrite `docs/testing/test_taxonomy.md` **in place** with level contracts, technique criteria,
     evidence classification, placement and the oracle principle (keeping its valid worldassembly
     and performance sections);
   - register domain/level metadata markers with an **advisory** consistency check, required for
     new or modified core-RPG tests;
   - shared scenario helper;
   - worked examples that are **synthetic or confirmed stable** with the feature team;
   - replay-diff helper limited to the **verified reproducibility envelope** (hand-built state, fixed
     seed, ≤ 10 ticks, the determinism-suite profile).
2. **Scenario-lane CI rule** (D-R2, approved with changes; in progress): the lane triggers on `src/**`, known scenario
   dependencies and `tests/mechanic_scenarios/**` (the old `PERF_RE` omitted the last, so a scenario-test-only PR ran
   no scenario test). Unknown/new paths run the lane and are named in the job summary; known-irrelevant paths are
   listed with evidence. Dedicated job, **not required** (`main` has no branch protection, so that is by convention),
   and it never double-runs what `perf-cert-arena` already runs. Lane cost is measured before any further rule change.
3. **Impact report v0** (ungated): changed paths → components/domains → recommended levels, tests and lanes,
   with reasons and an explicit `impact-unknown` list. It **never removes a lane**. It reports
   selected / triggered / executed separately.

## Out of Scope

- Feature-specific proof commitments.
- Bulk classification of existing tests beyond advisory proposals.
- Seeded-fault evaluation and per-test coverage contexts (deferred to their triggers).
- Mapping party (deferred, D-P).
- Any use of the impact report to skip tests.

## Acceptance Criteria

1. The taxonomy doc answers "which level and harness, and how is it reported" for every level. All
   existing links to `docs/testing/test_taxonomy.md` still resolve.
2. A newly marked test is located and classified by Epic A's report. A deliberately mismatched
   marker is flagged by the advisory check.
3. Each worked example runs green in its declared lane and is labelled synthetic or
   confirmed-stable. The replay-diff helper returns `outside-verified-scope` for inputs outside the
   envelope.
4. **Open** (job implemented. **Update 2026-10-03: 18 PRs and 23 rows are now recorded (#271-#288); the lane ran on 7 PRs (34-52 s whole-job), so a "lane ran on about 10 PRs" reading is NOT yet met; the `src/progression/**`-only trigger is still unobserved in CI; rule-level evidence exists (`tests/unit/tools/test_scenario_lane_paths.py::test_src_progression_only_routes_to_the_dedicated_job`); the cost summary was shared on 2026-10-03 with `rpg-feature-planning` and `agent-working-design` (sent, no reply recorded); see the cost record under Implementation Notes.** Earlier state, 2026-10-02: the ~10-PR cost record is started: 8 PRs of about 10: the lane ran on 5 (#271 and #275 tests-only fail-open, #272, #273 and #277 real trigger matches), was skipped on 2 because `Perf / cert / arena` covered the scenario tests (#274, #276), and was skipped on 1 as a docs-only skip (#278, an earlier head; its final head is a Perf-covers skip, row added 2026-10-02, still 8 PRs); the src/progression trigger is still unobserved; see the cost record under Implementation Notes). A PR touching only `src/progression/**` runs the scenario tests. A docs-only PR
   does not. An unknown path runs them and appears in the job summary. Lane wall time is recorded for
   the first ~10 relevant PRs. The measured cost is shared with the feature teams before any rule promotion.
5. The impact report, run on sample changes (local rule, shared substrate, cross-domain,
   content/config, unmapped), gives the expected domains and lanes with reasons, and flags the
   unmapped sample as `impact-unknown`.

## Related Tickets
- Child: `TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS` (impact report fixes found by the pilot, done).
- Depends on Epic A (report v0) for criterion 2.
- Feeds Epics C and D.

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (MT, R2, M1; non-binding)

## Related Stored Artifacts
None.

## Related Code Areas
`docs/testing/`; `pyproject.toml` (markers); `tests/helpers/`; `tests/mechanic_scenarios/`;
`.github/workflows/test.yml` (gated part only).

## Assumptions / Open Questions
- **D-R2 approved (2026-09-30):** part 2 is in progress; criterion 4 stays open until CI has actually run the lane on real PRs and the cost is recorded and shared.

## Implementation Notes
**Progress (2026-09-30):** parts 1 and 3 are DONE via child tickets `TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS`, `TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK`, `TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF`, `TCK-20260930-TEST-IMPACT-REPORT-V0` (acceptance criteria 1, 2, 3, 5). Part 2 (scenario-lane job, `tools/test_architecture/scenario_lane_paths.py`) is **in progress in the 2026-09-30 decisions batch**: implemented and locally tested, **not yet run in CI**. Criterion 4 is **open, half observed (2026-10-01)**: PR #271 (a `tests/`-and-`docs/`-only change that fails open into the lane and does not match `PERF_RE`) ran the `Scenario lane` job for the first time: it ran once, succeeded, and `Perf / cert / arena` was skipped (job time 51 s). The `src/progression/**`-only trigger and the docs-only skip are still unobserved, and the lane cost has one datapoint. Earlier note: PR #267 itself matched `PERF_RE` (it edits `test.yml`), so the dedicated job was skipped and its own steps (wall-time arithmetic, summary) have not run in CI. Criterion 4 closes only when a real PR whose paths hit `run_scenario_lane` but not `PERF_RE` (for example `src/progression/**` only) shows the lane running, and a docs-only PR shows it skipped; that first PR is also the first cost datapoint. This epic stays open in `todos/`.
**Gap flagged:** "tactical navigation" has no code root; the impact report lists such paths as `impact-unknown` and invents none.

Scenario-lane cost is assumed at 1–3 min per relevant PR; measured under criterion 4.

**Criterion 4 cost record (started 2026-10-01; every head SHA the job ran on, grouped per PR; figures from the Actions jobs API, re-checked).** The job that executed `tests/mechanic_scenarios` is named per row, never inferred from the routing statement.

| PR | Head SHA | Workflow run | Executing job | Conclusion | Job wall time (started to completed) | Why routed | Test count |
|---|---|---|---|---|---|---|---|
| #271 | `369acbac3` | 36810173881 | Scenario lane (perf-cert-arena skipped) | success | 51 s (03:23:37Z to 03:24:28Z) | **tests-only fail-open**: 0 matched, 3 unknown, 15 irrelevant paths at this head | not recorded (job JUnit not retrieved) |
| #271 | `a9646c9de` | 36812211906 | Scenario lane (perf-cert-arena skipped) | success | 50 s (03:50:29Z to 03:51:19Z) | tests-only fail-open (per-head path list not re-derived; final-head routing is in the next-but-one row) | not recorded |
| #271 | `e75ff2e77` | 36813602119 | Scenario lane (perf-cert-arena skipped) | success, **while the workflow as a whole failed**: job `API / tools / logging` failed (step `Run: tests/tools` failed; my own earlier report attributed it to `docs/REGISTRY.yaml` drift, and the fix, commit `248372a26`, regenerated `docs/REGISTRY.yaml`; I confirmed from the jobs API only the failing job and step names, not the failing test, because run logs are not retrievable from here) | 50 s (04:09:06Z to 04:09:56Z) | tests-only fail-open (per-head path list not re-derived) | not recorded |
| #271 | `248372a26` (final head) | 36815393173 | Scenario lane (perf-cert-arena skipped) | success | 34 s (04:31:37Z to 04:32:11Z) | tests-only fail-open: 0 matched, 3 unknown (`tests/mutation/reruns/...rerun.json`, `tests/unit/resource/test_conservation_rejection_paths.py`, `.../test_rejected_transfer_apply_path.py`), 16 irrelevant | not recorded |
| #275 | `e147d7514` (only head) | 36837239759 | Scenario lane (perf-cert-arena skipped) | success | 48 s (08:36:17Z to 08:37:05Z) | tests-only fail-open: 0 matched, 6 unknown (`tests/mutation/baselines/src_core_conservation_v2.json` and five `tests/unit/tools/test_*.py` files), 17 irrelevant | not recorded |
| #275 | `d15ff2163` | 36840523273 | Scenario lane (perf-cert-arena skipped) | success | 47 s (09:07:37Z to 09:08:24Z) | tests-only fail-open (same changed-path classes as the first head plus agent-working/tickets/stored_artifacts/docs text) | not recorded |
| #272 | `ff60cc2b8ee3d85427f5f9409b4583334b580db0` (final head) | 36816354840 | Scenario lane (perf-cert-arena skipped) | success | 46 s (04:43:44Z to 04:44:30Z) | **real trigger match** (via `tests/tools/`, a trigger class in `scenario_lane_paths` since #267, so not fail-open): 2 matched (`tests/tools/test_cited_evidence_advisory.py`, `tests/tools/test_skill_usage_metric.py`), 1 unknown (`.claude/agents/done-checker.md`), 13 irrelevant | not recorded |
| #273 | `e67f7ad039d5ad9e2bd2f6af512c96a348158c21` (final head) | 36827697928 | Scenario lane (perf-cert-arena skipped) | success | 52 s (07:00:23Z to 07:01:15Z) | **real trigger match** (a changed `tests/mechanic_scenarios/` file, the lane's own tests): 1 matched (`tests/mechanic_scenarios/test_entity_death_authority_boundary.py`), 0 unknown, 26 irrelevant | not recorded |
| #274 | `8822eecf5a67c46a70cfffeae86c7d2e7479f705` (final head) | 36844103080 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** (it runs `tests/mechanic_scenarios` itself, test.yml) | Perf success | Perf job wall time (includes non-scenario work) 131 s (09:40:43Z to 09:42:54Z); not comparable to the lane's figures | **skipped, Perf covers it**: the PR has no `src/` file but changes `Makefile`, which matches `PERF_RE`. **Not a docs-only skip.** | not recorded |
| #276 | `e6edcb70de40bceaec2ffe04c91ea5c8e5a32b70` (final head) | 36867926153 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** | Perf success | Perf job wall time (includes non-scenario work) 144 s (13:21:49Z to 13:24:13Z) | **skipped, Perf covers it**: `src/engine`, `src/core`, `src/systems` match `PERF_RE`. It touches `src/simulation_quality/scorers/progression.py` but no `src/progression/` path, so it is **not** the src/progression trigger case | not recorded |
| #278 | `343a880934e505e0d0496703ef1938b4a3999774` (**an earlier head of this PR**, not the final head; later heads are not enumerated) | 36890190328 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** (no job executed `tests/mechanic_scenarios`) | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 10 irrelevant paths (tickets, docs, monitoring shards only; no `src/`, `tests/`, `Makefile`) | not applicable |
| #277 | `385f362fecf01205d3eaf159e2f94da431a88e04` (final head) | 36876384416 | Scenario lane (perf-cert-arena skipped) | success | 52 s (14:28:29Z to 14:29:21Z) | **real trigger match** (via `tests/tools/`): 3 matched (`tests/tools/test_main_integrity_report.py`, `tests/tools/test_validate_working_log.py`, `tests/tools/test_working_log_content_duplicate_check.py`), 0 unknown, 10 irrelevant | not recorded |
| #278 | `bf468aca4606f5a317c7888b58afb4a668531c8f` (**final head**; the earlier head `343a88093` has its own row above) | 36960377039 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** (Frontend, Migration lanes, Slow regression and SimQ grade-anchor drift also skipped) | Perf success; run conclusion success | Perf job wall time (includes non-scenario work) 131 s (03:30:54Z to 03:33:05Z); not comparable to the lane's figures | **skipped, Perf covers it**: the final file list (25 paths) has 3 matched trigger paths (`src/observability/entity_kind_constants.py`, `event_extractor.py`, `event_shapers.py`), 2 unknown (`tests/unit/observability/test_entity_kind_constants.py`, `test_event_shapers_world_dynamics.py`), 20 irrelevant. **Not a docs-only skip at this head**, and not a `src/progression/` trigger | not recorded |
| #279 | `5a651462379dfff5957cdd80a447ed68d5490cf3` (final head) | 36900341228 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** | Perf success | Perf job wall time (includes non-scenario work) 166 s (17:35:45Z to 17:38:31Z); not comparable to the lane's figures | **skipped, Perf covers it**: 13 matched trigger paths (`src/progression/leveling.py` AND `src/core/builder.py`, `derived_stats.py`, `state.py`, `updates.py`, `src/engine/apply.py`, `patches.py`, `pipeline_phases/hardening.py`, `rpg_depth.py`, `src/entities/archetype_factory.py`, `src/systems/world_systems/generator.py`, `src/worldassembly/entity_spawner.py`, `src/worldbuilding/compiler.py`), 2 unknown (tests), 16 irrelevant. It touches `src/progression/` but also `src/core` and `src/engine`, so it is **not** the `src/progression/**`-only case | not recorded |
| #280 | `a1da6caa86026a01afe7d7723a421a4d742f3754` (final head) | 36964376584 | Scenario lane (perf-cert-arena skipped) | success | 38 s (04:25:41Z to 04:26:19Z) | **real trigger match** (via `tests/tools/`): 2 matched (`tests/tools/test_delivery_pr_render.py`, `tests/tools/test_main_integrity_report.py`), 0 unknown, 17 irrelevant | not recorded |
| #281 | `be1e6cf63319cfa9c1ef00b74e3a0204702c4861` (final head) | 36965381697 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 25 irrelevant paths | not applicable |
| #282 | `366c98028366bb29a88d045bf824732cff931110` (final head) | 36995844110 | Scenario lane (perf-cert-arena skipped) | success | 51 s (10:32:17Z to 10:33:08Z) | **real trigger match** (via `tests/tools/`): 2 matched (`tests/tools/test_arch_verify_read_check.py`, `tests/tools/test_arch_verify_test_quality_findings.py`), 3 unknown (`.agents/skills/implement-ticket/SKILL.md`, `.claude/skills/implement-ticket/SKILL.md`, `.claude/workflows/implement-ticket.js`), 14 irrelevant | not recorded |
| #283 | `4785fe49af22159547c2bedef3edbc48ff89e382` (final head; **new job layout**) | 37090371235 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 15 irrelevant paths | not applicable |
| #284 | `15a57172711c6050fb88ccb737af6b69621dddaa` (final head) | 36996812878 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 23 irrelevant paths | not applicable |
| #285 | `215a1b8368454c131e5cca69e4d3bb9d7b71c84b` (final head; **new job layout**) | 37090840973 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 10 irrelevant paths | not applicable |
| #286 | `e25b4f03c5c09398741623d5e28481dcb94307c9` (final head) | 37032971448 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** | Perf success | Perf job wall time (includes non-scenario work) 142 s (16:19:53Z to 16:22:15Z); not comparable to the lane's figures | **skipped, Perf covers it**: 3 matched trigger paths, 68 unknown, 25 irrelevant (96 paths in all); not a `src/progression/` trigger | not recorded |
| #287 | `3886a281f0951103ed841f7207e1456aad48e9be` (final head) | 37039518014 | **None: Scenario lane skipped and `Perf / cert / arena` skipped** | all jobs that ran passed (run conclusion success) | not applicable (no scenario job ran) | **docs-only skip**: 0 matched, 0 unknown, 26 irrelevant paths | not applicable |
| #288 | `107c04c9dccee3fa0ab333e76973b32a3ac66127` (final head; **new job layout**, this PR introduced it) | 37044570153 | **Scenario lane skipped; `Perf / cert / arena` was the executing job** | Perf success | Perf job wall time (includes non-scenario work) 89 s (18:02:40Z to 18:04:09Z); not comparable to the lane's figures | **skipped, Perf covers it**: 13 matched trigger paths, 12 unknown, 61 irrelevant (86 paths in all); not a `src/progression/` trigger | not recorded |

Method: query the runs API by the full 40-character head SHA, and treat an empty result as "not found by this query", never as evidence that no run exists. An earlier version of this record said `a9646c9de` and `e75ff2e77` had no run; that was wrong (both have runs, found by the reviewer and re-confirmed), and the cause of the empty result in the first query is not established (the query used full SHAs). The table lists heads up to `d15ff2163`; a later head of #275 carrying this correction would have its own run, not listed here. The "why routed" counts come from running `scenario_lane_paths` locally on each PR's changed file list (for `369acbac3`, the pilot report's recorded figures); the CI step summary could not be retrieved from the API.

Routing vocabulary for the "why routed" column: **real trigger match** / **tests-only fail-open** (0 matched, only unknown paths) / **skipped, Perf covers it** / **docs-only skip** (0 matched, 0 unknown, Scenario lane and Perf both skipped). A `src/progression/**`-only trigger has not occurred. Applies to every row: routing counts were recomputed locally with the post-#275 `scenario_lane_paths` and the PR's final file list (except `369acbac3`, which uses the pilot report's figures), not read from CI's step summary, and CI at the earlier heads ran an earlier version of the tool.

Added 2026-10-01 (PRs #272, #273, #274, #276): each row is the PR's final head, queried by full 40-character SHA, and each query returned exactly one `Tests` run. Earlier heads of those PRs are not enumerated here, so this part of the record is not "every head". #277 was open when the first rows were written and merged later; its row is added below (final head). The #278 row is one earlier head of its own PR (the PR was pushed again afterwards, and those later heads are not enumerated); its routing counts come from `scenario_lane_paths` run locally on `git diff` between `786f9ee9b` and that head, and both skipped jobs and the passing jobs were read from the Actions jobs API for run 36890190328.

**Added 2026-10-02 (#278 final head):** the row for `bf468aca4606f5a317c7888b58afb4a668531c8f` was read from the Actions jobs API for run 36960377039 (the run's `head_sha` is that full SHA; the job states and times above are the API's). Its routing counts come from `scenario_lane_paths --perf-covers true` run locally on the PR's final file list (`gh api pulls/278/files`), not from CI's step summary. This is a second row for PR #278, **not a ninth PR**: the PR count stays 8. PRs #280, #281 and #282 merged after #278 and are **not recorded**: their CI was not verified by full SHA here, and they are left for a later batch.

**Job layout note (2026-10-03):** `5d49a67c7` (#288) split the former `API / tools / logging` job into three jobs (`Tools · a–e`, `Tools · f–z`, `API / CLI / engine / logging`), and the three now upload the JUnit XML. Rows for heads before `5d49a67c7` use the old layout; the one failure named above (`API / tools / logging` on `e75ff2e77`) is that old job. I read the diff and the new workflow: the `Scenario lane` and `Perf / cert / arena` jobs, the `PERF_RE` pattern, the `run_scenario_lane` output and its `if:` condition, and `scenario_lane_paths.py` are unchanged by #288, so the routing categories and the rows above still hold. Not verified by running CI on the new layout.

<<<<<<<< HEAD:agent-working/tickets/done/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md
**Update 2026-10-03 (rows for #279-#288):** each row is the PR's final head from `gh api pulls/N`, queried by full 40-character SHA, and each query returned exactly one `Tests` run (event `pull_request`, conclusion success); the executing job per row is read from that run's jobs API, and routing counts come from `scenario_lane_paths` run locally on the PR's full paginated file list. The three rows marked "new job layout" (#283, #285, #288) are the only ones whose run contains the `Tools · a–e` / `Tools · f–z` jobs (checked per run); #284, #286 and #287 merged after #288 but their runs predate that layout. Earlier heads of these PRs are not enumerated. **Current totals: 18 PRs and 23 rows recorded (#271-#288).** The lane ran (executing job `Scenario lane`) on **7 PRs**: #271, #275, #272, #273, #277, #280, #282, across 11 rows, with whole-job wall time **34 s to 52 s**. It was skipped because `Perf / cert / arena` covered the scenario tests on **6 PRs** (#274, #276, #278 final head, #279, #286, #288), and **6 PRs show a docs-only skip** (#278 earlier head, #281, #283, #284, #285, #287). #278 appears in both the Perf-covers and docs-only counts (one row each, by head). **The "~10 relevant PRs" wall-time part is NOT yet satisfied if "relevant" means the lane actually ran: that is 7 PRs, not 10.** If it means every PR whose routing was observed, 18 PRs are recorded. The `src/progression/**`-only trigger is still **unobserved in CI**: #279 touches `src/progression/leveling.py` but also `src/core` and `src/engine`, so `Perf / cert / arena` covered it. Rule-level evidence exists and is not CI-observed: `tests/unit/tools/test_scenario_lane_paths.py::test_src_progression_only_routes_to_the_dedicated_job` asserts the routing against the real `PERF_RE` read from `test.yml`. Whether a rule-level test may stand in for an observed CI run is the user's closure decision; no test was added here.

**Cost shared (2026-10-03):** a short summary of the figures above (rows, lane wall-time range, Perf-covered and docs-only counts, limits) was sent on 2026-10-03, after test-architecture-reviewer approved the wording, to `rpg-feature-planning` and `agent-working-design` as cross-session messages. Both sends succeeded; neither recipient had replied when this was written, so this records that the summary was shared, not that anyone agreed. The summary states the 18 PRs are consecutive PRs merged to main by all sessions between 2026-10-01 and 2026-10-03 (about 2 days) and imply no rate, and that no rule promotion is proposed.

**Update 2026-10-03 (row for #290):** PR #290 (merged 2026-10-03T07:44:04Z as `2f520f0dd`), final head `d80e7ff9807053318e1937e67f7cdc00273e8b52`, queried by full SHA: exactly one `Tests` run, 37103148851 (event `pull_request`, conclusion success). Read from that run's jobs API: **`Scenario lane` ran and succeeded (whole-job wall time 54 s, 06:30:11Z to 06:31:05Z); `Perf / cert / arena` skipped.** This is the **8th PR on which the lane ran**, and the whole-job range widens from 34-52 s to **34-54 s**. #289 and PRs after #290 are not recorded here: #289's CI was not verified by full SHA and #291 is open. Routing counts (matched, unknown, irrelevant) are not recorded for this row. The `src/progression/**`-only trigger is still unobserved in CI, and 8 lane runs remain below the roughly 10 planned; the owner accepted that limit (decision D1), so this row only keeps the record current. Totals: **19 PRs and 24 rows**.

Reading this record (state as of 2026-10-02; see the 2026-10-03 update above for current totals): **8 of about 10 PRs were recorded (13 rows).** The lane ran on 5 (#271 and #275 tests-only fail-open; #272, #273 and #277 real trigger matches, #272 and #277 via `tests/tools/` and #273 via a changed `tests/mechanic_scenarios/` file, the first row routed by the lane's own tests) and was skipped on 2 because `Perf / cert / arena` covered the scenario tests (#274 via a `Makefile` change, #276 via `src/` paths), and **one row is a docs-only skip** (#278, an earlier head: both the lane and Perf skipped, only tickets/docs/monitoring paths changed), the first observed docs-only skip, from a single PR. **The same PR's final head is a "skipped, Perf covers it" row** (it added `src/observability/` files), so #278 contributes both a docs-only skip (earlier head) and a Perf-covered skip (final head); the skipped-Perf-covers count is therefore 2 PRs (#274, #276) plus #278's final-head row. No row is a `src/progression/**` trigger, so that criterion 4 case is still **unobserved** and the criterion stays open. #274 has no `src/` file but is not a docs-only skip (`Makefile` matches `PERF_RE`). The wall time is the **whole job** (checkout and `pip install` included), not test duration. This is **not yet the "shared with feature teams" step**: nothing here has been sent to them and nothing authorizes promotion of the lane to required.
========
Reading this record: **8 of about 10 PRs are recorded (13 rows).** The lane ran on 5 (#271 and #275 tests-only fail-open; #272, #273 and #277 real trigger matches, #272 and #277 via `tests/tools/` and #273 via a changed `tests/mechanic_scenarios/` file, the first row routed by the lane's own tests) and was skipped on 2 because `Perf / cert / arena` covered the scenario tests (#274 via a `Makefile` change, #276 via `src/` paths), and **one row is a docs-only skip** (#278, an earlier head: both the lane and Perf skipped, only agent-working/tickets/docs/monitoring paths changed), the first observed docs-only skip, from a single PR. **The same PR's final head is a "skipped, Perf covers it" row** (it added `src/observability/` files), so #278 contributes both a docs-only skip (earlier head) and a Perf-covered skip (final head); the skipped-Perf-covers count is therefore 2 PRs (#274, #276) plus #278's final-head row. No row is a `src/progression/**` trigger, so that criterion 4 case is still **unobserved** and the criterion stays open. #274 has no `src/` file but is not a docs-only skip (`Makefile` matches `PERF_RE`). The wall time is the **whole job** (checkout and `pip install` included), not test duration. This is **not yet the "shared with feature teams" step**: nothing here has been sent to them and nothing authorizes promotion of the lane to required.
>>>>>>>> origin/main:agent-working/tickets/todos/test-architecture/TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION.md

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
**Closed 2026-10-03 by owner decision** (the user's answers, relayed by `test-architecture-reviewer`). Classed in `tickets/done/test-architecture/INDEX.md` (closure-readiness audit of 2026-10-03, base `origin/main` c0980e27a): B1, B2 and B5 MET; B3 MET-with-caveat; **B4 MET-with-caveat by the user's decision (D1)**: routing is observed on 18 PRs (23 rows), the lane ran on 7 (34-52 s whole-job), and `tests/unit/tools/test_scenario_lane_paths.py::test_src_progression_only_routes_to_the_dedicated_job` (against the live `PERF_RE`) stands in for the progression-only case. **Both limits stand: 7 lane runs against about 10, and the `src/progression/**`-only trigger was not observed in CI.** The first CI-observed progression-only PR is a watch item, to be appended to the cost record. The cost summary was shared on 2026-10-03 (sent, no reply recorded). The lane stays non-required; this closure is not a promotion.
