---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-AUDIT-D06-LONGRUN
phase: open
date: 2026-06-19
tags: [audit, long-run, simulation-health, performance, attrition, ecology]
---

# TCK-20260619-AUDIT-D06-LONGRUN

## Title
Audit D06 — Long-Run Simulation Health (1,000-tick run)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Run 1,000-tick sandbox_world simulations (seeds 42 and 137) now that RC1/RC2/RC3 are fixed, and assess: tick compute stability over time, entity attrition vs replenishment, resource node depletion/recovery, behavioral continuity (do entities maintain active goal pursuit past tick 200), and rejection accumulation patterns.

## Scope
- Seeds 42 and 137, 1,000 ticks each
- Measure: tick compute ms trend, alive entity count over time, resource node charges over time, behavioral event density across tick windows, rejection counts
- Compare early (1–200) vs late (800–1,000) windows to detect degradation

## Out of Scope
- Code changes
- Fixing any new findings (audit only)

## Acceptance Criteria
1. Both 1,000-tick runs complete with LifecycleOutcome.SUCCESS
2. D06 audit document written to `docs/audits/D06_longrun_health.md`
3. Ticket moved to done, working log updated

## Related Tickets
- TCK-20260618-AUDIT-D03-BEHAVIOR (behavioral emergence — D06 was blocked pending RC fixes)
- TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING
- TCK-20260619-FIX-NEAR-SERVICE-REGION
- TCK-20260619-FIX-PERF-BUDGETS-RESET

## Related Docs
- `docs/audits/D03_behavioral_emergence.md`
- `docs/engine/performance_contract.md`
- `docs/mechanics/05_world_evolution.md`
- `docs/audits/audit_dimensions.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260518-LONG-RUN-STABILITY/`

## Related Code Areas
- `src/engine/kernel.py`
- `src/world/providers/resources.py`
- `src/domains/adventure/phase.py`

## Assumptions / Open Questions
- 1,000-tick run produces enough data to assess trends; 5,000-tick run exists in prior stability harness but is not needed for this audit
- Attrition-without-replenishment (D03 F4) may become critical at 1,000 ticks if SpawnService isn't triggered

## Implementation Notes
Run: `python3 -m src cli --ticks 1000 --seed 42` and `--seed 137`
Observe metric_windows.jsonl across full run range.

## Test Summary
N/A — observation-only audit.

## Files Changed
- `docs/audits/D06_longrun_health.md` (new)
- `tickets/done/TCK-20260619-AUDIT-D06-LONGRUN.md`

## Completion Summary
(fill on completion)
