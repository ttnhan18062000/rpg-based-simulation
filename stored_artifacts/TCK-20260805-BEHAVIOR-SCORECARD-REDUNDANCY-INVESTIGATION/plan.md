---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION
artifact_type: plan
tags: [cognition, observability, simulation-quality]
---

# plan.md — TCK-20260805-BEHAVIOR-SCORECARD-REDUNDANCY-INVESTIGATION

## Ordered Steps

1. **No code change.** Investigation concluded a nuanced, field-specific verdict (neither pure
   "redundant" nor pure "worth reviving as-is") — per the ticket's own AC3, documenting this
   precisely is the deliverable, not a code change.
2. **Update `docs/simulation_quality/extension_points.md`'s axis 3 addendum** — replace the
   "under investigation" framing with the concluded finding.
   - Files: `docs/simulation_quality/extension_points.md`.
3. **Fill this ticket's Completion Summary** with the field-by-field verdict and recommendation.

## Scope Guards

- Do NOT wire `BehaviorWorker` into the engine — that's explicitly a future ticket's scope if the
  recommendation here is ever acted on.
- Do NOT write new scoring logic for `stagnation_score`/etc. — confirmed unimplemented, out of
  scope for an investigation ticket.

## Dependency Map

Step 2 depends on step 1's conclusion (no code change) being final. Step 3 depends on step 2.

## Acceptance Criteria Map

- AC1 (field-by-field verdict, evidenced) → investigation.md's table.
- AC2 (clear recommendation, cross-referenced from extension_points.md) → Step 2.
- AC3 (precise scoping for a future revival ticket, if warranted) → investigation.md's
  Recommendation section.

No unresolved questions requiring human review.
