---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Plan — Test Architecture (core RPG first)

**Status: REVISION 2026-09-28d, targeted corrections + detailed milestone plans** (plans in [`milestone_plans.md`](milestone_plans.md)). The plan is organized around five
deliverables (A–E) and a behaviour-level dependency map (§9). No tickets exist yet. Milestones are
in §11 as **proposals awaiting reviewer and owner approval**. D1–D11 survive only as a decision
log (§12) and a mapping appendix.

**Inspected code:** `04f911110`; test, `src/`, CI and agent files are unchanged through
`origin/main` `9bcae32c5` (2026-09-28). **As-is facts live in
[`current_test_system_overview.md`](current_test_system_overview.md)** (cited as *OV §n*), not here.
**Labels:** **[O]** observed (path or command) · **[P]** provisional signal · **[I]** inference ·
**[H]** historical statement · **[U]** unknown · **[D]** owner decision needed · **[RR]** reviewer
recommendation, not owner-approved · `[R#]` external reference (§15).

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
| **Evaluation instrument**: judges tests or the system from outside a single test | mutation testing · SimQ corpus evaluation · execution census · static audit/review | [R5][R12] · OV §4.7 · [R25] |
| **Result type** | pass/fail · measured value · drift requiring classification · finding · unknown | oracle survey [R24] |

Two cautions:
- Pytest tests do not all have exact oracles; some assert tolerance bands, some only that code ran.
- SimQ's anchor comparison is a **tolerance-band pass/fail check on one seed per run key**, not a
  statistical test. Drift classification (`/simq-audit`) is a separate, later workflow whose result
  is a classification. Missing calibration data is its own **`skipped-no-data`** state (OV §4.7).

## 3 · Evidence producers and this epic's boundary

| Evidence | Produced by (owner) | This epic |
|---|---|---|
| Staged per-mechanic scenarios; scenario families and harness | `docs/plans/mechanic_verification_scenarios_proposal.md` (partly built: PRs #230, #232; its header still says "nothing built" [O]) | Owns the **lane / selection contract** and the level contract (§6.1) [RR]. Does not design scenario families [RR] |
| Real-run reachability | `tools/execution_census.py` | Consumes; `unstable` until determinism holds |
| Mechanism identity and verification; **canonical mechanism → test link** | `registries/mechanisms.yaml`, mechanism-registry epic (`tickets/todos/mechanism-registry/`), `mechanism_claims_as_tests_initiative.md` | Consumes the link and **validates its availability** [RR]; uses mechanism ids as behaviour ids (§10.1) |
| Law-level evidence | Parity ledger (`docs/parity_ledger/`) | Consumes law ids as behaviour ids when no mechanism id exists; evidence-state proposal §10.4 |
| Corpus balance / drift | SimQ + `/simq-audit` (owner of anchors and drift policy) | Reports state only. The **SimQ skip-visibility repair is owned by SimQ**, not on this epic's critical path |
| Long-run determinism | `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (**BLOCKED by owner**) | Replay reliability is an explicit precondition (§6.3) |
| combat → XP → level-up chain | `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` (its `SEQUENCE.md` is **stale**: it lists `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` as open, but that ticket is in `tickets/done/` dated 2026-09-17 [O]) | Must not add tests that record starvation as healthy |

---

## 4 · Deliverable A: Core-RPG domain and behaviour map

### 4.1 Scope and maturity

Core RPG means Mechanics Bible ch01–03 behaviour, plus the shared substrate it runs on. Cognition,
social, strategy and faction (ch04–05) come later.

| Domain | Spec | Runtime entry | Authoritative change → outcome | Consumers | Maturity [evidence] |
|---|---|---|---|---|---|
| **Shared substrate**: apply pipeline, RNG, inventory, registries | `docs/engine/kernel.md`, `authoritative_mutation_pipeline_contract.md`, `docs/core/state.md` | All phases; RNG only in `_phase_resolution()` | typed records → `AuthoritativeApplyPipeline` → committed state | every domain | Active [O `tests/integration/pipeline/test_mutation_boundary.py`, `src/core/inventory.py`] |
| **Movement** (incl. pursuit, opportunity attack) | ch02 | Scheduling / Resolution; `src/engine/movement.py` | position/task state; on disengagement, `CombatResolutionSystem.resolve_multi_attack(..., is_opportunity_attack=True, is_lethal=False)` (`src/engine/movement.py:240-242`) | combat, `combat_engagement/learning_outcome.py:146` | Active [O] |
| **Combat resolution** | ch02 | decision path: `TacticalDecisionSystem` → `ActionRouter` → `CombatActions.execute_attack()` → `resolve_attack()` (`src/engine/domain/combat_actions.py:65`) | HP / death (`KILL` only when lethal, `src/engine/combat.py:134-172`) / XP records | progression, loot | **Partial** (see §4.2) |
| **Progression / XP / level-up** | ch01 | Resolution via the pipeline | kill → XP → threshold → level → `stats_dirty` | anatomy | Partial: wiring proven by positive control [O `tickets/done/TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS.md`]; starved in real runs [H] |
| **Anatomy / derived stats** | ch01 | recalc on `stats_dirty` | level → `combat.atk/def/max_hp` | combat | Active, starved upstream [H] |
| **Economy**: harvest, craft, trade | ch03 | Resolution; `src/systems/` (harvest, crafting, market, economy), `src/economy/` | resource → inventory → market/craft, with conservation | quests, progression (materials) | Active [I]; 0 mechanic scenarios [O] |
| **Quests / guild** | ch03 + buildings/guild doc | `src/systems/quest*`, `guild_system.py`, `src/quests/`, pipeline phases `quests.py`, `quest_opportunity_rewards.py` | generation → completion → reward | economy, progression | Partial proof: generation scenario only [O] |
| **Party / group** | — | [U] | [U] | [U] | **Not assessed**: code exists (`src/systems/party.py`, `src/systems/social_systems/party*.py`) [O]; behind a selection gate (§9) |

### 4.2 Combat claim, evidence by part

| Part of the claim | Evidence | Status |
|---|---|---|
| The opportunity-attack call site is inside movement | `src/engine/movement.py:240` is the only caller of `resolve_multi_attack()` in `src/` | **[O] code** |
| That path is non-lethal | `is_lethal=False` at `src/engine/movement.py:241` and `src/engine/combat.py:252`; `KILL` requires lethal (`combat.py:172`) | **[O] code** |
| The decision path exists and is reached via `execute_attack()` | `src/engine/domain/combat_actions.py:65` | **[O] code** |
| "Most combat runs through the movement path" | Instrumented call counts, 1000 ticks, default gate: `crowded_frontier` 2 vs 181; `quest_dense_frontier` 0 vs 0; `hero_guild_routing` 0 vs 2177 (`tickets/todos/TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION.md:455-470`) | **[H] measured in 3 worlds, one run each, ~2026-09-15/17; not re-measured**; long-run determinism is parked |
| Why the decision path is rare | Closed investigation: strategic layer rarely assigns combat objectives; a winning `COMBAT_ENGAGE` goal is discarded at dispatch (hardcoded `reach_location`) (`tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md`, completion summary + 2026-09-19 addendum) | **[H] investigation finding**; recorded there as "a design question for the user". No follow-up ticket found [O] |

### 4.3 Dependency reading

- For **real-run outcome evidence**, the dependency runs substrate → movement/combat → progression
  (XP needs kills) [I].
- **Pure-law evidence** (damage formula, XP curve, conservation of one transaction) does **not**
  depend on real-run combat and can proceed earlier [RR].
- The owner-approved "progression first" order (D10) is kept for the **workflow pilot** (§7).
  Evidence building follows §9's behaviour-level map rather than a domain sequence.

### 4.4 Promises, experiments, and approval of changed expected outcomes

- **Promises:** Bible laws ("Certified Level 1", CLAUDE.md).
- **Experimental in practice:** any behaviour with an open *never fires* ticket.
- **Precedence:** Bible > code-with-logged-divergence (`docs/guidelines/intentional_divergences.md`)
  > ledger / registry > tickets [I].
- **Approval path [RR]:** a named mechanic/spec owner approves any changed expected outcome, and
  the approval is recorded (divergence-log entry, or `/simq-audit` `EXPECTED_DRIFT` citing a
  commit, as applicable). **Agents cannot re-approve an expectation by themselves.**
- Default planning assumption: the owner (the user) is the spec owner for all core-RPG domains [D].

---

## 5 · Deliverable B: Change-impact and test-selection model

**Question:** *when a rule, shared model, apply pipeline, content/config value, runtime
registration, or orchestration phase changes, which domains, components, levels, tests and lanes
are affected, and why?* As-is: OV §8.

### 5.1 Inputs (none alone is a complete dependency oracle)

| Input | Captures | Misses | Availability |
|---|---|---|---|
| Declared component → domain rules (§4.1) | ownership, intent | anything undeclared | authored |
| **Static import graph** | direct and transitive imports, incl. function-local imports (`src/engine/pipeline.py` loads phases lazily) | dynamic dispatch, string-keyed registries, content-activated behaviour | **Dependency:** must be generated in CI. **Temporary fallback:** generated locally, committed with its source SHA, and marked `stale` when that SHA falls behind the changed files |
| **Dynamic test → file map** from coverage contexts ("who tests what") [R26], the dynamic-dependency approach of [R28] | what each test *actually executed*, incl. dynamic dispatch and runtime registration | code paths no test executes | Produced by the standing coverage job (§8) at a recorded SHA; nightly |
| Content / config rules | `data/worlds/**`, `config/**`, world-composition fields that activate mechanisms (Pattern 6, `docs/guidelines/design_patterns.md`; live case: `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`) | new content keys with no rule | authored |
| Behaviour ids (mechanism / law) | the behaviour → proof link (§10.1) | behaviours with no id | registry epic / ledger |

### 5.2 Output contract

For each change, the impact report lists:
- impacted domains and components, each with a **reason** (which input and which rule matched);
- recommended tests grouped by level, and the CI lanes that contain them;
- an explicit **`impact-unknown`** list (unmatched files, stale inputs).

Per behaviour, it reports **four separate columns: `selected` · `executed` · `passed` ·
`proves outcome`**. A change can be fully selected yet unproven.

**Fallback:** `impact-unknown` → run all core-RPG lanes and flag the change. Never a silent skip.

### 5.3 Fault-revealing test recall on sampled seeded faults

This metric is **fault-revealing test recall on a sample of seeded faults**. It is **not** a
project-wide completeness guarantee: a perfect score on the sample says nothing about unsampled
changes. The ground truth follows the safety notion of regression test selection [R27] and the
failure-recall framing of predictive selection [R29].

**Evaluation protocol:**
1. **Clean baseline.** Run the reference test population (the fast tier over all lanes) at the
   pinned SHA; record passes, failures and skips. Pre-existing failures are excluded from all later
   comparisons.
2. **One fault at a time.** Apply exactly one declared fault (a mutant at the changed site) on an
   isolated revision.
3. **Reference run.** Run the reference population. The tests that newly fail are the *expected
   set* for that fault.
4. **Compare.** Compare the model's selected tests with the expected set, and **separately** the
   CI lanes the path rules would trigger (§5.6).
5. **Classify each fault** as `usable`, `equivalent`, `invalid` (does not build or import),
   `timed-out`, `unreachable` (no test executes the site), or `undetected` (executed but no test
   fails). Only `usable` faults enter the recall figures.
6. **Report:**
   - test recall: selected ∩ expected / expected;
   - lane recall: lanes containing ≥1 expected test that are both selected and triggered / such lanes;
   - over-selection cost: selected tests not in the expected set, and their runtime;
   - unknown-impact handling: faults whose change the model marked `impact-unknown`, counted
     separately and never as hits;
   - the number of usable faults.

An `undetected` fault is a **possible** proof gap. It may also be an equivalent mutant or sit
outside the exercised path, so it is not classified as a confirmed test gap without review. The five
changes in §5.4 are an **initial validation sample** only.

### 5.4 Representative changes (the evaluation set)

| # | Change (category) | Expected domains / levels / lanes (reason) | Existing mapping finds it? [O, OV §8] |
|---|---|---|---|
| 1 | Damage constant in `src/engine/combat.py` (**local domain rule**) | combat: unit/component + value-differential scenario; lanes `Unit · gameplay`, `Perf / cert / arena` (declared rule + import) | Unit dir yes; scenarios only if the agent's grep finds them; CI lane yes (`engine` ∈ `PERF_RE`) |
| 2 | Pipeline phase / `AuthoritativeState` in `src/engine/pipeline.py`, `src/core/state.py` (**shared substrate**) | all core-RPG domains: component + kernel integration + outcome scenarios (substrate rule + import fan-out) | CI over-runs (safe); local selection is an unenumerated grep |
| 3 | XP reward on kill (**cross-domain**, combat → progression) | progression and combat: value-differential scenarios; cross-domain scenario (declared consumer edge, §4.1) | **No**: `src/progression/` misses `PERF_RE`; the combat-side consumer is in no map |
| 4 | World-composition field that seeds camp/cohort state in `data/worlds/*/world.yaml` or a recipe (**content / runtime activation**) | the affected domain's scenarios using that world + the corpus instrument for that world (content rule + coverage contexts) | **No rule anywhere**; the import graph cannot see it |
| 5 | Change to `src/systems/party.py` (**unmapped**: party is not assessed) | must yield `impact-unknown` + a full core-RPG lane run | Today: static backstop SKIP, silent |

### 5.5 Dynamic dispatch, generated content, runtime registration, indirect consumers

- **Dynamic dispatch and runtime registration** (string-keyed registries, lazily imported pipeline
  phases): covered by the coverage-context map, which records what executed, and conservatively by
  the substrate rule.
- **Generated or compiled content** (`WorldCompiler` output): mapped via the world id → the
  scenarios and corpus runs that load it.
- **Indirect consumers:** the declared consumer edges in §4.1, plus import fan-out.
- **Residual risk:** code executed by no test is invisible to every input. That is reported as a
  proof gap, not assumed covered.

### 5.6 Model selection vs lane trigger vs execution

Three facts are recorded separately for each recommended test:
1. **selected by the model**;
2. **its lane triggered by the CI path rules**;
3. **executed and passed** in that lane.

The model can recommend the right test while a path rule (today: `PERF_RE`) prevents its lane from
running. That shows up as `selected, not-triggered`, never as a pass. Lane-rule repair (R2) is a
separate deliverable from the model (M1).

---

## 6 · Deliverable C: Test-level contracts and reusable framework

### 6.1 Level contracts (draft)

| Level | Executed boundary | Resources | Expected-behaviour source | Oracle | Observation point | Harness | Isolation | Budget [I] | Placement / metadata | CI cadence |
|---|---|---|---|---|---|---|---|---|---|---|
| Unit / component | function or domain service on hand-built state | in-process | Bible formula / contract | exact value or law | return value; one `ApplyPath.apply_generation` | `V2EntityBuilder`, `tests/helpers/*` | conftest registry reset | < 1 s | `tests/unit/<component>/` + declared metadata (§10.2) | every PR |
| Kernel integration | real `Kernel` + profile + RNG, no compiler | in-process | kernel / pipeline contracts | state over N ticks | committed state, events | `tests/integration/kernel/test_minimal_kernel.py` pattern | fresh kernel | < 10 s | `tests/integration/<area>/` | every PR |
| Mechanic outcome scenario | `WorldCompiler` + `Kernel`, one mechanic | small compiled world | Bible law + proposal §3.3 | **occurrence and effect**, present vs absent | authoritative state delta | open-coded today → shared helper (gap) | world compiled per test | < 30 s | `tests/mechanic_scenarios/` | every **relevant** PR (§11, R2) |
| Cross-domain scenario | ≥2 domains in one real run | small compiled world | Bible chain | effect at each hop | state deltas per hop | same helper | same | < 60 s | `tests/mechanic_scenarios/` | every relevant PR, or nightly if over budget |
| Broad simulation | long runs / corpus | profiles, corpus worlds | balance intent, invariants | `HardLawMonitor` invariants; anchor tolerance bands | monitors, SimQ reports | certification harness, SimQ | per run | minutes | slow markers | nightly / on demand |

Budgets are proposals derived from one local `--durations` run (OV §4.3), not measured contracts.

### 6.2 Technique selection (criteria, not a mandate)

| Technique | Choose when | Not when |
|---|---|---|
| Example | a documented value for a formula or branch | the law must hold over ranges |
| Property [R10] | bounds, monotonicity, per-transaction conservation | a single documented value is the whole oracle |
| Stateful property [R20] | invariants across action *sequences* (inventory, gold, HP) | behaviour only means something in a compiled world |
| Metamorphic [R11] | relations between runs | while replay reliability is unverified (§6.3) |
| Characterization [R23] | complex output must not drift unnoticed, with deliberate re-approval | a simpler exact oracle exists. Not required per domain |

### 6.3 Replay reliability (explicit, separately verified condition)

- **Short-run reproducibility is proven:** `tests/integration/kernel/test_determinism_suite.py`,
  10 runs × 10 ticks, one seed [O].
- **Long-run determinism is parked** (census UNSTABLE [O]).
- A multi-seed sweep may claim only *invariants held per seed* plus a per-seed short-run
  reproducibility re-check. **Exact seed replay of a sweep failure is not promised** until a
  replay-reliability check exists with its own state in §8. [R21] describes the target, not the
  current state.

### 6.4 Smallest framework gaps

1. A shared scenario helper: compile world → stage entity → run N ticks → observe the effect, with
   present/absent arms.
2. A shared replay-diff helper.
3. Declared test metadata (§10.2).
4. A per-test `data/runs` cleanup fixture.
5. [D] Retire or adopt `src/testing/` and the unused CLI helpers (OV §9).

---

## 7 · Deliverable D: AI-first test workflow and pilot

### 7.1 Responsibility map (current stages in OV §5.1)

| Decision | Stage / role (existing) | Evidence recorded |
|---|---|---|
| Impact set | Investigate / `investigator` (+ the §5 report once it exists) | impact report or, before it exists, the listed domains and reasons |
| Level, technique, oracle, fixture, expected effect, negative cases, non-functional risk | Investigate / `investigator`, via **extended `test_plan.md` fields** | one row per acceptance criterion |
| Tests written | Implement / `implementer` | files changed |
| Commands selected | Test / `test-scoper` | command + reason per test |
| Quality review | **Existing `architecture-reviewer` at Architecture-Verify (`implement-ticket.js:999`), with an added explicit test checklist** (Test Desiderata [R9], smells [R13], `testing-anti-patterns.md` [R14]; diff-scoped, advisory) [RR] | checklist result + findings |
| Completion | Verify / `done-checker` checks the fields are present | DoD line |
| Epic | `implement-epic.js` unchanged; each child follows the above | — |

A new conditional phase or a dedicated test agent stays a **later option**, triggered only by an
observed shortcoming in the pilot [RR].

### 7.2 Pilot (progression) — mutation delta removed from the decision criteria

**Choice:** mutation delta is **not** a decision criterion. Five small tickets cannot produce an
attributable change in a module-level mutation score, and no comparable progression mutation
baseline exists yet. A narrow progression mutation run is kept as **separate supporting
evidence** (§11, M3a), with its own provenance, and is never read as a pilot result.
Pipeline/inventory mutation scores say nothing about this pilot.

| Item | Rule |
|---|---|
| Eligible ticket | Tier `hotfix` or `standard`; *Files Changed* touches `src/progression/**`, `src/domains/progression/**`, or their tests; **not** a child of `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`; touches none of that epic's files |
| Baseline | Up to the 10 most recent closed eligible tickets (pool: 42 `tickets/done/` files mention those paths [O]), scored with the same checklist, using their `stored_artifacts/<id>/test_plan.md` |
| Intervention start | The commit that lands the extended template + reviewer checklist; tickets opened after it are treatment |
| Window | 5 eligible tickets or 6 weeks, whichever first. **< 5 at 6 weeks:** extend once by 4 weeks. **< 3 after that:** `inconclusive`. If the starvation epic starts changing the same files, pause the clock and exclude the overlapping tickets |
| Size variance | Report per ticket, stratified by tier and files-changed count; no pooled averages |
| Cost | `tool_call_count` per phase from `events.jsonl`, **only for pipeline runs with real event data**. Hand-orchestrated backfills are flagged and excluded. `duration_s` is not used (70% zeros, OV §5.1) |
| Fields | **Mandatory** (every AC): impact domains, level, proof kind (§10.1), oracle source, expected effect, selected commands. **Optional** (when applicable): negative/edge cases, fixture choice, non-functional risk |
| Quality signals | Mandatory-field completeness; substantive reviewer findings and whether each was acted on; new proofs registered (§10.1); title-classified escapes in the following 30 days [P] |
| **Keep** | **100%** of mandatory fields filled on every treatment ticket; Investigate `tool_call_count` ≤ +20% vs the baseline median; **every substantive finding was acted on or explicitly declined with a reason**. A clean review (no findings) is a valid outcome and counts neither for nor against |
| **Revise** | Any mandatory field repeatedly missing; or cost > +20%; or substantive findings routinely ignored |
| **Inconclusive** | < 3 eligible tickets, or baseline artifacts missing for most baseline tickets |
| Threshold rationale [RR: present for review] | Mandatory means mandatory: completeness is 100% on mandatory fields, and optional fields are reported, not thresholded. +20% ≈ 4 extra calls on the Investigate median of 18.5 (OV §5.1). Findings are measured by *action on substantive findings*, not by count, so the reviewer is not pressured to invent findings |
| Cost-proxy limits | `tool_call_count` counts tool invocations only. It is not elapsed time, not tokens, and not model cost; call sizes vary. Treat it as a coarse relative signal |
| Interpretation | With 3–5 tickets, results are **directional**: no causal improvement or failure is claimed from the threshold table. Every `keep` / `revise` / `inconclusive` decision carries a short qualitative review (what the checklist caught, what was ignored and why, the author's burden) recorded alongside the measurements |
| Escalation | Consider a conditional review phase only if substantive findings are often ignored; consider a split test-writer only if the checklist repeatedly finds oracle defects the implementer does not fix |

---

## 8 · Deliverable E: Metric dictionary (before any scorecard)

**States:** `pass` · `fail` · `measured` · `drift-classified` · `skipped` / `skipped-no-data` ·
`not-run` · `blocked` · `unstable` · `stale` · `unknown`. Nothing defaults to 0 or pass.

| Report layer | Measure | Rule / denominator | Producer | Provenance, cadence | Limitations |
|---|---|---|---|---|---|
| Code executed | line + branch coverage per package; coverage contexts | covered / statements (`src/`) | standing coverage job (new; `make test-cov` fixed) | SHA, tier list, **failed-test list**; nightly | Execution ≠ assertion. The 2026-09-27 88% is a one-off, fast tiers, 8 failures |
| Behaviour specified and linked | evidence state per behaviour id | behaviour ids (§10.1) by state | ledger + registry scan | SHA; per PR | Ledger not schema-valid yet (§10.4) |
| Mechanism reached in real runs | reachability | reached / registered mechanisms | census + registry view | run id, worlds, ticks; on demand | `unstable` |
| Effect asserted ("proves outcome") | proof state by proof kind (§10.1) | gameplay behaviours with a **valid, non-stale review record** and a passing proof in their lane / gameplay behaviours in scope. **Architecture guards are reported in a separate architecture-evidence layer** | proof validator (review-record checks) + JUnit | SHA; per PR | A new proof counts only after its bounded first review |
| Faults detected | mutation score | killed / (killed + survived); timeouts and equivalents listed separately | `mutmut` [R12] on a declared target | **target, selected tests, SHA, date, runtime**; `stale` once the target changes or after 30 days | One-off baselines only |
| Corpus drift / findings | anchor-band results; drift classes | per run key × pillar (81 anchor comparisons = 79 parametrized + 2 named probe tests; OV §4.7) | SimQ tests; `/simq-audit` | calibration run id | PR state `skipped-no-data` today |
| Hygiene | order-dependence; lane fit; skip/xfail | random-order failures; tests over level budget | scheduled random-order job; `--durations` | SHA; weekly | RNG-contract check first |
| Fault-revealing test recall (sampled) | §5.3 | usable seeded faults; test recall, lane recall, over-selection cost, unknown count | seeded-fault protocol (§5.3) | SHA, fault list, per-fault class; per model change | A sample, not a project-wide guarantee |
| Lane trigger | selected-but-not-triggered count | recommended tests whose lane did not run / recommended tests | impact report × CI run | per PR | Separate from model recall (§5.6) |

**Scorecard host:** decided after this dictionary and an example output exist [RR].

---

## 9 · Behaviour-level dependency map (evidence rows)

**Row states:** `proven` · `partial` · `gap` · `blocked` · `not assessed`. A recorded gap is an
honest investigation result; it is **not** a delivered proof.

| # | Behaviour | State now | Next evidence | Level / lane | Prerequisites | Can start | Blocked by / owner |
|---|---|---|---|---|---|---|---|
| E1 | Mutation only via typed records | proven (**architecture evidence**, not a gameplay effect) | — (monitor) | architecture guard + integration / PR | — | — | this epic |
| E2 | Damage-law bounds / monotonicity (ch02) | partial (example + value-differential) | property test | component / `Unit · gameplay` | metadata (§10.2) for reporting only | immediately after M0a | — |
| E3 | XP-curve monotonicity (ch01) | partial | property test | component / `Unit · gameplay` | same | immediately after M0a | — |
| E4 | Per-transaction and sequence conservation (ch03) | partial (examples) | stateful property | component / `Unit · gameplay` | same | immediately after M0a | — |
| E5 | XP reward → level-up scenarios run on relevant PRs | partial (exist; not selected for `src/progression`-only PRs) | lane repair | scenario / `Perf / cert / arena` (or successor) | R2 | with R2 | this epic |
| E6 | Derived-stat recalc scenario on relevant PRs | partial (same) | lane repair | same | R2 | with R2 | this epic |
| E7 | Pursuit → opportunity attack: occurrence + (non-lethal) damage effect | gap | outcome scenario | scenario / relevant-PR lane | shared scenario helper (§6.4); R2 | after helper | this epic, using the proposal's harness |
| E8 | Harvest → inventory → market chain | gap | cross-domain scenario | scenario / relevant-PR lane | helper; R2 | after helper (independent of combat) | this epic |
| E9 | Quest completion → reward | gap | cross-domain scenario | scenario / relevant-PR lane | helper; R2 | after helper (independent of combat) | this epic |
| E10 | Crafting material predicates isolated | partial (order-dependent) | isolation repair | unit | R1 | with R1 | this epic |
| E11 | Decision-driven attack in real runs | blocked | none: a **core mechanic design decision**, outside this plan | — | the owner's decision on the `COMBAT_ENGAGE` dispatch finding (evidence: `tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md`, 2026-09-19 addendum) | — | **decision owner: the user (mechanic/spec owner)**. **Does not block M0–M3.** No test may approve the current discarded-goal behaviour as correct while the intended behaviour is undecided |
| E12 | Real-run XP volume | blocked | corpus-level evidence later | broad simulation | starvation epic; E11 | — | starvation epic |
| E13 | Party / group behaviours | not assessed | selection gate G-P: map entry points, maturity, spec | — | — | any time (investigation only) | this epic |
| E14 | Replay reliability for sweeps | gap | reliability check | broad simulation | determinism unparked | — | parked ticket |

What can proceed independently: **E2–E4 (pure laws), E8 and E9 (economy/quests) do not wait for
combat evidence**. E7 waits only for the helper and R2. E11–E14 are blocked or gated by named
owners.

---

## 10 · Proof derivation, metadata, and the parity evidence model

### 10.1 Proof kinds and how each is validated

"Proves outcome" is **not one contract**. Each proof declares a **kind**; the checks depend on the
kind.

| Proof kind | What the claim must state | Automated on every run | Bounded first-registration review |
|---|---|---|---|
| **Law / property** | documented law (Bible section), input domain, assumptions, asserted invariant, generated cases or examples | node collected, ran in its lane, passed; property tests record the generator settings and seed | does the invariant encode the law; is the input domain faithful; are the assumptions acceptable |
| **Stateful invariant** | action vocabulary, reachable-state description, invariant, failure-reproduction data (shrunk sequence, seed) | same, plus the reproduction data is emitted on failure | are the actions realistic; does the invariant match the law |
| **Mechanic outcome** | trigger, authoritative effect (state field(s)), and a negative/absence control **only where the claim needs one** (e.g. "fires only when X") | same | does the trigger actually occur (not staged away); is the effect authoritative state, not a log/event; is the control meaningful |
| **Cross-domain chain** | each required hop: observed transition and its effect | same | is every hop observed, not inferred from the endpoint |
| **Architecture guard** | the protected boundary and the violation it detects | same | does it detect a real violation (e.g. a seeded bad write) — **reported as architecture evidence, never as a gameplay effect** |

**Not claimed:** a static check (e.g. "imports `WorldCompiler` and `Kernel`") establishes only the
*level*, never semantic correctness. Semantics come from the review record plus, optionally, a
periodic seeded-fault check at the behaviour's `implemented_by` site.

**Review record.** A done ticket alone is insufficient. Each approval binds:

| Field | Content |
|---|---|
| `behaviour_id` | mechanism id or law id |
| `test_identity` | node id + file path + a stable test name |
| `test_revision` | content hash of the test function / module at approval |
| `oracle_revision` | Bible section id + that doc's commit/hash; for tolerance oracles, the anchor file hash |
| `harness_revision` | hash of the shared helper(s) the test relies on |
| `path_revision` | the `implemented_by` file hashes of the behaviour at approval |
| `proof_kind`, `reviewer`, `decision` (approved / rejected / conditional), `date`, `ticket` | — |

**Staleness:** the approval becomes `stale` when any of `test_revision`, `oracle_revision`,
`harness_revision` or `path_revision` changes materially. A trivial formatting change is excluded
by hashing normalized AST/text. Later reports validate the record **mechanically**: fields present,
hashes current, test passing in its lane. They do not re-read the test. A `stale` proof shows as
`stale`, not `proven`.

**One authority for the mechanism → test link:**
- **Now:** the claim lives in in-test metadata, and the review record lives in a planner-proposed
  location, reported by this epic.
- **When the registry epic ships its canonical link:**
  1. a one-time reconciliation maps every in-test claim onto the registry link;
  2. conflicts are listed for the owner;
  3. the registry becomes the authority, and in-test metadata is reduced to a reference to the
     registry entry;
  4. a consistency check flags any in-test claim that has no matching registry link.
- Two independent authorities never persist past the reconciliation.

### 10.2 Test-metadata migration scope (staged)

The inventory (OV §10: 204 candidates, 89 agreeing signals, ~115 uncertain, 579 substrate-only, 7
multi-domain) is a **future implementation inventory**. This planning revision does not inspect
test files one by one.

| Stage | Scope | Rule |
|---|---|---|
| S1 | **New and modified** core-RPG tests | Metadata required (advisory check, then blocking once S2 lands) |
| S2 | Existing core-RPG candidates with agreeing signals (~89) | Auto-*proposed* labels, confirmed in bulk by domain owner review; never inferred silently |
| S3 | Uncertain candidates (~115) | Classified in domain-sized batches. Anything left unresolved stays `classification uncertain` |
| S4 | Multi-domain tests (7 by import) | Declare **all** domains plus a primary domain; reported under each declared domain as `multiple domains` |
| S5 | Substrate-only importers (579) | **Out of scope** for domain metadata unless the test is *about* the substrate (e.g. `tests/unit/core/`, `tests/integration/pipeline/`), which then gets `domain = substrate` |
| — | Everything else | `out of scope` or `unclassified`; both stay visible in the baseline |

**Consistency:**
- Metadata lives in the test file, so it moves with the file.
- A check compares the declared domain with the file's imports and directory, and flags
  disagreement for review. It is never auto-corrected.
- An ownership change edits the marker in the same PR.

### 10.3 Relevant-PR definition for mechanic scenarios

A PR is **relevant** if any changed path matches:
- (a) core-RPG source: `src/{core,engine,platform,entities,progression,economy,quests,systems,domains,worldbuilding,worldassembly,content}/**`;
- (b) test infrastructure: `tests/mechanic_scenarios/**`, `tests/helpers/**`, `tests/conftest.py`;
- (c) content / config: `data/worlds/**`, `config/**`;
- (d) execution environment: `requirements*.txt`, `pyproject.toml`, `.github/workflows/test.yml`.

**Fallback [I]:** any `src/**` path not in (a) counts as **relevant** (fail-open). A PR is
irrelevant only if it touches exclusively `docs/`, `tickets/`, `agent-monitoring/`, `tools/`,
`frontend*/`, `dashboard-frontend/`, or `tmp/`. Cost is small: 44 tests taking seconds (OV §3).

### 10.4 Parity evidence model

- Keep **P0 = importance** as the schema defines it.
- Add a *derived* evidence state (`test_linked` / `audit_only` / `legacy` / `missing`), computed and
  reported, never hand-set [RR].
- **Before any enforcement:** record the categorized baseline (OV §4.6: 2,842 `test_path` type
  errors + 25 `proof_type` enum errors across 1,561 entries) as a committed snapshot. New
  violations are then measured against it.

---

## 11 · Milestones (proposal — awaiting review)

| Milestone | Outcome | Dependencies |
|---|---|---|
| **M0a As-is baseline** | Reproducible inventory and measurements at a pinned SHA, with failures, skips, missing data and lane gaps visible (validity table below) | none |
| **R1 Progression isolation repair** | States: `verified` (combined + isolated + random-order pass) · `provisional` (combined + isolated pass; random order awaits the RNG-contract check) · `blocked/failed` | none |
| **R2 Mechanic-scenario PR selection** | Scenarios run on every relevant PR (§10.3) | none; owner: this epic (lane contract), delivered via a CI change |
| **R3 SimQ skip visibility** | Anchor tests report `skipped-no-data` visibly | owner: SimQ; **not on the core-RPG critical path**; never a prerequisite for M0a/M0b |
| **M0b Post-repair baseline** | Same measures after R1 + R2; scope changes documented. A *provisional post-R2 report* may be generated earlier and labelled as such; M0b **closes only when R1 is `verified`** | R1 `verified`, R2 (R3 **not** a prerequisite) |
| **M1 Impact model v0** | §5 report + seeded-fault evaluation on the 5 changes | M0a; import graph (CI-generated, or the committed fallback); coverage contexts from the standing coverage job |
| **M2 Workflow pilot** | §7.2 | R1 (trustworthy signals); M0a |
| **M3a Pure-law evidence** | E2, E3, E4 as property / stateful tests + a narrow progression mutation baseline as supporting evidence | M0a; metadata for reporting |
| **M3b Outcome scenarios** | Shared helper; E7, E8, E9 | R2 |
| **G-P Party selection gate** | E13 assessment → decide whether party enters a batch | none |
| Separate paths | parity evidence (§10.4), cleanup, API/UI | owner decisions / demonstrated dependency |

**M0a validity table:**

| Measure | Validity with the leak present |
|---|---|
| Inventory, lane map, path-filter gaps, metadata inventory, parity categories, SimQ skip as a finding | **valid** |
| Line coverage per package | **valid**, qualified: failing tests still executed code, listed alongside |
| `src/domains/progression` coverage and combined pass counts | **qualified** (includes the 7 failing tests) |
| Extent of order-dependence, current SimQ drift, mutation strength | **cannot be determined** in M0a (need a random-order run, a calibration run, and mutation runs) |

## 12 · Decision log

| Topic | Owner-approved (2026-09-28) | Reviewer recommendation [RR] | Default planning assumption | If the other option is chosen | Earliest milestone blocked |
|---|---|---|---|---|---|
| Core-RPG order | D10: domain by domain from progression | substrate → movement/combat → progression as an **evidence** dependency; pure-law work earlier; party gated | Follow §9 rows; the pilot stays on progression | A strict domain sequence delays E2–E4, E8, E9 | none (§9 works either way) |
| Parity | D7: re-tier P0 → P1 | derived evidence state; keep P0 = importance | RR | Re-tiering erases importance history | Parity path only |
| API / UI | D8: "API now" | separate, dependency-gated path | RR | API work displaces core RPG | none |
| SimQ / census / audits | — (D11 pending) | separate instrument layers and states | RR | Corpus questions unowned | M0a report layout |
| Scorecard host | D1: codebase-health | decide after the dictionary + an example output | RR | Per-domain drill-down missing | none before M0a output |
| Scenario ownership | — | this epic: lane/selection contract; initiative: families; CI repair owner named | R2 owned by this epic | Scenario PR gap persists | R2 |
| Mechanism → test link | — | registry epic owns it; this roadmap consumes and validates | RR | Duplicate link systems | §10.1 full form (interim: in-test metadata) |
| Test-review insertion | D9 (A → B → C) | existing reviewer checklist first | RR | Earlier phase/agent cost | M2 |
| Pilot thresholds | — | present the §7.2 values | §7.2 values | Owner-set values | M2 start |
| Changed expected outcomes | — | named spec owner + recorded approval; agents cannot re-approve | owner = user | — | M3b (first new scenario expectations) |
| `COMBAT_ENGAGE` dispatch finding | — | — | treated as blocked (E11) | — | E11 only |
| D3, D4, D5, D6 (delete intent), D9 | Owner-approved | — | kept; D6 on the cleanup path with a prerequisite inventory | — | — |

## 13 · Separate paths

| Path | Prerequisites |
|---|---|
| Cleanup (`agent_codex_*`, `src/testing/`, SimQ narrow tests, doc-text tests, duplicate directories) | Per target: record importers, Makefile/CI references, plan/ticket references. LOC ratio is not a criterion. Owner decision per deletion |
| API / UI | A core-RPG behaviour shown to cross the API boundary. Then: OpenAPI snapshot, Schemathesis [R19], raw-model guard. Frontend after the HUD sequencing rule |
| Parity evidence | §10.4 baseline → derived state → schema validation of the corpus |

## 14 · Out of scope

Scenario-family design; census and registry internals; the determinism root cause; SimQ scoring
and anchors; reviewing individual tests; the `COMBAT_ENGAGE` design decision.

## Appendix · Old directions → current sections

D1/D2 → §8, §9 · D3/D10 → §6.2, §9 · D4 → §8, §11 M3a · D5 → R1, §8 hygiene · D6/D8 → §13 ·
D7 → §10.4 · D9 → §7 · D11 → §2, §8.

## 15 · References

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
| R26 | coverage.py "Measurement contexts" (who-tests-what, dynamic contexts) — https://coverage.readthedocs.io/en/latest/contexts.html | Dynamic test → file map (§5.1) |
| R27 | Rothermel & Harrold, "A Safe, Efficient Regression Test Selection Technique", ACM TOSEM 6(2) 1997 — https://dl.acm.org/doi/10.1145/248233.248262 | Safety: fault-revealing tests as ground truth (§5.3) |
| R28 | Gligoric, Eloussi, Marinov, "Practical Regression Test Selection with Dynamic File Dependencies" (Ekstazi), ISSTA 2015 — https://dl.acm.org/doi/10.1145/2771783.2771784 | Dynamic dependencies for selection (§5.1) |
| R29 | Machalica, Samylkin, Porth, Chandra, "Predictive Test Selection", ICSE-SEIP 2019 — https://arxiv.org/abs/1810.05286 | Failure-recall framing of selection quality (§5.3) |
