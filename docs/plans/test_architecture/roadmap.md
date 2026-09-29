---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture Roadmap (core RPG as first application)

**Status: FOR OWNER REVIEW, 2026-09-29. All decisions below are PENDING.**

This roadmap and the four epic tickets in `tickets/todos/test-architecture/` are the **binding** plan.
Everything in [`reference/`](reference/) is non-binding investigation and design material for the
detail planner and implementer agents. Child tickets are **not** created here; they are the detail
planner's job.

**Evidence base:** `04f911110`, with the progression leak re-checked at `origin/main` `5d4e4a237`.

## 1 · Scope

**This roadmap owns** how tests are planned, written, selected, organized, executed, measured,
reviewed, maintained and repaired, applied first to core RPG.

**It does not own** RPG mechanic behaviour, feature acceptance criteria, feature proof portfolios, or
feature defect fixes. Those belong to the feature-owning teams, which are currently reworking core
RPG.

**Success** means the system can locate, run, report and invalidate test evidence honestly, and route
failures to the right owner. The number of feature behaviours proven is **not** the measure.

## 2 · Principles (binding)

1. **Behaviour source.** The Mechanics Bible and Engine Contracts define expected behaviour. The
   parity ledger is their evidence link. Changing an expectation means changing those documents first
   (CLAUDE.md's Authoritative Mechanics Rule). No agent re-approves an expectation by itself.
2. **Escalation to the user** when:
   - the document is silent (e.g. party);
   - ownership is missing;
   - domains dispute an expectation;
   - two Bible or contract sections disagree.
3. **No new authoritative proof-status record.** The parity ledger and mechanism registry keep their
   existing roles; this roadmap reports against them.
4. **Honest states.** Missing, skipped, stale, unstable and not-run data are reported as such, never
   as 0 or pass. In particular, "no JUnit available", "not run" and "passed" are distinct.
5. **Never make red green by weakening tests:** no silent snapshot or anchor updates, broad
   skip/xfail, weakened assertions, or changed expected values without the documents changing.
   Existing failures stay visible.
6. **Tooling follows evidence.** Expensive tooling is built only when its trigger fires (§5).
7. **Core RPG is the application scope, not a feature commitment.** Worked examples are synthetic or
   confirmed stable with the feature team.

## 3 · Epics

| Epic | Outcome | Depends on | Gated parts (pending decision) |
|---|---|---|---|
| **A. Test baseline and reliability** (`TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`) | A reproducible core-RPG test report that works with the **available** artifacts (`no-junit-artifact` / `no-coverage-artifact` where absent). The **known** progression order leak is fixed, and the known write to `docs/brainstorm/mechanism_verification_view.md` is stopped. Any general tracked-file guard is advisory, distinguishes test-caused from tool/hook writes, and is never a blocking gate. Remaining unknowns are reported. **No new CI job** | — | none |
| **B. Test structure and selection** (`TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION`) | Written test-level conventions and metadata. Scenario tests run on relevant PRs. A first impact report that adds reasons and `impact-unknown` flags and never removes lanes | A (report v0, for reporting only) | CI scenario-lane rule: **`HOLD — pending D-R2`** |
| **C. Test workflow and failure handling** (`TCK-20260929-EPIC-TEST-WORKFLOW-FAILURE-HANDLING`) | Test-plan fields and an advisory test-quality checklist in the existing workflow; one unified failure-triage procedure | B (conventions) | oracle-review step: **`HOLD — pending D-M2`**; quarantine policy: **`HOLD — pending D-MF`** |
| **D. Bounded core-RPG pilot** (`TCK-20260929-EPIC-CORE-RPG-TEST-PILOT`) | One or two exercises. The pilot report **lists which capabilities were actually demonstrated**. Approved-oracle review is claimable only if the D-M2 step was approved and exercised | The **minimum usable workflow** (below), not every part of A–C | surface confirmation at start (resource conservation is a **candidate** until confirmed) |

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
approves that decision. Ungated work is independently startable.

## 4 · Pending owner decisions

| Id | Decision | Recommendation | Gates |
|---|---|---|---|
| D-R2 | Scenario-lane rule: `src/**` + known scenario dependencies trigger; known-irrelevant paths listed; unknown/new paths run the lane and are named in the job summary; a dedicated job; no rule change until lane cost is measured | approve | the CI rule change in B |
| D-MF | Bounded quarantine replaces `regression_policy.md` §6's unbounded `xfail(strict=False)` (nondeterminism only; node-level strict xfail; owner, ticket, expiry ≤ 14 days, one renewal); tooling waits for a real case | approve | the quarantine policy in C |
| D-M2 | Oracle model as in §2.1–2.2; oracle review advisory during the pilot | approve | the oracle-review step in C |
| D-P | Party: no oracle document or owner | keep deferred | nothing in A–D |
| D-PR | Which implementation PR carries these plan docs (no plan-only PR) | the first A or B child PR | delivery only |

## 5 · Deferred (with triggers)

| Item | Trigger |
|---|---|
| Review-record validator | A feature team first asks to register a proof, or the registry epic ships its mechanism → test link |
| Seeded-fault evaluation harness | Before the impact report is ever used to skip a test or lane, or after the first recorded CI selection failure |
| Per-test coverage contexts | A recorded selection failure where static inputs missed a dynamic dependency |
| Quarantine enforcement tooling | The first real case needing quarantine |
| JUnit upload from every CI job | When manual JUnit input to the report becomes the recurring bottleneck (today only `api-tools` uploads) |
| CI coverage job | After its runtime is measured and its information is judged useful (not an owner-decision gate) |
| Party ownership assessment | The owner assigns party an oracle document and owner (D-P) |
| Parity evidence model, cleanup/pruning, API/UI tests, replay-dependent techniques | Their own decisions or dependencies; outside this roadmap's first program |

## 6 · Reference (non-binding)

- [`reference/current_test_system_overview.md`](reference/current_test_system_overview.md): as-is
  measurements (layout, lanes, coverage scope, failures, SimQ, parity baseline, classification
  inventory).
- [`reference/architecture_design_notes.md`](reference/architecture_design_notes.md): level
  contracts, evidence classification, proof kinds and freshness, the failure-triage class table,
  the quarantine mechanism, references [R1–R29].
- [`reference/milestone_design_notes.md`](reference/milestone_design_notes.md): per-milestone work
  packages, costs and acceptance ideas from earlier revisions.
