# TCK-20260422-PH7-M3-KERNEL-STABILITY

## Title
Phase 7 Milestone 3: Kernel Stability and Resource-Bounded Finalization

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Close the authoritative application model to ensure that one authoritative outcome is produced per tick, handling conflicts (e.g., occupancy), partial failures, and ensuring that authoritative outcomes are the source for replay/observability.

## Scope
- Implement formal Conflict Resolution (e.g., deterministic occupancy tie-breaking).
- Ensure authoritative world mutation occurs only after all proposal generation/refinement.
- Ensure partial rejection of an entity's update does not corrupt unrelated domains.
- Ensure authoritative outcomes define replay-visible truth (Snapshot integrity).
- Consolidate all "Intent Routers" and "Authoritative Laws" into a single, ordered pipeline in \`ApplyPath\`.

## Out of Scope
- Major architectural changes to the worker pool (handled in M2).
- Feature work for Phase 8.

## Acceptance Criteria
- 100% of Authoritative Phases (INIT -> ADVANCEMENT) have tracked compute costs in \`RuntimeStatus\`.
- Proactive shedding triggers correctly when compute pressure exceeds profile thresholds.
- Shutdown process is bounded and reliably flushes replay manifests within the timeout.
- All Phase 7 M3 requirements in \`resource_phase7_high_level.md\` satisfied.

## Related Tickets
- TCK-20260422-PH7-M2-SUBSTRATE-CLOSURE (Pre-requisite)

## Related Docs
- resource_phase7_high_level.md
- src_principle.md

## Related Code Areas
- \`src/engine/kernel.py\`
- \`src/engine/governor.py\`
- \`src/engine/runtime_status.py\`

## Assumptions / Open Questions
- Compute budgets are defined in the \`RuntimeProfile\`.

## Implementation Notes
- Focus on "Resource Integrity".

## Test Summary
- Load test with high compute pressure to verify Governor shedding.
- Shutdown reliability tests.

## Files Changed
- TBD

## Completion Summary
- TBD
