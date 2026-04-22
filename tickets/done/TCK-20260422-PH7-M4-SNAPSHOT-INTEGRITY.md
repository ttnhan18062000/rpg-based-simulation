# TCK-20260422-PH7-M4-SNAPSHOT-INTEGRITY

## Title
Phase 7 Milestone 4: Snapshot Integrity, Isolation, and Serialization Closure

## Status
OPEN

## Request Summary
Close the snapshot and state-isolation substrate to ensure read surfaces are immutable, deep-isolated, and produce stable serialization behavior without state-shape drift.

## Scope
- Enforce snapshot immutability for supported read surfaces.
- Ensure deep isolation for snapshots independent of live mutation.
- Close serialization-shape drift for deterministic comparison/replay.
- Define the supported deterministic state shape for Phase 7.

## Out of Scope
- World generation (Handled in M5).
- Strategic AI depth.

## Acceptance Criteria
- Snapshots are strictly immutable (verified by test).
- Serialization output is order-invariant and deterministic across all state components.
- Authoritative state export is trustworthy for proof and replay.
- All Milestone 4 requirements in \`resource_phase7_high_level.md\` satisfied.

## Related Tickets
- TCK-20260422-PH7-M3-AUTHORITATIVE-APPLY (Pre-requisite)

## Related Docs
- resource_phase7_high_level.md

## Related Code Areas
- \`src_v2/core/state.py\`
- \`src_v2/engine/checkpoint.py\`
- \`src_v2/core/export.py\`

## Assumptions / Open Questions
- We will use a combination of dataclass \`replace\` and frozen slots for integrity.

## Implementation Notes
- "State Integrity is Authority".

## Test Summary
- Immutability verification test.
- Deterministic serialization/hash stability test.

## Files Changed
- TBD

## Completion Summary
- TBD
