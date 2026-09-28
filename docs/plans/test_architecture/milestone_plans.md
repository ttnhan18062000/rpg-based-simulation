---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture — Detailed Milestone Plans (draft for review)

**Status: DRAFT 2026-09-28, for reviewer assessment.** This document derives from
[`test_architecture_epic.md`](test_architecture_epic.md) (revision d) and
[`current_test_system_overview.md`](current_test_system_overview.md) (OV). **No tickets exist.** A
separate ticket planner turns accepted milestones into tickets; §10 of each plan only *suggests*
ticket boundaries.

**Inspected code:** `04f911110`; unchanged in test, `src/`, CI and agent files through
`origin/main` `9bcae32c5`. **Labels:** [O] observed · [H] historical · [I] inference (includes
every proposed location, name and budget below) · [RR] reviewer recommendation · [D] owner
decision.

**Milestones planned here:** M0a · R1 · R2 · M0b · M1 · M2 · M3a · M3b · G-P.
**Kept separate (§10 at the end):** R3 (SimQ skip visibility, SimQ-owned) · parity evidence ·
cleanup · API/UI · replay-dependent techniques · E11.

**Dependency sketch** (behaviour-level; no forced M3a → M3b order):

```
M0a ─┬─► M1 (needs the coverage job + import-graph input)
     ├─► M2 (also needs R1 ≥ provisional)
     └─► M3a (E2, E3, E4)
R1 ──┬─► M0b (closes on R1 verified) ◄── R2
     └─► M2
R2 ──┴─► M3b (E7, E8, E9; also needs the shared scenario helper, built inside M3b)
G-P: independent
```

---

## M0a · As-is baseline

1. **Outcome and scope.** A reproducible, generated core-RPG report at a pinned SHA that shows the
   current state *including* failures, skips, missing data and lane gaps. Architecture level only;
   no test is changed.
2. **Inputs available today.**
   - [O] Inventory scripts' rules (OV §2, §10).
   - CI JUnit per job (`reports/junit/*.xml`, `.github/workflows/test.yml`).
   - The coverage command and scope (OV §4.1).
   - The parity schema-error categories (OV §4.6).
   - Lane path rules (`test.yml:620-655`).
   - SimQ skip behaviour (OV §4.7).
   - Behaviour rows E1–E14 (epic §9).
3. **Deliverables** [I locations]:
   - a report producer (proposed `tools/test_architecture/core_rpg_report.py`);
   - its output schema (JSON + rendered markdown) under `reports/test_architecture/<sha>/`;
   - a standing CI coverage job (nightly: line + branch + coverage contexts) plus a fixed
     `make test-cov`;
   - a committed parity-baseline snapshot (input for the separate parity path, produced here
     because it's cheap).
4. **Dependencies and owners.** None upstream. Owner: this epic. SimQ state is read, not changed
   (SimQ owner). Ledger and registry are read-only.
5. **Work packages (in order).**
   1. Report schema: layers from epic §8, the state vocabulary, and a denominator field on every
      count.
   2. Inventory + classification layer (directory / import signals; no manual labels).
   3. Lane layer (path rules → which jobs would run for a path category).
   4. Standing coverage job + `make test-cov` fix; the report ingests its artifact.
   5. Parity evidence-state derivation (read-only) + baseline snapshot.
   6. SimQ and census state ingestion (states only).
   7. Normalization rules for reproducibility (see 7).
6. **Automated evidence.**

| Layer | Producer | Denominator | Provenance | Missing-data state |
|---|---|---|---|---|
| Inventory / classification | report producer | 1,484 test files; 204 core-RPG candidates | SHA | `classification uncertain`, `unclassified` |
| Package line + branch coverage | coverage job | statements per package | SHA, tier list, failing-test list | `not-run` |
| Domain coverage | — | — | — | **`not-derived`** (no defensible code → domain map yet) |
| Lanes | producer over `test.yml` | path categories | SHA | — |
| Law evidence state | producer over the ledger | 2,190 entries / 1,685 P0 | SHA | — |
| Behaviour rows E1–E14 | producer (row states, epic §9) | 14 rows | SHA | `not assessed` |
| SimQ anchors | JUnit | 81 comparisons | run id | `skipped-no-data` |
| Census | — | — | — | `unstable` |
| Mutation / hygiene order-dependence | — | — | — | `not-run` |

7. **Acceptance criteria.**
   - Running the producer twice at the same SHA gives **identical normalized data and
     classifications**; timestamps, job ids and durations are excluded from the comparison.
   - Every layer shows either a value with its denominator or an explicit state.
   - The 8 known failing tests are listed, and any coverage figure carries the scope label.
   - Domain coverage shows `not-derived` rather than a relabelled package figure.
   - The progression package is marked `qualified`.
8. **Failure / blocked / provisional / inconclusive.**
   - **Failed:** normalized outputs differ between two runs at one SHA.
   - **Provisional:** the coverage job isn't landed yet, so coverage comes from a documented local
     run marked `local`.
   - **Not inconclusive merely because the 7 progression tests fail.** Only their package's figures
     are `qualified`.
9. **CI / runtime cost.** The fast-tier coverage run took about 17 min locally on 6 cores (OV §4.1);
   nightly only. The producer is a static scan, expected under 1 min [I]. **Validate:** time one
   nightly run and one producer run; record both in the report.
10. **Ticket-planner handoff.** Suggested boundaries:
    - (a) report schema + producer skeleton + inventory layer;
    - (b) coverage job + `make test-cov`;
    - (c) parity evidence-state + baseline snapshot;
    - (d) SimQ/census state ingestion.

    Order: a → (b, c, d in parallel).

## R1 · Progression isolation repair

1. **Outcome and scope.** Remove the shared-state leak that makes 7 tests in
   `tests/unit/domains/progression/` fail in combined runs (OV §4.2).
2. **Inputs.**
   - The failing node ids.
   - Reproduction: pass alone; fail inside the combined command (OV §4.2).
   - Registry-reset plumbing in `tests/conftest.py`.
3. **Deliverables.** The fix (test fixture or source), plus a regression guard that runs the 7
   tests after a representative polluting subset.
4. **Dependencies and owners.** None. Owner: this epic. Must not touch the starvation-chain epic's
   files; if the leak's source is in them, coordinate first.
5. **Work packages.**
   1. Bisect the polluting test (a standard order-dependency search).
   2. Identify the leaked state (likely a registry).
   3. Fix at the source of the leak; don't reorder tests.
   4. Add the guard.
   5. RNG-contract check for `pytest-randomly` (reseeding vs `DeterministicRNG`,
      `tests/unit/core/test_rng_contract.py`).
   6. Random-order run of the directory.
6. **Evidence.** JUnit for the combined, isolated and random-order runs at one SHA; R1 state in the
   report.
7. **Acceptance criteria.** `verified` = combined + isolated + random-order all pass at one SHA.
8. **States.**
   - `provisional`: combined + isolated pass, random order awaits the RNG check.
   - `blocked`: the leak originates in starvation-epic files pending coordination.
   - `failed`: any required run fails.
9. **Cost.** The combined subset reproduces the failure in about 17 min (full fast tier);
   narrowing by bisection is expected to cut this to minutes [I]. **Validate** by recording the
   minimal reproducing set's runtime.
10. **Handoff.** One ticket (bisect + fix + guard), plus one small ticket for the RNG-contract check
    and random-order run.

## R2 · Mechanic-scenario PR selection

1. **Outcome and scope.** Mechanic scenarios run on every **relevant** PR (epic §10.3), using the
   fail-open fallback. This is a lane-rule repair only; the M1 model is separate (epic §5.6).
2. **Inputs.**
   - `PERF_RE` and the `perf-cert-arena` job (`test.yml:620-696`).
   - Evidence that the job was skipped on sampled PR runs [O].
   - Scenario count and runtime (44 tests; up to about 28 s per test in local `--durations`, OV §4.3).
3. **Deliverables** [I]: either a dedicated `mechanic-scenarios` job or a widened filter, whose
   trigger is the §10.3 categories plus the fail-open rule; plus a lane-rule test (fixture diffs →
   expected trigger).
4. **Dependencies and owners.** Owner: **this epic** (lane contract, [RR]); delivered as a CI change
   through the normal delivery process. The scenario initiative owns scenario content.
5. **Work packages.**
   1. Encode the path categories.
   2. Choose between a dedicated job and a widened filter (a dedicated job avoids running
      perf/cert on core-RPG PRs).
   3. Lane-rule fixture test.
   4. Observe it on real PRs.
6. **Evidence.** Per PR: the path category matched, whether the job triggered, and scenario JUnit.
   Report layer: "relevant PRs, and scenarios ran on m / n".
7. **Acceptance criteria.**
   - The fixture test passes: `src/progression/**`, `src/entities/**`, `src/systems/**`,
     `tests/mechanic_scenarios/**` and `data/worlds/**` trigger; docs/tickets-only diffs don't.
   - On real PRs over the observation window, every relevant PR ran the scenarios (m = n).
8. **States.**
   - `provisional`: the fixture test passes but no relevant PR has occurred yet.
   - `failed`: any relevant PR skipped.
9. **Cost.** Scenario lane wall time roughly 1–3 min per PR [I, from per-test durations]; PR wall
   time today is 7–9 min with parallel jobs [O]. **Validate** by recording the lane duration over
   the first 10 PRs.
10. **Handoff.** One ticket: rule + job + fixture test.

## M0b · Post-repair baseline

1. **Outcome and scope.** The M0a measures re-run after R1 and R2, with every difference explained.
2. **Inputs.** The M0a report and the R1/R2 results.
3. **Deliverables.** The M0b report plus a diff note (scope changes, e.g. the scenario lane now
   triggered).
4. **Dependencies.** R2 done; **closes only when R1 is `verified`**. R3 is **not** a prerequisite.
   A *provisional post-R2 report* may be produced earlier, labelled `provisional`.
5. **Work packages.** Re-run the producer at the post-repair SHA; explain the diff line by line.
6. **Evidence.** The same layers as M0a; progression is no longer `qualified` if R1 is `verified`.
7. **Acceptance criteria.** Every M0a → M0b difference is attributed to a repair, a scope change or
   code drift. There is no unexplained change.
8. **States.**
   - `provisional`: R1 is still `provisional`.
   - `blocked`: R1 is `blocked`.
9. **Cost.** Same as M0a.
10. **Handoff.** Folded into the M0a producer ticket's follow-up, or one small ticket.

## M1 · Change-impact model v0

1. **Outcome and scope.** The impact report (epic §5.2) with reasons, `impact-unknown` and the four
   status columns, validated by the seeded-fault protocol (epic §5.3) on the 5 sample changes
   (§5.4). Component → domain granularity; the mechanism tier is deferred.
2. **Inputs.**
   - The declared domain map (epic §4.1).
   - The static import graph. **Dependency:** a CI-generated graph. **Fallback:** a local graph
     committed with its source SHA and marked `stale` when behind.
   - Coverage contexts (who-tests-what) from the M0a nightly job [R26][R28].
   - The content rules (§5.1).
3. **Deliverables** [I]:
   - a producer (proposed `tools/test_architecture/impact.py`) with a JSON output per changed-path
     set;
   - an agent-readable rendering for `investigator` and `test-scoper`;
   - an evaluation harness applying the §5.3 protocol;
   - an evaluation record per fault.
4. **Dependencies and owners.** M0a (coverage contexts, classification). Mechanism ids come from the
   registry epic when available. Owner: this epic.
5. **Work packages.**
   1. Rule model (paths → components → domains).
   2. Import-graph input + staleness state.
   3. Coverage-context input.
   4. Content/config rules.
   5. Output contract incl. `impact-unknown`.
   6. Seeded-fault harness (clean baseline → one fault per isolated revision → reference run →
      classify).
   7. Evaluate the 5 changes.
   8. Lane trigger vs selection report (§5.6).
6. **Evidence.** Per fault: class (usable / equivalent / invalid / timed-out / unreachable /
   undetected), expected set, selected set, triggered lanes. Aggregates: test recall, lane recall,
   over-selection cost, unknown count, number of usable faults.
7. **Acceptance criteria.**
   - Change 5 (party, unmapped) yields `impact-unknown` and the full core-RPG lane recommendation.
   - For changes 1–4, **lane recall = 100% on usable faults**, with test recall reported.
   - Changes 3 and 4 (cross-domain, content activation) are found by a rule or by coverage
     contexts, not by chance.
   - At least one usable fault per change 1–4.
   - `undetected` faults are listed as *possible* proof gaps, not counted as test gaps.
8. **States.**
   - `provisional`: the import graph comes from the committed fallback.
   - `inconclusive`: fewer than 4 usable faults across changes 1–4.
   - `failed`: lane recall < 100% on a usable fault, or change 5 not flagged.
9. **Cost.** Each fault needs a reference run of the fast tier (about 17 min locally) → 5–10 faults
   ≈ 1.5–3 h per evaluation [I]. Run on demand, not per PR. **Validate** by timing the first
   fault; consider restricting the reference population to core-RPG lanes if cost dominates, and
   record that restriction.
10. **Handoff.** Suggested order:
    - (a) rule model + output contract;
    - (b) import graph + coverage-context inputs;
    - (c) content rules;
    - (d) seeded-fault harness + evaluation;
    - (e) agent rendering wired into `investigator` / `test-scoper` prompts, **after** (d) passes.

## M2 · AI-first workflow pilot (progression)

1. **Outcome and scope.** Test the extended `test_plan.md` fields and the reviewer checklist on
   eligible progression tickets (epic §7.2), then decide keep / revise / inconclusive with a
   qualitative review. No new phase or agent.
2. **Inputs.**
   - The baseline pool: 42 `tickets/done/` files mention the progression paths [O]; their
     `stored_artifacts/*/test_plan.md`.
   - `events.jsonl` `tool_call_count`.
   - The Architecture-Verify stage (`implement-ticket.js:999`).
3. **Deliverables** [I]:
   - the template field change (investigator prompt, `investigator.md:153-191`);
   - the reviewer checklist text (in `architecture-reviewer.md`, applied to changed tests, advisory);
   - a pilot record per ticket;
   - a final pilot report.
4. **Dependencies and owners.**
   - **R1 ≥ `provisional`**, so test signals are trustworthy. M0a supplies the baseline report.
   - M1 is **not** required; the impact report is used if it exists.
   - Owner: this epic. Agent/workflow files change only through the pilot's own ticket.
5. **Work packages.**
   1. Freeze eligibility rules and the baseline set.
   2. Score the baseline tickets with the checklist.
   3. Land the template + checklist; record the intervention commit.
   4. Run the window.
   5. Record per ticket.
   6. Final decision with a qualitative review.
6. **Evidence.** Per ticket:
   - mandatory-field completeness;
   - optional fields present;
   - substantive findings and whether each was acted on or declined with a reason;
   - `tool_call_count` per phase (pipeline runs only; backfills flagged);
   - proofs registered.
7. **Acceptance criteria.** The pilot **completes** when a keep / revise / inconclusive decision is
   recorded with its measurements and qualitative review. The decision is directional (3–5
   tickets), and no causal claim is made.
8. **States.**
   - `inconclusive`: fewer than 3 eligible tickets after the extension, or most baseline artifacts
     are missing.
   - Paused: the starvation epic overlaps the surface.
   - `blocked`: R1 `blocked`.
9. **Cost.** The added Investigate effort is bounded by the +20% `tool_call_count` criterion.
   `tool_call_count` is a coarse proxy, not elapsed time or tokens. **Validate** by comparing
   per-phase calls on the baseline vs treatment tickets that have real event data.
10. **Handoff.** Two tickets:
    - (a) baseline scoring + eligibility freeze (read-only);
    - (b) template + checklist change (the intervention).

    The pilot record and decision are process outputs, not tickets.

## M3a · Pure-law and invariant evidence

1. **Outcome and scope.** New law evidence for E2 (damage-law bounds/monotonicity, ch02), E3
   (XP-curve monotonicity, ch01) and E4 (conservation per transaction and over action sequences,
   ch03).
2. **Inputs.**
   - Bible chapters 01–03.
   - The existing example tests (e.g. `tests/unit/resource/`,
     `tests/integration/kernel/test_resource_conservation.py`).
   - Hypothesis, installed but unused [O].
3. **Deliverables.**
   - Property tests (E2, E3) and a stateful property test (E4) with in-file metadata and review
     records (epic §10.1).
   - A narrow progression mutation baseline (`mutmut`) with a provenance record, as **supporting
     evidence only** (not a pilot measure, not a close criterion).
4. **Dependencies and owners.** M0a, for reporting and metadata. **Independent of M3b, R2 and
   combat real-run evidence.** Owner: this epic. The spec owner approves oracle interpretations.
5. **Work packages.**
   1. Law statements extracted with Bible section ids.
   2. E2 property test.
   3. E3 property test.
   4. E4 stateful machine (action vocabulary: harvest / craft / trade / consume).
   5. Review records.
   6. Supporting mutation baseline.
6. **Evidence.** Proof states by kind (law/property for E2 and E3; stateful invariant for E4) in the
   effect-asserted layer; the mutation record (target, tests, SHA, date, runtime, killed / survived
   / timeout / equivalent).
7. **Acceptance criteria (close).**
   - **E2, E3 and E4 are each `proven`**: a passing test in the `Unit · gameplay` lane plus a
     current, approved review record of the correct proof kind.
   - A recorded gap does **not** close M3a.
   - The mutation baseline exists with provenance (a supporting deliverable; no score threshold).
8. **States.**
   - `blocked`: a law is ambiguous in the Bible → spec-owner decision.
   - `provisional`: tests pass but the review is pending.
   - `failed`: the property finds a real law violation. That's a valuable finding: it becomes a
     defect ticket, and the row stays `gap` until fixed.
9. **Cost.** Property tests are small (< 1 s each, a bounded Hypothesis example count) [I];
   stateful tests up to about 10 s. Mutation on narrow progression modules: minutes to an hour [I].
   **Validate** by recording the Hypothesis settings and actual runtimes; cap examples if the unit
   lane budget is exceeded.
10. **Handoff.** Three independent proof tickets (E2, E3, E4) plus one supporting mutation ticket;
    no mutual ordering.

## M3b · Real-run outcome and chain evidence

1. **Outcome and scope.** New outcome proofs for E7 (pursuit → opportunity attack: occurrence plus
   the non-lethal damage effect), E8 (harvest → inventory → market chain) and E9 (quest completion
   → reward chain), plus the shared scenario helper (epic §6.4 gap 1).
2. **Inputs.**
   - Existing scenario patterns (`tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py`,
     proposal §3.3).
   - Call sites `src/engine/movement.py:240-242` and `src/engine/combat.py`.
   - Economy/quest code paths (epic §4.1).
3. **Deliverables.**
   - The shared helper (compile → stage → run N ticks → observe; optional control arm).
   - Three proofs: E7 **mechanic outcome**; E8 and E9 **cross-domain chain**, with review records.
4. **Dependencies and owners.**
   - **R2**, so the proofs run on relevant PRs.
   - The helper is built inside M3b first.
   - E7, E8 and E9 are **mutually independent**, and **independent of M3a**.
   - The scenario initiative owns families; this epic uses its harness pattern.
   - E11 is excluded: no proof may approve the discarded `COMBAT_ENGAGE` behaviour.
5. **Work packages.**
   1. Shared helper.
   2. E7 scenario, with a control only if the claim needs one (e.g. no opportunity attack without
      disengagement).
   3. E8 chain, with an observation at each hop.
   4. E9 chain.
   5. Review records.
6. **Evidence.** Proof states (mechanic outcome, chain); scenario-lane JUnit per relevant PR.
7. **Acceptance criteria (close).**
   - **E7, E8 and E9 each `proven`**: passing in the relevant-PR scenario lane, with a current
     approved review record of the correct kind.
   - Each chain proof observes every hop, not only the endpoint.
   - A recorded gap does not close M3b.
8. **States.**
   - `blocked`: the Bible's opportunity-attack or economy rule is ambiguous → spec owner; or R2 not
     done.
   - `provisional`: review pending.
   - `failed`: the scenario shows the behaviour does not occur. That becomes a defect ticket, and
     the row stays `gap`.
9. **Cost.** Each scenario is bounded at < 30 s (chains < 60 s) per epic §6.1 [I]. Three proofs add
   roughly 1–2 min to the scenario lane. **Validate** by measuring in the lane; move a chain to
   nightly if it exceeds the budget, and record the move.
10. **Handoff.** Order: helper first; then E7, E8 and E9 as three independent tickets.

## G-P · Party selection gate

1. **Outcome and scope.** An **assessment** of party/group, plus an owner go/no-go on whether it
   enters an evidence batch. No implementation maturity is presumed.
2. **Inputs.** `src/systems/party.py`, `src/systems/social_systems/party*.py`,
   `group_service.py` [O]; any Bible or plan references to party (to be searched).
3. **Deliverables.** An assessment note:
   - runtime entry points (kernel phase / pipeline phase);
   - spec source (or its absence);
   - active / partial / planned / deferred maturity, with evidence;
   - existing tests;
   - dependencies on other domains;
   - a recommended E13 row.
4. **Dependencies.** None. Owner: this epic (assessment); the owner decides go/no-go.
5. **Work packages.**
   1. `search_docs` + registry lookup.
   2. Trace the entry points.
   3. Check for real-run activity using existing evidence (census reports, if any).
   4. Write up the assessment.
   5. Owner decision.
6. **Evidence.** The filled E13 row, with evidence labels.
7. **Acceptance criteria.** The assessment covers every field in item 3, and the owner decision is
   recorded (go / no-go / defer).
8. **States.** `inconclusive` if the entry points can't be traced without runtime instrumentation.
   That is recorded, with the instrumentation need stated.
9. **Cost.** Read-only investigation; no CI cost.
10. **Handoff.** One investigation ticket.

---

## 10 · Separate paths (not planned in detail here)

| Path | Why separate | Next step |
|---|---|---|
| **R3 SimQ skip visibility** | SimQ owner; not a core-RPG prerequisite | SimQ owner schedules; this epic only reads its state |
| **Parity evidence model** | Needs the owner's D7 re-decision | The baseline snapshot is already produced in M0a (cheap); derived state and corpus validation after the decision |
| **Cleanup** (`agent_codex_*`, `src/testing/`, SimQ narrow tests, doc-text tests, duplicate directories) | Off the core-RPG path | Per-target consumer and CI inventory before any owner deletion decision |
| **API / UI** | No demonstrated core-RPG dependency | Re-open when a dependency is shown |
| **Replay-dependent** (metamorphic tests, exact-replay sweeps, E14) | Determinism parked | Wait for the parked ticket |
| **E11 decision-driven attack** | Core mechanic design decision | Owner decides; no test may encode the current behaviour as correct |
