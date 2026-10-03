# Implementation Sequence — adventure-cognition-merge

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260811-ADVENTURE-GOAL-SCORER  (no deps in this batch)
2. TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION  (no deps in this batch)
3. TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE  (no deps in this batch; requires ADVENTURE-GOAL-SCORER to exist as a testable target before its own shadow-diff test is meaningful, though not a hard file-level ticket dependency)
4. TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE  (depends on: TCK-20260811-ADVENTURE-GOAL-SCORER, TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE)
5. TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER  (no deps in this batch)
6. TCK-20260811-REGION-STABILIZATION-GOAL-SCORER  (no deps in this batch)
7. TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING  (no deps in this batch; recommended to land after ADVENTURE-GOAL-SCORER settles to avoid merge churn on shared adventure scoring files)
8. TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING  (no deps in this batch; same merge-churn recommendation as above)
9. TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY  (no deps in this batch; same merge-churn recommendation as above)
10. TCK-20260811-MULTI-STEP-PLANNING-DESIGN  (no deps in this batch; recommended to wait for ADVENTURE-GOAL-SCORER and THREAT-RESOLVED-ARBITER-RELOCATION to stabilize the current_project_id model this design must reason about)

## Why This Order Matters

`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` is a hard, ticket-level dependency: its own
Acceptance Criteria state its Implement phase must not proceed until both
`TCK-20260811-ADVENTURE-GOAL-SCORER` and `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE` are in
`tickets/done/`. Running it earlier would delete the only live adventure decision path before its
replacement is built and shadow-validated, per the source design doc's own explicit staged
4-step rollout plan (§7).

The remaining tickets (`SOCIAL-CONTRACT-GOAL-SCORER`, `REGION-STABILIZATION-GOAL-SCORER`,
`MEMORY-INFORMED-ROUTE-SCORING`, `CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`,
`RELATIONSHIP-AWARE-FORM-PARTY`, `MULTI-STEP-PLANNING-DESIGN`) have no hard file-level
dependency on the other tickets in this batch, but several carry a disclosed, non-blocking
merge-churn recommendation (landing after the core `ADVENTURE-GOAL-SCORER`/
`THREAT-RESOLVED-ARBITER-RELOCATION` pair settles, since they touch the same adventure-scoring
files) — noted per-ticket above rather than encoded as a hard sequence constraint, since none of
them structurally require the others to be DONE first.

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.
