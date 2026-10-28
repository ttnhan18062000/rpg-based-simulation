---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261023-PRESSURE-SIGNALS-SWITCH-FEATURE-FLAGS-OUTSIDE-THE-HASH
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-PRESSURE-SIGNALS-SWITCH-FEATURE-FLAGS-OUTSIDE-THE-HASH

## Title
Unhashed state.pressure_signals keys starting ENABLE_ switch feature flags (pipeline.py:86-91) (#593 F5)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
#593 F5 (lead-planner relay 2026-10-23; low priority, dormant in production). `src/engine/pipeline.py:86-91` maps `state.pressure_signals` keys that start with `ENABLE_` onto feature flags, and `pressure_signals` is not in CanonicalStateHasher. Unhashed state can therefore switch behaviour.

## Scope
1. Check that no world, scenario or test relies on the ENABLE_ mapping.
2. If none: delete the mapping (perf-planner's preference). Otherwise hash the field (with perf's digest-scheme bump, F1) and document it.

## Out of Scope
F1 hashing of the other omitted fields (perf).

## Acceptance Criteria
- No behaviour reachable from unhashed pressure_signals; a test asserts ENABLE_* signals do not change flags (or that the field is hashed).

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0; after-v1 work).

## Related Docs
#593 (lead-planner relays); docs/plans/architecture/faster_feature_testing_draft_tickets.md; docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/engine/pipeline.py; src/engine/checkpoint.py

## Assumptions / Open Questions


## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
