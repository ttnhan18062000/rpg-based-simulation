---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-INVESTIGATION
phase: done
date: 2026-06-28
tags: [simulation-quality, scoring, pillars, investigation, major-feature, observability]
---

# TCK-20260628-SIMQ-INVESTIGATION

## Title
Simulation Quality Scoring Module — Investigation & Design

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design a runtime simulation quality scoring module that evaluates every significant event,
action, and state change during a run and produces a multi-pillar quality score per
subsystem. The module must expose traceability (drill down to which events drove a bad
score), be loosely coupled to the engine (subscribes to the event bus, does not mutate
simulation state directly), and leave a door open for future engine feedback (e.g.,
mastery scoring from quality signals). This investigation phase produces the architectural
blueprint and feature plan before any implementation begins.

## Scope
- Survey all live pipeline phases (D19), RPG feature tiers (D01), and existing scoring
  infrastructure to derive a complete pillar taxonomy
- Design the 10-pillar structure grounded in concrete usage scenarios
- Define the module's architectural position, data flow, score model, traceability path,
  and API surface
- Document all decisions in `docs/plans/sim_quality_scoring_module.md`
- Produce staging artifacts: `investigation.md`, `plan.md`, `test_plan.md`
- Conflict-check against: `RunBehaviorScorecard`, `CampaignScorecard`,
  `AnalyzerQualityReporter`, `hard_law_monitor`, `audit dimensions D01–D19`

## Out of Scope
- Implementation of any scoring code
- Changes to the engine pipeline, event bus, or observability layer
- Defining exact scoring constants or grade thresholds (calibration phase, post-MVP)
- Automated test generation for the scoring module

## Acceptance Criteria
- [ ] `docs/plans/sim_quality_scoring_module.md` exists with: pillar definitions, usage
      scenarios, architecture diagram, data flow, score model, traceability design,
      API surface, and non-overlap analysis
- [ ] All 10 pillars are grounded in specific pipeline phases from D19 and feature tiers
      from D01
- [ ] Every usage scenario listed in the plan maps to at least one pillar
- [ ] Conflict analysis with existing scoring infrastructure is explicit and complete
- [ ] Investigation and plan artifacts exist in staging

## Related Tickets
- TCK-20260627-P1E-DOMAIN-INVENTORY — D19 domain phase inventory (source for pillar grounding)
- TCK-20260618-AUDIT-EPIC — parent audit programme
- TCK-20260519-SIM-OBS-PHASE2 — observability event bus (subscription infrastructure)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` — **OFFICIAL FEATURE CONTRACT** (produced by this investigation)
- `docs/audits/D19_domain_phase_inventory.md` — 53 live pipeline phases
- `docs/audits/D01_rpg_feature_impact.md` — RPG feature tiers and scores
- `docs/audits/D03_behavioral_emergence.md` — behavioral quality baseline
- `docs/audits/D06_longrun_health.md` — long-run quality observations
- `docs/audits/D04_balance_tuning.md` — balance scoring methodology (existing)
- `docs/engine/contracts/rpg_refinement_pillars.md` — 4 architectural pillars
- `docs/engine/architecture_reference.md` — architectural conventions and layer boundaries
- `docs/engine/contracts/observability_artifact_contract.md` — observability infrastructure

## Related Stored Artifacts
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/investigation.md`
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/plan.md`

## Related Epic
- TCK-20260628-SIMQ-EPIC — implementation epic (produced by this investigation)

## Related Code Areas
- `src/observability/events.py` — SimulationEvent, EventCategory taxonomy
- `src/observability/behavior/behavior_scorecard.py` — existing post-run scorecard (non-overlap)
- `src/domains/campaigns/scorecard.py` — existing campaign verdict (non-overlap)
- `src/observability/understanding/quality/quality_report.py` — analyzer quality (non-overlap)
- `src/observability/hard_law_monitor.py` — correctness monitor (non-overlap)
- `src/engine/pipeline.py` — authoritative pipeline (subscription point, not direct coupling)

## Assumptions / Open Questions
1. **Pillar count final**: 10 pillars confirmed by this investigation. Can be collapsed or
   split based on user feedback post-investigation review.
2. **Score scale**: Normalized per-tick scores (raw_delta / tick_count) chosen for
   comparability across run lengths. To be validated in calibration phase.
3. **Window-based detection**: Loop/stagnation detection uses sliding windows (100-tick
   default). Window size is a tunable constant, not hardcoded.
4. **Engine feedback path**: Read-only query interface designed but not implemented in MVP.
   The mastery/scoring feedback idea is architecturally reserved, not committed.

## Implementation Notes
This is an investigation ticket. Implementation follows in a child ticket after the
plan is reviewed and accepted. See `docs/plans/sim_quality_scoring_module.md` for the
complete feature design.

The proposed module location is `src/simulation_quality/` — sibling of `src/observability/`
and `src/domains/`, not nested inside either. This keeps the meta-evaluation layer
architecturally distinct from both the event-recording layer and the domain logic layer.

## Test Summary
N/A — investigation phase. Test plan stub included in staging artifacts.

## Files Changed
- `tickets/inprogress/TCK-20260628-SIMQ-INVESTIGATION.md` (this file)
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/investigation.md`
- `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/plan.md`
- `docs/plans/sim_quality_scoring_module.md`

## Completion Summary
Investigation and design completed. Produced `docs/plans/sim_quality_scoring_module.md` (39KB) — the official SimQ feature contract defining the 10-pillar architecture, data flow, score model, traceability design, and API surface. Conflict analysis confirmed non-overlap with RunBehaviorScorecard, CampaignScorecard, AnalyzerQualityReporter, and hard_law_monitor. Investigation spawned TCK-20260628-SIMQ-EPIC and all child implementation tickets (E1–E7, EMIT-*), which are now fully implemented and merged. Staging artifacts (investigation.md, plan.md) preserved in stored_artifacts/.
