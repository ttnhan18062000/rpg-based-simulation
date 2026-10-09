---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN
phase: open
date: 2026-10-09
tags: [testing, regression, simulation-quality]
---

# TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN

## Title
The rpg gate report evaluates validity exactly and outcomes paired against both baselines, reruns the same SHA on non-pass, and reports six states

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 4 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. States (the metric set v1, adopting outcome neutrality): pass / fail (VALIDITY only) / drift (OUTCOME only: "trace the cause") / unstable / stale / no-data.

## Scope
1. Evaluation per metric id and group:
   - validity: `violations > 0` gives `fail`, with up to 5 examples; otherwise `pass`;
   - outcome: the paired per-seed difference against the LAST baseline and the milestone-FIRST baseline. `drift` when |mean diff| > k*SE AND > the metric's floor (k and floors from rpg's config); otherwise `pass`. Report both references.
   - `stale` (child 2) and `no-data` (child 3) pass through; neither ever becomes pass.
2. Same-SHA rerun: when a report has any `fail` or `drift`, rerun the affected (world, seed) set once at the same SHA (fresh processes). If the rerun disagrees, mark those metrics `unstable` and route them to test infrastructure (roadmap §4.5, nondeterminism), not to the feature team.
3. Ownership (child 1's metric registry): an unowned `fail` fails the report; an owned one shows as known; an unowned `drift` is listed as "needs a trace ticket" (advisory); expired entries behave like the slow registry.
4. Output: a JSON report (machine) plus a markdown summary (step summary and rolling issue body): states per metric, both references, the examples, and the cited oracle per validity metric (from rpg's config).
5. The report's verdict, for CI: red only for an unowned or expired `fail`, or for `unstable`. Drift never makes the job red.

## Out of Scope
- Opening or updating the rolling issue (child 5).

## Acceptance Criteria
1. Unit tests for each state, from fixture documents, covering both references, the k*SE AND floor rule (one case inside SE but over the floor, one over SE but under the floor), owned/unowned/expired, and a rerun disagreement giving unstable.
2. The report cites each validity metric's oracle from the config, never from code constants.
3. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE, TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS, TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
None.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
