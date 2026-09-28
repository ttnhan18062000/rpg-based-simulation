---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Current Test System — Status and Overview

**Snapshot of `origin/main` at `04f911110`, measured 2026-09-27/28.** This is the single home for
the *as-is* state of the test system: layout, lanes, authoring process, measured numbers, and
per-domain verdicts. The *to-be* direction and decisions live in
[`test_architecture_epic.md`](test_architecture_epic.md); reference IDs `[R#]` point to that
doc's §9 References.

**Corrections applied 2026-09-28** (from the reviewer evidence memo): the perf verdict (§6.3); the
mechanic-scenario path filter also misses `tests/mechanic_scenarios/` itself (§3); SimQ and audits
added (§4.7).

How this was measured: file and LOC counts by script over `tests/`, `src/`, `tools/`; one
`coverage run --source=src` over the fast tiers; four read-only domain assessments that sampled
5–10 test files per area (not every test); and a direct read of `.github/workflows/test.yml`,
`pyproject.toml`, `.claude/agents/`, and `.claude/workflows/implement-ticket.js`. Re-measure
before citing any number after this date.

---

## 1 · Status at a glance

| Area | Status | One-line reason |
|---|---|---|
| Execution breadth | 🟢 Good | 88% line coverage of `src/` from the fast tiers alone |
| Assertion strength | 🔴 Unknown / weak | Never measured (no mutation testing); the escaped-defect record suggests weak |
| Liveness in real runs | 🔴 Gap | ~30 closed + ~15 open *never fires / never seeded / always empty* defects shipped green |
| Shape | 🟠 Top-thin | 44 mechanic-scenario tests against ~5.7k unit tests |
| Determinism proof | 🟠 Partial | Fast-lane `test_reproducibility` exists; nightly slow lane red (parked by decision) |
| Isolation | 🟠 Leaking | 7 progression tests are order-dependent; hidden by CI's per-directory split |
| Traceability | 🔴 Broken | 93% of parity-ledger P0 entries have no `test_path` |
| Proportionality | 🟠 Skewed | Agent-infra tests are ~25% of all test LOC; dead Codex-pilot suites still in CI |
| Measurement tooling | 🔴 Missing | `make test-cov` points at non-existent `tests_v2/`/`src_v2/`; no scorecard |
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
16m54s. **Total: 88%.**

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

**Reading:** coverage is not the bottleneck. High coverage alongside escaped *never fires*
defects is the pseudo-tested pattern: code runs under tests that would still pass if its effect
were removed [R6]. Only mutation testing measures that [R5].

### 4.2 Failures on `main` in a combined run

- 7 in `tests/unit/domains/progression/` (`test_material_possession_predicate.py`,
  `test_phase6_growth_gap_evaluator.py`, `test_phase6_possession_understanding_service.py`). All
  18 tests in those files **pass when run alone**, so this is order-dependent shared state [R15].
- `tests/unit/tools/test_mechanism_state_caller_check.py::test_real_registry_findings_pinned`:
  pins live repository data, so it fails as the repo changes.

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

### 4.5 Escaped-defect record (defect-escape analysis)

Ticket titles in `tickets/done/` and `tickets/todos/` matching *never fires / never applied /
never seeded / always empty / never wired / starvation*: about **30 closed** (for example
`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`,
`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`,
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`) and about **15 open** (for example
`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`,
`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`). These were found by SimQ runs, the
execution census, and manual audits, not by the test suite.

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
rule "P0 entries require a passing `test_path`" is not enforced.

### 4.7 Corpus evaluation (SimQ), exploratory measurement, and audits

These instruments sit **outside** the pytest level stack. They differ in what the result is
compared against (the *oracle* [R24]), not only in scope.

**World corpus (test input, not a level).** `data/worlds/` holds 23 worlds.
`config/simulation_quality/corpus_registry.yaml` lists 81 anchor runs (world × seed × ticks: 51 at
200t, 12 at 500t, 12 at 1000t, 6 at 2000t) and tiers the worlds as unit 5 · end-to-end 8 ·
stress 6 · regression-baseline 2. The tiering follows
`docs/simulation_quality/corpus_tier_taxonomy.md`, which applies the test pyramid to *worlds*.
The corpus is shared input for SimQ, the execution census, and some mechanic scenarios.

**SimQ (`src/simulation_quality/`)** scores runs on 10 pillars (COGNITION, AGENCY, COMBAT,
FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE;
`docs/simulation_quality/quality_scoring_contract.md` §5). It compares grades against committed
anchors in `tests/simulation_quality/fixtures/grade_anchors.json` (61 fast ≤500t keys and 18 slow
keys in `tests/simulation_quality/test_grade_regression.py`). The oracle is **statistical**:
grade bands and drift. The result is not pass/fail. `/simq-audit` classifies each drift as
`EXPECTED_DRIFT` / `REGRESSION` / `DA_NEEDED` / `NO_ACTION` (`docs/simulation_quality/audit_workflow.md`).

- **PR lane:** `tests/simulation_quality -m "not slow"` runs, but **the anchor-comparison tests
  `pytest.skip()` silently** because they read `data/calibration/`, which is gitignored and never
  populated in CI. 61 of 81 anchors drifted from `main` with no signal (`.github/workflows/test.yml`
  comment at the *SimQ grade-anchor drift* job; `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`).
- **Drift lane:** `simq-grade-drift` runs `make simq-full-audit-full` on `main`, nightly, and on
  manual dispatch. It is `continue-on-error` (informational) by design, so the historical drift
  backlog does not block.
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

Existing policy docs in `docs/testing/`: `test_taxonomy.md` (legacy-parity marker taxonomy),
`test_delta_budget.md`, `no_duplication_test_policy.md`, `regression_policy.md`,
`requirement_traceability.md`, `how_to_add_requirement_tests.md`,
`content_migration_test_ownership.md`, `migration_ci_lanes.md`, `expansion_gate.md`,
`observability_coverage.md` (historical). Prior audit: `docs/audits/D10_test_coverage.md`
(2026-06-18, closed).

---

## 6 · Per-domain verdicts

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

Classified with the reference models in the epic's §3:

- **Pyramid [R7] and test sizes [R1]:** the base is broad and healthy. The top (medium/large
  outcome proofs) is thin, and many large real-kernel tests sit in unit directories, so size is
  not visible from layout.
- **Quadrants [R3]:** Q1 (technology-facing unit) is saturated. Q2 (business-facing functional,
  meaning mechanic scenarios) is the thinnest and is where the escaped defects live. Q3
  (exploratory: SimQ, census) is doing Q2's job, which is why SimQ carries narrow corpus tests.
  Q4 (perf, determinism) is healthy in the fast lane and parked in the slow lane.
- **Test Desiderata [R9]:** *structure-insensitive* is the most violated property (doc/source
  text tests, positional pins); *isolated* is violated by the progression leak; *predictive* is
  weak where scorer tests run on hand-built state.
- **Effectiveness:** coverage 88% (measured); mutation score unmeasured; defect escapes about 45
  of one class. This is the signature of high coverage with weak oracles [R6].
