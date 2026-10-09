---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261009-PERF-M2-DETAILED-PLAN
phase: done
date: 2026-10-09
tags: [performance, planning, benchmarking]
---

# TCK-20261009-PERF-M2-DETAILED-PLAN

## Title
Perf M2: detailed delivery plan for the remaining performance-contract work (T02b to T06 and the M1 reruns)

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
M1 closed on 2026-10-09 (#473). M2 has T01 (clause inventory) and T02 (provisional identity schema) done;
T03 to T06 and the reruns the M1 invalidation ledger hands to M2 are unplanned. Write the ordered M2 plan
into the M2 epic document: tickets, sequence, files, the owner lifts and owner decisions each one needs,
and how the open P2 todo `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE` fits.

## Scope
1. Re-read the T02 schema against the M1 ledger (schema §8 asks for this) and record the identity fields
   M1 showed are missing.
2. Add a "Delivery plan" section to `performance_m2_performance_contract_epic.md`: owner decisions,
   ticket list with dependencies and file lists, sequence, and what stays out of M2.
3. Update the M2 entry conditions and the roadmap milestone-map row to point at the plan.

## Out of Scope
- Filing the child tickets (offered as `/create-tickets` after this lands).
- Any `src/`, test or baseline change, and any measurement.
- Deciding the owner questions; the plan states them with a recommendation.

## Acceptance Criteria
1. The M2 epic has a delivery plan naming every remaining ticket with dependencies, files, and the owner
   lift or decision it waits on.
2. The schema revalidation findings are recorded with their source (ledger row or merged change).
3. The roadmap's M2 row links the plan. Frontmatter validates.

## Related Tickets
- `TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER`
- `TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA`
- `TCK-20261003-PERF-M2-CLAUSE-INVENTORY`
- `TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE`

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`
- `docs/performance/benchmark_identity_schema.md`
- `docs/performance/baseline_invalidation_ledger.md`
- `docs/performance/performance_clause_inventory.md`
- `docs/engine/performance_contract.md`

## Related Stored Artifacts
None.

## Related Code Areas
None changed. Read: `src/perf/`, `tools/perf/`, `src/observability/reporting/`, `src/config/profiles.py`,
`src/engine/work_units.py`.

## Assumptions / Open Questions
- The RPG-core entry gate has not fully lifted, so every `src/` file in the plan needs a named owner lift
  and every measurement stays provisional. The plan lists the files per ticket so the lift can be asked once.

## Implementation Notes
Plan written as a new "Delivery plan" section in the M2 epic: eight owner decisions (OD-1 to OD-8) with recommendations, a schema revalidation against M1 (R-1 to R-5), and seven tickets plus the existing P2 todo, with order, dependencies and per-file lift needs. Revalidation found two missing blocking identity fields: the signal contract and work-model version (DEV-018), and the cost-accounting version (DEV-017). The second is the schema-level cause of the vacuous sweep-gate pass.

Follow-up on #475 (2026-10-09): rpg-planner answered Ask 13. The owner accepted OD-1 to OD-8 as recommended, including the OD-8 lift recorded as roadmap gate item 8, and accepted testing-planner's shared baseline-change policy and registry module for T05. The OD-2/OD-3 refinements are folded into T03/T05, and T08's timing follows Ask 13.

## Test Summary
Docs only. `validate_frontmatter.py` passes on the three files; `pytest tests/docs -q`: 69 passed, 2 skipped, 1 xfailed.

## Files Changed
- `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (M2 row)
- `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md` (Ask 13)
- this ticket

## Completion Summary
The M2 delivery plan is in the epic. Nothing is filed or implemented: the child tickets wait for the owner's answers to OD-1 to OD-8, then `/create-tickets` into `todos/perf-m2-contract/`.
