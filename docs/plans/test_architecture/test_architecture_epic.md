---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture: Measurement Model and Direction

**Status, drafted 2026-09-28. D1–D10 decided (several are being re-opened after the reviewer evidence memo, `tmp/test_architecture_evidence_memo.md`); D11 pending. Core RPG is the first program (§1a). No tickets exist yet.** Each `D#` section below
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

## 1a · Focus: core RPG first (user direction, 2026-09-28)

The epic's first program is **core-RPG testing across many test types** (D10). Everything else
is sequenced behind it or scoped to serve it. Core RPG follows the bottom-up rule
(movement / combat / interaction → party / group → cognition) and Mechanics Bible chapters 01–03:

| Core-RPG domain | Bible | Main code |
|---|---|---|
| Entity anatomy and derived stats | ch01 | `src/entities/`, `src/domains/progression/` (stats) |
| Progression / XP / level-up | ch01 | `src/progression/`, `src/domains/progression/` |
| Movement | ch02 | `src/engine/` (tactical movement), `src/domains/combat_engagement/` (pursuit) |
| Combat resolution | ch02 | `src/domains/combat_engagement/`, `src/engine/` combat path |
| Economy: harvest, craft, trade, inventory | ch03 | `src/systems/` (harvest, crafting, market, economy), `src/economy/` |
| Quests / guild (interaction) | ch03 + buildings/guild doc | `src/systems/quest*`, `guild_system.py`, `src/quests/` |

Cognition, social and strategy (ch04) come **after** this program. Of the other directions:
D3, D4, D5.1 and D9 serve the core-RPG program directly. D1 and D2 are measured for the core-RPG
domains first. D6, D7 (for non-core ledgers) and D8 follow afterwards.

## 2 · Evidence (as-is state)

The measured state of the test system (layout, CI lanes, coverage, failures, smell signals,
escaped defects, parity traceability, authoring process, per-domain verdicts) lives in
[`current_test_system_overview.md`](current_test_system_overview.md). The core finding it
supports: **the suite executes most code (88% line coverage) but asserts weakly on whether core
mechanics actually happen**. That is the pseudo-tested pattern [R6], visible as ~45 escaped
*never fires* defects.

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
- **Oracle as a second classification axis** [R24]: scope/size alone cannot place SimQ, the
  census, or audits. Every instrument is classified by *scope × oracle × result type × cadence*
  (D11). Reviews are *static testing*, distinct from executing tests [R25].
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
| SimQ (`src/simulation_quality/`, `/simq-audit`) | Pillar scoring logic, anchors, drift classification | Classifies SimQ as the *corpus evaluation* instrument (D11), reports its state in the scorecard, and relocates misfiled narrow tests (D6). Does not change scoring or anchors |
| Slow-regression determinism (`TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2`) | Kernel determinism root cause | **Parked by user decision.** Out of scope; noted as a precondition for D3's metamorphic half |

What this epic uniquely owns: the **suite-wide measurement model**, **assertion strength**
(property and mutation), **isolation and lane hygiene**, **proportionality and pruning**, and the
**parity-ledger traceability rule**.

---

## 5 · Directions to decide (D1–D11)

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

D1–D8 treat the suite's symptoms. D9 targets the process that produces them. The current
authoring process (investigator's `test_plan.md` categories, per-AC and per-bug test budget, the
implementer writing its own tests, no test-quality review, unused test skills) is described in
[`current_test_system_overview.md` §5](current_test_system_overview.md#5--how-tests-are-written-today-authoring-process).

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

### D10 · Core-RPG test portfolio (many test types, one matrix)

Each core-RPG domain gets a deliberate portfolio of test types, each chosen for what it proves,
not for volume. The test types and their references:

| # | Test type | Proves | Size [R1] | Reference |
|---|---|---|---|---|
| T1 | Example-based unit | A formula or rule gives the right value for chosen inputs | small | [R7] |
| T2 | Property-based | A law holds for *all* generated inputs (bounds, monotonicity, conservation) | small | Hypothesis [R10] |
| T3 | Stateful property | Any generated *sequence* of actions preserves invariants (inventory, gold, HP) | small/medium | Hypothesis `RuleBasedStateMachine` [R20] |
| T4 | Mechanic scenario | One mechanic fires with the right effect in a minimal real world + kernel | medium/large | repo `tests/mechanic_scenarios/`; Sea of Thieves minimal-map *actor tests* [R22] |
| T5 | Cross-domain outcome scenario | A chain works end to end (combat → XP → level-up; harvest → market → inventory) | large | [R8][R22] |
| T6 | Deterministic simulation sweep | Many seeds × short runs with invariant monitors (`HardLawMonitor`) checked every tick; any failure replays exactly from its seed | large | FoundationDB-style DST [R21] |
| T7 | Metamorphic | Relations between runs hold (same seed → same hash; ID permutation → same outcome) | large | [R11]; **after determinism is unparked** |
| T8 | Golden master / characterization | A small canonical run's combat or economy log is unchanged unless deliberately re-approved | medium | Feathers characterization tests [R23] |
| T9 | Mutation run | The tests above actually catch injected faults | tool | [R5][R12] |
| T10 | Architecture guard | Durable-state writes go only through the authoritative path | small | existing `tests/architecture/` |

**Portfolio matrix: current state → target** (✓ exists · ◐ partial · ✗ none; *current* from the
overview doc and a scan of `tests/mechanic_scenarios/`):

| Domain | T1 | T2 | T3 | T4 | T5 | T6 | T8 | T9 |
|---|---|---|---|---|---|---|---|---|
| Anatomy / derived stats | ✓ | ✗ → ✓ | – | ◐ (1) → ✓ | – | ◐ → ✓ | ✗ → ◐ | ✗ → ✓ |
| Progression / XP | ✓ (leaky) | ✗ → ✓ | ✗ → ✓ | ✓ (3) | ◐ (1) → ✓ | ◐ → ✓ | ✗ → ◐ | ✗ → ✓ (D9 pilot) |
| Movement | ✓ | ✗ → ✓ | – | **✗ (0) → ✓** | ◐ → ✓ | ◐ → ✓ | ✗ → ◐ | ✗ |
| Combat | ✓ | ✗ → ✓ | – | ✓ (4) | ◐ → ✓ | ◐ → ✓ | ✗ → ✓ | ✗ → ✓ |
| Economy / inventory | ✓ | ✗ → ✓ | **✗ → ✓** | **✗ (0) → ✓** | ◐ (1) → ✓ | ◐ → ✓ | ✗ → ✓ | ✗ → ✓ |
| Quests / guild | ✓ | – | ✗ → ◐ | ◐ (1) → ✓ | **✗ → ✓** | ◐ → ✓ | ✗ | ✗ |

T7 applies to all domains once determinism is unparked; T10 already exists and is unchanged.
*T6 current* = the fast-lane `test_reproducibility` (one seed, 10 ticks) plus `HardLawMonitor`
per-law tests; no multi-seed invariant sweep exists.

**Also required so the portfolio actually runs on PRs:** widen the CI path filter (`PERF_RE` in
`.github/workflows/test.yml`) or move `tests/mechanic_scenarios` to a job that always runs.
Today a PR touching only `src/{systems,progression,entities,economy,quests}` skips the mechanic
scenarios entirely (overview §3).

- **A. Build the portfolio domain by domain in bottom-up order** (anatomy/progression → movement
  → combat → economy → quests). Each domain batch adds its T2/T3/T4/T5 and one T8, then a T9 run.
- B. Build by test type across all core domains (all T2 first, then all T4, ...).
- C. Only fill the ✗ cells marked in bold (economy and movement scenarios, economy stateful,
  quest chain).

**Recommendation: A, starting with progression** (it is already the D9 pilot, so review and build
reinforce each other), with **C's bold cells pulled forward** inside their domain batches because
they are the largest gaps. B spreads effort thin and delays any domain reaching a complete
portfolio.

**Decision (2026-09-28): A, domain by domain, bottom-up, starting with progression;** the bold ✗ cells are pulled forward inside their domain batches.

### D11 · Verification instruments beyond the pytest levels (corpus evaluation, measurement, audits)

The level stack (unit → component → kernel integration → mechanic scenario → cross-domain) covers
only instruments with an *exact* oracle and a pass/fail result. Three more instruments exist and
answer different questions (as-is facts in
[overview §4.7](current_test_system_overview.md)):

| Instrument | Scope | Oracle [R24] | Result | Cadence today |
|---|---|---|---|---|
| Unit / component / property | code | exact value or law | pass / fail | every PR |
| Mechanic / cross-domain scenario | small real run | present-vs-absent effect | pass / fail | PR only if path filter matches |
| **Corpus evaluation (SimQ)** | many real runs over the tiered world corpus | reference grades and bands (statistical) | graded drift → classified | PR subset **silently skips** anchor tests; full run informational on `main` and nightly |
| Exploratory measurement (census, long-run observation) | real runs | none | report | on demand |
| Review / static testing (audits, `mechanics-auditor`) | code, docs, design | human or agent judgment | findings → tickets | occasional |

- **A. Adopt this instrument taxonomy in the architecture.** Each core-RPG domain states which
  question it answers at each instrument; for example, "does combat produce enough XP over 1000t"
  is a corpus-evaluation question, not a scenario question. The scorecard (D1) reports each
  instrument as a **separate column with explicit states** (`pass`, `drift-classified`,
  `skipped-no-data`, `unstable`, `stale`, `not-run`), never blended into coverage. Two concrete
  asks: make SimQ's skipped anchor tests *visible* (reported as `skipped-no-data`, not silent), and
  record the date of the last engine-audit review per dimension. SimQ scoring, anchors and
  drift policy stay owned by SimQ and `/simq-audit`.
- B. Keep only the pytest levels in this roadmap; treat SimQ, census and audits as external.
- C. Also re-baseline SimQ anchors and make the drift job blocking.

**Recommendation: A.** B leaves the core-RPG portfolio with no answer to long-horizon balance
questions (the starvation chain is exactly that class). C overlaps
`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS` and `/simq-audit`'s own mandate, and the
CI comment records why the drift job is deliberately non-blocking.

**Decision:**

---

## 6 · Proposed sequencing (core RPG first)

1. **Enable:** fix the CI path filter so mechanic scenarios run on core-RPG PRs (D10); fix the
   progression order leak (D5.1); fix `make test-cov` (D1).
2. **Core-RPG program, domain by domain (D10, with D3/D4/D9 inside it):**
   progression (D9 pilot review → template change → portfolio) → anatomy → movement → combat →
   economy → quests. Each domain closes with a mutation run (D4) and a scorecard reading (D1/D2).
3. **Then:** scorecard for the remaining domains (D1/D2), hygiene items D5.2–5.4, pruning (D6),
   parity re-tier (D7), API contracts (D8).
4. **Later:** cognition / social / strategy portfolios (second pilot: strategic), and T7
   metamorphic tests once determinism is unparked.

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
6. ~~D10 build order~~ Resolved 2026-09-28: domain by domain, starting with progression.
7. D11: adopt the instrument taxonomy (corpus evaluation / measurement / review) into the architecture?

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
| R20 | Hypothesis stateful testing (`RuleBasedStateMachine`) — https://hypothesis.readthedocs.io/en/latest/stateful.html · https://hypothesis.works/articles/rule-based-stateful-testing/ | Action-sequence invariants (D10 T3) |
| R21 | Deterministic simulation testing — Will Wilson, "Testing Distributed Systems w/ Deterministic Simulation", Strange Loop 2014 — https://www.thestrangeloop.com/2014/testing-distributed-systems-w-slash-deterministic-simulation.html · https://antithesis.com/docs/resources/deterministic_simulation_testing/ | Seed sweeps with invariants (D10 T6) |
| R22 | Rare, "Automated Testing of Gameplay Features in *Sea of Thieves*", GDC 2019 — https://www.gdcvault.com/play/1026042/Automated-Testing-of-Gameplay-Features · "Automated Testing at Scale in Sea of Thieves", Unreal Fest Europe 2019 — https://www.unrealengine.com/events/unreal-fest-europe-2019/automated-testing-at-scale-in-sea-of-thieves | Gameplay tests in minimal worlds (D10 T4/T5) |
| R23 | Characterization / golden-master tests (Feathers, *Working Effectively with Legacy Code*) — https://en.wikipedia.org/wiki/Characterization_test · https://understandlegacycode.com/blog/characterization-tests-or-approval-tests/ | Canonical-run snapshots (D10 T8) |
| R24 | Barr, Harman, McMinn, Shahbaz, Yoo, "The Oracle Problem in Software Testing: A Survey", IEEE TSE 41(5) 2015 — https://doi.org/10.1109/TSE.2014.2372785 | Oracle as a classification axis; statistical and implicit oracles (D11) |
| R25 | ISTQB Glossary, "static testing" — https://glossary.istqb.org/en_US/term/static-testing · ISTQB CTFL ch. 3 — https://astqb.org/3-1-static-testing-basics/ | Audits and reviews as static testing (D11) |
