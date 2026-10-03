---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D15-INSPECT
artifact_type: investigation
tags: [audit, entity-inspection, decision-tooling, observability]
---

# D15 Investigation — Entity Decision Inspection Tooling

## Evidence Sources

- `src/observability/live/entity_inspector.py` — EntityInspector, EntityInspectionSnapshot
- `src/observability/entity_timeline.py` — EntityTimelineStore (mode-bounded ring buffer)
- `src/observability/behavior/behavior_timeline_store.py` — BehaviorTimelineStore
- `src/observability/cognition/recorder.py` — ObservabilityCognitionRecorder, CognitionCapturePolicy
- `src/observability/cognition/schema.py` — snapshot/diff schema, VALID_REASONS
- `src/observability/config.py` — ObservabilityMode enum + 15 feature flags
- `src/api/routes/search.py` — 5 search endpoints
- `src/api/server.py:111–123` — live entity inspect route
- `docs/audits/D01_rpg_feature_impact.md:509–518` — Decision Explanation Model `[PARTIAL]`

## Inventory of Existing Capabilities

### Live Inspection API

`GET /api/v1/observability/live/entities/{entity_id}` → `EntityInspectionSnapshot`

Fields returned:
- `entity_id`, `exists`, `alive`
- `position`, `faction_id`, `region_id`
- `current_goal` — `entity.strategic.current_objective_id` (ID string only)
- `current_target` — navigation target coordinate string
- `current_action` — `entity.task.work_kind`
- `combat_summary` — hp, max_hp, tactical_role
- `inventory_summary` — gold, item_count, max_slots
- `quest_summary` — quest ID, name, status, progress_ratio
- `strategic_summary` — current_project_id, blockers_count, contracts_count, leads_count, boredom
- `recent_timeline_events` — last 20 events from EntityTimelineStore (tick, type, severity, message)
- `latest_rejection_reason` — from `entity.identity.latest_intent_results` (first non-accepted) or `entity.navigation.last_failure_reason`
- `latest_anomaly_flags` — HIGH_OSCILLATION, HIGH_WAIT_COUNT, HIGH_BOREDOM

Assessment: Shows WHAT entity is doing. Does NOT show WHY goal was selected over alternatives.

### Historical Entity Timeline API

`GET /observability/search/entity-timeline?run_id=X&entity_id=Y`
- Merges all `events` (from warehouse) + `anomalies` for that entity, sorted by tick
- Returns type, tick, event_type, event_category, severity, message, details
- Requires `run_id` — no tick-N lookup without knowing which run

Assessment: Good post-run forensics for WHAT happened. No goal-score context.

### Cognition Snapshot System

`ObservabilityCognitionRecorder.record_tick()` writes to:
- `data/runs/{run_id}/cognition_graph_snapshots.jsonl`
- `data/runs/{run_id}/cognition_graph_diffs.jsonl`

Snapshot record contains:
- `current_project_id`, `current_objective_id`, `source_goal_score` (current project's score only)
- `resulting_action`, `target_pos`
- `reason` — one of: ANOMALY_TRIGGERED / PROJECT_CHANGED / OBJECTIVE_CHANGED / BLOCKER_CHANGED / LEAD_CHANGED / CONCERN_CHANGED / OVERLOAD_CHANGED / DEBUG_SELECTED_ENTITY
- `graph` — nodes and edges of the cognition graph (goals, blockers, leads, concerns)

Capture policy (`CognitionCapturePolicy.should_capture()`):
- OFF mode: never
- LIGHT/LONG_RUN modes: anomaly-triggered ONLY
- DEBUG/CERTIFICATION modes: on state-change reasons + debug-selected entities
- NORMAL/FULL/RESEARCH: only anomaly-triggered (same as LIGHT for cognition snapshots)

No REST API to query cognition snapshots — file-based only.

### Behavior Timeline

`BehaviorTimelineStore` — capacity 500 per entity, in-memory.
- Enabled when `OBS_BEHAVIOR_TIMELINE` flag is true (NORMAL, FULL, RESEARCH, DEBUG, CERTIFICATION)
- No REST API endpoint exposes it
- `get_entity_timeline(run_id, entity_id)` returns `EntityBehaviorTimeline` (in-process only)

### EntityTimelineStore

Mode-bounded ring buffer: LIGHT=20, DEBUG=500, CERTIFICATION=200, LONG_RUN=100, OFF=0.
- Enabled in LIGHT+ (default mode captures entity timelines)
- `get_entity_timeline(entity_id)` used by EntityInspector to populate `recent_timeline_events`
- Drops events when buffer full (tracks `dropped_event_count`)

### Dashboard UI

`performEntityInspection()` in server.py dashboard HTML:
- Text input for entity ID + INSPECT button
- Clicking an entity ID in an event auto-loads the inspector
- Shows live snapshot fields in structured panel
- Calls `search/entity-timeline` for historical view

## Critical Gaps Found

### Gap 1: No "WHY goal was chosen" answer (P0)
`current_goal` = objective ID string. No API or artifact shows:
- What other goals were scored
- What scores they received
- Why goal X beat goal Y

`source_goal_score` in cognition snapshots = current project's score, not a comparison.
Goal scoring happens transiently in `execute_brain()` → `CognitionDomain`. Scores are not retained after the tick. The "route decision trace" referenced in D01 is generated but discarded.

### Gap 2: No "entity at tick N" historical state (P1)
Historical API requires `run_id` and returns event streams, not reconstructed state.
No endpoint: "what was entity 42's goal at tick 157?"
Cognition snapshots are nearest approximation but: (a) file-based only, (b) only written in DEBUG+ for state changes, (c) no query API.

### Gap 3: Cognition snapshots not queryable via API (P1)
Snapshots written to `cognition_graph_snapshots.jsonl` per run but not indexed or served via any REST route. Developer must `grep` the file manually.

### Gap 4: BehaviorTimeline has no API route (P2)
`BehaviorTimelineStore` captures narrative behavior events in NORMAL+ modes but there is no REST endpoint to retrieve them. In-process access only (e.g. from test code).

### Gap 5: Route trace not stored (P1 — D01 confirmation)
Navigation route decisions are computed per tick but discarded. No trace of "entity went north because path cost was lower" is preserved beyond the tick boundary.

### Gap 6: Cognition capture in LIGHT mode = anomaly-only (P2)
Default mode is LIGHT. In LIGHT mode, cognition snapshots are only written when an anomaly fires. Normal strategic evolution (goal switching, blocker resolution) produces no snapshot unless the developer explicitly runs in DEBUG/CERTIFICATION mode. Most developer sessions miss routine cognition context.

## What Works Well

- Live inspect endpoint is clean and well-structured; dashboard UX is usable
- Rejection reason surfacing (`latest_rejection_reason` from intent results) answers the WHAT-went-wrong question for action failures
- Anomaly flags (HIGH_OSCILLATION, HIGH_WAIT_COUNT, HIGH_BOREDOM) give quick behavioral health indicators
- Historical entity-timeline merges events + anomalies cleanly with tick sorting
- EntityTimelineStore is on by default (LIGHT mode) — basic event history always available
- Cognition graph structure is well-designed; snapshot schema is compact and deterministic
- `CognitionEventMapper` promotes key cognitive changes into SimulationEvents (visible in timeline)
