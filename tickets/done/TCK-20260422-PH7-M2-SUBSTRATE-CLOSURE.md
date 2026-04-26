# TCK-20260422-PH7-M2-SUBSTRATE-CLOSURE

## Title
Phase 7 Milestone 2: Substrate Closure and Intent Hardening

## Status
OPEN

## Request Summary
Audit and harden the action/update substrate to ensure all mutation intent is explicit, typed, and emitted through the authoritative substrate model. Eliminate non-deterministic shortcuts and "decorative" bypasses.

## Scope
- Audit \`src/engine/worker_manager.py\` for intent emission patterns.
- Audit \`src/core/updates.py\` for typed coverage of all current gameplay interactions.
- Migrate remaining durable state from \`properties\` to typed components (e.g., \`NavigationComponent\` or \`StrategicComponent\` expansions).
- Ensure all worker-side logic emits structured \`EntityUpdate\` objects instead of raw dicts or direct state mutations (which are already prohibited by \`ApplyPath\`, but must be enforced at the worker interface).

## Out of Scope
- Major gameplay feature additions (Phase 8+).
- Refactoring the Kernel itself (Phase 7 M1/M3).

## Acceptance Criteria
- 100% of durable state transitions in worker logic flow through typed \`EntityUpdate\` fields.
- Zero usage of \`property_updates\` for P0 gameplay state (HP, Position, Trust, etc.).
- Audit report documented in \`investigation.md\`.
- All Phase 7 M2 goals in \`resource_phase7_milestone2.md\` satisfied.

## Related Tickets
- TCK-20260422-PH6-M7-M8-HARDENING (Parent/Pre-requisite)

## Related Docs
- resource_phase7_milestone2.md
- src_principle.md

## Related Code Areas
- \`src/engine/worker_manager.py\`
- \`src/core/updates.py\`
- \`src/engine/apply.py\`

## Assumptions / Open Questions
- None at this stage.

## Implementation Notes
- Focus on "Intent Emittance" purity.

## Test Summary
- Verify intent emittance via unit tests of worker handlers.
- Regression test of full state application loop.

## Files Changed
- TBD

## Completion Summary
- TBD
