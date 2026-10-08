---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED
phase: open
date: 2026-10-01
tags: [simulation-quality, grade-thresholds]
---

# TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED

## Title
13 of 15 SimQ grade-anchor tests in `tests/unit/worldassembly/test_corpus_diversity.py` fail on
untouched `origin/main` (measured 2026-10-01 @ `e9db40f0a`; supersedes the unverified "11 of 16"
lead), and nothing reports it because the whole family is `@slow` and CI does not gate on it —
the anchors currently protect nothing

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found 2026-10-01 while landing `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND`
(PR #269). That batch's fix caused 16 grade-anchor tests to fail, so a control run was done on
untouched `origin/main` (`73cbf116b`) to separate fix-caused drift from pre-existing red.

**The control run is the finding.** Of the 16, **11 also fail on untouched `main`** — they were
already red, independent of any change in that batch. Only 5 failed solely with the fix, and of
those, 2 passed on re-run, 1 was a per-test resource `TimeoutError`, 1 was noise confirmed by a
5-vs-5 trial (see below), and exactly **1** was a genuine fix-caused shift (tracked separately in
`TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE`).

**Why nobody noticed:** the whole family is marked `@slow`, and CI does not gate on `@slow`. So
these anchors can be red on `main` indefinitely with no signal to anyone. Their failure is only
observable to someone who runs them deliberately — which, in this case, happened by accident,
because a batch needed a control run for an unrelated reason.

**The consequence is what makes this P1, not the 11 failures themselves.** A grade anchor exists to
detect unintended drift in simulation quality. An anchor that has been failing on `main` for an
unknown period cannot do that: it cannot distinguish "this change broke something" from "this was
already broken", and every future change that touches these pillars inherits an unreadable signal.
That is precisely the cost paid in PR #269 — a real fix produced 16 red tests and the batch had to
spend a full control run establishing that 11 of them were not its fault. **Every future batch
touching ECONOMY/NARRATIVE/SOCIAL pays that same tax until this is resolved.**

> **The contrast with the gating lane, observed the same day, in the same PR.** PR #269's gating CI
> caught a real defect on its first run — a `tests/simulation_quality/` test that had pinned the
> exact collision the PR was fixing, asserting `yields_item == 'frost_shard_cluster'` with a
> docstring claiming no `frost_shard` item existed when the catalog defines one. One run, real
> signal, acted on immediately. In the same repository on the same day, 11 grade anchors had been
> failing on `main` for an unknown period with no signal reaching anyone, because `@slow` is
> excluded from the gating lane. **The difference is not test quality — it is whether anything
> reads the result.** An unread assertion and an absent assertion are the same thing operationally,
> and the anchors have been in the first category for long enough that nobody knows when it
> started. This is the concrete case for the reporting-path requirement in Scope, and it is why
> visibility (not gating) is the minimum bar: the gating lane's value here came from someone being
> *told*, within minutes, by a mechanism that does not depend on anyone choosing to look.

**Provenance and verification status — read before acting.** The 11-of-16 measurement was made by
`rpg-implementer (2)` during PR #269's control run, not by this ticket's author, and **has not been
independently re-verified**. It is recorded here because it was load-bearing for that PR's merge
decision and would otherwise exist only in a session transcript. **Re-run the 16 before acting on
the count** — the first task below. The qualitative claim (some anchors are red on `main` and
nothing reports it) is what this ticket rests on; the exact number is not yet confirmed.

## Verified Measurement — 2026-10-01 (supersedes the unverified 11-of-16)

**Re-run done, and it is worse than the lead claimed.** The first Scope item is complete; the rest
of the ticket is untouched and still OPEN.

- **Conditions.** `origin/main` @ `e9db40f0a`; worktree tree identical to that SHA for all `src/`
  and `tests/` paths (only a ticket move and monitoring-shard rows differed, neither of which the
  tests read). `python -m pytest tests/unit/worldassembly/test_corpus_diversity.py
  -k "grade_stability or population_stability" -v -rA`. 32 selected / 61 deselected. Wall clock
  **25m59s**. Seeds and tick budgets are per-test, as encoded in each test name.
- **Result: 15 failed, 17 passed, 1 error.**
- **Of the 15 `*_grade_stability` anchors, 13 fail.** Only two pass:
  `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`.
- Plus 2 `population_stability` failures: `[frontier_marches]` (already classified **confirmed
  noise** in Out of Scope — not re-investigated here) and
  `test_generated_frontier_3_42_extended_population_stability`.
- The **1 error is not an anchor failure**: it is a session-teardown `QueueDrainWorker` leak
  sentinel firing at teardown of the last test. Recorded separately so it is not miscounted as a
  14th red anchor; it may deserve its own ticket.

**Full red list** (13 grade + 2 population):
`test_urban_political_seed123_500t_cognition`, `test_simq_routing_test_seed42_500t_cognition`,
`test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative`,
`test_urban_political_seed42_1000t_social`, `test_urban_political_seed123_1000t_social_economy`,
`test_urban_political_selfmodel_probe_seed42_200t_social_world`,
`test_generated_frontier_3_42_seed123_200t_combat_narrative`,
`test_urban_political_seed42_200t_social`, `test_frontier_extended_seed42_200t_narrative`,
`test_frontier_extended_seed123_200t_combat_progression_narrative`,
`test_frontier_living_world_seed42_200t_social`,
`test_frontier_living_world_seed123_200t_combat_narrative`,
`test_frontier_marches_seed42_200t_narrative`;
`test_population_stability[frontier_marches]`,
`test_generated_frontier_3_42_extended_population_stability`.

**What this does and does not establish.** The qualitative claim the ticket rests on is
**confirmed**: anchors are red on untouched `main` and nothing reports it. The count is now
measured rather than inherited — **13 of 15 grade anchors**, not 11 of 16. What remains entirely
**unaddressed**: how long they have been red, the per-anchor (a)/(b)/(c) classification, the
reporting path, and the other-`@slow`-families audit. **No anchor value was touched**, per Out of
Scope.

**Provenance.** Measured by `rpg-feature-planning`, run alongside
`TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` as a verification-only re-run on the
recommendation of `world-rule-catalog-design`. Single run per anchor — **flakiness was not
re-tested here**, so class (c) remains open for every one of the 13.

## Diagnosis Correction — 2026-10-05 (test-architecture-reviewer)

**The "ungated" diagnosis above is wrong: these anchors are executed on every `main` push and nightly, and nobody reads the result.** Step 5 of the `Slow regression` job in `.github/workflows/test.yml` is `make simq-corpus-diversity-slow-isolated`. It runs exactly the `tests/unit/worldassembly/test_corpus_diversity.py -m slow` anchors as isolated subprocesses, on push to `main`, on the nightly schedule and on manual dispatch. Over the 40 `main` push runs of `Tests` up to run 37278526329 (REST jobs API, 2026-10-05), step 5 **failed in 19** and was cancelled in 17 (a newer push to `main` evicted the running job via the workflow's `cancel-in-progress`), with 4 runs having no step-5 outcome. The nightlies show the same pattern. The red never reaches anyone, because the job runs only after merge and the owner has parked its step-5 cause as expected state (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`, 2026-09-16, reconfirmed 2026-10-05).

**Relationship to `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN`: sibling, not child, and neither supersedes the other.** This ticket owns the anchors' red (step 5). The gate ticket restores steps 6–7, which have been skipped after every step-5 failure, and makes each step's outcome visible in the job summary. When the gate ticket lands, this ticket's "reporting path" requirement is partly met by that summary line for step 5. The summary is visibility, not a notification. Re-read the Scope against it before closing.

**Ownership (owner decision 2026-10-06, relayed by `test-architecture-reviewer`):** testing adopts this ticket's remaining scope, limited to **reporting and triage**; holder: `test-architecture-implementer`. Fixes stay with the owning domains, and the step-5 determinism cause stays parked under `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`. Per Scope bullet: (1) **Measure:** done on run 37403688489 (head 9299891a916c93d5047b999bc16b371ba78939d4, job 112078415756): step 5 ran 32 isolated anchor invocations, 10 failed and 22 passed. That supersedes the 11-of-16 and is recorded in `TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN`. (2) **How long red:** answered from CI history. Step 5 failed on 19 of 40 main pushes up to run 37278526329, and the further bracket is still owed. (3) **Classify (a)/(b)/(c):** testing classifies with evidence and routes (a)/(b) to the owning domain via rpg-feature-planning. Class (c) (non-determinism) is the parked cause and is recorded, not investigated. (4) **Reporting path:** the #360 step-outcome summary gives visibility only. A mechanism that surfaces a newly-red anchor without a human, proven against a seeded failure, is still owed and is testing's to design. (5) **Other `@slow` families:** answered **yes**. Step 6 (`slow or extra_slow`) had the same blind spot. It went from green on 2026-08-26 to 8 failures, unseen (the green-to-red bracket holds for 7 of the 8; the campaign test was added 2026-09-09 and first went bad at #175), and is tracked in `TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX`. The reporting path in (4) must therefore cover the whole `slow` job (steps 5–7), not just the anchors.

## Reporting-Path Design — 2026-10-06 (test-architecture-reviewer; scope item 4 of this ticket, extended to the whole `slow` job per item 5)

**Problem, measured.** (1) The `Slow regression` job lives in `Tests` (`.github/workflows/test.yml`), whose workflow-level concurrency is `group: test-${{ github.ref }}`, `cancel-in-progress: true`. The job takes about 2 h (run 37403688489: step 5 21 min, step 6 1 h 37 min, step 7 2 min), and `main` receives a push every 20–40 min on a working day, so a newer push almost always evicts it. Since 2026-09-29, 95 `main` push runs of `Tests` gave **43 cancelled, 51 failure, 0 success** (1 running), and 5 nightly `schedule` runs gave 2 cancelled and 3 failure. The nightly shares the group `test-refs/heads/main`, so a late push cancels it too. On 2026-10-06, four consecutive main runs (37417841303, 37425900959, 37427998271, 37430231927) were cancelled before step 6 finished. (2) Every completed `main` run is red, because step 5 is red (parked) and step 6 is red (triage ticket). The `Tests` conclusion on `main` therefore carries no information: a new fast-job break on `main` looks the same as yesterday. (3) Nothing notifies anyone. The #360 step-outcome summary is visible only to someone who opens the run.

**Design (three parts).**

**P1: a workflow of its own for the slow suite, non-cancelling.** Move the `slow` job out of `test.yml` into `.github/workflows/slow-regression.yml` (name `Slow regression`):
- `on: schedule` (cron below, owner decision D2) + `workflow_dispatch`. **No `push` trigger.**
- `concurrency: { group: slow-regression-${{ github.ref }}, cancel-in-progress: false }`. GitHub keeps at most one running and one pending run per group, and a newer pending replaces an older pending, so every run that starts also finishes.
- `timeout-minutes: 240` on the job (it has none today, a finding of `TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX`).
- Steps 5–9 unchanged, including `!cancelled()` on 6–7 and the outcome summary. The `needs:` on the 13 fast jobs is dropped: the slow suite is informational, and gating it on a fast run that may itself be cancelled is what kept it from running.
- `test.yml`'s nightly `schedule` trigger is removed: its own comment says it exists only for the slow suite. Static pins that name the `slow` job move or are updated (`tests/static/test_ci_step_summary_reporting.py::_EXPECTED_SLOW_YAML`, `tests/static/test_ci_slow_job_step_gating.py`); the #338 skip-set pin already excludes `slow`.
- `test.yml` keeps `cancel-in-progress: true` for PRs and main pushes. Its `main` conclusion becomes meaningful again: green unless a fast job broke.
- Cadence (owner decision D2; this is a private repo, so minutes are billed): **every 6 h** (`0 3,9,15,21 * * *`), about 4 × 2 h = 8 runner-hours a day. The alternatives are nightly only (2 h a day, latency up to 24 h) or every push (back-to-back, about 24 runner-hours a day). This costs attribution: a red names a 6 h window of merges, not one PR. Today it names nothing, because the run never finishes.

**P2: an alert on change, not on red.** A final step in the new workflow, `if: ${{ !cancelled() }}`, runs `tools/test_architecture/slow_regression_report.py`:
- Input: JUnit XML from steps 5, 6 and 7 (add `--junitxml=reports/slow/<step>.xml`; for step 5's per-test subprocesses, one file per invocation).
- Output: one rolling GitHub issue, labelled `slow-regression`, titled "Slow regression: N failing on main". Its body is the current failing set, grouped by step, each test id linked to the run. On each run the script compares the new failing set with the set recorded in the issue (a fenced JSON block in the body) and **comments only when the set changes**: `NEW: …` / `FIXED: …`, with the run id and head SHA. When the set becomes empty, it closes the issue with a comment. A run whose set is unchanged edits the body's "last seen" line and does not comment.
- Known reds are not suppressed. They are simply not new, so they never comment twice. The issue body links them to their tickets through a small mapping file (`tools/test_architecture/slow_known_reds.yaml`: test id → ticket id), so an unmapped red is visibly unowned.
- Permissions: `issues: write` on that job only.

**P3: proof.** The ticket's acceptance criterion says "a test or check proving the mechanism reports a seeded failure":
- `tests/unit/tools/test_slow_regression_report.py` (not slow): JUnit fixtures for (a) a seeded new failure, which yields a NEW comment containing the test id; (b) an unchanged set, which yields no comment; (c) a fixed test, which yields FIXED; (d) an empty set, which closes the issue; (e) an unmapped red, which is flagged unowned. The GitHub calls go through an injected client, faked in tests.
- `tests/static/test_ci_slow_workflow_shape.py`: pins `cancel-in-progress: false`, the absence of a `push` trigger, `timeout-minutes`, `!cancelled()` on steps 6–7 and the report step, and that `test.yml` no longer has a `slow` job. This replaces `tests/static/test_ci_slow_job_step_gating.py`'s location and keeps its assertions.
- After merge, a `workflow_dispatch` run on `main` must open the issue with the current reds (expected: 10 step-5 anchors and 8 step-6 failures, minus whatever is fixed by then). That run is the live proof, recorded in the ticket.

**Not in this design:** fixing any red, un-parking step 5, PR-gating the slow suite, or the `Tests`-level `cancel-in-progress` for PRs.

**Owner decisions (2026-10-06, relayed by `test-architecture-reviewer`):** (D1) the alert channel is a rolling GitHub issue, labelled `slow-regression`; (D2) the cadence is **every 6 h** (`0 3,9,15,21 * * *`) plus `workflow_dispatch`; (D3) the `push` trigger is **dropped**, so a red names a window of merges of up to 6 h.

**Implementation note (test-architecture-implementer, 2026-10-06; rulings from test-architecture-reviewer):** the P1 bullet on removing `test.yml`'s nightly `schedule` is superseded: other jobs use it (`test.yml:957` and the code-health ratchet job), found by the implementer. Only the `slow` job moved out; the nightly trigger stays and its comment now says so. The Makefile loop `simq-corpus-diversity-slow-isolated` gained a per-invocation `--junitxml="reports/slow/corpus_$$n.xml"`; its 32-test floor and exit logic are unchanged (pinned by `tests/static/test_ci_slow_workflow_shape.py`). The job sets `permissions: { contents: read, issues: write }` at job level. First run with no open issue creates it with the full set and posts no per-test comments; a strict XPASS counts as red; a step with no JUnit file carries its previous failures over and keeps the issue open. `slow_known_reds.yaml` is accurate as of the PR's base, and an id mapped but no longer failing is shown as a stale mapping. `tools/test_architecture/impact_report.py` now also parses `slow-regression.yml` so the slow lane stays in its nightly/main-only list.

## Reporting-path hardening (2026-10-07, research-backed)

Source: the research report `CI known failure tracking patterns.md` (`/mnt/data/Working/reports/`, its "Ranked changes" table). The owner told `test-architecture-reviewer` "continue" after ranks 1–4 were recommended, so ranks 1–4 are approved and implemented here; ranks 5–14 are not approved and are not built.

- **Rank 1, dedup key.** The tracker issue is found through the REST issues list (never search): open, label `slow-regression`, creator `github-actions[bot]`, body marker `<!-- slow-regression-tracker -->` written by every render. The title carries a count, so it is not matched. More than one marked issue is a `::error` and exit 1. A human-created labelled issue is ignored. **Legacy adoption (migration, reviewer ruling):** exactly one open bot-created labelled issue with the JSON state block but no marker (issue #390, created before the marker existed) is adopted and gets the marker on the next render; two legacy issues is an error; a marked issue is preferred over a legacy one with a `::warning`. The legacy path can be deleted once #390 carries the marker: a one-line follow-up for a later batch, not now.
- **Rank 2, YAML aging.** Every `tools/test_architecture/slow_known_reds.yaml` entry carries `owner`, `added_on`, `expires_on` (ISO dates) and `kind: broken|flaky` beside `match`, `ticket`, `note`. A lint test fails on a missing field, a malformed date, `expires_on < added_on` or an unknown kind. An entry past `expires_on` is listed under **EXPIRED** and its failing tests count as red. Initial values as of 2026-10-07 (the reviewer's proposal; the owner can change them): corpus anchors, owner `test-architecture-implementer`, `flaky` (the failing set changed 10 → 12 between runs with different members), expires 2026-11-04; 5k and ph9, owner `rpg-implementer-2` (Lane B), `broken`, expires 2026-10-21; the movement, passive_scaling and strategic perf benches, owner `rpg-implementer` (Lane A, cooperation ticket; Lane B's combat ticket is named in the note), `broken`, expires 2026-10-21. The stale `test_perf_combat` entry is removed (combat[500] passed). Dates are not backdated or extended: if a merge slips past 2026-10-21 the run goes red for the expired entries, which is the mechanism working.
- **Rank 3, weekly digest.** On the first run in each ISO week (detected by the comment marker `<!-- slow-regression-digest YYYY-Www -->` already on the issue) one digest comment lists each failing test with its ticket, owner, kind, "tracked since", age in days, days to expiry and EXPIRED/UNOWNED flags. `first_seen` is kept in the state block and carried forward. When the previous state has none (issue #390's), every id already in it is seeded from the issue's `created_at` (run 37551894246, 2026-10-07), and the column is labelled "tracked since", not "first seen", so it does not claim more than is known. Ids new after merge get their real first-run timestamp.
- **Rank 4, exit semantics (reverses an earlier pin).** Steps 5–7 are `continue-on-error: true`; the report step is not. The report step exits 1 if a failing test is UNOWNED (matches no entry), if a failing test matches an EXPIRED entry, if a step produced no JUnit or an expected corpus id has no result, or if the GitHub API fails; otherwise 0, so a run whose every red is mapped and in date is green. A NEW mapped red (for example a new corpus anchor) still gets its NEW comment but does not fail the job. **A failing test that matches no entry is UNOWNED and the run is red on its first appearance: that is intended** (UNOWNED means nobody has triaged it, the one case that should be loud; a new corpus anchor matches the corpus pattern, so it is mapped). This **deliberately reverses** the "no `continue-on-error` on steps 5–7" assertion that #360 and #377 pinned; `tests/static/test_ci_slow_workflow_shape.py` now pins the new contract (steps 5–7 `continue-on-error: true`, the report step not). Reason, from the report: a permanently red workflow gets ignored; Trunk's exit-0-when-all-quarantined. `steps.<id>.outcome` stays "failure" for a red step, so the outcome summary stays truthful, while the job conclusion is the reporter's.
- **Beyond the brief (flagged):** an expected corpus id with no JUnit result ("unmeasured") also makes the run red, for the same reason a missing step does (absence of proof). The known-reds lint also runs inside the report step and fails the run on a bad entry.

## Scope
- Re-run the 16 sampled anchors on current `origin/main` and record which fail, with counts and
  conditions (seed, flags, world, tick budget). Establish the real number rather than inheriting 11.
- Determine **how long** they have been red. Bisect or sample historical commits — an anchor red for
  two days is a different problem from one red for two months, and the answer decides whether the
  fix is "repair the anchors" or "repair what the anchors were watching".
- For each failing anchor, classify: (a) the anchor's expected value is stale and the current
  behaviour is correct, (b) the simulation genuinely regressed and the anchor is right, or
  (c) the anchor is non-deterministic / flaky by construction and never protected anything.
  **These have different fixes and must not be resolved as one batch edit.**
- Decide and implement a reporting path so a red `@slow` anchor becomes visible without waiting for
  someone to trip over it — e.g. a scheduled (non-gating) lane, a periodic report, or promoting a
  deterministic subset out of `@slow`. Design call, not pre-decided.
- Audit whether other `@slow`-marked families have the same blind spot. This ticket was found by
  accident; the same failure mode may be sitting in test families nobody has had reason to run.

## Out of Scope
- **Editing any anchor's expected value to make it pass.** Re-baselining a specific anchor against
  evidence is legitimate and is handled per `docs/testing/regression_policy.md` §9-11 in its own
  ticket; blanket-adjusting 11 anchors to green is not, and would destroy the only record of what
  broke.
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` — the one genuine fix-caused
  shift from PR #269, already filed and owned separately.
- Making CI gate on `@slow`. That is a cost/runtime decision with its own trade-offs; this ticket
  needs the failures to be *visible*, which is a weaker and cheaper requirement. Raise gating as a
  separate proposal if the investigation concludes visibility is insufficient.
- The `frontier_marches` population_stability anchor — investigated during PR #269 and **confirmed
  noise**, not a regression: 5-vs-5 trials at t300 gave fix-tree 46/36/47/41/43 (mean 42.6) and
  untouched main 42/46/47/36/39 (mean 42.0) against a 37.2 floor. Both scatter across the floor and
  main dips below it too. Recorded here so it is not re-investigated; it may still qualify as
  class (c) above.

## Acceptance Criteria
- The real current count of failing anchors on `origin/main` is measured and recorded, with
  conditions, superseding the unverified 11.
- Each failing anchor is classified (a)/(b)/(c) with evidence, not assumed.
- How long the anchors have been red is established, at least to the nearest few weeks.
- A reporting mechanism exists such that a newly-red `@slow` anchor is surfaced without a human
  happening to run it, and there is a test or check proving the mechanism reports a seeded failure.
- Any anchor whose expected value changes cites its evidence per
  `docs/testing/regression_policy.md` §9-11.
- A statement on whether other `@slow` families share the blind spot.

## Related Tickets
- `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE` (rpg-planner; widened to the NARRATIVE step-change family, bisect then rebaseline)
- `TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE` (rpg-planner; SOCIAL step-change family; drafted, not yet on `main`)
- `TCK-20261006-SLOW-STEP-6-REDS-UNMASKED-BY-GATE-FIX` (the step-6 reds unmasked by the #360 gate fix)
- `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND` (PR #269 — the batch whose
  control run surfaced this)
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` (the one real fix-caused
  shift, filed in PR #269)

## Related Docs
- `docs/testing/regression_policy.md` §9-11 — the re-baselining procedure any anchor value change
  must follow.
- `docs/testing/test_taxonomy.md` — test classification rules, including what `@slow` is meant to
  signify.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` — the grade-anchor family itself.
- `src/simulation_quality/` — the scorers producing the ECONOMY / NARRATIVE / SOCIAL pillar values
  the anchors assert against.
- CI workflow definitions — wherever the `@slow` marker is excluded from the gating lane.

## Assumptions / Open Questions
- **The 11 count is unverified by this ticket's author** (see Request Summary). Treat it as a lead,
  not a measurement.
- Whether the right fix is "repair the anchors" or "repair the simulation" is genuinely unknown
  until the (a)/(b)/(c) classification is done, and the answer may differ per anchor. **Do not
  assume stale anchors** — that is the comfortable conclusion, and the one that would quietly erase
  a real regression if it is wrong.
- Whether a non-gating reporting lane is sufficient, or whether anything unreported eventually goes
  unread too, is a design question for the investigation.

## Implementation Notes
**Live run 1 — 2026-10-06 (test-architecture-reviewer).** `Slow regression` run **37472297079** (`workflow_dispatch` on `main` `d135dd6be041b51711411bfb9fad516c58fb2bfc`, the merge of #377; job 112298632075, 13:37:43Z → 15:36:52Z, about 2 h). Step conclusions from the REST jobs API: 5 corpus diversity **failure** (expected; cause parked), 6 slow tests **failure**, 7 legacy regression **success**, 8 step outcomes success, **9 report failing-set changes failure**, 10–11 uploads success. Step 9 failed because the repository had **Issues disabled**: `gh` returned "the 'ttnhan18062000/rpg-based-simulation' repository has disabled issues" (read from the background run of the reviewer's API polling). That is the B1 rule working as designed: a broken alert channel turns the step red rather than staying silent. The design's channel decision (D1) had not checked that Issues were enabled; the reviewer missed it. **Owner decision 2026-10-07: enable Issues.** `test-architecture-reviewer` set `has_issues=true` through the API at about 01:55Z with the owner's go-ahead. Not yet proven: the issue's first creation (first-run rule) and the failing set itself. The job log and the JUnit artifact are unreadable from the reviewer's host (TLS block on the log and blob hosts), so step 6's per-test outcomes, including the #367 campaign tests and the #373 milestone gate, are not confirmed by this run. Both are deferred to the next scheduled run, 37551894246 (started 00:25Z, before Issues were enabled; its report step runs after), whose issue body will list the failing set and can be read through the API.

**Run 3, 37551894246 (schedule, head bc4f7553c), report step success:** created issue #390 'Slow regression: 17 failing on main' with 0 comments (first-run rule), 12 corpus + 5 slow, all mapped, none UNOWNED, one stale mapping (test_perf_combat; combat[500] passed). Issues were enabled by the reviewer at ~01:55Z 2026-10-07 at the owner's direction.

**Owner direction 2026-10-07 (relayed by `test-architecture-reviewer`): perf-test failures are temporarily allowed during the core RPG and perf core implementation, so minimal effort on them.** The three perf-bench entries (movement, passive_scaling, strategic) in `slow_known_reds.yaml` are repointed to `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`, owner `rpg-implementer-2`, with `expires_on` 2026-12-31 and the note "allowed during core RPG + perf core implementation (owner, 2026-10-07)". Without this they would expire 2026-10-21 and turn the run red, which the owner does not want. This is an owner-decided extension, not a backdating; the other entries keep their dates (5k and ph9: 2026-10-21; corpus anchors: 2026-11-04).

**Measured classification and bracket, 2026-10-07 (testing-implementer).** Full table, method and limits in the staging `investigation.md` ("Measured classification — 2026-10-07"); per-run evidence in `anchor_history.tsv` (205 completed `main` corpus-step runs, 2026-08-26 → 2026-10-07, parsed from job logs) plus 3 local isolated rounds at 6e7ef56ec. Result: of the 12 reds in #390, **10 are step changes, not flakes**: NARRATIVE up on 5 frontier anchors (onsets #90–#104), SOCIAL up on 4 urban_political/frontier_living_world anchors (onsets #144–#172), and unit_selfmodel_pilot (ECONOMY after #269, which stays with its rebaseline ticket). The other 2 are the simq_routing COGNITION anchors, class (c). A fifth SOCIAL anchor, urban_political_seed42_1000t, is green in the #390 run but red in 120/121 runs since 09-15, so the two families hold 10 anchors in all. (a)-versus-(b) is routed to rpg-planner, with no anchor value touched. **Class (c)** overall: the 3 COGNITION anchors (both simq_routing, hero_guild; 12–28% red rates, flips at a fixed SHA) and 3 population anchors (about 3–4% red, no onset). Count corrections from testing-planner's review of #408 (comment 6035652280). This corrects the 2026-10-01 documentary table, which had classed most of the set (c). Age: last green corpus step 0d77b6877 (run 33247910319, 2026-08-29), red on every completed run from 2026-08-31, about 5.5 weeks; intermittent at a fixed SHA before that. Follow-up for the planner (not done here): `slow_known_reds.yaml` maps the whole corpus file as one `flaky` entry; the evidence says most of it is `broken`.

**Domain ruling, 2026-10-07 (rpg-planner, cross-session message in reply to #408).** All 10 step-change anchors are **class (a) pending bisect; domain-owned; deferred to after #407 / SURV-07 / decision 25.**
- Condition: each anchor is class (a) only if its onset bisects onto a deliberate behaviour PR. NARRATIVE: #90 (wound/scar system, reputation wiring), #98 and #101 (M2 foundational batches). SOCIAL: #144 (dormant mechanisms wired on purpose), #165 (survivor last-known-position fix), #172 (JOIN_PARTY accept path; trust accumulating is the point of that ticket). An onset that lands on a PR that must be behaviour-neutral is **class (b)** and gets its own fix ticket, not a rebaseline. The neutral PRs are #91 (semantic-index carry-forward) and #104 (spatial index), which are performance-only; #95-#97, #99, #100 and #102, which are docs-only; and #146 (dead Doctrine chain removed, test mocks) and #164 (frontmatter, pinning). frontier_marches (bracket starts at #91) and urban_political_seed42_1000t (no attributable onset) need the bisect most.
- Timing (regression_policy §11, re-measure after related fixes): no rebaseline yet. #407 (eating and sleeping), SURV-07 need escalation and decision 25 (whole-tile movement) will move these same worlds. The rebaselines happen after those three merge, on a fresh measurement at the §9-11 evidence bar.
- Tickets (rpg-planner owns them): `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE` is widened to the NARRATIVE family, and the SOCIAL-family twin is `TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE` (drafted by rpg-planner 2026-10-07; an rpg lane commits it to `todos/` with its next batch, so it is not on `main` yet). Each starts with the bisect and the (a)/(b) split. Both are queued for the rpg lanes after the starvation chain. Testing touches no anchor values.
- Known-reds expiry: rpg-planner says 2026-11-15 is acceptable if the gate needs one. Not changed here; the corpus entry's date (2026-11-04) is an owner/planner call, raised with testing-planner.

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
