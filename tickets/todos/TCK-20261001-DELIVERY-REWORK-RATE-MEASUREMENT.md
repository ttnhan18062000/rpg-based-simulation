---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT
phase: open
date: 2026-10-01
tags: [delivery, agent-monitoring]
---

# TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT

## Title
Delivery rework rate: first-pass CI rate, failure class and push-after-green count

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`delivery_cost_measurement.py` reports `gh` calls per PR and subject traceability. It does not say how often a PR needs rework. PR #270's first CI run failed on a gitignored evidence file, and #271 and #272 hit the same live-shard test class. Extend the tool to report rework, read-only.

## Scope
1. Add first-pass CI rate per PR, using `pr_status.py`'s existing CI-state detection and `ci_triage_classifier.py`'s failure classes.
2. Add pushes-after-first-green and failed-then-fixed counts per PR.
3. Keep the tool's rules: `--ref` reads, snapshot caveat, measures a baseline only and never presents an "after" claim.

## Out of Scope
- Judging whether the delivery epic succeeded.
- Any new `gh` call pattern beyond what the classifier already uses (watch the TLS-block trap).

## Acceptance Criteria
1. On a fixture of PR/CI records with one first-pass failure, the rate and class are correct.
2. Output is labelled as a snapshot with the ref and SHA.
3. Existing `delivery_cost_measurement` tests pass unchanged.

## Related Tickets
- TCK-20260924-DELIVERY-COST-MEASUREMENT (done; the tool extended here)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (update the matching row's status in this ticket's own batch)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/delivery/delivery_cost_measurement.py`, `tools/delivery/pr_status.py`, `tools/delivery/ci_triage_classifier.py`

## Assumptions / Open Questions
- Open: where the per-PR CI history comes from without an extra `gh` call per PR; check what `pr_status.py` already returns.

## Implementation Notes
Draft by agent-working-design; the implementer commits it.

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
