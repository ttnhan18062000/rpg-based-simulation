---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D15-INSPECT
phase: done
date: 2026-06-18
tags: [audit, entity-inspection, decision-tooling, observability, developer-tooling]
---

# TCK-20260618-AUDIT-D15-INSPECT

## Title
Audit D15 — Entity Decision Inspection Tooling

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit the entity decision inspection tooling. Can a developer see WHY an entity made
a decision on tick N? This covers live APIs, historical timeline, cognition snapshots,
behavior timeline, and decision tracing gaps.

## Scope
- Live entity inspection API (`/api/v1/observability/live/entities/{id}`)
- Historical timeline API (`/observability/search/entity-timeline`)
- Cognition snapshot + diff system (`ObservabilityCognitionRecorder`)
- `EntityTimelineStore`, `BehaviorTimelineStore`
- `ObservabilityConfig` mode/flag matrix
- Dashboard inspection UI

## Out of Scope
- Implementing missing capabilities (create separate tickets)
- Performance profiling of the observability pipeline
- Warehouse backend internals

## Acceptance Criteria
- [x] Live inspection capabilities enumerated and rated
- [x] Historical inspection capabilities enumerated and rated
- [x] Cognition snapshot system coverage assessed
- [x] Key gaps identified with DX impact
- [x] `docs/audits/D15_entity_decision_inspection.md` produced
- [x] `audit_dimensions.md` D15 state updated to `done`

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent epic)
- TCK-20260520-SIM-OBS-PHASE5-M22 (Entity Inspector V1)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` — Decision Explanation Model `[PARTIAL]`
- `docs/engine/architecture_reference.md` §8 — Observability conventions

## Related Code Areas
- `src/observability/live/entity_inspector.py`
- `src/observability/entity_timeline.py`
- `src/observability/behavior/behavior_timeline_store.py`
- `src/observability/cognition/recorder.py`
- `src/observability/cognition/schema.py`
- `src/observability/config.py`
- `src/api/routes/search.py`
- `src/api/server.py`

## Assumptions / Open Questions
- "Decision" = goal selection rationale, not just the current goal label
- LIGHT is the default mode; capabilities in higher modes are opt-in

## Implementation Notes
Full investigation in `staging_artifacts/TCK-20260618-AUDIT-D15/investigation.md`.

## Test Summary
N/A — audit produces documentation, not code.

## Files Changed
- `docs/audits/D15_entity_decision_inspection.md` — created
- `docs/audits/audit_dimensions.md` — D15 state updated to `done`, insights added
- `staging_artifacts/TCK-20260618-AUDIT-D15/investigation.md` — created
- `tickets/done/TCK-20260618-AUDIT-D15-INSPECT.md` — moved here

## Completion Summary

**Score: 8 capabilities present / 6 missing. All 6 missing cluster around the "WHY" question.**

**P0 gap — Goal score comparison missing:**
Live inspect API shows `current_goal` (objective ID string). Goal scoring in `execute_brain()`
computes ranked scores for all candidates per tick but discards them at tick boundary. No
API or artifact shows why goal X beat goal Y. `source_goal_score` in cognition snapshots
captures the winning project's score only — not alternatives.

**P1 gaps:**
- Cognition snapshots exist but are file-based JSONL only — no REST query API
- Cognition snapshots only written on strategic changes in DEBUG/CERTIFICATION mode; LIGHT/NORMAL miss routine goal switching
- Route trace computed per tick but discarded (D01 confirmation)
- No "entity state at tick N" reconstruction endpoint

**What works well:**
- Live snapshot for current state is clean and dashboard-integrated
- `latest_rejection_reason` from intent results answers action-failure questions
- Historical entity-timeline merges events + anomalies cleanly
- `BehaviorTimelineStore` architecture is sound; needs a REST route
- Cognition graph schema is rich and deterministic

**Recommended P0 follow-up:** Retain top-3 goal scores (winner + alternatives) at tick commit
in `EntityInspectionSnapshot.goal_scores` — promotes existing computed data to queryable form,
no new simulation logic required.
