---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE
phase: open
date: 2026-10-24
tags: []
---

# TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE

## Title
Find the cause of the 36 SimQ rows held at the v1 re-anchor: the routing worlds' decline, urban_political seed 456's early stall, wilderness_survival seed 123 SOCIAL, and 5 pillars that switched on from 0.0

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
rpg-planner's ruling (2026-10-24) on the SimQ re-anchor on baseline v1 (TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1; tables in testing's stored_artifacts) held 31 moved rows, because each shows a possible regression signal and has no proven cause. Attribution (read-only investigation; the anchors were measured at b396080cc, and the window b396080cc..341f700d0 has one SimQ src change, #645's min_events gate):
1. hero_guild_routing_seed42 and simq_routing_test_seed42 (500t and 1000t): several pillars decline together (SOCIAL about 4x down, PROGRESSION more negative, hero_guild_routing_s42_1000t PROGRESSION B->C). Inferred cause: #645's route_search change (div 2.128: node cap 3000, greedy fallback). A routing regression would show exactly here.
2. urban_political_seed456 (500t and 1000t): COGNITION is identical at 500t and 1000t (1.6025), so cognition events stop before t500; FACTION goes 0 -> -0.069. Possible early world stall. Inferred, not proven.
3. wilderness_survival_seed123_200t SOCIAL S->A: cause unknown (candidates: #645 D70 no spawning from nothing; #714 need admission).
4. Five rows went from a committed 0.0 to a grade, and no divergence or disclosure explains them (per-row cause table /mnt/data/scratch-rpg-planner/simq_112_causes.tsv, fits=no): generated_frontier_3_42_seed42_200t AGENCY C(0.0)->B(0.104); simq_scale_stress_seed42_seed42_200t AGENCY C(0.0)->B(0.073); hero_guild_routing_seed123_500t COGNITION C(0.0)->A(1.620), 140 events; simq_routing_test_seed123_500t COGNITION C(0.0)->A(1.149), 100 events; frontier_marches_seed123_200t FACTION C(0.0)->B(0.076), which also contradicts v1 disclosure S4 (faction tension never rises).

## Scope
For each group: inspect the event timeline and route outcomes on the v1 tree (341f700d0) against the pre-change tree (b396080cc or the #645 parent), and name the cause. Then either (a) intended v1 behaviour: release the held rows to the v1 values with the cause stated (rpg-planner rules; designer if a Bible meaning is involved), or (b) a regression: file the fix, and the rows stay held until it lands.

## Out of Scope
The other 500 moved rows (ruled 2026-10-24).

## Acceptance Criteria
- Each of the 36 rows has a named cause, and is either released with that cause or held under a named fix ticket.

## Related Tickets
TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing); TCK-20261019-RECORD-BASELINE-V1.

## Related Docs
docs/guidelines/intentional_divergences.md 2.128; docs/plans/systemic_world/v1_disclosure.md

## Related Stored Artifacts
.claude/worktrees/testing/agent-working/stored_artifacts/TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1/ruling_table.tsv

## Related Code Areas
src/ (route_search; the cognition, faction and social event producers)

## Assumptions / Open Questions
- Runs are short (200t-1000t on corpus worlds), but each still takes its turn on the host.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
