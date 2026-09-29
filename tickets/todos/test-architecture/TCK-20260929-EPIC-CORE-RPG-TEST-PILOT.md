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

**Per exercise, demonstrate that an agent can:**
1. identify the impacted domains and levels;
2. produce a test plan citing the oracle source (Bible/contract + parity ledger). **Approved-oracle
   review** is a separate capability (2b). It can be claimed only if the oracle-review step (Epic C
   part 5, `HOLD — pending D-M2`) is approved and was actually exercised;
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
2. **Capability 2b (approved-oracle review):** if the oracle-review step is on HOLD or absent, the
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

## Related Docs
- `docs/plans/test_architecture/roadmap.md`
- `docs/plans/test_architecture/reference/milestone_design_notes.md` (MP; non-binding)

## Related Stored Artifacts
None.

## Related Code Areas
Depends on the chosen surface. Candidate: economy conservation code and its tests.

## Assumptions / Open Questions
- The surface is confirmed at start; otherwise the pilot uses the synthetic exercise (a
  `provisional` result, which cannot establish that the workflow works on a real RPG change).
- D-M2 pending: capability 2b is not claimable while the oracle-review step is on HOLD.

## Implementation Notes
Cost: about one small ticket per exercise, plus reporting.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
