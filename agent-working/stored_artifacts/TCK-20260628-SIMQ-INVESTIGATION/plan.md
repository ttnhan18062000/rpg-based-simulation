---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-INVESTIGATION
artifact_type: plan
tags: [simulation-quality, scoring, pillars, architecture]
---

# Plan — TCK-20260628-SIMQ-INVESTIGATION

## Phase
Investigation only. Implementation is a separate child ticket.

## Deliverables
1. `docs/plans/sim_quality_scoring_module.md` — master feature design document
2. `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/investigation.md` — conflict analysis, existing system survey, module positioning
3. This plan file
4. Updated ticket in `tickets/inprogress/`

## Steps Completed
- [x] Semantic search: scoring, evaluation, observability, audit, event infrastructure
- [x] Read D19 domain phase inventory (all 53 live phases)
- [x] Read D01 RPG feature tiers (Tier 1/2/3 feature landscape)
- [x] Read D03/D04 behavioral emergence and balance audit methods
- [x] Read RPG refinement pillars contract
- [x] Read architecture reference conventions
- [x] Read existing scoring infrastructure (behavior scorecard, campaign scorecard, analyzer quality reporter)
- [x] Read observability event contracts and event category taxonomy
- [x] Derived 10 pillars from pipeline phases + feature tiers + usage scenarios
- [x] Conflict-checked against all existing scoring systems
- [x] Wrote investigation.md
- [x] Wrote sim_quality_scoring_module.md (master plan)
- [x] Created ticket

## Open Questions for Implementation Phase
1. Should `WorldInfrastructure` scores (capacity violations, occupancy conflicts) be surfaced
   to developers at all, or suppressed unless they exceed a threshold?
2. What is the initial window size for stagnation/loop detection? 100 ticks is proposed;
   validate against long-run health data from D06.
3. Should the `QualityHub` subscribe synchronously (in the event emission path) or
   asynchronously (via a secondary queue)? Async is safer for performance but adds latency
   to live score queries.
4. When the engine feedback path is implemented: which pillar signals are candidates for
   engine consumption first? Cognition and Agency are the most natural (mastery, doctrine).
