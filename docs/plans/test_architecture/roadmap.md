---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture Roadmap (core RPG as first application)

**Status: owner decisions recorded 2026-09-30 (§11): D-R2, D-MF and D-M2 approved with changes; D-P deferred; D-PERF assigned when its trigger fires; D-PR resolved.** Approval lifts a HOLD; it does not mean the epic is complete. See each epic's own status.

This roadmap and the four epic tickets in `tickets/todos/test-architecture/` are the **binding** plan.
Everything in [`reference/`](reference/) is non-binding investigation and design material for the
detail planner and implementer agents. Child tickets are **not** created here; they are the detail
planner's job.

**Evidence base:** `04f911110`, with the progression leak re-checked at `5d4e4a237`. Main has since
moved substantially (about +6,200 lines by `e176e277e`), so **figures are dated, and every epic
re-measures before acting**.

**Domain map scope:** the ownership map (reference §3.1) covers the core-RPG domains **and** maps
strategic cognition, world dynamics and social/narrative at ownership level only, so the impact
model can route changes there. Mapping them is not a commitment to test them in the first
program. The RPG-feature facts were reviewed by `rpg-feature-planning` on 2026-09-29.

---

## 1 · Why this roadmap exists

A read-only assessment of the whole suite (1,491 test files, about 11k tests) found five problems.
Detail is in `reference/current_test_system_overview.md`.

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F1 | **High execution, unmeasured assertion strength** | 88% line coverage of `src/` (selected fast tiers, one local run); **0** mutation data; a recurring class of *never fires / never applied / always empty* tickets that shipped past green tests. The count depends on the matching method (exact title phrases gave 8 closed / 9 open on 2026-09-29; broader patterns give more), so it is **provisional**, and §4.7's escaped-defect tag replaces it | Green tests do not tell us whether behaviour is actually checked |
| F2 | **Test selection is agent judgement** | Test directories are mapped by prose; importers are found by a per-ticket grep; the static backstop silently skips unmapped files; mechanic scenarios are skipped on PRs touching several core-RPG paths (`PERF_RE`) | Relevant tests can be missed without anyone knowing |
| F3 | **Test planning and review are shallow in the agent workflow** | Only the test *level* is decided in `test_plan.md`; the implementer writes both code and tests; no phase reviews test quality; the installed test skills are never invoked | Test design quality depends on luck |
| F4 | **Hidden reliability defects** | 7 progression tests fail after any of 8 registry/catalog tests (CI hides it by splitting directories); a test run rewrites a tracked doc; `perf_baselines.json` has 0 entries; long-run determinism is parked | Combined measurements and perf claims are untrustworthy |
| F5 | **Uneven investment** | Agent-tooling tests are about 25% of all test code; `agent_codex_*` suites test a deferred pilot; about 240 files assert on doc/source text; 32 of 48 SimQ test files are narrow-mechanism checks | Maintenance cost without matching protection |

## 2 · Scope and success

**This roadmap owns** how tests are planned, written, selected, organized, executed, measured,
reviewed, maintained and repaired, applied first to core RPG.

**It does not own** RPG mechanic behaviour, feature acceptance criteria, feature proof portfolios, or
feature defect fixes. Those belong to the feature-owning teams, which are currently reworking core
RPG.

**Roadmap success** is measured by capabilities and trends, never by a count of feature behaviours
proven:

| Measure | How it is observed | Target direction |
|---|---|---|
| **Locate**: an agent finds the right domains, levels, tests and lanes for a change | impact report reasons; pilot capability 1 | selection misses recorded and falling |
| **Run**: relevant tests actually execute on PRs | report: relevant PRs → lane triggered → executed | no relevant PR without its lane |
| **Report honestly**: no silent zero, no false pass | report states; no-artifact vs not-in-supplied-runs vs outcome | every layer has a denominator or a state |
| **Detect faults**: tests catch injected faults in a baseline target | mutation score on a declared target, with provenance (§4.7) | baseline recorded, then non-decreasing on that target |
| **Escape less**: fewer defects reach `main` past green tests | `escaped-defect` tag count per month (§4.7) | trend visible, then falling |
| **Route failures**: failures reach the right owner with evidence | triage records by class | no unowned failure older than its closure condition |
| **Stay proportionate**: agent overhead stays bounded | Investigate/Implement `tool_call_count` per phase (a coarse proxy) | within the pilot's recorded bounds |

## 3 · Principles (binding)

1. **Behaviour source.** The Mechanics Bible and Engine Contracts define expected behaviour. The
   parity ledger is their evidence link. Changing an expectation means changing those documents first
   (CLAUDE.md's Authoritative Mechanics Rule). No agent re-approves an expectation by itself.
2. **Escalation to the user** when:
   - the document is silent (e.g. party);
   - ownership is missing;
   - domains dispute an expectation;
   - two Bible or contract sections disagree (date the competing sections first).
3. **No new authoritative proof-status record.** The parity ledger and mechanism registry keep their
   existing roles; this roadmap reports against them.
4. **Honest states.** Missing, skipped, stale, unstable and not-in-supplied-runs data are reported as such, never
   as 0 or pass.
5. **Never make red green by weakening tests:** no silent snapshot or anchor updates, broad
   skip/xfail, weakened assertions, or changed expected values without the documents changing.
   Existing failures stay visible.
6. **Tooling follows evidence.** Expensive tooling is built only when its trigger fires (§11).
7. **Core RPG is the application scope, not a feature commitment.** Worked examples are synthetic or
   confirmed stable with the feature team.
8. **Advisory first, required later.** New checks start advisory. Promotion to required is a
   recorded decision at the post-pilot review (§6), based on observed false-positive rate and cost.

---

## 4 · Target architecture (summary; detail in `reference/architecture_design_notes.md`)

The architecture has six capabilities. Each one feeds the next:

```
C1 structure ──► C2 impact/selection ──► C3 authoring workflow ──► C4 execution & evidence
      ▲                                                                   │
      └──────────── C5 failure triage & maintenance ◄────────────────────┘
C6 bounded pilot exercises C1–C5 on a real (or labelled synthetic) core-RPG change
```

### 4.1 Test levels (C1)

| Level | What runs together | Oracle | Typical cadence |
|---|---|---|---|
| Unit / component | a function or domain service on hand-built state | exact value or law | every PR |
| Kernel integration | real `Kernel` + profile + RNG, no world compiler | state over N ticks | every PR |
| Mechanic outcome scenario | a compiled world + kernel, one mechanic | occurrence **and** effect; a control only where the claim needs one | every relevant PR |
| Cross-domain scenario | ≥2 domains in one run | effect at each hop | relevant PR, or nightly (then **not** PR evidence) |
| Broad simulation | long runs, corpus | invariant monitors; SimQ tolerance bands | nightly / on demand |

**Techniques** (example, property, stateful property, metamorphic, characterization) are chosen per
behaviour by documented criteria, not required everywhere. Metamorphic and exact-replay techniques
wait for long-run determinism.

### 4.2 Evidence and report layers (C4)

The report keeps these **separate**:
- package coverage;
- domain coverage (`not-derived` until defensible);
- test classification;
- lane execution;
- architecture evidence;
- gameplay proof claims;
- mutation evidence;
- escaped defects;
- SimQ anchors;
- census reachability;
- hygiene.

States: `pass` · `fail` · `skipped` · `not-run` (a layer that was not run) · `not-in-supplied-runs` (a file absent from every supplied JUnit run; not "never executed") · `no-junit-artifact` · `no-coverage-artifact` ·
`drift-classified` · `unstable` · `stale` · `unknown` · `quarantined`.

Tests without an approved claim appear only as *executed evidence*:
- characterization tests are *change-detection* evidence, never correctness proof;
- broad simulation is *system-health* evidence.

### 4.3 Change impact and selection (C2)

- **Inputs:**
  - the ownership map (component → domain → oracle document → parity ledger);
  - a static import graph;
  - content/config rules for `data/worlds/**` and `config/**`.
- **Output:** recommended domains, levels, tests and lanes, each with a **reason**, plus an explicit
  `impact-unknown` list.
- **Rules:**
  - the impact report **never removes a lane**;
  - unknown impact triggers the **PR-eligible fallback**: every always-on PR job that holds core-RPG
    tests, plus the path-filtered core-RPG lanes forced on (the scenario lane, today inside
    `perf-cert-arena`, and `migration-lanes`). Jobs that CI runs only on `main`, nightly or by
    manual dispatch (`slow`, `simq-grade-drift`) are **not** part of the PR fallback. Their results
    are reported separately as nightly evidence, never as PR evidence;
  - it reports *selected*, *lane-triggered* and *executed* as three separate facts.

### 4.4 Authoring workflow (C3)

| Stage (existing agent) | Decides / records |
|---|---|
| Investigate (`investigator`) | impact set; per acceptance criterion: level, proof kind, oracle source (Bible/contract section + ledger id), expected effect, commands; optionally negative cases, fixtures, non-functional risk |
| Implement (`implementer`) | tests written using the level contracts and patterns |
| Architecture-Verify (`architecture-reviewer`) | advisory, diff-scoped test-quality checklist; each substantive finding acted on or declined with a reason |
| Test (`test-scoper`) | commands and the reason for each |
| Verify (`done-checker`) | mandatory fields present |
| Epic (`implement-epic`) | shared fixtures and patterns recorded at the epic level |

No new phase or agent unless the pilot shows the existing roles fall short.

### 4.5 Failure triage and maintenance (C5)

Every failure starts with an evidence record:
- reproduction command;
- seed / world / config;
- SHA and run ids;
- expected vs observed;
- whether a rerun changes the outcome.

| Class | Who acts | Immediate action |
|---|---|---|
| Product regression | change author → feature team | fix the code, not the test |
| Test defect / wrong oracle | test author; the oracle document decides | fix the test, keeping an equivalent-or-stronger assertion |
| Intentional spec change | change the oracle document + ledger first | then update the expectation |
| Order dependence / nondeterminism | test infrastructure | fix the root cause; bounded quarantine only if needed |
| Environment / fixture | CI / infrastructure | fix the environment |
| Stale baseline / missing data | the baseline's owner | show `stale` / `no-data`; regenerate only via the approved process |
| CI selection failure | this roadmap | run the missed lane; record a selection failure |
| Unknown | triage owner | keep the evidence; escalate; change nothing |

### 4.6 Maintenance rules

- A test's expectation changes only with its oracle document.
- Flaky tests get an owner and a bounded quarantine, never a permanent xfail.
- Tests that start rewriting tracked files are hygiene defects.
- Defects that tests find go to the feature-owning team.

### 4.7 Test effectiveness (addresses F1)

Coverage says code ran; it doesn't say faults would be caught. Two lightweight measures, both in
Epic A:

1. **Mutation baseline on one declared target** (`mutmut`).
   - **Candidate:** the resource-conservation code (Bible ch03), used **only if the feature team
     confirms a stable window**. `rpg-feature-planning` (2026-09-29) said it is not in their first
     wave, with no stability window promised.
   - **Otherwise** a synthetic target, reported as a **tooling exercise**: it shows the mutation
     workflow works, **not** how strong the core-RPG tests are. Recorded with the target, selected tests, SHA, date, runtime and result
   categories (killed / survived / timeout / equivalent). It becomes `stale` when the target changes
   or after 30 days. **Local and on demand; no CI job.** This is a narrowed form of the D4 direction
   approved on 2026-09-28.
2. **Escaped-defect tracking.** A registered `escaped-defect` ticket tag for defects that reached
   `main` past green tests, with the failure class from §4.5. Counted per month in the report. This
   replaces today's title-matched estimate with a declared signal.

Neither is a gate. Both feed the post-pilot review (§6).

---

## 5 · How an agent uses it (one change, end to end)

1. **Locate.** A ticket changes a rule in `src/systems/…`. The impact report names the economy
   domain, the recommended levels, the tests and lanes with reasons, and any `impact-unknown` paths.
2. **Plan.** The `investigator` fills `test_plan.md`: level and proof kind per acceptance criterion,
   the oracle (Bible ch03 section + parity-ledger id), the expected effect, and the commands. If the
   acceptance criterion changes an expectation, the Bible and ledger change first, or it escalates.
3. **Write.** The implementer uses the level contract and a documented pattern (e.g. a stateful
   property for conservation) and marks the test with domain and level metadata.
4. **Review.** The architecture reviewer runs the test-quality checklist on the changed tests.
5. **Run.** The test-scoper runs the recommended commands locally.
   - **D-R2 (approved with changes, implemented 2026-09-30):** a `src/systems/…` change triggers the
     scenario lane on the PR, and so does a change to `tests/mechanic_scenarios/**` alone. The lane
     runs once per PR: inside `perf-cert-arena` when that job's filter matches, otherwise in the
     dedicated non-required `scenario-lane` job. The job is not a merge gate by convention
     (`main` has no branch protection).
   - The agent still runs the scenario tests locally, and the report records what was supplied.
6. **Report.** The report shows the new test classified, executed and passed in its lane.
7. **Fail** (if it fails). The failure gets an evidence record and a class, and goes to its owner. A
   product defect goes to the feature team.

## 6 · Phases and decision points

| Phase | Content | Exit / decision point |
|---|---|---|
| **1. Build and prove** | Epics A–D (§7) | The pilot report (Epic D) |
| **Post-pilot review** (a recorded owner decision) | Review the pilot's capability results, the report trends (§2 measures) and each advisory check's false-positive rate and cost | For each advisory check (metadata, test-quality checklist, tracked-file guard, oracle review): **keep advisory / promote to required / drop**. Whether to extend to the next domains (cognition, social, strategy) in bottom-up order. Which deferred items (§11) have fired |
| **2. Scale out** (only if approved) | Apply conventions and metadata to the next domain batch; promote the approved checks | Per-batch review, same measures |
| **3. Steady state** | Report trends reviewed periodically; cleanup (§9) driven by report data | Ongoing |

No phase has a date; each starts on its predecessor's decision.

## 7 · Epics (Phase 1)

| Epic | Outcome | Depends on | Parts that were gated (decision recorded 2026-09-30) |
|---|---|---|---|
| **A. Test baseline and reliability** (`TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`) | A reproducible core-RPG test report that works with the **available** artifacts (`no-junit-artifact` / `no-coverage-artifact` where absent). The **known** progression order leak is fixed, and the known write to `docs/brainstorm/mechanism_verification_view.md` is stopped. A mutation baseline and escaped-defect tracking are set up (§4.7). Any general tracked-file guard is advisory. Remaining unknowns are reported. **No new CI job** | — | none |
| **B. Test structure and selection** (`TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION`) | Written test-level conventions and metadata. Scenario tests run on relevant PRs. A first impact report that adds reasons and `impact-unknown` flags and never removes lanes | A (report v0, for reporting only) | CI scenario-lane rule (D-R2 approved; implemented, job non-required until cost is measured) |
| **C. Test workflow and failure handling** (`TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING`) | Test-plan fields and an advisory test-quality checklist in the existing workflow; one unified failure-triage procedure | B (conventions) | oracle-review step (D-M2 approved; advisory, text only); quarantine policy (D-MF approved; policy text only, nothing quarantined) |
| **D. Bounded core-RPG pilot** (`TCK-20260929-EPIC-CORE-RPG-TEST-PILOT`) | One or two exercises. The pilot report **lists which capabilities were actually demonstrated**. Approved-oracle review is claimable only if the D-M2 step was exercised on a real change | The **minimum usable workflow** (below), not every part of A–C | surface confirmation at start (resource conservation is a **candidate** until confirmed) |

**Minimum usable workflow for D:**
- A's report v0;
- A's known-leak fix, at least `provisional`;
- B's taxonomy doc;
- C's test-plan fields;
- C's triage procedure.

Optional parts (impact report, pattern library, quarantine policy, oracle-review step) are used if
they are ready.

**A synthetic-only pilot is `provisional`.** It does not establish that the workflow works on a real
RPG change.

**Hold rule.** Work marked `HOLD — pending D-x` may be *described* by detail planners, but no
implementation child ticket for it may be activated, and no gated work may start, until the owner
approves that decision. Ungated work is independently startable. As of 2026-09-30 no HOLD is open: D-R2, D-MF and D-M2 are approved, and D-P and D-PERF gate nothing in A–D.

## 8 · Non-functional risk register (addresses F4)

| Risk | Current state [dated] | Owner | Handling in this roadmap |
|---|---|---|---|
| Order dependence | 7 known progression failures; more unknown | this roadmap | Epic A fixes the known case; the random-order extent stays an explicit unknown in the report |
| Tests writing tracked files | 1 known file | this roadmap | Epic A fixes the known file; any general guard is advisory |
| Long-run determinism / replay | parked by owner (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`) | kernel / determinism owner | Only short-run reproducibility may be claimed; metamorphic and exact-replay techniques wait (§11) |
| Performance | `tests/perf` framework exists; `perf_baselines.json` has **0 entries**; only 2 test files use the fixture | performance owner [D: unassigned] | The report shows perf as `no-baseline`; calibrating core-RPG perf baselines is deferred with a trigger (§11) |
| CI cost | PR wall time about 7–9 min; the scenario lane adds an estimated 1–3 min | this roadmap | Measured before any rule expansion (D-R2) |
| Content/config compatibility | migration lanes are path-filtered; `data/worlds/**` changes have no selection rule | this roadmap | Content/config rules in the impact report (Epic B) |
| SimQ anchor drift | Anchor tests skip silently on PRs. Two historical measurements with different populations, **not a trend**: (a) about 2026-09-01, tool-level sweep: 61 drifted of 81 run keys (79 executed, 2 not run); (b) 2026-09-03, pytest re-check: 62 failed of the 79 parametrized comparisons. No current measurement | SimQ owner | The report shows `skipped-no-data`; the repair belongs to SimQ |

## 9 · Test-suite health and cleanup (addresses F5)

The assessment found cost without matching protection (F5). Pruning by line-count ratio alone is
**not** allowed.

1. **Measure first.** Once Epic A's report exists, it adds a per-directory cost view: test count,
   runtime, failure history, and whether tests protect a declared behaviour or only assert text.
2. **Candidates:**
   - the `agent_codex_*` suites (deletion intent approved 2026-09-28 as D6, execution still pending);
   - doc/source-text assertion tests;
   - positional hook pins;
   - SimQ narrow-mechanism tests that belong in mechanic scenarios;
   - duplicate or empty test directories.
3. **Per-target record before any change:** importers, Makefile and CI references, and plan/ticket
   references.
4. **Trigger** (§11): Epic A's cost view exists **and** the post-pilot review (§6) accepts a cleanup
   batch. Deletion needs an owner decision per target.

## 10 · Roles and ownership

| Role | Responsibility |
|---|---|
| **Owner (the user)** | Approves D-decisions and phase transitions; the escalation point for oracle silence, disputes and intra-Bible conflicts; approves deletions |
| **Feature-owning teams** (via `rpg-feature-planning`) | Mechanic behaviour, oracle documents and ledger changes for their features, feature acceptance criteria, and fixing defects routed to them; confirm stable pilot surfaces |
| **This roadmap's implementers** | Epics A–D child work: report, repairs, conventions, workflow changes, pilot |
| **Detail planner** | Breaks the epics into child tickets; respects the HOLD markers |
| **SimQ owner** | Anchors, drift policy, the silent-skip repair |
| **Mechanism-registry epic** | The canonical mechanism → test link |
| **Kernel / determinism owner** | The parked long-run determinism root cause |

## 11 · Pending owner decisions and deferred items

**Owner decisions (recorded 2026-09-30):**

| Id | Decision | Status | Gates |
|---|---|---|---|
| D-R2 | Scenario-lane rule, approved with changes. The lane triggers on `src/**`, on known scenario dependencies and on `tests/mechanic_scenarios/**` (the old `PERF_RE` omitted that last path, so a PR editing only a scenario test ran no scenario test in CI). Unknown or new paths fail open and are named in the job summary. Known-irrelevant paths are listed explicitly, each with evidence. The job stays non-required until CI run cost is measured over real PRs **and the measured cost is shared with the feature teams (through rpg-feature-planning) before the rule is promoted**. | approved; implemented (job non-required) | the CI rule change in B |
| D-MF | Bounded quarantine replaces `regression_policy.md` §6's unbounded `xfail(strict=False)`: nondeterminism only; node-level strict xfail; owner, ticket, expiry at most 14 days, one renewal that keeps the original start date; a recorded failure signature (`raises=` plus a message or node pattern). **No quarantine is applied until a minimal expiry check exists**; the first real case triggers building it before the quarantine is applied. Policy text only: no enforcement tooling, and nothing is quarantined. | approved; policy text landed | the quarantine policy in C |
| D-M2 | Oracle model: the Mechanics Bible / engine contract (behaviour) plus the parity ledger (evidence links); see `reference/architecture_design_notes.md` §3.1–3.2. **An expected value no document states (a balance or emergent threshold) stays an exploratory measurement, not a proof, until the owner or feature team approves a derivation.** Oracle review is advisory during the pilot and never authorizes an agent to change an expectation: an expectation change still needs the oracle document and ledger to change first, or an escalation record. | approved; rule recorded (advisory, text only) | the oracle-review step in C |
| D-P | Party: no oracle document or owner | deferred | nothing in A–D |
| D-PERF | Who owns calibrating core-RPG performance baselines | assigned when its trigger fires | nothing in A–D |
| D-PR | Which PR carries these plan docs | resolved by owner instruction: plan PR #256 | — |

**Deferred items and their triggers:**

| Item | Trigger |
|---|---|
| Review-record validator | A feature team first asks to register a proof, or the registry epic ships its mechanism → test link |
| Seeded-fault evaluation harness | Before the impact report is ever used to skip a test or lane, or after the first recorded CI selection failure |
| Per-test coverage contexts | A recorded selection failure where static inputs missed a dynamic dependency |
| Quarantine enforcement tooling | The first real case needing quarantine |
| JUnit upload from every CI job | When manual JUnit input to the report becomes the recurring bottleneck (today only `api-tools` uploads) |
| CI coverage job | After its runtime is measured and its information is judged useful (not an owner-decision gate) |
| Broader mutation testing (more targets, scheduled runs) | The post-pilot review, if the baseline showed useful survivors |
| Core-RPG perf baselines | A feature change needing a perf claim, or the post-pilot review (D-PERF) |
| Party ownership assessment | The owner assigns party an oracle document and owner (D-P) |
| Metamorphic tests, exact-replay sweeps | Long-run determinism unparked |
| Cleanup batch (§9) | Epic A's cost view exists and the post-pilot review accepts a batch |
| Scale-out to further domains | Post-pilot review approval (§6) |
| Parity evidence model, API/UI tests | Their own decisions or a demonstrated core-RPG dependency |

## 12 · Risks to this roadmap

| Risk | Mitigation |
|---|---|
| Feature rework makes examples and pilot surfaces obsolete | Oracle = documents, and approvals go stale when they change; synthetic fallback; the pilot surface is confirmed at start |
| Advisory conventions get ignored | Measures in §2; the post-pilot promotion decision (§6) |
| Over-planning or over-tooling | Tooling behind triggers (§11); detail left to the detail planner |
| Agent-prompt edits conflict with other sessions | Epic C coordinates prompt changes with the agent-working sessions before editing |
| CI cost creep | Every CI change measures its cost first; the impact report never adds blocking gates on its own |
| Stale evidence | Every figure dated; epics re-measure at start |

## 13 · Reference (non-binding) and key sources

- [`reference/current_test_system_overview.md`](reference/current_test_system_overview.md): as-is
  measurements.
- [`reference/architecture_design_notes.md`](reference/architecture_design_notes.md): full level
  contracts, proof kinds and freshness, the triage class table, the quarantine mechanism with the
  observed pytest 9.0.2 behaviour, and references R1–R29.
- [`reference/milestone_design_notes.md`](reference/milestone_design_notes.md): work packages and
  costs.

Key external sources behind the design:
- Google test sizes and the practical test pyramid (R1, R7);
- Beck's Test Desiderata (R9);
- mutation testing at Google and pseudo-tested methods (R5, R6);
- flaky-test root causes (R15);
- the test oracle survey (R24);
- safe regression test selection (R27).
