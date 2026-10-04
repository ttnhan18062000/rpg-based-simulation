---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC
phase: open
date: 2026-10-03
tags: [planning]
---

# TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC

## Title
Bring the parity ledger to zero schema errors without loosening the schema, routed per subsystem

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
Owner decision 2026-10-03: the 2,862 schema errors are fixed through a scope-only epic whose children go to the domain that owns each ledger file. The schema rules stay: a verified/divergent entry needs a test_path, and a P0 entry needs a test_path unless it is missing/unsupported with a support_boundary. So downgrading a P0 entry to legacy_verified does NOT clear its error.

## Scope
- One child ticket per ledger file (or per part of a large file), filed with the owning domain's planner: substrate, combat_movement, social_narrative, strategic_cognition, town_resource, world_dynamics, progression, faction (rpg); infrastructure (testing / agent-working, to be confirmed by the owner)
- Per entry, exactly one of: cite the real test that proves it (test_path); change status to what the evidence supports (missing/unsupported with a support_boundary for P0, or legacy_verified for non-P0) with the reason; or an owner-approved exception through a mechanism the owner first approves (none exists today)
- Owner decision on the 25 proof_type values (feature 13, architecture 6, unit 5, integration 1): add them to the enum with definitions, or remap; recorded before the child that touches them
- Each child tightens the ratchet baseline from TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
- Each child runs `python3 -m codebase.gates.parity_ledger_schema tighten --yes` in the same PR as its ledger fix and commits `codebase/baselines/parity_ledger_schema_baseline.json` (any domain may lower a count; none may raise one; see `docs/parity_ledger/README.md`)

## Out of Scope
- Loosening schema.json to reach zero
- Writing new tests to justify an entry inside these children (a missing test is a finding for the owning domain, not something to invent here)

## Acceptance Criteria
- [ ] Every child filed with its owning domain and listed here
- [ ] proof_type decision recorded
- [ ] Ratchet baseline at zero, or the remainder carried forward by explicit owner decision

## Related Tickets
- TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET
- TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
- TCK-20260902-PARITY-TEST-PATH-GAP

## Related Docs
- docs/parity_ledger/schema.json
- CLAUDE.md (Parity Ledger section: P0 entries require a passing test_path)

## Related Stored Artifacts
None.

## Related Code Areas
- docs/parity_ledger/*.yaml

## Assumptions / Open Questions
- Counts on main 2026-10-03: 1,312 verified entries with null test_path (1,304 P0, 7 P1, 1 P2), 1,525 P0 test_path errors, 25 proof_type; per file (entries with any error, per perf-planner/planner run): infrastructure, substrate, combat_movement, social_narrative largest
- Routing children to other domains is a request to their planners (outbox if not running); this epic does not assign their work

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
