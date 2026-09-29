---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture — Detailed Milestone Plans (revision e, for review)

> **NON-BINDING REFERENCE (2026-09-29).** This document is investigation and design material kept
> for the detail planner and implementer agents. The **binding** plan is
> [`../roadmap.md`](../roadmap.md) plus the four epic tickets in
> `tickets/todos/test-architecture/`. Where this document is more specific than those, treat it as a
> suggestion, not a commitment. Decisions marked here remain **pending** unless the roadmap says
> otherwise.


**Status: DRAFT 2026-09-29h, reviewable; decisions PENDING** (g: deferrals per owner direction; see epic status) (revision f: R2 `tools/` mapping, freshness split, quarantine enforcement, evidence classification, MT scope; ticket outlines in (ticket outlines removed; see ../../../../tickets/todos/test-architecture/)). Centred on test architecture and operations, following the owner's
scope clarification: feature teams own mechanic behaviour and feature proofs (epic §1). Derived
from [`architecture_design_notes.md`](architecture_design_notes.md) and
[`current_test_system_overview.md`](current_test_system_overview.md) (OV). **No tickets exist**;
item 10 of each plan only suggests boundaries for the ticket planner.

**Inspected code:** `04f911110` (unchanged in test, `src/`, CI and agent files through `origin/main`
`9bcae32c5`). Every proposed tool name, file location and budget is **[I]**.

**Acceptance philosophy:** milestones close on **operational capabilities observed in use**
(register, locate, run, review, invalidate, report, route), never on a count of feature proofs. A
recorded gap is honest output, but it never satisfies a capability criterion.

```
M0a ──┬──► MT ──┬──► M1 (+ coverage job from M0a)
      │         └──► M2 ──┐
      ├──► MF ────────────┼──► MP (bounded pilot; + R2; M1 optional)
R1 ───┴──► M0b ◄── R2 ────┘
G-P deferred (party oracle and owner unknown)
```

---

## M0a · As-is baseline

1. **Outcome and scope.** A generated core-RPG test report at a pinned SHA that makes the current
   state visible: failures, skips, missing data, lane gaps.
2. **Inputs available today.**
   - [O] Inventory rules (OV §2, §10); CI JUnit per job; lane rules (`test.yml:620-655`).
   - The coverage command and its scope (OV §4.1); parity error categories (OV §4.6).
   - SimQ skip behaviour and anchor populations (OV §4.7).
3. **Deliverables** [I]:
   - a report producer (e.g. `tools/test_architecture/core_rpg_report.py`);
   - its output under `reports/test_architecture/<sha>/`: JSON with a versioned schema, plus
     markdown;
   - a standing nightly coverage job (line + branch; **per-test contexts deferred**) and a fixed
     `make test-cov`;
   - a parity baseline snapshot (cheap input for the separate parity path).
4. **Dependencies / owners.** None. Owner: this roadmap. SimQ, ledger and registry are read-only.
5. **Work packages.**
   1. Report schema: the layers and states from epic §6.2, a denominator on every count, and an
      input-artifact manifest.
   2. Inventory and classification layer (signals only; `uncertain` preserved).
   3. Lane layer.
   4. Coverage job + `make test-cov`; report ingestion.
   5. Parity evidence derivation + snapshot.
   6. SimQ/census state ingestion.
   7. Normalization.
6. **Automated evidence.** Every layer shows a value with its denominator, or a state: package
   coverage (`provisional-local` until the CI job exists); domain coverage `not-derived`;
   classification (`uncertain`, `unclassified`); SimQ `skipped-no-data`; census `unstable`;
   mutation `not-run`; order-dependence `not-run`. Provenance: SHA + an input-artifact manifest
   (JUnit / coverage file ids).
7. **Acceptance criteria.**
   - Running the producer twice on the **same input artifacts** gives identical normalized data and
     classifications.
   - Separate executions keep their own results and run ids.
   - Failing tests present in the inputs are listed and bound to their run id. **No specific
     failure count is an acceptance criterion.**
   - Package coverage is never relabelled as domain coverage.
8. **Failure / provisional.**
   - Failed: normalized output differs on identical inputs.
   - Provisional: coverage comes from a documented local run.
   - Known test failures only *qualify* the affected package figures; they don't make the
     baseline inconclusive.
9. **Cost.** Producer: a static scan, expected under 1 min. Nightly coverage: about 17 min locally
   on 6 cores for the fast tiers (OV §4.1). **Validate** by recording both runtimes in the report.
10. **Ticket-planner handoff.**
    - (a) schema + producer + inventory;
    - (b) coverage job + `make test-cov`;
    - (c) parity snapshot;
    - (d) SimQ/census ingestion.

    Order: a → (b, c, d).

## R1 · Test-isolation repair (progression order dependence)

1. **Outcome.** The shared-state leak behind the 7 order-dependent progression tests (OV §4.2) is
   removed, and the repair is used to validate C5's order-dependence class.
2. **Inputs.** Failing node ids; the reproduction (pass alone, fail combined); conftest
   registry-reset plumbing.
3. **Deliverables.** The fix; a regression guard; an RNG-contract check for `pytest-randomly`; a
   triage evidence record in the MF format.
4. **Dependencies / owners.** None. Owner: this roadmap (test infrastructure). If the leak source
   is in feature code under rework, route it to the feature team per C5.
5. **Work packages.**
   1. Bisect the polluter.
   2. Identify the leaked state.
   3. Fix at the source.
   4. Add the guard.
   5. RNG-contract check.
   6. Random-order run.
6. **Evidence.** JUnit for the combined, isolated and random-order runs at one SHA; R1 state in the
   report.
7. **Acceptance.** `verified` = combined + isolated + random order all pass at one SHA.
8. **States.**
   - `provisional`: combined + isolated pass; random order awaits the RNG check.
   - `blocked`: the leak source needs a feature-team fix.
   - `failed`: otherwise.
9. **Cost.** The first reproduction takes about 17 min; after bisection, minutes. **Validate** by
   recording the minimal reproducer's runtime.
10. **Handoff.** One ticket (bisect + fix + guard), plus one small ticket (RNG check + random-order
    run).

## R2 · Scenario lane selection

1. **Outcome.** Mechanic scenarios run on every **relevant PR** (rule below) at a measured cost.
   This lane rule is separate from the impact model.
2. **Inputs.**
   - `PERF_RE` and `perf-cert-arena` (`test.yml:620-696`).
   - Skipped-lane evidence [O].
   - Local per-test durations (OV §4.3).
3. **Deliverables.**
   - A dedicated scenario job, or a widened filter.
   - A lane-rule fixture test.
   - A cost record.
4. **Relevant-PR rule.** Every changed path is classified into one of three outcomes:

   | Outcome | Paths |
   |---|---|
   | **relevant** (scenario lane runs) | `src/**`; `tests/mechanic_scenarios/**`, `tests/helpers/**`, `tests/conftest.py`; `data/**` (incl. `data/worlds/**`); `config/**`; `requirements*.txt`, `pyproject.toml`, `.github/workflows/test.yml`; **`tools/` paths mapped as scenario-input producers** |
   | **not relevant** | `docs/**`, `tickets/**`, `agent-monitoring/**`, `frontend/**`, `dashboard-frontend/**`, `tmp/**`; **`tools/` paths mapped as scenario-irrelevant** |
   | **impact-unknown → conservative fallback: run the lane** | any path not matched above, including **unmapped `tools/` paths** |

   **`tools/` mapping** [O evidence, 2026-09-29; I design]:
   - `src/**` imports nothing from `tools/`; `tests/mechanic_scenarios/**`, `tests/helpers/**` and
     `tests/conftest.py` import nothing from `tools/` (the conftest imports `tests.tools`, a
     different package). **No `tools/` code executes inside the scenario lane today.**
   - `tools/` can still affect scenario **inputs**: about 13 root-level scripts generate committed
     files under `config/` or `data/` (e.g. `tools/generate_corpus_registry.py` →
     `config/simulation_quality/corpus_registry.yaml`; `tools/evaluate_simq.py`,
     `tools/calibrate_simq.py` → calibration data). These are mapped **relevant**.
   - Subdirectories with no import or write path into scenario inputs (e.g. `tools/agent-monitoring/`,
     `tools/delivery/`, `tools/gate_checks/`, `tools/mechanism_registry/`, `tools/agent_*`,
     `tools/hooks/`, `tools/search/`) are mapped **not relevant**. Each mapping line carries a
     one-line justification.
   - **Mapping honesty check** (required, cheap): a static scan fails if any `tools/` path mapped
     *not relevant* becomes importable by `src/`, the scenario tests, helpers or conftest, or gains
     a write to `data/` / `config/`. Any new `tools/` path is unmapped, and therefore
     `impact-unknown`, until classified.

   Owner: this roadmap (lane contract) [RR], delivered through the normal CI change process.
5. **Work packages.**
   1. Encode the rule.
   2. Choose a dedicated job over reusing `perf-cert-arena`, which avoids pulling perf/cert into
      core PRs.
   3. Fixture test.
   4. Observe it on real PRs.
6. **Evidence.** Per PR: classification outcome per changed path (relevant / not relevant /
   impact-unknown), lane triggered, lane executed, JUnit, **lane wall time**. Report: PRs *n* by
   outcome; triggered *m*; executed *k*; **fallback-triggered count** (the cost of unknowns); median
   and p90 lane wall time.
7. **Acceptance.**
   - The fixture test passes: `src/progression/**`, `tests/mechanic_scenarios/**`, `data/worlds/**`
     and `tools/generate_corpus_registry.py` trigger; `tools/agent-monitoring/**` and docs-only
     don't; a new unmapped `tools/x.py` triggers via the fallback and is reported as
     `impact-unknown`.
   - The mapping honesty check fails on a seeded violation.
   - Over the observation window, every relevant PR triggered and executed the lane (m = k = n).
   - The measured cost is reported.
8. **States.**
   - `provisional`: the fixture passes but no relevant PR has been observed yet.
   - `failed`: any relevant PR is not triggered.
9. **Cost.** Assumed 1–3 min of lane wall time [I]; today's PR wall time is 7–9 min [O].
   **Validate:** actual lane durations over the first 10 relevant PRs. If the median exceeds 5 min,
   revisit the job split.
10. **Handoff.** One ticket.

## M0b · Post-repair baseline

1. **Outcome.** The M0a measures after R1 and R2, with every difference explained.
2. **Inputs.** The M0a report and input manifest; the R1 and R2 results.
3. **Deliverables.** The M0b report plus a diff note. A **provisional post-R2 report** may be issued
   earlier, labelled as such.
4. **Dependencies.** R2 done; **closes only when R1 is `verified`**. R3 is not required.
5. **Work packages.** Re-run on new input artifacts; attribute each difference.
6. **Evidence.** Same layers as M0a; the scenario-lane layer is now populated.
7. **Acceptance.** Every difference is attributed to a repair, a scope change or code drift.
8. **States.** `provisional` (R1 provisional) · `blocked` (R1 blocked).
9. **Cost.** As M0a.
10. **Handoff.** A small follow-up to M0a (a).

## MT · Test taxonomy and structure (C1)

1. **Outcome.** Agents and feature teams have written, reusable conventions: level contracts,
   ownership map, placement, metadata, shared harness patterns, and conventions for new tests.
2. **Inputs.** Epic §3; the OV §9 harness inventory; the OV §10 classification inventory; existing
   `docs/testing/*.md` (the taxonomy there is stale and legacy-parity oriented).
3. **Deliverables** [I]:
   - a replacement for `docs/testing/test_taxonomy.md`: level contracts, technique criteria,
     placement, ownership map;
   - registered metadata markers + an advisory consistency check;
   - pattern library entries, each with **one worked example that is synthetic (a labelled test-only
     toy) or confirmed stable with the feature agents** (candidate: resource conservation, ch03; the
     authoritative-write boundary is excluded as actively changing): property test, stateful property test, mechanic-outcome scenario via the shared
     helper, cross-domain chain, characterization. **No feature-specific proof commitments**;
   - the shared scenario helper;
   - the replay-diff helper, **restricted to the verified reproducibility envelope** (epic §3.5:
     hand-built state, fixed seed, ≤ 10 ticks, the determinism-suite profile; sequential vs
     concurrent over 5 ticks). It returns `outside-verified-scope` for anything else;
   - a `data/runs` cleanup fixture;
   - the S1 metadata rule, plus S2 proposal tooling.
4. **Dependencies / owners.** M0a (inventory). Owner: this roadmap. Scenario families remain with
   the scenario initiative; the helper follows its harness pattern.
5. **Work packages.**
   1. Taxonomy doc.
   2. Markers + check.
   3. Shared helpers.
   4. Pattern examples.
   5. S1 rule.
   6. S2 proposal tooling (labels proposed, not applied).
6. **Evidence.** Report classification layer: declared / proposed / uncertain / unclassified counts
   over the stated denominators; the pattern examples run in their lanes.
7. **Acceptance (operational).**
   - A new test written with the markers is located and classified by the report.
   - The consistency check flags a deliberately mismatched test.
   - Each pattern example runs green in its declared lane and is labelled synthetic or
     confirmed-stable.
   - The replay-diff helper returns `outside-verified-scope` for a compiled-world or >10-tick input
     (a negative test).
   - The helper is used by ≥ 1 pattern example.
   - **The staged migration is not required to be finished.**
8. **States.** `provisional` if the consistency check is advisory only; `failed` if a marked test
   isn't located by the report.
9. **Cost.** Pattern examples: under 30 s each [I]. **Validate** with in-lane durations.
10. **Handoff.**
    - (a) taxonomy doc;
    - (b) markers + check;
    - (c) shared helpers;
    - (d) pattern examples (one ticket per pattern);
    - (e) S2 proposal tooling.

    Order: a → b → c → d; e after b.

## M1 · Change-impact model v0 (C2)

1. **Outcome.** An impact report with reasons, `impact-unknown`, and **separate** selected /
   lane-triggered / executed facts.
2. **Inputs.**
   - The ownership map and domain ids (MT).
   - Import graph: CI-generated; interim fallback committed with its SHA and marked `stale`.
   - Coverage contexts: **deferred, evidence-triggered** (deferred triggers now listed in the epic tickets). v0 uses the
     ownership map, the import graph and the content rules only.
   - Content/config rules.
3. **Deliverables** [I]:
   - an impact producer + JSON contract;
   - an agent-readable rendering.
   - The seeded-fault evaluation harness is **deferred, evidence-triggered**. v0 never removes a lane;
     it only adds reasons and `impact-unknown` flags.
4. **Dependencies / owners.** M0a, MT. The mechanism tier waits on the registry epic.
5. **Work packages.**
   1. Rule model.
   2. Import-graph input + staleness.
   3. Coverage-context input.
   4. Content rules.
   5. Output contract.
   6. Seeded-fault harness.
   7. Evaluate the 5 sample categories.
   8. Wire the rendering into the `investigator` and `test-scoper` prompts, **after** the
      evaluation.
6. **Evidence.** Per fault: class, expected set, selected set, triggered lanes, executed lanes.
   Aggregates: test recall, lane recall, over-selection cost, unknown count, usable faults. Every
   figure is labelled a **sample validation**.
7. **Acceptance.**
   - The unmapped sample yields `impact-unknown` plus the full core-RPG fallback.
   - The other four categories produce the expected domains and lanes with reasons, checked against
     a hand-written expectation per sample.
   - Recall measurement waits for the seeded-fault trigger.
   - Cross-domain and content samples are found by a rule or by contexts.
   - Selected-not-triggered cases are reported separately.
8. **States.**
   - `provisional`: the fallback import graph is in use.
   - `inconclusive`: fewer than 4 usable faults.
   - `failed`: lane recall below 100%, or the unmapped sample not flagged.
9. **Cost.** About 17 min per fault reference run → 1.5–3 h per evaluation; run on demand.
   **Validate** by timing the first fault. A narrower reference population is allowed if recorded.
10. **Handoff.**
    - (a) rules + contract;
    - (b) graph + contexts;
    - (c) content rules;
    - (d) evaluation harness + evaluation;
    - (e) prompt wiring.

## M2 · AI-first authoring workflow (C3)

1. **Outcome.** The authoring workflow of epic §5 is written into the existing agents and
   templates: mandatory/optional `test_plan.md` fields, the oracle/spec review step, the reviewer
   checklist, and epic coordination rules.
2. **Inputs.** The OV §5.1 stage map; `investigator.md:153-191`; `architecture-reviewer.md`;
   `implement-ticket.js:999`; `implement-epic.js`.
3. **Deliverables.**
   - Template field changes.
   - The oracle/spec review step: the plan cites the oracle document section + parity-ledger entry.
     A changed expectation changes those documents first. Escalation to the user on silence,
     dispute or intra-Bible conflict.
   - The reviewer checklist (advisory, diff-scoped).
   - Epic coordination notes.
   - Review-record fields (epic §6.3). **No separate store and no validator yet**: the approval is
     recorded in the ticket, referencing the registry/ledger entry. The validator is
     evidence-triggered.
4. **Dependencies / owners.** MT (contracts, proof kinds). Owner: this roadmap. Agent-file changes go
   through their own tickets. The feature teams are the approvers.
5. **Work packages.**
   1. Template.
   2. Oracle/spec review step.
   3. Checklist.
   4. Review-record format + mechanical validator.
   5. Epic rules.
6. **Evidence.** Per ticket: mandatory-field completeness; substantive findings and the action
   taken; review records created and validated; `tool_call_count` per phase (pipeline runs only).
7. **Acceptance (operational).** On ≥ 2 real or synthetic tickets:
   - mandatory fields are present;
   - an oracle approval is recorded and mechanically validated;
   - a checklist finding (if any) is acted on or declined with a reason; a clean review is valid;
   - (deferred until the validator trigger fires) a review record turns `stale-approval` after a
     deliberate oracle change.
8. **States.**
   - `provisional`: exercised only on synthetic tickets.
   - `failed`: the validator can't detect staleness.
9. **Cost.** Bounded by the MP measurements; `tool_call_count` is a coarse proxy.
10. **Handoff.**
    - (a) template;
    - (b) oracle review step + review-record validator;
    - (c) checklist;
    - (d) epic rules.

## MF · Failure-triage and test-maintenance workflow (C5)

1. **Outcome.** The unified triage workflow (epic §7) as the single authoritative procedure: the
   evidence record, the 8 classes, roles, closure, the prohibitions, and bounded quarantine.
2. **Inputs.** `docs/testing/regression_policy.md` §4–7; the `delivery_process.md` CI Failure
   Triage section; CLAUDE.md gate integrity; the R1 repair as a live case.
3. **Deliverables** [I]:
   - the workflow merged into `regression_policy.md`, with the other docs linking to it;
   - an evidence-record template;
   - the bounded-quarantine **policy text** of epic §7.3, incl. the interim manual rule. The
     enforcement **tooling** (marker, hook, required check, report states) is **deferred until a
     real case needs quarantine**;
   - report support for `quarantined`;
   - a feature-team handoff template for defects found by tests.
4. **Dependencies / owners.** M0a (report states). Owner: this roadmap. Oracle documents and the ledger (escalation: the user)
   approve expectation changes. The quarantine-policy change to §6 needs an owner decision.
5. **Work packages.**
   1. Class table + evidence record.
   2. Reconcile the three existing documents.
   3. Quarantine policy + marker.
   4. Report state.
   5. Handoff template.
   6. Drill: apply it to R1's case and to one synthetic failure per class that has a cheap
      synthetic.
6. **Evidence.** Evidence records from the drills; the report shows `quarantined` with owner and
   expiry.
7. **Acceptance (operational).**
   - The drills classify correctly and route to the right role.
   - The policy is published and `regression_policy.md` §6 updated (after D-MF approval).
   - No existing failure is quarantined or hidden.
   - The tooling criteria (JUnit fields, expiry fails a required check, class-level rejected,
     `XPASS(strict)`) apply only when the deferred tooling ticket is triggered.
   - An attempted expectation change without a recorded approval is caught by the review-record
     validator (M2).
8. **States.** `blocked` if the quarantine-policy decision is pending (the rest proceeds);
   `provisional` if the drills are synthetic only.
9. **Cost.** Documentation and small tooling; the drills are local runs.
10. **Handoff.**
    - (a) unified doc + evidence template;
    - (b) quarantine marker + report state;
    - (c) handoff template;
    - (d) drill.

## MP · Bounded core-RPG pilot (C6)

1. **Outcome.** A demonstration that an agent can perform all six pilot capabilities (epic §8) on
   core RPG. It replaces the earlier progression workflow pilot and the M3a/M3b proof batches.
2. **Inputs.**
   - **Candidate surface:** resource conservation (ch03). It is not in the feature team's first wave
     (`rpg-feature-planning`, 2026-09-29), but no stability window is promised.
   - **At MP start**, the feature team is asked to confirm a stable window. If they can't, MP uses a
     **clearly labelled synthetic exercise**.
   - The authoritative-write boundary is excluded (actively changing).
3. **Deliverables.** A pilot record per exercise, covering capabilities 1–6 with artifacts; a final
   pilot report with a qualitative review and a keep / revise / inconclusive decision per
   intervention.
4. **Dependencies / owners.**
   - M2, MF and R2 are required.
   - M1 if available; otherwise a manual impact analysis with reasons, recorded as such.
   - Owner: this roadmap. The feature agents choose the surface and approve oracles.
   - It must not block on a feature redesign.
5. **Work packages.**
   1. Choose the surface with the feature agents.
   2. Run the exercise through C2 → C3 → C1 → C4.
   3. Inject or observe one failure and triage it (C5).
   4. Register evidence; deliberately invalidate it (change the oracle hash); confirm the report
      shows `stale`.
   5. Write up.
6. **Evidence.**
   - Impact report or manual impact.
   - `test_plan.md` with the approved oracle.
   - Test file with metadata.
   - Lane runs (local + CI) with run ids.
   - Triage record.
   - Review record and the report before/after invalidation.
7. **Acceptance.** All six capabilities are observed at least once, each with an artifact. A
   capability that fails is recorded as a finding and triggers a revise decision, **not a pass**.
8. **States.**
   - `provisional`: synthetic-only exercise.
   - `inconclusive`: a capability couldn't be exercised for lack of a surface, with the reason
     recorded.
   - `failed`: a capability was attempted and didn't work.
9. **Cost.** The size of a normal small ticket per exercise, plus reporting. `tool_call_count` is
   recorded as a coarse proxy. **Validate** by comparing it with typical small tickets.
10. **Handoff.**
    - (a) surface selection note, jointly with the feature agents;
    - (b) exercise ticket(s);
    - (c) pilot report.

## G-P · Party ownership assessment (DEFERRED)

**Deferred while party's oracle and owner are unknown.** No Bible chapter covers party/group
composition (`rpg-feature-planning`, 2026-09-29). Re-open when the owner assigns an oracle document
and an owner for party, or decides to bring party into core RPG. Until then, `src/systems/party*.py`
and `src/systems/social_systems/party*.py` are listed as **unmapped** in C2, so a change there
yields `impact-unknown` and the conservative fallback.

---

## Separate paths (not planned in detail)

| Path | Next step |
|---|---|
| R3 SimQ skip visibility | SimQ owner; this roadmap only reads the state |
| Parity evidence model | After the D7 decision; the baseline snapshot comes from M0a |
| Cleanup | Per-target consumer and CI inventory before any deletion decision |
| API / UI | Only on a demonstrated core-RPG dependency |
| Replay-dependent techniques, E14 | After determinism is unparked |
| Feature proof batches (former E2, E3, E7–E9, E12) | **Feature-owner responsibility**; they use MT patterns, the M2 workflow and C4 reporting |
| E11 | Feature design decision; outside this roadmap |
