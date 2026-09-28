---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture (core RPG first)

**Status: REVISION 2026-09-28b, direction review.** This plan is organized around five
deliverables (A–E) and their dependencies. No tickets exist yet. Milestones are proposed
separately for reviewer approval and will be merged here only after that. The earlier D1–D11
technique decisions survive as a **decision log (§10)** and a **mapping appendix**; they are not
milestones.

**Inspected code:** `04f911110`; test, `src/`, CI and agent files are unchanged through
`origin/main` `9bcae32c5` (2026-09-28). **As-is facts live in
[`current_test_system_overview.md`](current_test_system_overview.md)** (cited as *OV §n*), not here.
**Labels:** **[O]** observed (path or command) · **[P]** provisional signal · **[I]** inference ·
**[H]** historical statement · **[U]** unknown · **[D]** owner decision needed · `[R#]` external
reference (§13).

---

## 0 · Owner priorities (governing)

1. A coherent test structure and conventions, so an agent can tell which **domains, components,
   test levels and CI lanes** matter when logic changes.
2. **Core RPG first.** API and UI are planned surfaces; they enter the first program only if a
   current core-RPG behaviour demonstrably depends on them.
3. Test planning, authoring, selection and quality review are explicit steps in the AI-first
   workflows (the `investigator` stage, `implement-ticket`, `implement-epic`).
4. Coverage and verification are reported by reproducible scripts or workflows, never by manual
   review of individual cases.
5. Reusable test-level contracts and authoring conventions, at architecture and domain level.
   Individual tests are read only as evidence for a specific question.
6. Functional and non-functional risks, prioritized by current core-RPG needs and existing
   initiative ownership.

## 1 · Problem

The suite executes most of `src/`: 88% line coverage, with the scope caveats in OV §4.1. What it
cannot yet do is answer three questions:

- *which* tests matter for a change (OV §8);
- whether core-RPG behaviour is *proven to happen with the right effect* in a real run;
- how strong the assertions are (OV §4.5, §7: provisional signals, no mutation data).

Test planning and review are also largely absent from the agent workflows (OV §5.1).

## 2 · Classification axes (kept distinct)

| Axis | Values | Reference |
|---|---|---|
| **Level / scope**: what runs together | unit/component · kernel integration · mechanic outcome scenario · cross-domain scenario · broad simulation | Google test sizes [R1][R2]; pyramid [R7] |
| **Technique**: how cases are chosen | example · property · stateful property · metamorphic · characterization | [R10][R20][R11][R23] |
| **Evaluation instrument**: judges the tests or the system from outside a single test | mutation testing · SimQ corpus evaluation · execution census · static audit/review | [R5][R12] · OV §4.7 · [R25] |
| **Result type** | pass/fail · measured value · drift requiring classification · finding · unknown | oracle survey [R24] |

Two cautions:
- Pytest tests do **not** all have exact oracles. Some assert tolerance bands (SimQ anchors), and
  some assert only that a function ran.
- SimQ is **not** "non-pass/fail". Its anchor-band check is pass/fail against reference values
  with tolerances; only the later drift classification is a judgment (OV §4.7).

## 3 · Evidence producers and this epic's boundary

| Evidence | Produced by (owner) | This epic |
|---|---|---|
| Staged per-mechanic scenarios; scenario families and harness | `docs/plans/mechanic_verification_scenarios_proposal.md` (partly built: PRs #230, #232; its header still says "nothing built" [O]) | **Consumes.** Specifies where scenarios are *required* (§9 gaps) and their level contract (§6.1). Does not design scenario families. Who owns the proposal's open §6 items (CI integration, build order) [D] |
| Real-run reachability | `tools/execution_census.py` (`simulation_execution_census_initiative.md`) | Consumes as a reachability layer. Treated as `unstable` until determinism holds |
| Mechanism identity, state, verification axis | `registries/mechanisms.yaml` + mechanism-registry epic (`tickets/todos/mechanism-registry/`) and `mechanism_claims_as_tests_initiative.md` | Consumes mechanism ids for the impact model (§5, tier 2). The **mechanism → test link belongs to that epic** [D] |
| Corpus balance / drift | SimQ + `/simq-audit` | Reports its state as a separate instrument (§8). Does not change scoring, anchors or drift policy |
| Long-run determinism | `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (**BLOCKED by owner**) | Treats replay reliability as an **explicit precondition** (§6.3). No long-run replay claims |
| combat → XP → level-up root cause | `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` | Must not add tests that record starvation as healthy. Consumes its outcome |
| Law priority vs verification | Parity ledger (`docs/parity_ledger/`) and mechanism registry both claim "proven"; nobody owns de-duplication [O] | Separate evidence-state proposal (§9.2); de-duplication ownership [D] |

---

## 4 · Deliverable A: Core-RPG domain and behaviour map

### 4.1 Scope (current stage)

Core RPG means Mechanics Bible chapters 01–03 behaviour, plus the shared substrate it runs on.
Cognition, social, strategy and faction (ch04–05) come after core RPG (bottom-up rule).

| Domain | Spec | Runtime entry (kernel phase) | Authoritative change → observable outcome | Consumers | Maturity [evidence] |
|---|---|---|---|---|---|
| **Shared substrate**: apply pipeline, RNG/clock, inventory, registries | `docs/engine/kernel.md`, `docs/engine/authoritative_mutation_pipeline_contract.md`, `docs/core/state.md` | All phases; RNG only in `_phase_resolution()` | Typed records through `AuthoritativeApplyPipeline` → committed state | Every domain | **Active** [O `tests/integration/pipeline/test_mutation_boundary.py`, `src/core/inventory.py`] |
| **Movement** (incl. pursuit) | ch02 | Scheduling (decide), Resolution (execute); `src/engine/movement.py` | Position / task state → FLED and other transitions | Combat (`src/domains/combat_engagement/learning_outcome.py:146`) | **Active** [O] |
| **Combat resolution** | ch02 | Resolution (`CombatResolutionSystem`, `src/engine/combat.py`); decisions in Scheduling | Attack → HP / death / XP records | Progression, loot/economy | **Partial.** The opportunity-attack path is live; the decision-driven path is nearly dead (0–2 vs 181–2177 calls per 1–2k ticks) [O starvation epic §1; open P0 `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`] |
| **Progression / XP / level-up** | ch01 | Resolution via the pipeline | Kill → XP → threshold → level → `stats_dirty` | Anatomy | **Partial**: wiring proven by positive control, starved in real runs [O `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`] |
| **Anatomy / derived stats** | ch01 | Resolution (recalc on `stats_dirty`) | Level → `combat.atk/def/max_hp` | Combat | **Active, starved upstream** [O] |
| **Economy**: harvest, craft, trade | ch03 | Resolution; `src/systems/` (harvest, crafting, market, economy), `src/economy/` | Resource → inventory → market/craft, with conservation | Quests, progression (materials) | **Active** [I]; 0 mechanic scenarios [O] |
| **Quests / guild** | ch03 + buildings/guild doc | Resolution; `src/systems/quest*`, `guild_system.py`, `src/quests/` | Generation → completion → reward | Economy, progression | **Partial proof**: generation has a scenario (`tests/mechanic_scenarios/test_quest_generation_sourcing_orphan_calibration.py`); completion → reward has none [O] |
| **Party / group** | bottom-up rule | [U] | [U] | [U] | **Mapped, unassessed**: `src/systems/party.py`, `src/systems/social_systems/party*.py` exist [O]. Planned for after quests |

### 4.2 Order check

The earlier order (progression → anatomy → movement → combat → economy → quests) does **not**
follow runtime dependencies [O]:
- Real combat happens mostly *inside* movement/pursuit (`resolve_multi_attack()`).
- Progression depends on combat volume.
- Inventory and the apply pipeline sit under everything.

**Proposed dependency order [I]:** shared substrate → movement + combat (one unit) → progression +
anatomy → economy → quests → party. This reverses an owner-approved order, so it is presented as a
**reopened decision** (§10). The *workflow pilot* stays on progression (§7), because it measures
authoring quality rather than portfolio completeness.

### 4.3 Promises vs experimental; who approves a changed outcome

- **Promises:** Bible laws ("Certified Level 1", CLAUDE.md).
- **Experimental in practice:** any behaviour with an open *never fires* ticket.
- **Precedence:** Bible > code-with-logged-divergence (`docs/guidelines/intentional_divergences.md`)
  > ledger / registry > tickets [I; no single doc states the chain].
- **Approver of a changed expected outcome:** not named in the repo [U]. Proposed: the owner, via
  the divergence log [D].

---

## 5 · Deliverable B: Change-impact and test-selection model

**Question answered:** *when a rule, shared model, apply pipeline, content/config value, or
orchestration phase changes, how does an agent find the affected domains, components, test levels,
test paths and CI lanes, and why?*

**As-is** (OV §8): prose maps, a per-ticket agent grep for importers, a static backstop that is
silent for unmapped files, three coarse CI path filters, and no identifier joining mechanism,
law, domain, test and lane.

**Target model (architecture, not implementation):**

| Element | v1 proposal [I] |
|---|---|
| Granularity | **Component** (the ~30 `src/` packages the scoper already uses) → **domain** (§4.1). Mechanism tier later, once the registry carries a test link (§3) |
| Stable identifiers | Package path → component id → domain id (§4.1 names) → level (§6.1) → test path → CI job name |
| Fan-out for shared components (`src/core/*`, the pipeline, `src/engine/kernel.py`) | Computed from a **generated, committed import graph** (not local-only graphify), plus the declared domain consumers in §4.1 |
| Content / config (`data/worlds/`, `config/`) | Explicit rule: world/content → corpus instrument + scenarios using that world; config profile → kernel integration + determinism |
| Orchestration phase (kernel phases, pipeline phases) | Treated as shared substrate: all core-RPG domains' outcome levels |
| **Output** | An impact report: for each recommended test set, the **reason** (which rule matched); plus an explicit **`unknown impact`** list, never silent |
| Fallback when unknown | Run the full core-RPG lane set and mark the change `impact-unknown` in the report |
| **Selected ≠ proven** | The report has two columns: *relevant tests selected* and *behaviour proof status* (from §8: outcome asserted? mutation-checked?). A change can be fully selected yet unproven |

Representative examples (current behaviour in OV §8):

| Change | v1 would recommend (reason) | Proof status it would expose |
|---|---|---|
| Damage constant, `src/engine/combat.py` | combat component tests; the combat value-differential scenario; the combat mechanic-scenario lane (domain = combat) | Proven by an outcome scenario; property bounds missing |
| XP curve, `src/progression/` | progression tests **and** mechanic scenarios (domain rule, fixing today's `PERF_RE` miss) | Real-run volume unproven (starvation epic) |
| `src/systems/market.py` | economy domain: `tests/unit/resource/test_domain_8_economy.py`, the import-boundary guard (import-graph fan-out) | No real-run chain scenario |
| `AuthoritativeState` in `src/core/state.py` | substrate rule: all core-RPG outcome levels | Mutation boundary proven; conservation proven by example tests only |
| A value in `data/worlds/<w>/` | the corpus instrument for `<w>` + scenarios using `<w>` | SimQ anchor state (possibly `skipped-no-data`) |

---

## 6 · Deliverable C: Test-level contracts and reusable framework

### 6.1 Level contracts (draft)

| Level | Executed boundary | Resources | Expected-behaviour source | Oracle | Observation point | Harness | Isolation | Budget | Placement / marker | CI cadence |
|---|---|---|---|---|---|---|---|---|---|---|
| Unit / component | function or domain service on hand-built state | in-process | Bible formula / contract | exact value or law | return value; one `ApplyPath.apply_generation` | `V2EntityBuilder`, `tests/helpers/*` | registry reset (conftest) | < 1 s | `tests/unit/<component>/`; size marker (new) | every PR |
| Kernel integration | real `Kernel` + profile + RNG, no compiler | in-process | kernel/pipeline contracts | state fields over N ticks | committed state, events | `tests/integration/kernel/test_minimal_kernel.py` pattern | fresh kernel per test | < 10 s | `tests/integration/<area>/` | every PR |
| Mechanic outcome scenario | `WorldCompiler` + `Kernel`, one mechanic | small compiled world | Bible law + proposal §3.3 | **occurrence and effect**, present vs absent | authoritative state delta | open-coded today → **shared helper (gap)** | world compiled per test | < 30 s | `tests/mechanic_scenarios/`; marker (new) | **every PR** (requires the path-filter fix) |
| Cross-domain scenario | ≥2 domains chained in one real run | small compiled world | Bible chain | chained effect | state deltas at each hop | same helper | same | < 60 s | `tests/mechanic_scenarios/` (chain marker) | every PR, or nightly if over budget |
| Broad simulation | many ticks / corpus | profiles, corpus worlds | balance intent, laws | invariants (`HardLawMonitor`), anchor bands | monitors, SimQ reports | certification harness, SimQ | per run | minutes | slow markers | nightly / on demand |

Budgets are proposals derived from observed durations (OV §4.3), not measured contracts [I].

### 6.2 Choosing a technique (criteria, not a mandate) [I, from OV §9 and the references]

| Technique | Choose when | Not when |
|---|---|---|
| Example | a formula or branch has a documented value | the law holds over ranges you'd only sample by hand |
| Property [R10] | a law over input ranges: bounds, monotonicity, conservation of one transaction | the oracle is a single documented value |
| Stateful property [R20] | invariants must hold across *sequences* of actions (inventory, gold, HP) | behaviour needs a compiled world to mean anything |
| Metamorphic [R11] | relations between runs (seed, permutation) | **while replay reliability is unverified** (§6.3) |
| Characterization / golden [R23] | a complex output must not drift unnoticed, with deliberate re-approval | a simpler exact oracle exists. **Not required per domain** |

### 6.3 Replay reliability as an explicit condition

- Short-run reproducibility is proven: `tests/integration/kernel/test_determinism_suite.py`,
  10 runs × 10 ticks, one seed [O].
- Long-run determinism is **unproven and parked**. The census found an UNSTABLE result [O].
- A multi-seed invariant sweep may therefore claim only: *invariants held on each seed's run;
  short-run reproducibility re-checked per seed*.
- **Exact seed replay of a sweep failure is not promised.** Replay reliability becomes a separately
  verified condition (its own check, with its own state in §8) before any sweep or metamorphic
  test claims it. [R21] describes the target, not the current state.

### 6.4 Smallest framework gaps (from OV §9)

1. A shared scenario helper: compile world → stage entity → run N ticks → observe the effect,
   with present/absent arms.
2. A shared replay-diff helper.
3. Declared test metadata: domain, level, size.
4. A per-test `data/runs` cleanup fixture.
5. [D] Retire or adopt `src/testing/` and the unused CLI helpers.

---

## 7 · Deliverable D: AI-first test workflow

### 7.1 Responsibility map (target; current state in OV §5.1)

| Decision | Stage / agent (existing) | Evidence recorded |
|---|---|---|
| Impact set (domains, components) | Investigate / `investigator`, fed by the §5 impact report | the impact report, incl. the `unknown` list |
| Level, technique, oracle, fixture, expected effect, negative cases, non-functional risk | Investigate / `investigator` via **extended `test_plan.md` fields** | one row per acceptance criterion with these fields |
| Tests written | Implement / `implementer` (unchanged at first) | files changed |
| Commands selected | Test / `test-scoper`, from the impact report | command + reason per test |
| Quality review | **Advisory, diff-scoped** review of changed tests against a fixed rubric (Test Desiderata [R9], smells [R13], `testing-anti-patterns.md` [R14]). Insertion point [D]: an existing reviewer's checklist, or a conditional phase like Security-Review (`implement-ticket.js:1473`) | findings list; no blocking |
| Completion | Verify / `done-checker` checks the fields are present (not their quality) | DoD line |
| Epic level | `implement-epic.js` unchanged; each child follows the above | — |

**Assessment [I]:** the existing workflow can carry all of this with template fields, prompt
additions and one advisory check. **A new test-writing agent is not justified yet**; it stays a
conditional option (§7.2 criteria).

### 7.2 Measurable pilot (progression)

| Item | Design |
|---|---|
| Scope | Tickets changing `src/progression/` or `src/domains/progression/`, **excluding** files owned by the starvation-chain epic |
| Baseline | Closed tickets touching those paths (42 in `tickets/done/` mention them [O]); their `test_plan.md` fields; one `mutmut` run on the progression modules at pilot start (with provenance, §8) |
| Prerequisite | The progression order leak is fixed first (OV §4.2); otherwise the pilot's test signals are untrustworthy |
| Treatment | Extended `test_plan.md` fields; the advisory review; the impact report (as soon as §5 v0 exists) |
| Controls | Concurrent non-progression tickets under the unchanged process; the same mutation targets re-run at the end |
| Observation | The next **5 progression tickets or 6 weeks**, whichever comes first |
| Cost | `tool_call_count` per phase from `events.jsonl` (tokens are not recorded; `duration_s` is unusable, OV §5.1) |
| Quality signals | Field completeness; review findings per ticket; mutation score delta on touched modules; outcome-scenario presence; title-classified escapes in the following 30 days [P] |
| Keep / change criteria (thresholds [D]) | Keep the template if fields are filled with ≤ +20% Investigate tool calls. Keep the review if its findings led to test changes in ≥ half the tickets. Consider a split test-writer only if the mutation score does not improve after both |
| Limitation | The small sample makes the result directional, not statistically conclusive |

---

## 8 · Deliverable E: Metric dictionary (before any scorecard)

**States for every measure:** `pass` · `fail` · `measured` · `drift-classified` · `skipped`
(incl. `skipped-no-data`) · `not-run` · `blocked` · `unstable` · `stale` · `unknown`. Nothing is
reported as 0 or pass by default.

| Report layer | Measure | Rule / denominator | Producer (automated) | Provenance and cadence | Limitations |
|---|---|---|---|---|---|
| Code executed | line + branch coverage | covered / statements in `src/`, per package | a standing CI coverage job (new; `make test-cov` fixed) | commit SHA, tier list, failed-test count; nightly | Execution ≠ assertion. The existing 88% is a one-off with 8 failures |
| Behaviour specified and linked | law evidence state | ledger entries by (priority, evidence state) | parity-ledger scan (existing `tools/parity_index_baseline.py` pattern) | commit SHA; per PR | The corpus is not schema-valid (§9.2) |
| Mechanism reached in real runs | reachability | mechanisms reached / registered | census + registry verification view | run id, worlds, ticks; on demand | `unstable` until determinism holds |
| Effect asserted | outcome-proof presence | core-RPG behaviours (§4.1, §9) with a passing outcome-level test / total | declared test metadata + JUnit | commit SHA; per PR | Needs metadata (§6.4 gap 3) |
| Faults detected | mutation score | killed / (killed + survived); timeouts and equivalents listed separately | `mutmut` [R12] on a declared target | **target modules, selected tests, commit, date, runtime**; becomes `stale` after the target code changes or 30 days | One-off baselines only at first |
| Corpus drift / findings | anchor-band results; drift classes | per run key × pillar | SimQ tests + `/simq-audit` | calibration run id; nightly / on demand | PR runs are `skipped-no-data` today (OV §4.7) |
| Hygiene | order-dependence; lane fit; skip/xfail | failures in a random-order run; tests over budget per level | scheduled random-order job; `--durations` | commit SHA; weekly | Random order vs the RNG contract to be checked first |
| Selection completeness | mapped-change rate | changed files with a matching rule / changed files | impact report (§5) | per PR | — |

**Scorecard:** comes after the dictionary. Report layers stay separate, with **no aggregate
quality score**. Host to be decided after the dictionary is accepted: `codebase-health` appends
immutable, versioned history but has no per-domain drill-down (`tools/codebase_health_baseline.py:233-253`) [D].

---

## 9 · Core-RPG evidence gaps (replaces the old ✗ → ✓ matrix)

"Exists" · "runs on PRs" · "passes" · "proves outcome" are tracked separately [O unless marked].

| Behaviour | Existing evidence | Runs on PR? | Missing proof | Owner | Level / technique | Why |
|---|---|---|---|---|---|---|
| Apply pipeline only mutates via typed records | `test_mutation_boundary.py`, `tests/architecture/` | yes | none material | this epic (monitor) | — | Healthy |
| Resource conservation across action sequences | example tests (`tests/unit/resource/`, `integration/kernel/test_resource_conservation.py`) | yes | conservation over *generated sequences* | this epic | component / stateful property | Invariant with a huge input space |
| Pursuit closes and the opportunity attack lands | unit movement/combat tests; escaped defects `TCK-20260809-COMBAT-PURSUIT-*` [P] | unit yes | a real-run occurrence + effect scenario | this epic, using the proposal's harness | mechanic scenario | Dominant real combat path |
| Damage formula | unit + `test_combat_resolution_damage_value_differential.py` | yes (engine/domains match `PERF_RE`) | bounds / monotonicity over ranges | this epic | property | Formula law |
| Decision-driven attack | none effective | — | **blocked** on the P0 investigation | starvation epic | — | Don't test the symptom |
| XP reward → level-up | 3 value-differential scenarios | **no** for `src/progression/`-only PRs | the PR lane; curve monotonicity | this epic | CI fix; property | Filter gap |
| Real-run XP volume | none | — | **blocked** | starvation epic | corpus instrument later | Owned elsewhere |
| Derived-stat recalc | `test_readiness_and_derived_stats_value_differential.py` | **no** for `src/entities/`-only PRs | the PR lane | this epic | CI fix | Filter gap |
| Harvest → inventory → market chain | example tests only | unit yes | a real-run chain scenario | this epic | cross-domain scenario | No chain proof |
| Crafting material predicates | unit tests, **order-dependent** (OV §4.2) | pass alone, fail combined | isolation fix first | this epic | — | Measurement trust |
| Quest completion → reward | generation scenario only | partial | a completion → reward chain scenario | this epic | cross-domain scenario | Chain unproven |
| Party / group | [U] | [U] | map first | this epic (after quests) | — | Unassessed |

No golden master is prescribed per domain. A characterization test is added only where the table
names one.

### 9.1 Non-functional risks (current core-RPG needs)

| Risk | Owner | Proposal |
|---|---|---|
| Replay / determinism | parked ticket | Explicit precondition (§6.3); short-run check per sweep seed |
| Mutation integrity | existing guards | Keep |
| Isolation | none today | Fix the leak; scheduled random-order run (after the RNG check) |
| Perf / scale | `tests/perf` framework, **0 baselines** (OV §6.3) | Calibrate core-RPG baselines before any perf claim |
| Content compatibility | migration lanes (path-filtered) | Add `data/worlds/` to the impact rules (§5) |
| Persistence round-trip / recovery | [U] | Investigate before planning |

### 9.2 Parity-ledger evidence model

- `priority` is **importance** only. Verification lives in `status` and `proof_type` /
  `test_path` (`docs/parity_ledger/schema.json`) [O].
- The P0 → `test_path` rule was added by `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` and is
  enforced only on writes (`tools/parity_ledger_writer.py`); the corpus fails its own schema 2,867
  times (planner run of `jsonschema` over all shards, 2026-09-28) [O].
- **Proposal:** keep `priority` and `status` as they are. Add a *derived* evidence state
  (`test_linked` / `audit_only` / `legacy` / `missing`) and report it. Validate the corpus against
  the schema only after a recorded baseline. No mass P0 → P1 migration.

---

## 10 · Decision log

Status values: **Owner-approved** (the owner chose it; in every case the planner's recommended
option was chosen via an option prompt on 2026-09-28) · **Provisional** (planner recommendation,
never put to the owner) · **Reopened** (an owner decision with new evidence against it; a revision
is proposed for review, not applied) · **Pending**.

| # | Decision | Status | Consequence / proposed revision |
|---|---|---|---|
| D1 | Scorecard report-only, hosted in codebase-health | Owner-approved (report-only) · **Reopened** (hosting) | Host lacks per-domain drill-down. Proposed: dictionary first (§8), host decided after |
| D2 | Per-domain shape bands | Owner-approved · **Reopened** | Proposed: replace with the risk-based gaps (§9) |
| D3 | Property tests now; metamorphic after determinism | Owner-approved | Unchanged; replay condition made explicit (§6.3) |
| D4 | One-off `mutmut` baseline on 3 targets (+ progression) | Owner-approved | Adds provenance and staleness rules (§8) |
| D5 | Hygiene: leak, random order, lane fit, pinned-data test | Owner-approved | Random order gated on the RNG-contract check |
| D6 | Delete `agent_codex_*` | Owner-approved · **Reopened** (placement) | Moved to its own cleanup path (§11); consumer and CI inventory required first. Other D6 rows are **Provisional** |
| D7 | Re-tier P0 → P1 when no test | Owner-approved on a flawed premise · **Reopened** | Proposed: separate evidence state (§9.2) |
| D8 | API items now | Owner-approved · **Reopened** | No demonstrated core-RPG dependency found. Proposed: defer to the API/UI path (§11) |
| D9 | Workflow pilot on progression, A → B → C | Owner-approved | Made measurable (§7.2); the split test-writer is conditional |
| D10 | Portfolio domain by domain from progression; ✗ → ✓ matrix | Owner-approved · **Reopened** | Order not dependency-true (§4.2); matrix replaced by gaps (§9) |
| D11 | Instrument axis (SimQ, census, audits) | **Pending** | Revised wording (§2) |
| — | Core-RPG scope and dependency order (§4.1–4.2) | **Pending** | — |
| — | Owner of the scenario proposal's §6 items; owner of ledger/registry de-duplication | **Pending** | §3 |

## 11 · Separate dependency paths (not on the core-RPG critical path)

| Path | Prerequisites before any action |
|---|---|
| **Cleanup / pruning** (`agent_codex_*`, `src/testing/`, SimQ narrow-test relocation, doc-text tests, duplicate directories) | For each target: list its importers, Makefile and CI references, and plan/ticket references; record them. The test/source LOC ratio alone is **not** a pruning criterion. Deletion follows an owner decision per target |
| **API / UI** | Enters only when a core-RPG behaviour is shown to cross the API boundary. Candidate items then: OpenAPI snapshot, Schemathesis [R19], raw-model guard, `test_rest_parity.py` → `TestClient`. Frontend follows the HUD sequencing rule |
| **Parity evidence model** | §9.2 decision (D7), then a recorded baseline, then schema validation of the corpus |

## 12 · Out of scope

- Designing scenario families (proposal), census changes, registry verification.
- The kernel determinism root cause.
- SimQ scoring and anchors.
- Reviewing individual test cases.

## Appendix · Mapping of old directions to deliverables

| Old | Now |
|---|---|
| D1 scorecard, D2 shape | Deliverable E (§8); D2 superseded by §9 |
| D3 property/metamorphic, D10 portfolio | Deliverable C (§6.2) and A gaps (§9) |
| D4 mutation | E (§8, faults detected) |
| D5 hygiene | §9.1 isolation; E hygiene |
| D6 prune, D8 API | §11 separate paths |
| D7 parity | §9.2 |
| D9 workflow | Deliverable D (§7) |
| D11 instruments | §2 axes, §8 layers |

## 13 · References

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
