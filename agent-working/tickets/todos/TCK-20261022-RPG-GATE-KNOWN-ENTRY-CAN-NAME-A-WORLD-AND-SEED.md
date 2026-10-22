---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED
phase: open
date: 2026-10-22
tags: []
---

# TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED

## Title
An rpg gate known entry can name the (world, seed) it owns, so owning one known validity fail does not hide every other fail of the same metric

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner: testing-planner (tools/test_architecture/**). Filed by rpg-planner for testing.

`tools/test_architecture/rpg_gate_known.yaml` entries match only `<metric_id>[:<group>]` (`known_reds.RPG_GATE_SPEC`, `rpg_gate_candidate._omissions` via `known_reds.owner_of(metric_test_id(...))`). The v1 validity rows are run rows with group `*`, so an entry cannot say which (world, seed) it owns. At v1 the owner accepted exactly three V3 known reds (urban_political/44 merchant 28 t3140; crowded_frontier/46 raider 38 t3778; frontier_living_world/44 worker 2 t3736; cutoff 2026-10-21), but the only expressible entry is a blanket `match: "V3"`, which also owns any NEW starvation death on any world or seed until it expires. The user accepted that breadth with expires_on 2026-11-05 and manual checks of each gate report (#715 comment 6337993346). The existing V1 free-meal entry has the same breadth.

## Scope
1. Optional `world` and `seeds` (or a `cases` list of {world, seed, entity_id}) on an `rpg_gate_known.yaml` entry; the matcher owns a validity fail only when its (world, seed) (and, if given, the example entity ids) are covered. Unscoped entries keep today's meaning.
2. `rpg_gate_candidate` omits only the covered (world, seed) rows; an uncovered fail of the same metric stays unowned (refuses the candidate; RED in the report).
3. Lint: shadowing rules extended to scoped entries; tests in tests/unit/tools/test_known_reds.py and the candidate/report tests.
4. Replace the blanket V3 entry with three scoped entries (each with its own ticket: N14 -> TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT, N15 x2 -> TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE), before 2026-11-05.

## Out of Scope
Changing which reds are accepted (owner); rpg simulation fixes.

## Acceptance Criteria
- A gate run with a fourth V3 fail on an uncovered (world, seed) reports it RED/unowned while the three scoped ones stay owned.
- Existing V1 entry behaviour unchanged unless scoped deliberately.
- Lands before the blanket V3 entry expires (2026-11-05).

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1; TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE.

## Related Docs
docs/plans/systemic_world/v1_disclosure.md (M5); docs/plans/systemic_world/owner_decision_memo.md.

## Related Stored Artifacts

## Related Code Areas
tools/test_architecture/known_reds.py; tools/test_architecture/rpg_gate_candidate.py; tools/test_architecture/rpg_gate_report.py; tools/test_architecture/rpg_gate_known.yaml.

## Assumptions / Open Questions
- Testing decides the schema shape (world/seeds vs cases).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
