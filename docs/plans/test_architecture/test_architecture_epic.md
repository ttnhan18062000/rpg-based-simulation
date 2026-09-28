---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture: Measurement Model and Direction

**Status, drafted 2026-09-28. ALL DIRECTIONS DECIDED (D1–D9). No tickets exist yet.** Each `D#` section below
is a direction that needs a decision. Tickets are cut only after the directions are agreed, one
child ticket per accepted direction (or per phase of one), under a future
`tickets/todos/test-architecture/` epic folder.

Evidence was measured at `origin/main` `04f911110`. Read-only scan and one coverage run; nothing
was changed.

---

## 1 · Problem

The repository has no high-level measurement of its own test suite. Size is known only
anecdotally, and nobody can currently answer these questions from data: is the suite the right
*shape*? Do the tests *prove* what the Mechanics Bible claims? Which domains are over-invested,
and which are thin?

The evidence below shows the bottleneck is **not how much code the tests run**. It is **what the
tests assert**, and at which level they assert it.

## 2 · Evidence snapshot (2026-09-27, `04f911110`)

| Signal | Value | Reading |
|---|---|---|
| Size | 1,484 test files · 11.1k tests · 252k test LOC vs 135k `src/` + 47k `tools/` LOC | Test code is about 1.4× the code it covers |
| Shape | ~5.7k unit · ~0.8k integration · **44** `tests/mechanic_scenarios` | Inverted at the top: the tier that catches wiring defects is the thinnest |
| Line coverage, fast tiers (`coverage run` over unit+integration+mechanic_scenarios+api+engine+simulation_quality, `not slow`) | **88%** of `src/` (domains 96%, engine 91%, core 92%) | Code is *executed*; execution is not the gap |
| Escaped-defect class | ~30 closed + ~15 open tickets titled *never fires / never seeded / always empty / never wired* | Every one of these shipped with green tests and high coverage |
| Parity-ledger traceability | **1,564 / 1,685 P0 entries (93%) have no `test_path`**; 28 cite missing files | The CLAUDE.md "P0 requires a passing test_path" rule is not enforced; P0 is 77% of all entries, so it no longer discriminates |
| Property-based tests | 0 (Hypothesis is installed and unused) | Laws are proven on hand-picked seeds only |
| Isolation | 7 `tests/unit/domains/progression/` tests fail in a combined run and pass alone | Order-dependent global state, hidden by CI's per-directory job split |
| Lane fit | 80s and 60s tests in `tests/unit/tools/test_mechanism_state_caller_check.py` | Large tests sitting in the small-test lane |
| Coverage tooling | `make test-cov` targets `tests_v2/` and `src_v2/`, which don't exist | Coverage has never been routinely measured |
| Agent-infra share | `tests/tools` + `tests/unit/tools` + `tests/agent_*` ≈ 63k LOC (~25% of all test LOC) | Larger than the gameplay tests; see D6 |
| Text-matching tests | 243 test files read `.md` docs; 152 match `src/`/`tools/` paths as text; ~38% of `tests/tools` | Structure-sensitive and brittle (Beck's Test Desiderata) |

Per-domain verdicts from the four domain assessments:

| Domain | Verdict | Key evidence |
|---|---|---|
| engine / core | Healthy | `tests/integration/kernel/test_determinism_suite.py`, `tests/integration/pipeline/test_mutation_boundary.py` prove real contracts |
| worldassembly | Misdirected | 3.5× test/src ratio, but the weight is `test_corpus_diversity.py`, which is slow-lane only (`regression_policy.md` §12) |
| config / replay | Under-invested | `tests/unit/config/` tests `feature_flags.py`, not `src/config/`; replay fingerprint is covered only indirectly |
| combat_engagement / resource | Healthy | Real `WorldCompiler`+`Kernel` outcome proofs; conservation regressions exist |
| strategic / social | Over-invested, misdirected | ~595 decision-scoring tests on hand-built state; 1 of 61 strategic files runs the kernel; ticket-appendage files (`test_opportunities.py`) |
| quest / progression cross-domain | Under-invested | combat→XP and harvest→market each have one scenario; guild→quest→reward has none |
| observability | Healthy | Largest package, tracked by `docs/testing/observability_coverage.md` |
| simulation_quality | Misdirected | 32 of 48 files are single-mechanism `*_corpus.py` proofs, which contradicts SimQ's balance-only role |
| api | Mostly healthy | `TestClient` throughout, except `tests/api/test_rest_parity.py` (subprocess + `sleep(3)`); no schema snapshot or raw-model guard |
| frontend (game view) | Under-invested | 4 test files / 22 source files; `dashboard-frontend` has 15 of 19 |
| tools: gate_checks, delivery, mechanism_registry | Healthy | 0.75–1.7× ratio on load-bearing gates |
| tools: agent-monitoring | Over-invested | ~2.7× ratio, against the "proportionate agent-tooling checks" rule |
| tools/tests: agent_codex_* | Dead weight | ~4.2k test LOC + 3k tool LOC for a pilot its status doc marks deferred and never activated (`docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`) |

## 3 · Reference models

The direction uses established, cited models, not a bespoke rubric. **Rule for this epic: every
direction and every child ticket cites at least one external reference from §9. Nothing is
invented without one.**

- **Test pyramid [R7][R8], with Google test sizes (small / medium / large) [R1][R2]** for *shape*: size is decided
  by resources used (process, I/O, real kernel ticks), not by directory name.
- **Marick's agile testing quadrants, as extended by Crispin and Gregory [R3],** for *purpose*: Q1 technology-facing unit tests · Q2
  business-facing functional tests (mechanic scenarios) · Q3 exploratory / emergent (SimQ, census)
  · Q4 non-functional (perf, determinism).
- **Kent Beck's Test Desiderata [R9]** and **Meszaros' test smells [R13]** for *per-test quality*: behavioural, structure-insensitive,
  deterministic, isolated, fast, specific.
- **Effectiveness metrics:** line/branch coverage (does code run?), **mutation score** [R5][R12] (do
  assertions catch a changed operator or constant?; high coverage with a low mutation score is the
  pseudo-tested-method pattern [R6]), and **defect-escape analysis** (which defect
  classes reached `main` past a green suite).
- **Simulation-specific oracles:** property-based tests (Hypothesis [R10]) for laws, metamorphic tests [R11]
  for the kernel (relations between runs, not absolute values), and golden-master tests for
  regression snapshots.

## 4 · Boundary with existing initiatives (read first)

Several initiatives already own the "does the mechanism actually happen" axis. This epic **must
not** rebuild them; it consumes their outputs as scorecard inputs.

| Existing initiative | Owns | This epic's relation |
|---|---|---|
| `docs/plans/mechanic_verification_scenarios_proposal.md` | Q2 per-mechanic staged scenarios (`tests/mechanic_scenarios/`) | Sets the target *share* of the scenario tier and measures it; does not design scenarios |
| `docs/plans/simulation_execution_census_initiative.md` (`tools/execution_census.py`) | Reachability in real runs | Consumes the census as the liveness signal; provisional until determinism holds |
| `docs/plans/mechanism_registry_initiative.md` + `mechanism_claims_as_tests_initiative.md` (epic `TCK-20260915-EPIC-MECHANISM-REGISTRY`) | Per-mechanism verification state | Consumes the verification axis; does not duplicate it |
| SimQ (`src/simulation_quality/`) | Q3 balance and emergent health | Only relocates misfiled narrow tests out of it (D6) |
| Slow-regression determinism (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`) | Kernel determinism root cause | **Parked by user decision.** Out of scope; noted as a precondition for D3's metamorphic half |

What this epic uniquely owns: the **suite-wide measurement model**, **assertion strength**
(property and mutation), **isolation and lane hygiene**, **proportionality and pruning**, and the
**parity-ledger traceability rule**.

---

## 5 · Directions to decide (D1–D9)

Each direction lists options and a recommendation. **Decision:** is left blank for review.

### D1 · Test-architecture scorecard (the core deliverable)

A generated, per-domain report with seven dimensions: **Shape** (small/medium/large counts),
**Execution** (line and branch coverage), **Assertion strength** (mutation score, where D4 has
baselined it), **Liveness** (read from the census and the mechanism registry, never recomputed),
**Traceability** (P0 entries with a passing `test_path`), **Hygiene** (order-dependence, lane
fit, skip/xfail count), and **Proportionality** (test LOC / src LOC, plus agent-infra share).

- **A. Report-only**, generated on demand plus weekly, like the codebase-health scorecard. It
  never fails CI.
- B. Report plus ratchets on 2–3 hygiene items only (no new order-dependent tests, no >10s test in
  a unit lane).
- C. Full gate with per-domain thresholds.

**Recommendation: A first, then B for hygiene only once D5 lands.** C conflicts with the
proportionate-checks rule, and coverage thresholds reward exactly the execution-without-assertion
pattern that caused the escaped defects. It also fixes `make test-cov` so the coverage input
exists at all. Output location TBD: extend `make codebase-health-scorecard` rather than add a
parallel report ("define once").

**Decision (2026-09-28): A, report-only.** Hosted inside `make codebase-health-scorecard` (not a separate target). Hygiene ratchets are reconsidered only after D5 lands. Basis: Google advises against a mandated coverage threshold as a quality gate [R4]; coverage without assertions is the pseudo-tested-method pattern [R6].

### D2 · Target shape of the pyramid

- **A. Set a target shape per domain as a scorecard band**, e.g. gameplay domains must have at
  least one medium/large outcome proof per registered mechanism. The scenarios themselves stay
  owned by the mechanic-verification plan.
- B. A global numeric ratio (e.g. 70/20/10).

**Recommendation: A.** A global ratio fits badly across domains: observability is legitimately
unit-heavy, while strategic and social need outcome proofs, not more scorers. Pairs with a soft
rule for strategic/social: new behaviour gets a scenario, not another scorer unit test.

**Decision (2026-09-28): A, per-domain bands.** Size is classified by Google test sizes [R1][R2] and purpose by the agile testing quadrants [R3]; the pyramid is the shape reference [R7][R8].

### D3 · Property-based and metamorphic tests for Mechanics Bible laws

Hypothesis tests on pure laws: damage-formula bounds and monotonicity (ch02), atomic conservation
through the apply pipeline (ch03), XP curve monotonicity (ch01), and authoritative state
immutability (`docs/core/state.md`). Metamorphic tests on the kernel, e.g. entity-ID permutation
invariance, and same seed twice gives the same hash over generated small worlds.

- **A. Property tests on pure laws now; metamorphic kernel tests after the determinism root cause
  is unparked.**
- B. Both now, with metamorphic tests marked `xfail` until determinism holds.
- C. Skip; rely on scenarios.

**Recommendation: A.** Pure-law properties are cheap, deterministic and fast (small tests).
Kernel metamorphic tests would fail for the parked reason and add noise.

**Decision (2026-09-28): A, pure laws now; kernel metamorphic tests after determinism is unparked.** Tools: Hypothesis [R10]; metamorphic relations per Chen et al. [R11].

### D4 · Mutation-score baseline

`mutmut` (or `cosmic-ray`) over a narrow, high-value target set: the combat damage path, the
economy conservation path, and the apply pipeline.

- **A. One-off baseline on 3 targets, recorded in the scorecard, re-run manually.**
- B. Nightly scheduled mutation run.
- C. Skip.

**Recommendation: A.** This is the only direct measure of assertion strength. Full-repo mutation
is too expensive and not needed to answer "are our core law tests real?"

**Decision (2026-09-28): A, one-off baseline on 3 targets (plus progression for the D9 pilot), using `mutmut` [R12].** Diff-scoped, suppression-aware practice follows Google's mutation-testing deployment [R5].

### D5 · Isolation and lane hygiene

1. Fix the order-dependent leak behind the 7 progression failures (likely registry or global
   state that the other directories' fixtures set).
2. Add one random-order run (`pytest-randomly` [R16]) as a scheduled job to surface the rest.
   Order dependence is one of the top root causes of flaky tests [R15]. Caveat: `pytest-randomly`
   also reseeds `random` per test, so check that interaction with the engine's own RNG contract
   (`tests/unit/core/test_rng_contract.py`) before enabling it.
3. Move large tests out of unit lanes, starting with the two in `test_mechanism_state_caller_check.py`.
4. Replace `test_real_registry_findings_pinned` (pins live repo data) with a fixture-backed
   assertion.

- **A. All four.** B. Items 1, 3 and 4 only (no random-order job).

**Recommendation: A.** Item 2 is the only way to find the rest of the leaks, because CI's
directory split hides them.

**Decision (2026-09-28): A, all four items.** Random-order runs via `pytest-randomly` [R16] after the RNG-contract interaction check; slow tests leave unit lanes per Google test sizes [R1].

### D6 · Prune and relocate

| Item | Options | Recommendation |
|---|---|---|
| `agent_codex_*` (7 test dirs + 7 tool dirs) | delete · park (excluded from CI, kept in repo) · keep | **Delete** (decided 2026-09-28); git history keeps it recoverable |
| SimQ `*_corpus.py` (32 files) | relocate to the owning domain / `mechanic_scenarios` · leave | Relocate; keeps SimQ balance-only |
| Doc-text and source-grep tests (~243/152 files) | policy + convert-or-delete sweep · policy only | Structure-coupled tests violate *structure-insensitive* [R9] and are Meszaros' *Fragile Test* smell [R13]. **Policy only first:** a doc-text assertion is allowed only when the doc is itself a machine contract. Sweep opportunistically |
| Index-pinned hook tests (`PreToolUse[4]`) | convert to name/matcher lookup | Convert; cheap |
| agent-monitoring tests (~2.7×) | trim toward ~1.5× · leave | Trim duplicated doc/prose assertions only |
| Structural clutter: `tests/unit/entity`+`entities`, orphan `tests/observability/`, empty `tests/integration/perf/` and `tests/unit/motivation/`, mis-targeted `tests/unit/config/`, ticket-appendage files | fix · leave | Fix in one mechanical chore ticket |
| `pyproject.toml` markers (27 declared, most unused, legacy-parity ones reference `src_legacy`) | prune + update `docs/testing/test_taxonomy.md` · leave | Prune; replace the taxonomy with D2's size/quadrant model |

**Decision (2026-09-28): `agent_codex_*` → delete** (tools and tests; git history keeps them recoverable). Other D6 rows follow their recommendations as written, unless revisited when tickets are cut.

### D7 · Parity-ledger traceability honesty

93% of P0 entries have no test, so P0 has stopped meaning "must be proven".

- **A. Re-tier.** P0 is reserved for entries with a passing `test_path`, or entries with a
  test-backlog ticket. Everything else drops to P1 with `proof_type: audit`. Enforced by the
  existing parity-ledger writer and schema.
- B. Mass-link: backfill `test_path` for all ~1,560 entries.
- C. Leave as is and document the gap.

**Recommendation: A.** Standard practice is a requirement→test traceability link per verified requirement (ISO/IEC/IEEE 29148 traceability, 29119 test coverage items) [R18]; an unlinked "verified" entry is not traceable. B is weeks of mostly clerical linking with low defect-finding yield.
Also flagged, but out of this epic's scope: the parity ledger and the mechanism registry now both
record "is this proven". That duplication should be resolved by the mechanism-registry epic, not
here.

**Decision (2026-09-28): A, re-tier.** P0 requires a passing `test_path` or a test-backlog ticket; the rest become P1 with `proof_type: audit` [R18].

### D8 · API contract and frontend (candidate for deferral)

A schema snapshot of the OpenAPI output plus schema-driven contract tests with Schemathesis, which runs in-process against FastAPI on top of Hypothesis [R19], a generic "no route serializes a domain class" test,
converting `test_rest_parity.py` to `TestClient`, and game-view frontend tests.

- **A. Defer the frontend part until after RPG-core work (HUD sequencing rule); take the two API
  items now.** B. All now. C. Defer all.

**Recommendation: A.**

**Decision (2026-09-28): A, API items now** (OpenAPI snapshot + Schemathesis [R19], raw-domain-model guard, `test_rest_parity.py` → `TestClient`); game-view frontend tests deferred until after RPG-core work.

### D9 · Test-authoring process (how tests get written), piloted on one narrow domain

D1–D8 treat the suite's symptoms. D9 targets the process that produces them. How tests are
authored today (measured from `.claude/workflows/implement-ticket.js` and `.claude/agents/`):

| Current behaviour | Pattern it produces |
|---|---|
| `investigator` writes `test_plan.md` with categories *unit / integration / architecture guard* only; no scenario, property or outcome category, and no required test size or oracle | Inverted pyramid top; scorer tests built on hand-made `AuthoritativeState` |
| "One new test per acceptance criterion"; `docs/testing/test_delta_budget.md` "bug fix = 1 regression test" | Per-ticket appendage files (`tests/unit/strategic/test_opportunities.py`, `tests/unit/social/test_social_memory.py`) |
| `implementer` writes both the code and its tests | Tests confirm the implementation as written rather than the Bible law, so *never fires* defects ship with green unit tests |
| `test-scoper` selects and runs tests; `test_scope_coverage_static` checks directory mapping | **No phase ever reviews test quality** |
| Skills `test-driven-development`, `python-testing-patterns`, `backend-testing` exist | No agent or workflow references them |

**Pilot first, change the pipeline second.** Steps, all in one pilot domain:

1. **Review current behaviour (read-only):** classify each test by size (small/medium/large),
   oracle (hand-picked value / Bible law / real run), and against Beck's Test Desiderata.
2. **Measure assertion strength:** a mutation run on the domain (shares D4's tooling).
3. **Defect-escape trace:** for each escaped defect in the domain, record which test should have
   caught it and which pipeline step failed to ask for that test.
4. **Derive authoring rules**, then change the pipeline in the cheapest order:
   - **A.** Extend the `test_plan.md` template with a required size, oracle, and a
     scenario/property category, and reference the existing test skills. Smallest change.
   - **B.** Add an **advisory** test-review step after Implement (an existing reviewer agent or
     a popular community skill, not a bespoke one).
   - **C.** A separate agent writes the tests before the implementer writes the code (TDD with
     split roles). Only if mutation scores stay weak after A and B. Industry reference for
     mutation-guided, agent-written tests: Meta's ACH [R17].
5. **Measure the effect** on the next few tickets in the domain with the D1 scorecard and
   agent-monitoring.

**Pilot-domain options:**

| Option | Size | Why | Risk |
|---|---|---|---|
| **Progression** (`src/progression` + `src/domains/progression`) | 373 src LOC · 103 unit tests plus domain tests | Low in the bottom-up order (ch01 entity anatomy / XP). Shows every symptom: order-dependent failures on `main`, escaped defects (`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`, `allocate_ap` unreachable), and the open starvation-chain epic `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` | Must not touch the starvation-chain epic's files. The pilot is review-only until step 4 |
| Strategic (`src/strategy` + `src/ai/goals`, `tests/unit/strategic`) | 299 unit tests across 61 files; 1 runs the kernel | Clearest *over-engineering* case (decision-scoring on hand-built state, ticket appendage) | Higher in the bottom-up order (cognition layer); findings are mostly about pruning, less about escaped defects |

**Recommendation: progression**, because it exercises both halves (gaps and escapes, plus
hygiene) on a small surface. Strategic is the natural second pilot, to validate the rules on the
over-engineering side.

**Decision (pilot domain):** Progression (user decision, 2026-09-28). Strategic stays the candidate second pilot.

**Decision (D9 overall, 2026-09-28):** Pilot, then A → B → C. Step B uses an existing popular skill run as an advisory step, not a bespoke agent: the repo already installs `obra/superpowers`' `test-driven-development` skill (`skills-lock.json`), which ships `testing-anti-patterns.md` [R14]. That reference plus Beck's Test Desiderata [R9] and the Meszaros test-smell catalog [R13] form the review rubric.

---

## 6 · Proposed sequencing (after decisions)

1. **Measure:** D1 (scorecard + `make test-cov` fix) and D5.1 (isolation leak). Everything
   after this is judged against the baseline. D9 pilot steps 1–3 (review-only) run alongside;
   they feed D2's shape bands and D9 step 4's pipeline changes.
2. **Strengthen:** D3 (property tests) and D4 (mutation baseline), which touch different files
   from step 3 and can run in parallel with it.
3. **Prune:** D6 and D5.2–5.4.
4. **Traceability:** D7. **API:** D8's API half.

## 7 · Out of scope

- Designing or building mechanic scenarios, census changes, or mechanism-registry verification
  (owned by the initiatives in §4).
- The kernel determinism root cause (parked).
- Test-case-by-test-case review; this epic works at domain level.

## 8 · Open questions for review

1. ~~`agent_codex_*`~~ Resolved 2026-09-28: delete.
2. ~~Scorecard location~~ Resolved 2026-09-28: extend `codebase-health-scorecard`.
3. ~~D7 re-tier~~ Resolved 2026-09-28: accepted.
4. ~~Mutation tool~~ Resolved 2026-09-28: `mutmut`.
5. ~~D9 pilot domain~~ Resolved 2026-09-28: progression.

## 9 · References

| # | Reference | Used for |
|---|---|---|
| R1 | Google Testing Blog, "Test Sizes" (2010) — https://testing.googleblog.com/2010/12/test-sizes.html | Small/medium/large classification (D1, D2, D9) |
| R2 | Winters, Manshreck, Wright, *Software Engineering at Google*, ch. 11 & 14 — https://abseil.io/resources/swe-book/html/ch14.html | Test size and scope, larger tests |
| R3 | Crispin & Gregory, "The Agile Testing Quadrants" (after Brian Marick) — https://lisacrispin.com/2024/10/11/the-agile-testing-quadrants/ | Test purpose (Q1–Q4) |
| R4 | Google Testing Blog, "Code Coverage Best Practices" (2020) — https://testing.googleblog.com/2020/08/code-coverage-best-practices.html | Coverage is a signal, not a gate (D1) |
| R5 | Petrović & Ivanković, "State of Mutation Testing at Google", ICSE-SEIP 2018 — https://research.google/pubs/pub46584/ | Practical, scoped mutation testing (D4) |
| R6 | Vera-Pérez et al., "A Comprehensive Study of Pseudo-tested Methods", EMSE 2019 — https://arxiv.org/abs/1807.05030 | Covered-but-not-asserted code (§2 main finding) |
| R7 | Vocke, "The Practical Test Pyramid" (martinfowler.com) — https://martinfowler.com/articles/practical-test-pyramid.html | Pyramid shape (D2) |
| R8 | Google Testing Blog, "Just Say No to More End-to-End Tests" (2015) — https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html | Balancing tiers (D2) |
| R9 | Kent Beck, Test Desiderata — https://testdesiderata.com/ | Per-test quality rubric (D6, D9) |
| R10 | MacIver et al., "Hypothesis: A new approach to property-based testing", JOSS 2019 — https://doi.org/10.21105/joss.01891 | Property tests (D3) |
| R11 | Chen et al., "Metamorphic Testing: A Review of Challenges and Opportunities", ACM CSUR 51(1) 2018 | Kernel run-relation tests (D3) |
| R12 | mutmut — https://github.com/boxed/mutmut · https://mutmut.readthedocs.io/ | Mutation tool (D4) |
| R13 | Meszaros, *xUnit Test Patterns* test smells — http://xunitpatterns.com/Test%20Smells.html · https://testsmells.org/ | Smell catalog (D6, D9) |
| R14 | obra/superpowers `test-driven-development` skill + `testing-anti-patterns.md` — https://github.com/obra/superpowers (installed locally, `.claude/skills/test-driven-development/`) | Advisory test-review rubric (D9-B) |
| R15 | Luo, Hariri, Eloussi, Marinov, "An Empirical Analysis of Flaky Tests", FSE 2014 | Order-dependence as a flakiness root cause (D5) |
| R16 | pytest-randomly — https://github.com/pytest-dev/pytest-randomly | Random-order runs (D5) |
| R17 | Foster et al., "Mutation-Guided LLM-based Test Generation at Meta" (ACH), FSE 2025 — https://arxiv.org/abs/2501.12862 | Agent-written tests guided by mutants (D9-C) |
| R18 | Requirements traceability (ISO/IEC/IEEE 29148; test coverage items in ISO/IEC/IEEE 29119) — https://en.wikipedia.org/wiki/Requirements_traceability | Parity-ledger traceability (D7) |
| R19 | Schemathesis, property-based OpenAPI testing — https://github.com/schemathesis/schemathesis · https://testdriven.io/blog/fastapi-hypothesis/ | API contract tests (D8) |
