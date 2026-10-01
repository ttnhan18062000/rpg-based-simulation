---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-CORE-RPG-TEST-PILOT
phase: open
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-EPIC-CORE-RPG-TEST-PILOT

## Title
Epic D — Bounded core-RPG pilot: show that the test workflow works end to end on one or two small changes

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Epics A–C build conventions, reporting and workflow. This epic checks whether an agent can actually
use them on core RPG. It is a demonstration of the workflow, **not** a feature proof portfolio.

Roadmap: `docs/plans/test_architecture/roadmap.md` §3.

## Scope

**Start condition** (the minimum usable workflow, not every part of A–C):
- Epic A report v0;
- Epic A known-leak fix, at least `provisional`;
- Epic B taxonomy doc;
- Epic C test-plan fields;
- Epic C triage procedure.

Optional parts are used if ready: impact report, pattern library, scenario-lane rule, oracle-review
step, quarantine policy.

**Surface:**
- **Candidate only: resource conservation (Bible ch03)**. It stays a candidate until the feature team
  confirms it is stable. It is not in the feature team's first wave
  (`rpg-feature-planning`, 2026-09-29), but no stability window is promised.
- At start, ask the feature team to confirm a stable window.
- If they can't, run a **clearly labelled synthetic exercise**. That result is **`provisional`**:
  it does **not** establish that the workflow works on a real RPG change.
- The authoritative-write boundary is excluded (actively changing).
- **Notes on the candidate** (`rpg-feature-planning` review, 2026-09-29):
  - The nearest economy work, the `pressure-propagation-economy` epic, is all-or-nothing and touches
    `src/economy/` and shared state. Name it explicitly when asking for stability confirmation.
  - Economy paths **do not trigger the scenario lane today** (F2). The pilot either runs after the
    lane rule (B; D-R2 approved 2026-09-30, job implemented, not yet run in CI) or records a manual lane run and states that CI would not
    have run it. That makes the lane gap part of what the pilot demonstrates.

**Per exercise, demonstrate that an agent can:**
1. identify the impacted domains and levels;
2. produce a test plan citing the oracle source (Bible/contract + parity ledger). **Approved-oracle
   review** is a separate capability (2b). It can be claimed only if the oracle-review step (Epic C
   part 5; D-M2 approved 2026-09-30 as advisory text) was actually exercised on a real change;
3. choose or create the test using a documented pattern;
4. run the correct local and CI lanes;
5. interpret a real or injected failure and route it per the triage procedure;
6. see the evidence reflected accurately in the report, including a state change after a deliberate
   invalidation.

## Out of Scope

- Completing tests for any feature.
- Any change to feature behaviour.
- Waiting on feature redesigns.
- Building deferred tooling.

## Acceptance Criteria

1. The pilot report **lists which capabilities each exercise actually demonstrated** (1, 2, 2b, 3–6),
   each with its artifact. Nothing is claimed that was not exercised. Each of capabilities 1–6 is
   observed at least once, with an artifact:
   - impact output or a manual impact analysis;
   - `test_plan.md`;
   - the test with metadata;
   - lane runs with run ids;
   - a triage record;
   - the report before and after invalidation.
2. **Capability 2b (approved-oracle review):** if the oracle-review step was not exercised on a real change, the
   report states "not demonstrated", and the pilot makes **no** claim about approved-oracle review.
3. **Result classification:**
   - `established` only if at least one exercise uses a **confirmed real** surface;
   - `provisional` if synthetic-only;
   - `inconclusive` if a capability could not be exercised, with the reason recorded;
   - `failed` if a capability was attempted and did not work.
4. A short pilot report records, per workflow intervention, keep / revise / inconclusive with
   measurements and a qualitative review. It is directional; no causal claim is made.
5. Capabilities that failed produce revise items for Epics A–C, not a pass.

## Related Tickets
- Depends on the minimum usable workflow from Epics A, B, C.
- Coordinates with `rpg-feature-planning` for the surface.
- Child: `TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING` (D1, real surface, done).

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (MP; non-binding)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING/pilot/` (evidence)
- `docs/testing/core_rpg_test_pilot_2026-09-30.md` (pilot report)

## Related Code Areas
Depends on the chosen surface. Candidate: economy conservation code and its tests.

## Assumptions / Open Questions
- The surface is confirmed at start; otherwise the pilot uses the synthetic exercise (a
  `provisional` result, which cannot establish that the workflow works on a real RPG change).
- D-M2 approved (2026-09-30) as advisory text; capability 2b is claimable only once a real change exercises the oracle-review step.

## Implementation Notes
Cost: about one small ticket per exercise, plus reporting.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

**Status (2026-10-01): OPEN, with the real-pipeline gap closed and CI scenario execution recorded separately.** Earlier correction (2026-09-30): the pilot was hand-orchestrated and CI skipped the scenario job. **Update 2026-10-01:** the real `implement-ticket` pipeline (via the `/implement-ticket` skill; the native `Workflow` tool cannot parse the script) has run to DONE on `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP` (pilot report capability 7), with five orchestrator interventions recorded there. CI scenario execution is recorded from this change's own CI run (pilot report capability 7, CI note). The original sentence follows. Component demonstrations on a real surface are established. ~~Not yet demonstrated: the real `implement-ticket` pipeline, and CI scenario execution.~~ This epic title's "end to end" claim is not met until a real-pipeline exercise (about 8–10 agents, on a small behaviour-owned ticket named by rpg-feature-planning, launched only with the user's own go-ahead) is recorded as a new capability row in the pilot report. That exercise is also what exercises Epic C's checklist and `test_plan.md` field check.

Acceptance criteria as stated by the first pilot report (2026-09-30), with the scope corrected above:
1. Capabilities 1 (after two fixes made in this batch; before/after artifacts kept), 2, 3, 4, 5, 6 each have an artifact.
2. Capability 2b stated as not demonstrated; no claim made.
3. Result `established`, on a real surface whose stability was confirmed at scope level only (caveats in the report).
4. Keep / revise / inconclusive per intervention recorded, directional.
5. The shortfalls (conservation mapped to substrate only; no domain/level for a tests-only change; parity layer not showing test_path) were revise items for Epics A and B and are fixed in this batch. The heuristic file classification stays as a documented decision.
No D2 synthetic exercise was needed.
