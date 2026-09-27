---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture: Measurement Model and Direction

**Status, drafted 2026-09-28. DIRECTION REVIEW. No tickets exist yet.** Each `D#` section below
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

The direction uses established models, not a bespoke rubric:

- **Test pyramid, with Google test sizes (small / medium / large)** for *shape*: size is decided
  by resources used (process, I/O, real kernel ticks), not by directory name.
- **Marick's agile testing quadrants** for *purpose*: Q1 technology-facing unit tests · Q2
  business-facing functional tests (mechanic scenarios) · Q3 exploratory / emergent (SimQ, census)
  · Q4 non-functional (perf, determinism).
- **Kent Beck's Test Desiderata** for *per-test quality*: behavioural, structure-insensitive,
  deterministic, isolated, fast, specific.
- **Effectiveness metrics:** line/branch coverage (does code run?), **mutation score** (do
  assertions catch a changed operator or constant?), and **defect-escape analysis** (which defect
  classes reached `main` past a green suite).
- **Simulation-specific oracles:** property-based tests (Hypothesis) for laws, metamorphic tests
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

## 5 · Directions to decide

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

**Decision:**

### D2 · Target shape of the pyramid

- **A. Set a target shape per domain as a scorecard band**, e.g. gameplay domains must have at
  least one medium/large outcome proof per registered mechanism. The scenarios themselves stay
  owned by the mechanic-verification plan.
- B. A global numeric ratio (e.g. 70/20/10).

**Recommendation: A.** A global ratio fits badly across domains: observability is legitimately
unit-heavy, while strategic and social need outcome proofs, not more scorers. Pairs with a soft
rule for strategic/social: new behaviour gets a scenario, not another scorer unit test.

**Decision:**

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

**Decision:**

### D4 · Mutation-score baseline

`mutmut` (or `cosmic-ray`) over a narrow, high-value target set: the combat damage path, the
economy conservation path, and the apply pipeline.

- **A. One-off baseline on 3 targets, recorded in the scorecard, re-run manually.**
- B. Nightly scheduled mutation run.
- C. Skip.

**Recommendation: A.** This is the only direct measure of assertion strength. Full-repo mutation
is too expensive and not needed to answer "are our core law tests real?"

**Decision:**

### D5 · Isolation and lane hygiene

1. Fix the order-dependent leak behind the 7 progression failures (likely registry or global
   state that the other directories' fixtures set).
2. Add one random-order run (`pytest-randomly` or `-p random_order`) as a scheduled job to surface
   the rest.
3. Move large tests out of unit lanes, starting with the two in `test_mechanism_state_caller_check.py`.
4. Replace `test_real_registry_findings_pinned` (pins live repo data) with a fixture-backed
   assertion.

- **A. All four.** B. Items 1, 3 and 4 only (no random-order job).

**Recommendation: A.** Item 2 is the only way to find the rest of the leaks, because CI's
directory split hides them.

**Decision:**

### D6 · Prune and relocate

| Item | Options | Recommendation |
|---|---|---|
| `agent_codex_*` (7 test dirs + 7 tool dirs) | delete · park (excluded from CI, kept in repo) · keep | **Open: user decision.** Delete if the Codex pilot has no reactivation date; git history keeps it recoverable |
| SimQ `*_corpus.py` (32 files) | relocate to the owning domain / `mechanic_scenarios` · leave | Relocate; keeps SimQ balance-only |
| Doc-text and source-grep tests (~243/152 files) | policy + convert-or-delete sweep · policy only | **Policy only first:** a doc-text assertion is allowed only when the doc is itself a machine contract. Sweep opportunistically |
| Index-pinned hook tests (`PreToolUse[4]`) | convert to name/matcher lookup | Convert; cheap |
| agent-monitoring tests (~2.7×) | trim toward ~1.5× · leave | Trim duplicated doc/prose assertions only |
| Structural clutter: `tests/unit/entity`+`entities`, orphan `tests/observability/`, empty `tests/integration/perf/` and `tests/unit/motivation/`, mis-targeted `tests/unit/config/`, ticket-appendage files | fix · leave | Fix in one mechanical chore ticket |
| `pyproject.toml` markers (27 declared, most unused, legacy-parity ones reference `src_legacy`) | prune + update `docs/testing/test_taxonomy.md` · leave | Prune; replace the taxonomy with D2's size/quadrant model |

**Decision:**

### D7 · Parity-ledger traceability honesty

93% of P0 entries have no test, so P0 has stopped meaning "must be proven".

- **A. Re-tier.** P0 is reserved for entries with a passing `test_path`, or entries with a
  test-backlog ticket. Everything else drops to P1 with `proof_type: audit`. Enforced by the
  existing parity-ledger writer and schema.
- B. Mass-link: backfill `test_path` for all ~1,560 entries.
- C. Leave as is and document the gap.

**Recommendation: A.** B is weeks of mostly clerical linking with low defect-finding yield.
Also flagged, but out of this epic's scope: the parity ledger and the mechanism registry now both
record "is this proven". That duplication should be resolved by the mechanism-registry epic, not
here.

**Decision:**

### D8 · API contract and frontend (candidate for deferral)

A schema snapshot of the OpenAPI output, a generic "no route serializes a domain class" test,
converting `test_rest_parity.py` to `TestClient`, and game-view frontend tests.

- **A. Defer the frontend part until after RPG-core work (HUD sequencing rule); take the two API
  items now.** B. All now. C. Defer all.

**Recommendation: A.**

**Decision:**

---

## 6 · Proposed sequencing (after decisions)

1. **Measure:** D1 (scorecard + `make test-cov` fix) and D5.1 (isolation leak). Everything
   after this is judged against the baseline.
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

1. `agent_codex_*`: delete or park?
2. Should the scorecard extend `codebase-health-scorecard` or be a separate `make` target?
3. Is D7's re-tier acceptable, given it will visibly demote ~1,400 entries?
4. Mutation tool preference (`mutmut` vs `cosmic-ray`); `mutmut` is the more common default.
