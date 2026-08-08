---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT
artifact_type: test_plan
tags: [simulation-quality, documentation]
---

# test_plan.md — TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT

Documentation-only ticket, no code changed. "Testing" here means citation accuracy:

## Normal flow
- Every event name quoted in the audit doc must appear verbatim in
  `entity_lifecycle_weights.yaml`'s real `lifecycle_phase_buckets` — verified by direct
  cross-read, not typed from memory.
- Every weight value quoted must match `scoring_weights.yaml`'s real current values.

## Edge cases
- N/A — no code paths, no runtime behavior.

## Failure modes
- A stale citation (a ticket ID, event name, or weight value that drifts from its real source)
  would be a real documentation defect — checked directly against source files during Implement,
  not assumed correct.

## Regression-prone paths
- `make docs-registry` must pick up the new doc file with valid frontmatter.
