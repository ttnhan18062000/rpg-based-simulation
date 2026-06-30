---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260628-SIMQ-EPIC
phase: open
date: 2026-06-28
tags: [simulation-quality, scoring, pillars, epic, major-feature]
---

# TCK-20260628-SIMQ-EPIC

## Title
Simulation Quality Scoring Module — Implementation Epic

## Status
INPROGRESS

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Implement the Simulation Quality Scoring Module: a runtime, per-event, multi-pillar
quality evaluation layer that scores simulation health across 10 subsystem pillars,
exposes a REST API for live and post-run quality data, and writes `quality_scores.jsonl`
and `quality_report.json` per run. The module is non-blocking, independently disableable,
and separate-process-ready.

## Scope
Full implementation of `src/simulation_quality/` as specified in
`docs/simulation_quality/quality_scoring_contract.md`, including:
- All 10 pillar scorers with scoring rules from §5
- QualityHub subscriber wiring and error isolation
- PillarAccumulator with window-based loop detection
- Persistence layer (quality_scores.jsonl, quality_report.json)
- REST API (/api/v1/quality/*)
- Full test suite (unit, integration, regression, performance, scenario coverage)
- Calibration run and grade threshold constants

## Out of Scope
- Per-entity quality profiles
- Historical cross-run comparison infrastructure
- WebSocket push alerts
- ML-based anomaly detection
- Engine feedback path (mastery from quality scores) — reserved for post-MVP epic
- Changes to the simulation pipeline, event bus, or existing observability layer

## Acceptance Criteria
See `docs/simulation_quality/quality_scoring_contract.md` §12 for the full checklist.
All criteria in §12 must pass before this epic closes.

## Related Tickets

### Investigation (prerequisite — done)
- TCK-20260628-SIMQ-INVESTIGATION — investigation, pillar design, plan docs

### Child tickets (implementation sequence)
- TCK-20260628-SIMQ-E1-FOUNDATION — Core models & data layer ✓ done
- TCK-20260628-SIMQ-E2-HUB-CORE — Hub wiring + Agency & Combat scorers ✓ done
- TCK-20260628-SIMQ-E3-SCORERS-A — Cognition, Faction, Economy, Progression scorers ✓ done
- TCK-20260628-SIMQ-E4-SCORERS-B — Social, Information, World Dynamics, Narrative scorers ✓ done
- TCK-20260628-SIMQ-E5-API — REST API + post-run artifact generation ✓ done
- TCK-20260628-SIMQ-E6-TESTS — Full test suite ✓ done
- TCK-20260628-SIMQ-E7-CALIBRATE — Calibration & grade threshold tuning ✓ done (re-run pending TCK-20260630-SIMQ-RECALIBRATE)

### Integration gap tickets (D20 audit findings — blocking full acceptance)
- TCK-20260630-SIMQ-WIRE-KERNEL — Wire quality_fn into kernel event pipeline (G1 + G3, **P1**)
- TCK-20260630-SIMQ-WIRE-SERVER — Wire set_quality_hub() into server lifespan (G2, **P1**)
- TCK-20260630-SIMQ-RECALIBRATE — Re-run calibration with live event data (blocked on WIRE-KERNEL)

### Upstream dependencies
- TCK-20260519-SIM-OBS-PHASE2 — Observability event bus (subscription infrastructure)
- TCK-20260627-P1E-DOMAIN-INVENTORY — D19 domain phase inventory (scorer grounding)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` — **AUTHORITATIVE REFERENCE**
- `docs/plans/sim_quality_scoring_module.md` — investigation source (historical)
- `docs/audits/D19_domain_phase_inventory.md` — pipeline phase anchors for all scorers
- `docs/audits/D01_rpg_feature_impact.md` — RPG feature tiers for pillar priority
- `docs/engine/architecture_reference.md` — coupling laws, layer boundaries
- `docs/performance/perf_baseline_policy.md` — performance constraints

## Related Code Areas
- `src/simulation_quality/` — new module (this epic)
- `src/observability/events.py` — ObservabilityEventEnvelope (input to QualityHub)
- `src/observability/queue.py` — BoundedObservabilityQueue (subscription point)
- `src/api/` — REST routes (output from QualityHub)

## Assumptions / Open Questions
1. Scorer registration: `SCORER_REGISTRY` uses a dict mapping `event_type → list[PillarScorer]`.
   If the event taxonomy changes (new event_types added), scorers must be updated
   to register for new types.
2. Grade thresholds are estimates until E7-CALIBRATE runs baseline scenarios. Do not
   treat initial thresholds as stable until that ticket closes.
3. Separate-process promotion: if E6 performance tests show >5% drain worker overhead,
   evaluate moving QualityHub to a QualityWorker process before E7.

## Implementation Notes
Implementation order is strict: E1 → E2 → (E3 ‖ E4) → E5 → E6 → E7.
E3 and E4 can run in parallel since they produce independent scorer files with no
cross-dependency. E5 requires E3 and E4 complete (needs all pillar accumulators).
E6 requires E5 (needs full API for integration tests). E7 requires E6 (calibration
runs against the complete implementation).

Every child ticket must update `docs/simulation_quality/quality_scoring_contract.md`
if its implementation deviates from the specification (scoring formula changes, new
tags, revised grade thresholds, API schema changes). The contract is the source of
truth; it must stay in parity with the code.

## Test Summary
Delegated to TCK-20260628-SIMQ-E6-TESTS. See §11 of the contract for full taxonomy.

## Files Changed
- `tickets/inprogress/TCK-20260628-SIMQ-EPIC.md` (this file)
- Child tickets: see Related Tickets above

## Completion Summary
Pending. Epic closes when all 7 child tickets are done and §12 acceptance criteria pass.
