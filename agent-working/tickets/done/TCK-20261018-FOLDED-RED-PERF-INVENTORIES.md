---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261018-FOLDED-RED-PERF-INVENTORIES
phase: done
date: 2026-10-18
tags: []
---

# TCK-20261018-FOLDED-RED-PERF-INVENTORIES

## Title
Regenerate the phase and wall-clock perf inventories for the folded rpg-next tree

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
rpg-planner dispatch: tests/tools/test_perf_inventories_committed_in_sync.py was red on rpg-next b23e78128 for both inventories.

## Scope
docs/performance/phase_inventory.{md,json} and docs/performance/wall_clock_inventory.{md,json}, regenerated with the commands in their .md files.

## Out of Scope
Any change to src or to the scanners.

## Acceptance Criteria
Both sync tests green; each new entry traced to its folded source commit and confirmed a real call or read, not a regression.

## Related Tickets
None.

## Related Docs
docs/performance/phase_inventory.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
docs/performance/phase_inventory.md, phase_inventory.json, wall_clock_inventory.md, wall_clock_inventory.json

## Assumptions / Open Questions
None.

## Implementation Notes
Phase inventory: direct_calls 5 to 6, EntityGenerator.for_state, added by 4bbb0cdf5 (one generator factory takes its id base from the world), replacing `EntityGenerator(seed+tick)` plus a `_last_id` assignment at the Phase 5 world_dynamics site; same position, run_phase count unchanged at 43, later line numbers shifted. Wall-clock inventory: three reads added: DeathLedger._event time.time (8b8118fe0), RunLedger._event time.time (ecf4f33c0, 7d555533c), metrics_port_from_env os.environ (ef014783b). The two time.time reads stamp an observability event record's timestamp.

## Test Summary
tests/tools/test_perf_inventories_committed_in_sync.py plus tests/unit/kernel: 86 passed, --resource-budget off.

## Files Changed
docs/performance/phase_inventory.md, phase_inventory.json, wall_clock_inventory.md, wall_clock_inventory.json

## Completion Summary
Regenerated in 8bd8aa083.
