---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Current Test System — Status and Overview

**Snapshot of code at `04f911110` (test, `src/`, CI and agent files unchanged through `origin/main` `9bcae32c5`), measured 2026-09-27/28.** This is the single home for
the *as-is* state of the test system: layout, lanes, authoring process, measured numbers, and
per-domain verdicts. The *to-be* direction and decisions live in
[`test_architecture_epic.md`](test_architecture_epic.md); reference IDs `[R#]` point to that
doc's §13 References.

**Revision 2026-09-28b** (after external review). Corrected: perf verdict (§6.3); world and anchor
counts; the SimQ oracle description and the historical status of the drift figures (§4.7). Added:
change-impact / test-selection as-is (§8), reusable harness inventory (§9), and the workflow stage
map (§5.1). Relabelled: sampled verdicts and title-based escape counts are **provisional signals**.

**Revision 2026-09-28c** (second review). Added: parity schema-error categories (§4.6) and the
core-RPG test-classification inventory (§10).

**Evidence labels used here:** **[O]** observed in the repo or command output (path or command
given) · **[P]** provisional signal (sampled or title-matched, not exhaustive) · **[I]** inference ·
**[H]** historical statement quoted from a ticket or comment, not re-measured.

How this was measured: file and LOC counts by script over `tests/`, `src/`, `tools/`; one
`coverage run --source=src` over the fast tiers; four read-only domain assessments that sampled
5–10 test files per area (not every test); and a direct read of `.github/workflows/test.yml`,
`pyproject.toml`, `.claude/agents/`, and `.claude/workflows/implement-ticket.js`. Re-measure
before citing any number after this date.

---

## 1 · Status at a glance

| Area | Status | One-line reason |
|---|---|---|
| Execution breadth | 🟢 Good | 88% line coverage of `src/`: selected fast tiers only, one run with 8 failures (§4.1) [O] |
| Assertion strength | ⚪ Unmeasured | No mutation testing exists; the escaped-defect titles *suggest* weak assertions [P] |
| Liveness in real runs | 🔴 Gap | ~30 closed + ~15 open tickets with *never fires / never seeded / always empty* titles [P] |
| Shape | 🟠 Top-thin | 44 mechanic-scenario tests against ~5.7k unit tests |
| Determinism proof | 🟠 Partial | Fast-lane `test_reproducibility` exists; nightly slow lane red (parked by decision) |
| Isolation | 🟠 Leaking | 7 progression tests are order-dependent; hidden by CI's per-directory split |
| Traceability | 🔴 Broken | 93% of parity-ledger P0 entries have no `test_path` |
| Proportionality | 🟠 Skewed | Agent-infra tests are ~25% of all test LOC; Codex-pilot suites for a deferred feature still in CI [O] |
| Measurement tooling | 🔴 Missing | `make test-cov` points at non-existent `tests_v2/`/`src_v2/` (`Makefile:209-210`); no scorecard [O] |
| Corpus evaluation | 🟠 Silent on PRs | SimQ anchor-band tests skip when `data/calibration/` is absent, which is every CI PR run (§4.7) [O] |
| Test selection | 🟠 Agent-judgment | No machine map joins change → domain → tests → CI lane; unmapped files are skipped silently (§8) [O] |
| Authoring process | 🟠 No quality review | No pipeline phase reviews test quality (§5) |

---

## 2 · Layout

### 2.1 Test tree (`tests/`)

| Directory | Files | Tests | LOC | Role |
|---|---|---|---|---|
| `unit/` | 780 | 5,717 | 127k | Per-package unit tests, 42 sub-dirs (breakdown §2.2) |
| `tools/` | 185 | 3,052 | 53k | Tests for `tools/` (agent-monitoring, gate checks, registries, delivery) |
| `integration/` | 199 | 776 | 34k | Multi-component and real-kernel runs, 24 sub-dirs |
| `simulation_quality/` | 48 | 503 | 7.5k | SimQ scorers; 32 of 48 files are single-mechanism `*_corpus.py` |
| `api/` | 21 | 150 | 3.6k | FastAPI via `TestClient` (one subprocess outlier) |
| `architecture/` | 32 | 95 | 3.2k | Import-boundary and durable-state write-path guards |
| `certification/` | 16 | 75 | 2.5k | Milestone/manifest gates |
| `perf/` | 34 | 69 | 2.9k | Budget tests against `perf_baselines.json` |
| `mechanic_scenarios/` | 18 | 44 | 2.4k | One mechanic per real `WorldCompiler` + `Kernel` run |
| `docs/`, `static/`, `integrity/`, `refactor/` | 37 | 166 | 4.9k | Doc/static/integrity guards |
| `agent_*` (12 dirs) | ~95 | ~408 | ~8.1k | Agent orchestration / replay / Codex-pilot suites |
| other (`cli`, `engine`, `arena`, `observability`, `logging`, `regression`) | 19 | 64 | 2.3k | Small or legacy top-level suites |
| **Total** | **1,484** | **11,119** | **252k** | vs `src/` 135k LOC and `tools/` 47.6k LOC |

Support code: root `tests/conftest.py` (225 lines) plus 10 suite conftests (6 of them in
`agent_codex_*`, `agent_replay_codex`, and `unit/tools`); `tests/helpers/` (entities, presets,
resources, runtime, assertions, domain, content-usage gate); `tests/fixtures/` (agent-monitoring,
agent-replay, hook payloads, lab runs, one world-grammar baseline); `tests/parity/oracles/` holds
3 legacy oracle JSONs only.

Frontend: `frontend/` runs `vitest` in CI (4 test files for 22 source files) and has one
Playwright spec (`frontend/e2e/live_map.spec.ts`) that **no CI job runs**. `dashboard-frontend/`
has 15 vitest files that **no CI job runs**.

### 2.2 Unit tests by sub-directory (top 20 by test count)

| Sub-dir | Files | Tests | | Sub-dir | Files | Tests |
|---|---|---|---|---|---|---|
| observability | 117 | 1,062 | | lab | 18 | 119 |
| domains | 185 | 1,044 | | combat | 24 | 113 |
| world | 44 | 330 | | progression | 12 | 103 |
| tools | 24 | 317 | | worldassembly | 10 | 101 |
| strategic | 61 | 299 | | resource | 18 | 87 |
| social | 33 | 296 | | quest | 9 | 82 |
| core | 51 | 253 | | rendering | 12 | 76 |
| content | 17 | 244 | | kernel | 20 | 64 |
| engine | 23 | 230 | | movement | 12 | 57 |
| worldbuilding | 12 | 169 | | api | 9 | 53 |

Structural oddities: `unit/entity/` and `unit/entities/` both test `src/entities/`;
`unit/motivation/` and `integration/perf/` are empty; `unit/config/` tests
`src/domains/optimization/feature_flags.py` rather than `src/config/`; top-level
`tests/observability/` (3 files) sits beside `unit/observability/` and `integration/observability/`.

### 2.3 Classification in use

`pyproject.toml` declares 27 markers. Actual usage: `slow` 147, `parametrize` 111, `v2_contract`
~109, `anyio` 62, `perf` 20, `extra_slow` 17, `integration` 13, `resource_budget_large` 12; most
others are used 0–5 times. The legacy-parity markers (`legacy_characterization`, `differential`)
describe a `src_legacy` comparison that no longer exists. There is no size marker (small / medium
/ large [R1]) and no purpose marker (quadrant [R3]); directory name is the only tier signal.

---

## 3 · CI lanes (`.github/workflows/test.yml`)

| Job | Runs | Trigger |
|---|---|---|
| Unit · core / world | `unit/{core,kernel,engine,config,runtime,platform,world,world*,content*,replay}` | PR + push |
| Unit · gameplay | `unit/{strategic,combat,social,economy,resource,progression,quest,movement,motivation,tactical,scenarios,systems,actions,ai}` | PR + push |
| Unit · infra / observability | `unit/{domains,observability,rendering,lab,lab_agent,api,cli,views,perf,entity,entities,cognition,docs,certification,tools}` (one step each) | PR + push |
| Integration | `tests/integration` | PR + push |
| API / tools / logging | `tests/{api,cli,tools,logging,engine,observability}` | PR + push |
| Agent orchestration / codex / replay | all 12 `tests/agent_*` | PR + push |
| Simulation quality | `tests/simulation_quality` | PR + push |
| Architecture / docs / static | `tests/{architecture,docs,integrity,static,refactor}` | PR + push |
| Perf / cert / arena | `tests/{perf,certification,arena,mechanic_scenarios}` | push; on PRs **only if the path filter matches** (below) |
| Frontend | `frontend/` `vitest run` + build | PR + push |
| Migration lanes | `make lane-all-fast`, `make gate-expansion` | path-filtered |
| Type check, SimQ grade-anchor drift | informational | mixed |
| **Slow regression** | `pytest tests/ -m "slow or extra_slow"` (excludes `test_corpus_diversity.py`) | main push + nightly 03:00 + manual; **red, parked** |

All PR lanes use `-m "not slow and not extra_slow"`. Every pytest lane also runs a base-branch
`--collect-only` diff for its job summary.

**Path-filter gap for the scenario tier:** `tests/mechanic_scenarios` runs only in *Perf / cert /
arena*, which on PRs runs only when the diff matches `PERF_RE`: `tests/(perf|certification|arena)/`
or `src/(ai|api|certification|cognition|config|core|domains|engine|observability|perf|platform|replay|world|worldbuilding)/`.
A PR touching only `src/{systems,progression,entities,economy,quests,town,actions,strategy}` or
`tests/mechanic_scenarios/` itself does **not** run the mechanic scenarios before merge; they run
only on the post-merge push to `main`.

---

## 4 · Measured health

### 4.1 Coverage (fast tiers, `coverage run --source=src`)

Run: `tests/{unit,integration,mechanic_scenarios,api,engine,simulation_quality}`,
`-m "not slow and not extra_slow"` → 7,489 passed · 8 failed · 73 skipped · 122 deselected in
16m54s. **Total: 88% line coverage** (not branch). Scope label, to carry wherever the figure is
quoted: *`src/` only; selected fast tiers; `tools/`, `agent_*`, perf, certification, arena,
architecture, slow tests and frontend excluded; 8 failing tests were not excluded from the data;
one local run, no CI job reproduces it* [O]. Command: `coverage run --source=src -m pytest
tests/{unit,integration,mechanic_scenarios,api,engine,simulation_quality} -m "not slow and not
extra_slow"`.

| Package | Stmts | Cover | | Package | Stmts | Cover |
|---|---|---|---|---|---|---|
| observability | 13,397 | 85% | | api | 2,018 | 75% |
| engine | 9,216 | 91% | | worldbuilding | 1,407 | 79% |
| domains | 5,859 | 96% | | content | 1,409 | 93% |
| core | 4,705 | 92% | | simulation_quality | 1,383 | 95% |
| lab | 4,025 | 83% | | world | 1,292 | 91% |
| systems | 3,191 | 90% | | certification | 780 | 59% |
| cli | 735 | 56% | | perf | 270 | 44% |

Large files under 25%: `src/lab/cli.py` (0%), `src/api/ws/stream.py` (13%),
`src/perf/bench_harness.py` (19%), `src/perf/scenarios.py` (21%).

**Reading [I]:** execution breadth is not the bottleneck. High coverage together with escaped
*never fires* defects is *consistent with* the pseudo-tested pattern [R6], but **no mutation run
has confirmed it**; that is a hypothesis for the first mutation baseline to test [R5].

### 4.2 Failures on `main` in a combined run

- **At `04f911110` (2026-09-27):** 7 in `tests/unit/domains/progression/`, plus
  `test_real_registry_findings_pinned` (pins live repo data).
- **Re-checked at `5d4e4a237` (2026-09-29):** the **same 7** fail in the combined run (7,498
  passed; 563 s) and in `tests/unit` alone (263 s). All 18 tests in their files pass alone. **CI's
  `Run: tests/unit/domains` step is green** (run `36522228787`), because it runs that directory on
  its own, so the failures are invisible in CI [O].
- **Polluters:** 8 files, each sufficient on its own:
  - `tests/unit/content/test_adapter_heuristic_reporting.py`, `test_runtime_content_mode.py`;
  - `tests/unit/core/test_catalog_fallback.py`, `test_catalog_smoke_simulation.py`,
    `test_hardcoded_regression_guard.py`, `test_registry_adapters.py`,
    `test_registry_cross_reference.py`, `test_registry_parity.py`.

  All exercise catalog/registry/content-mode switching [O]; a shared registry state is the
  suspected cause [I].
- `test_real_registry_findings_pinned` no longer fails at `5d4e4a237`.

### 4.3 Slowest fast-lane tests

80s and 60s: `tests/unit/tools/test_mechanism_state_caller_check.py` (two tests, in a *unit*
lane). Then 20–28s real-kernel tests in `integration/world`, `unit/observability`,
`integration/domains/progression`, and `unit/engine`, several of which are *large* tests [R1]
living in unit directories.

### 4.4 Assertion style and test-smell signals (repo-wide script counts)

| Signal | Count | Note |
|---|---|---|
| Test files reading `.md` docs | 243 | Doc-text assertions; structure-coupled [R9] |
| Test files matching `src/`/`tools/` `.py` paths as text | 152 | Source-grep tests; *Fragile Test* smell [R13] |
| Test files using `subprocess` | 122 | Often medium/large, not small |
| Test files using mocks/monkeypatch | 246 | Of 1,484 |
| Test files citing a `TCK-2026…` ticket ID | 786 | Traceability comments (fine); some files grow one ticket block at a time |
| `skip` / `xfail` occurrences | 96 / 12 | |
| Property-based tests (Hypothesis) | 0 | Installed (`requirements.txt`), unused |
| Positional hook-array pins (`PreToolUse[4]`) | 3 files | Break on hook reorder |

### 4.5 Escaped-defect record (defect-escape analysis) [P]

Ticket titles in `tickets/done/` and `tickets/todos/` matching *never fires / never applied /
never seeded / always empty / never wired / starvation*: about **30 closed** (for example
`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`,
`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`,
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`) and about **15 open** (for example
`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`,
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`). These were found by SimQ runs, the
execution census, and manual audits, not by the test suite. **Provisional:** counted by title match
only; titles were not individually confirmed as defects that tests *should* have caught, and one
root cause can span several tickets.

### 4.6 Parity-ledger traceability (`docs/parity_ledger/*.yaml`)

| File | Entries | P0 | P0 without `test_path` | P0 citing a missing file |
|---|---|---|---|---|
| substrate | 405 | 371 | 361 | 2 |
| combat_movement | 323 | 296 | 278 | 2 |
| infrastructure | 421 | 188 | 173 | 2 |
| social_narrative | 294 | 227 | 211 | 11 |
| strategic_cognition | 274 | 229 | 205 | 4 |
| town_resource | 191 | 168 | 145 | 6 |
| progression | 125 | 108 | 102 | 1 |
| world_dynamics | 141 | 97 | 89 | 0 |
| faction | 16 | 1 | 0 | 0 |
| **Total** | **2,190** | **1,685** | **1,564 (93%)** | **28** |

Most unlinked entries carry a recycled narrative `v2_evidence`, not a runnable test. The CLAUDE.md
rule "P0 entries require a passing `test_path`" is not enforced on the corpus.

**Schema-validation baseline [O]** (planner run of `jsonschema.Draft7Validator` against
`docs/parity_ledger/schema.json` over all 9 shards, 2026-09-28): **2,867 errors across 1,561
entries**, in two categories only:
- **2,842** `type` errors on `test_path`: the value is null where the schema's conditional branches
  require a string. The P0 / verified branches overlap, so one entry can raise more than one.
- **25** `enum` errors on `proof_type`.

By shard: substrate 664, combat_movement 514, social_narrative 376, strategic_cognition 340,
infrastructure 330, town_resource 277, progression 189, world_dynamics 177, faction 0. In the
schema, `priority` means **importance** and is independent of `status` / `proof_type` / `test_path`.
The P0 → `test_path` rule dates from `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` and applies on
writes only (`tools/parity_ledger_writer.py`).

### 4.7 Corpus evaluation (SimQ), exploratory measurement, and audits

These instruments sit **outside** the pytest level stack. They differ in what the result is
compared against (the *oracle* [R24]), not only in scope.

**World corpus (test input, not a level).** `data/worlds/` holds **24 world directories** [O];
**21** are tiered in `corpus_registry.yaml` `_worlds`; the 3 untiered are
`camp_maturity_calibration_pilot`, `unit_information_routing_pilot`, and
`mechanic_scenario_combat_judgement_withdrawal` (a scenario fixture, not a corpus world).
`config/simulation_quality/corpus_registry.yaml` lists 81 anchor runs (world × seed × ticks: 51 at
200t, 12 at 500t, 12 at 1000t, 6 at 2000t) and tiers the 21 worlds as unit 5 · end-to-end 8 ·
stress 6 · regression-baseline 2. The tiering follows
`docs/simulation_quality/corpus_tier_taxonomy.md`, which applies the test pyramid to *worlds*.
The corpus is shared input for SimQ, the execution census, and some mechanic scenarios.

**SimQ (`src/simulation_quality/`)** scores runs on 10 pillars (COGNITION, AGENCY, COMBAT,
FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE;
`docs/simulation_quality/quality_scoring_contract.md` §5). It compares grades against committed
anchors in `tests/simulation_quality/fixtures/grade_anchors.json`. That file has **81 anchors, the same 81
run keys as the registry**. `tests/simulation_quality/test_grade_regression.py` parametrizes
**79** of them (61 fast ≤500t + 18 slow; no overlap). The remaining 2
(`urban_political_selfmodel_probe_seed42_200t`, `urban_political_selfmodel_execution_probe_seed42_200t`)
are compared by **two named, non-parametrized tests** (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`…_execution_isolated_grade_anchor`, `test_grade_regression.py:437, 479`). So all 81 anchors have
exactly one comparison test: **81 anchor comparisons = 79 parametrized + 2 named** [O].
*Correction:* revision b of this overview called the 2 probe keys "unreferenced"; that was
wrong, because the scan only read the parametrize lists.

Two separate stages, with different result types [O]:

1. **Anchor-band check (execution level, pass/fail).** For each run key, every pillar must stay within
   ±1 grade letter of its anchor **and** within `max(0.05, 20% × |anchor score|)` of its score,
   with evidence-derived per-(run key, pillar) overrides (`SCORE_TOLERANCE_OVERRIDES`,
   `test_grade_regression.py:59-120, 244-268`). This is a **reference-value (golden) oracle with
   tolerance bands**, evaluated on **one seed per run key**. It is *not* a statistical test: there is
   no distribution or hypothesis test. Some bands were widened from observed run-to-run variance.
2. **Drift classification (human/agent judgment).** `/simq-audit` classifies each flagged drift
   as `EXPECTED_DRIFT` / `REGRESSION` / `DA_NEEDED` / `NO_ACTION` and may update anchors
   (`docs/simulation_quality/audit_workflow.md`). This result is a *classification*, not pass/fail.

- **PR lane:** `tests/simulation_quality -m "not slow"` runs, but **the anchor-comparison tests
  `pytest.skip()` silently** because they read `data/calibration/`, which is gitignored and never
  populated in CI [O]. **Historical drift figures [H], not re-measured.** Source:
  `tickets/done/TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS.md` (ticket dated 2026-09-03).
  These are two different measurements, with different denominators:

  | Measurement | Date | Population | Executed | Pass | Fail | Not run | Source lines |
  |---|---|---|---|---|---|---|---|
  | A: tool-level sweep (`tools/evaluate_simq.py` per run key) | ≈2026-09-01 (the ticket calls it "2-day-old" at re-check) | 81 run keys | 79 | 18 (matched) | 61 (drifted) | 2 (`RUN_FAILED`: probe keys not resolvable via `--name`) | ticket ~l.66-68 |
  | B: pytest re-check, **parametrized anchor tests only** | 2026-09-03 | 79 parametrized comparisons (61 fast + 18 slow) | 79 | 17 (fast) | 62 (44 fast + 18 slow) | 0 | ticket Test Summary ~l.199-208 |
  | B: pytest re-check, **2 named probe tests** | 2026-09-03 | 2 | 2 | 0 | 2 (as reported) | — | same |

  **Unresolved conflict:** the same ticket reports both named probe tests as *failed*, yet also says
  the 2 probe keys "remain `RUN_FAILED` / out of scope". Those tests `pytest.skip()` when no
  calibration report exists (`test_grade_regression.py:450-461`), so they must have compared
  against reports of **unknown provenance**. The ticket's combined "64/81 fail, 17/81 pass" is
  therefore **not used here**; only the parametrized figure (62/79 fail) is unambiguous. At the
  file level the same run reported "64 failed, 25 passed" across all tests in
  `test_grade_regression.py`, which includes non-anchor tests. The CI comment quotes
  measurement A's 61/81. No current measurement exists; the per-key split between staleness and
  non-determinism was not triaged.
- **Drift lane:** `simq-grade-drift` runs `make simq-full-audit-full` on `main`, nightly, and on
  manual dispatch. It is `continue-on-error` (informational) by design, so the historical drift
  backlog does not block. **Its job conclusion reads `success` even when drift is found** (e.g. run
  `36401320085`, 2026-09-28), so the job status is not a drift signal; its log is [O].
- **Known blind spots:** slow (≥1000t) anchors once showed invariant grades for
  AGENCY/COMBAT/PROGRESSION/WORLD (`TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`, since closed;
  current state not re-measured). Effects too small to show at corpus scale are invisible, which is
  why `mechanic_verification_scenarios_proposal.md` §1 bars citing SimQ for narrow changes. 32 of
  48 test files are narrow-mechanism corpus tests (§6.3).

**Exploratory measurement (no oracle):** `tools/execution_census.py` (reachability; self-declared
UNSTABLE); `make simq-long-run-lifecycle-observation` (5000-tick observation);
`make codebase-health-*`. All three are on demand or report-only.

**Audits:**

| Kind | Examples | Executes the simulation? | Output |
|---|---|---|---|
| Engine audit reviews | `docs/audits/D01–D28` (feature impact, system wiring, test coverage, dead code, …; index `docs/audits/audit_dimensions.md`) | No: human/agent review, *static testing* [R25] | Rated findings, then tickets; one-off, not re-run |
| Agent review | `mechanics-auditor` (Bible ↔ code) | No | PARITY / DIVERGENT / MISSING findings |
| SimQ audit workflow | `/simq-audit` (`.claude/workflows/simq-audit.js`) | Yes, via `make simq-full-audit*` | Drift classification, anchor updates, optional ticket |
| CI registry checks | mechanism-registry validate / completeness (`arch-docs` job) | No (static) | Blocking or report-only gates |

---

## 5 · How tests are written today (authoring process)

Measured from `.claude/workflows/implement-ticket.js` and `.claude/agents/`:

| Step | Current behaviour | Pattern it produces |
|---|---|---|
| Investigate | `investigator` writes `test_plan.md`: *Regression Surface · New Tests Required (one per AC; category unit / integration / architecture guard) · Scoped Pytest Commands · Anti-Drift Guards*. No scenario or property category; no required size or oracle | Top-thin shape; scorer tests on hand-built `AuthoritativeState` |
| Budget | `docs/testing/test_delta_budget.md`: "bug fix = 1 regression test", "3–6 tests per small resolver" | Per-ticket appendage files (`unit/strategic/test_opportunities.py`, `unit/social/test_social_memory.py`) |
| Implement | `implementer` writes both the code and its tests | Tests confirm the implementation as written rather than the Bible law |
| Test | `test-scoper` maps changed files to tests and runs them; `test_scope_coverage_static` checks directory mapping | Correct selection, but **no phase reviews test quality** |
| Skills | `test-driven-development` (from `obra/superpowers`, ships `testing-anti-patterns.md` [R14]), `python-testing-patterns`, `backend-testing` are installed | **No agent or workflow references them** |

### 5.1 Workflow stage map (`.claude/workflows/implement-ticket.js`, 1,951 lines) [O]

Scope (`:30`) → Investigate (`:534`, `investigator`: `investigation.md`, `test_plan.md`) → Plan
(`:658`) → Review (`:726`, `architecture-reviewer`: durable state/API/parity only) → Implement
(`:795`, code **and** tests, `implementer.md:88`) → Document-Update → Architecture-Verify (`:999`) →
Test (`:1158`, `test-scoper` + static backstop) → Parity → Security-Review (conditional, `:1473`) →
Verify (`:1596`, `done-checker`: artifacts present, tests pass, "new behaviour has coverage") →
Finalize.

- **Decided somewhere:** test *level* only (`test_plan.md` category, `:557-559`).
- **Decided nowhere:** impact set, oracle, fixture, expected effect, negative/edge cases,
  non-functional risk.
- **Gate failures return** and a human re-runs the workflow; there is no retry loop.
- `implement-epic.js` and `create-tickets.js` contain no test logic. There is **no standalone
  ticket-investigation workflow**; "investigation" is the `investigator` agent inside
  implement-ticket.
- **Installed test skills are never invoked:** 0 references in workflows, agents or hooks, and 0
  Skill calls across 245,460 logged tool calls in 60 weekly `tools.jsonl` shards.
- **Monitoring data:** `events.jsonl` has per-phase `tool_call_count` but no tokens. **70% of 400
  runs have `duration_s: 0`** (hand-orchestrated backfills), so run duration cannot measure a
  pilot.

Existing policy docs in `docs/testing/`: `test_taxonomy.md` (legacy-parity marker taxonomy),
`test_delta_budget.md`, `no_duplication_test_policy.md`, `regression_policy.md`,
`requirement_traceability.md`, `how_to_add_requirement_tests.md`,
`content_migration_test_ownership.md`, `migration_ci_lanes.md`, `expansion_gate.md`,
`observability_coverage.md` (historical). Prior audit: `docs/audits/D10_test_coverage.md`
(2026-06-18, closed).

---

## 6 · Per-domain verdicts [P]

**Provisional:** each verdict comes from counts plus sampling 5–10 files per area, not from an
exhaustive review or a mutation measurement.

Verdict scale: **Healthy** · **Over-invested** (cost above risk) · **Under-invested** (risk above
coverage) · **Misdirected** (volume in the wrong tier or on the wrong target) · **Dead weight**
(subject is dormant).

### 6.1 Simulation core / world

| Area | test/src LOC | Verdict | Evidence |
|---|---|---|---|
| engine | ~0.5 | Healthy | `integration/kernel/test_determinism_suite.py::test_reproducibility` (10 runs, one hash, fast lane) |
| core | ~0.7 | Healthy | `unit/core/test_authoritative_state_contract.py`; `integration/pipeline/test_mutation_boundary.py` |
| world | ~2.4 | Over-invested (unverified depth) | Ratio outlier; duplication not confirmed |
| worldassembly | ~3.5 | Misdirected | Weight is `test_corpus_diversity.py`, slow-lane only and excluded even from the slow job |
| content | ~1.4 | Healthy | |
| config | ~0 on target | Misdirected | `unit/config/` tests feature flags; `docs/engine/matrices/simulation_kernel_test_matrix.md` cites non-existent `tests/platform/`, `tests/config/` |
| replay | ~0.2 | Under-invested | `fingerprint.py` covered only indirectly |
| entities | ~2.9 | Misplaced | Two parallel dirs; phase-numbered files unrelated to anatomy |
| progression | ~6.8 | Over-invested and leaking | 103 unit tests on 373 LOC; order-dependent failures; escaped defects. **D9 pilot domain** |

### 6.2 Gameplay / behaviour

| Area | Tests (unit/int/scenario) | Verdict | Evidence |
|---|---|---|---|
| combat_engagement | 113 / 7 / 3 | Healthy | `mechanic_scenarios/test_combat_resolution_damage_value_differential.py` asserts real HP deltas |
| resource / harvest | 87 / 4 | Healthy core, thin market | Conservation regressions in `unit/resource/` and `integration/kernel/test_resource_conservation.py` |
| quest / guild | 82 / – | Under-invested (integration) | No guild → quest → reward flow test |
| strategic | 299 / 1 | Over-invested, misdirected | Scorer tests on hand-built state; 1 of 61 files runs the kernel |
| social | 296 / few | Over-invested | Same pattern; ticket-appendage files |
| cross-domain | – / – / 2 | Under-invested | combat → XP and harvest → market have one scenario each |
| motivation, demographics, fidelity | ~0 dedicated | Under-invested | Empty `unit/motivation/`; indirect coverage only |
| mechanic_scenarios tier | 44 tests | Right shape, too small | Exactly the production-like pattern; skipped on PRs that touch only systems/progression/economy/quests (§3) |

### 6.3 Observability / lab / SimQ / API / perf

| Area | Verdict | Evidence |
|---|---|---|
| observability | Healthy | Real per-law `HardLawMonitor` tests (`tests/engine/test_hard_law_monitor.py`) |
| simulation_quality | Misdirected, and silent on PRs | 32/48 files are narrow-mechanism corpus tests, contrary to SimQ's balance-only role; anchor-comparison tests skip silently on PRs (§4.7) |
| api | Mostly healthy | `TestClient` throughout except `tests/api/test_rest_parity.py` (subprocess + `sleep(3)`); no schema snapshot or raw-model guard |
| perf | Framework only | `perf_budget` fixture + tolerance bands exist, but `perf_baselines.json` has **0 entries** and only 2 test files use the fixture (which fails without an entry) |
| certification / arena | Healthy, rarely run | Mostly slow-marked |
| frontend (game view) | Under-invested | 4 vitest files / 22 sources; e2e never run in CI |
| dashboard-frontend | Healthy tests, not in CI | 15 vitest files, no CI job |

### 6.4 Tooling / agent-infra / governance

| Area | test/src LOC | Verdict | Evidence |
|---|---|---|---|
| tools/gate_checks | ~1.7 | Healthy | Every one of 24 modules has direct tests |
| tools/mechanism_registry | ~0.75 | Healthy | |
| tools/delivery | ~1.2 | Healthy | |
| tools/agent-monitoring | ~2.7 | Over-invested | Against the "proportionate agent-tooling checks" rule |
| tools/semantic_control_plane | ~1.5 | Over-invested (unverified use) | Make targets only; no CI or workflow reference |
| `agent_codex_*` + `agent_replay_codex` | ~1.4 | **Dead weight** | Pilot deferred and never activated (`docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`); **decided: delete** |
| doc/prose-content tests in `tests/tools` | – | Misdirected | ~38% of files assert strings in docs or source, e.g. `test_cognition_strategy_skill_content.py` pins formula prose |

---

## 7 · What the models say about this system

Classified with the axes and models in the epic's §2. All readings are **[I]**, built on the
provisional signals above.

- **Pyramid [R7] and test sizes [R1]:** the base is broad. The top (medium/large outcome proofs) is
  thin, and many large real-kernel tests sit in unit directories, so size is not visible from
  layout.
- **Quadrants [R3]:** Q1 (technology-facing unit) is dense. Q2 (business-facing functional, meaning
  mechanic scenarios) is the thinnest, and the titles of escaped defects point there [P]. Q3
  (exploratory: SimQ, census) carries narrow corpus tests that belong in Q2. Q4 is mixed:
  short-run determinism is proven in the fast lane; long-run determinism is parked; perf has a
  framework but **no calibrated baselines** (§6.3).
- **Test Desiderata [R9]:** *structure-insensitive* is the most visibly violated property (doc/source
  text tests, positional pins); *isolated* is violated by the progression leak; *predictive* is
  likely weak where scorer tests run on hand-built state [P].
- **Effectiveness:** line coverage 88% (scope-limited, §4.1); mutation score **unmeasured**; about
  45 title-matched escapes of one class [P]. This is *consistent with* high execution and weak
  oracles [R6], and is to be confirmed or refuted by the first mutation baseline, not assumed.

---

## 8 · Change impact and test selection (as-is)

How a changed file becomes a set of tests today [O]:

| Step | Mechanism | Nature | Gap |
|---|---|---|---|
| Investigate | `investigator` writes prose `test_plan.md` (`.claude/agents/investigator.md:153-191`) | Agent reading of "Related Code Areas" | No map feeds it; completeness unverifiable |
| Test phase | `test-scoper` "Test Directory Map" (`.claude/agents/test-scoper.md:11-59`): `src/<x>/` → `tests/unit/<x>/`; for `src/{core,systems,engine,ai}` and flat `tools/*.py` a **manual importer grep** (`:69-104`) | Agent judgment, re-derived per ticket, not persisted | Indirect consumers found only if the grep finds them |
| Static backstop | `tools/gate_checks/test_scope_coverage_static.py:60-172`: same allowlist; `ai` and `systems` **deliberately excluded** (`:80-103`) | Code | An unmapped file yields **SKIP with no output**; FAIL only for known omissions |
| Epic | `implement-epic.js:323` calls `implement-ticket` per child | — | No cross-ticket selection |
| CI | 12 of 15 jobs always run; `frontend`, `perf-cert-arena` (+ `tests/mechanic_scenarios`), `migration-lanes` are path-filtered (`test.yml:620-655`) | Regex over the PR diff | `PERF_RE` omits `src/{systems,progression,entities,economy,quests,town,actions,strategy}/` and `tests/mechanic_scenarios/`; `data/` and `config/` appear in no filter |
| Fallback | "flag as untested" (`test-scoper.md:112`) | Prose instruction | Nothing checks it was emitted |

**Machine-readable sources and identifiers** [O]:

| Source | Stable id | Links today | Missing link |
|---|---|---|---|
| `registries/mechanisms.yaml` | mechanism `id` (93) | → `implemented_by` code (77/93, all paths resolve) | No structured test link (prose in `verified.note` only) |
| `docs/parity_ledger/*.yaml` | law `id` (2,190) | → `v2_evidence`, `test_path` (596 set; 98 point at missing files) | No join to mechanism id or domain |
| `docs/REGISTRY.yaml` | ticket id | → free-text `related_code_areas` | Historical, not a live map |
| `docs/testing/requirement_traceability.md` | 12–14 prose groups | → test files | Hand-maintained, `last_verified: 2026-06-13` |
| pytest markers | 27 | → speed / proof type | No domain, level, or size axis |
| CI path regex | — | → 3 jobs | Coarse boolean |
| graphify import graph | — | code ↔ code | Local-only (`graphify-out/` untracked); unavailable to workflows and CI |

No identifier joins mechanism ↔ law ↔ domain ↔ test level ↔ CI lane; each source is a separate
two-hop chain [O]. Guidance (tests recommended) and proof (an outcome assertion exists) are not
distinguished anywhere [I].

---

## 9 · Reusable test infrastructure (as-is)

| Concern | Existing, stable | Notes / gap [O unless marked] |
|---|---|---|
| Entities / state | `V2EntityBuilder` (`src/core/builder.py`), `tests/helpers/{entities,presets,resources,domain,assertions}.py` | Used by unit, component and scenario tests |
| Worlds | `WorldRepository.load_world_with_context`, `WorldCompiler.compile(spec, seed, context)` | **No shared "compile + stage + run + observe" helper**; each scenario open-codes `_compile_world` / `_stage_*` |
| Seeds / clock | `DeterministicRNG` (`src/platform/rng.py`; contract `tests/unit/core/test_rng_contract.py`) | Stable |
| Kernel | `Kernel` with `RuntimeProfile` (`src/config/profiles.py`: `PROD_SMALL/DEFAULT/LARGE/STRESS`) | Stable |
| Observation | `CanonicalStateHasher`, `StateFingerprinter`, `HardLawMonitor`, events | No shared replay-diff helper |
| Isolation | Registry-reset plumbing in `tests/conftest.py` | Load-bearing; still leaks (§4.2) |
| Golden / snapshot | `tests/integration/lab_agent/test_golden_run_fixture.py` (`e2e_golden`) | Lab registration only, not gameplay |
| Product E2E | `run_src_module()` / `module_cmd()` in `tests/helpers/runtime.py` | **Defined, never called**; no E2E level exists |
| Scenario runner | `src/testing/` (`ScenarioRunner`, `route_family_classifier`) | Imported only by its own tests and one architecture test; currency unclear [I] |
| Cleanup | `rm -rf data/runs/*` at ticket close (CLAUDE.md) | No per-test fixture |

---

## 10 · Test-classification inventory for core RPG (as-is) [O]

Planner script over all 1,484 `tests/**/test_*.py` files (AST imports plus path prefixes),
2026-09-28:

| Population | Files | Rule |
|---|---|---|
| Import any core-RPG or substrate module | 724 | imports matching `src.core`, `src.engine.{pipeline,kernel,movement,combat,…}`, `src.{progression,entities,economy,quests}`, `src.domains.{progression,combat_engagement}`, `src.systems.{harvest,craft,market,economy,resource,quest,guild,party}` |
| …of which import **only** substrate (`src.core` etc.) | 579 | `src.core` is a shared model library imported almost everywhere, so an import of it does not mean the test is *about* the substrate |
| Core-RPG gameplay by **directory** | 148 | `tests/unit/{combat,movement,progression,resource,economy,quest,entity,entities,tactical}/`, `tests/unit/domains/{combat_engagement,progression}/`, `tests/mechanic_scenarios/`, matching `tests/integration/*` sub-directories |
| Core-RPG gameplay by **import** | 145 | imports a gameplay module (substrate excluded) |
| Agree (both) | 89 | — |
| Directory-only / import-only | 59 / 56 | Disagreements. The import-only files sit in `unit/{domains,engine,strategic,core,world,social}`, `integration/{scenarios,pipeline}` |
| Union (candidate set) | 204 | — |
| Import ≥ 2 gameplay domains | 7 | Genuine multi-domain candidates |

**Reading [I]:** neither directory nor imports classifies reliably. About 115 of the 204 candidates
would be *classification uncertain* without an author declaration, and an import of `src.core` says
nothing about a test's subject. No test declares domain, level or size today (§2.3).
