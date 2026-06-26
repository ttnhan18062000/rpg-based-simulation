---
status: active
layer: observability
authority: P1
audience: agent
tags: [audit, entity-inspection, decision-tooling, observability, developer-tooling]
---

# D15 — Entity Decision Inspection Tooling

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | C — Developer Tooling |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 5 / 5 |
| **Priority** | 9 |
| **Method** | code-read + review |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Can a developer see why an entity made a decision on tick N?
This is the primary debuggability question for a multi-agent simulation. "Why" means goal
selection rationale, not just the current goal label.

**Related dimensions:** D10 (Test Coverage) — cognition snapshot coverage of the goal-score
comparison gap is zero; tests exist for the snapshot artifact but not for the missing data.
D14 (Coupling Depth) — `GET /api/v1/entities/{entity_id}` exposes raw domain model, a
potential architecture violation worth investigating.

---

## Review Method

Each capability area is surveyed by reading source code and API routes, then assessed
against the primary question: "Can a developer see WHY an entity made this decision?"

"Decision" is scoped to: goal selection (why X over Y), navigation routing (why north),
and action choice (why attack over retreat). Live and historical tooling are both assessed.

### Gap Impact Scoring

Capability gaps are scored on three dimensions, each 1–5. Maximum: 15.
Higher score = higher development priority.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Debug Time Cost** | < 5 min workaround exists | 30–60 min log archaeology | Hours lost or question permanently unanswerable |
| **Frequency of Need** | Rare edge case | Weekly during active development | Required on every non-trivial debugging session |
| **Fix Leverage** | Narrow one-off fix | Closes one common debug scenario | Eliminates a whole class of black-box investigation |

---

## Capability Inventory

### 1. Live Entity Snapshot

**Endpoint:** `GET /api/v1/observability/live/entities/{entity_id}` → `EntityInspectionSnapshot`

| Field | Answers |
|---|---|
| `current_goal` | Current objective ID (string) |
| `current_target` | Navigation target coordinate |
| `current_action` | Work kind being executed |
| `combat_summary` | HP, max HP, tactical role |
| `inventory_summary` | Gold, item count, slot limit |
| `quest_summary` | Active quest IDs, names, progress ratios |
| `strategic_summary` | Project ID, blocker/contract/lead counts, boredom map |
| `recent_timeline_events` | Last N events from `EntityTimelineStore` (tick, type, severity, message) |
| `latest_rejection_reason` | Most recent non-accepted intent result or navigation failure |
| `latest_anomaly_flags` | `HIGH_OSCILLATION`, `HIGH_WAIT_COUNT`, `HIGH_BOREDOM` |

**Rating:** Answers WHAT the entity is doing. Does not answer WHY goal X was chosen over Y.

**Dashboard:** `performEntityInspection()` in the server-embedded UI — click any entity ID
in an event stream to auto-load the inspector. Usable UX.

---

### 2. Historical Entity Timeline

**Endpoint:** `GET /observability/search/entity-timeline?run_id=X&entity_id=Y`

- Merges `events` (from warehouse) + `anomalies` for one entity, sorted by tick
- Returns: `type`, `tick`, `event_type`, `event_category`, `severity`, `message`, `details`
- `run_id` is required — no anonymous "latest" lookup

**Rating:** Good post-run forensics for WHAT happened on which tick. No goal-score context,
no state reconstruction for tick N. Read-only forensic use.

---

### 3. Event and Anomaly Search

**Endpoints:** `GET /observability/search/events` · `/search/anomalies`

- Filter by `run_id`, `entity_id`, `tick_start`/`tick_end`, `severity`, `rule_id`
- Up to 100 results per query

**Rating:** Solid filtering surface for post-run investigation. Covers standard event stream.
Does not surface cognition snapshots or behavior timeline events.

---

### 4. Cognition Snapshot System

**Source:** `ObservabilityCognitionRecorder.record_tick()` in `src/observability/cognition/recorder.py`

**Artifacts produced per run:**
- `data/runs/{run_id}/cognition_graph_snapshots.jsonl` — full cognition graph per trigger
- `data/runs/{run_id}/cognition_graph_diffs.jsonl` — incremental diffs between snapshots

**What a snapshot contains:**
- `current_project_id`, `current_objective_id`
- `source_goal_score` — the *current project's* score at snapshot time
- `resulting_action`, `target_pos`
- `reason` — trigger (ANOMALY_TRIGGERED, PROJECT_CHANGED, OBJECTIVE_CHANGED, BLOCKER_CHANGED, etc.)
- `graph.nodes` / `graph.edges` — full cognition graph: goals, blockers, leads, concerns, contracts

**Capture policy (`CognitionCapturePolicy.should_capture()`):**

| Mode | State-change triggers captured | Anomaly triggers captured |
|---|---|---|
| OFF | No | No |
| LIGHT (default) | **No** | Yes |
| NORMAL / FULL / RESEARCH | **No** | Yes |
| DEBUG | Yes (all entities) | Yes |
| CERTIFICATION | Yes (selected entities) | Yes |
| LONG_RUN | **No** | Yes |

**No REST API query surface.** Snapshots are JSONL files — developer must access the
run directory directly or `grep` them.

**Rating:** Architecture is sound and the data model is rich. Two problems: (a) not queryable
via API; (b) only available in DEBUG/CERTIFICATION mode for routine strategic changes.

---

### 5. EntityTimelineStore

**Source:** `src/observability/entity_timeline.py`

Mode-bounded ring buffer — always on in LIGHT+ (default):

| Mode | Retention limit |
|---|---|
| OFF | 0 (disabled) |
| LIGHT | 20 events per entity |
| DEBUG | 500 events per entity |
| CERTIFICATION | 200 events per entity |
| LONG_RUN | 100 events per entity |

Used by `EntityInspector` to populate `recent_timeline_events` in the live snapshot.
Drops events when buffer is full (tracked via `dropped_event_count`).

**Rating:** Functional but shallow in the default (LIGHT=20) case. 20 events over a run
of thousands of ticks means most history is dropped. DEBUG mode retention (500) is
more useful but requires explicit mode switch.

---

### 6. BehaviorTimelineStore

**Source:** `src/observability/behavior/behavior_timeline_store.py`

- Per-entity bounded buffer: 500 events capacity
- Enabled when `OBS_BEHAVIOR_TIMELINE=true` (NORMAL, FULL, RESEARCH, DEBUG, CERTIFICATION)
- Stores `BehaviorEvent` objects (narrative behavioral events)
- `get_entity_timeline(run_id, entity_id)` → `EntityBehaviorTimeline`

**No REST endpoint.** In-process access only (test code, internal reporting).

**Rating:** Exists but is invisible to external tools. NORMAL mode captures it but there
is no way for a developer to query it without writing Python.

---

## Gap Analysis

### Gap 1 — No "why goal X was chosen" explanation — Impact: 15 / 15 — **RESOLVED by TCK-20260619-E22A-TRACE-WRITER**

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 5 | Cannot be answered at all from current tooling — hours or permanently unanswerable |
| Frequency of Need | 5 | Every behavioral debugging session requires understanding goal selection |
| Fix Leverage | 5 | One change (retain top-N scores at commit) eliminates an entire class of black-box work |
| **Total** | **15** | |

**The core gap.** Every inspection tool shows the entity's *current* goal ID. None show
why that goal won the scoring competition this tick.

Goal scoring happens inside `execute_brain()` → `CognitionDomain` during `_phase_collection()`.
The ranked scores for all candidate goals are computed transiently and discarded at tick
boundary. `source_goal_score` in cognition snapshots captures only the winning project's
score — not the runner-up scores.

**DX impact:** Developer cannot distinguish "entity stuck on low-priority goal because
all alternatives scored lower" from "entity stuck on high-priority goal that should be
interrupted but isn't." These require completely different fixes but look identical from
the inspection API.

**Gap from D01:** "Route decision trace is already computed every tick — this is promotion
of existing data to a queryable API, not new logic." (D01 §Decision Explanation Model)

---

### Gap 2 — No entity state reconstruction for tick N — Impact: 12 / 15

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 4 | Must cross-reference event streams manually to reconstruct what the entity knew at tick N |
| Frequency of Need | 4 | Any historical anomaly investigation requires tick-N context |
| Fix Leverage | 4 | A cognition snapshot API with tick filter closes most historical investigation needs |
| **Total** | **12** | |

`GET /observability/search/entity-timeline` returns event streams, not entity state.
There is no endpoint: "reconstruct entity 42's strategic state at tick 157."

Cognition snapshots are the nearest substitute, but: they are file-based, only written
on state-change triggers in DEBUG+ mode, and not indexed by tick.

**DX impact:** Developer investigating a behavioral anomaly at tick 500 must cross-reference
event messages manually to reconstruct what the entity knew. No single call answers the question.

---

### Gap 3 — Cognition snapshots not queryable via API — Impact: 10 / 15

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 4 | Must shell into the run directory and grep JSONL files manually |
| Frequency of Need | 3 | Needed for strategic anomaly investigation, not every debugging session |
| Fix Leverage | 3 | Adding a query route is contained; data model already exists |
| **Total** | **10** | |

Snapshots are rich and well-structured but accessible only by reading
`data/runs/{run_id}/cognition_graph_snapshots.jsonl` directly. No REST route exposes them.

**Closest analogy:** `search/events` and `search/anomalies` serve similar data through
a query layer — cognition snapshots need the same treatment.

---

### Gap 4 — Route trace not preserved — Impact: 12 / 15

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 5 | Movement bugs permanently unanswerable — path costs are discarded each tick |
| Frequency of Need | 4 | Navigation is exercised in almost every tick; movement bugs are common |
| Fix Leverage | 3 | Narrow fix (store last N route decisions in NavigationComponent) for a specific category |
| **Total** | **12** | |

Navigation decisions ("go north not south") are computed per tick but discarded.
D01 confirmed this gap. The `last_failure_reason` on `NavigationComponent` captures
only the most recent failure, not a history of route decisions and their costs.

**DX impact:** Movement bugs ("entity keeps walking into a wall") cannot be explained
without adding custom logging. The engine computes the path cost but throws it away.

---

### Gap 5 — BehaviorTimeline not accessible via API — Impact: 8 / 15

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 3 | Readable via Python in tests; only blocked for external tooling / dashboards |
| Frequency of Need | 3 | Useful for narrative event analysis but not daily debugging |
| Fix Leverage | 2 | Adding one REST endpoint is low-risk but doesn't unlock new investigation scenarios |
| **Total** | **8** | |

`BehaviorTimelineStore` collects rich narrative events in NORMAL+ modes.
There is no REST endpoint to retrieve them. The data exists in process but is
invisible to external tools, dashboards, or CLI queries.

---

### Gap 6 — Default mode (LIGHT) severely limits cognition capture — Impact: 7 / 15

> **RESOLVED: TCK-20260619-E22-DECISION-EXPLAIN (2026-06-20):** Decision trace promoted to first-class durable object; REST API at /api/v1/observability/cognition/{entity_id}/tick/{n} implemented; tick index and LIGHT-mode capture added.

| Dimension | Score | Reason |
|---|---|---|
| Debug Time Cost | 2 | Workaround is known: switch to DEBUG mode and re-run |
| Frequency of Need | 3 | Affects every LIGHT-mode run; common scenario |
| Fix Leverage | 2 | Requires policy change; risk of performance impact in LIGHT mode |
| **Total** | **7** | |

In LIGHT mode — the mode most developers run — cognition snapshots are only written
when an anomaly fires. Normal goal switching, blocker resolution, and project changes
produce no cognition artifact. Developers who don't run in DEBUG mode see a black box
for all routine strategic decisions.

---

### Gap Impact Summary

| Gap | Description | Impact Score |
|---|---|---|
| Gap 1 | No goal score comparison (WHY goal X was chosen) | **15 / 15** |
| Gap 2 | No entity state reconstruction for tick N | **12 / 15** |
| Gap 4 | Route trace not preserved | **12 / 15** |
| Gap 3 | Cognition snapshots not queryable via API | **10 / 15** |
| Gap 5 | BehaviorTimeline no API route | **8 / 15** |
| Gap 6 | LIGHT mode cognition capture limitation | **7 / 15** |

---

## Feature Rating

| Capability | Status | DX Impact |
|---|---|---|
| Live snapshot (what entity is doing) | ✅ Present | Low gap — usable now |
| Current goal / action / target | ✅ Present | Low gap |
| Rejection reason (action failures) | ✅ Present | Low gap |
| Anomaly flags (oscillation, wait, boredom) | ✅ Present | Low gap |
| Historical event timeline (post-run) | ✅ Present | Low gap |
| Anomaly search with tick range filter | ✅ Present | Low gap |
| EntityTimelineStore (ring buffer, in-proc) | ✅ Present | Low gap in DEBUG mode; LIGHT=20 is shallow |
| Dashboard entity inspection UI | ✅ Present | Good UX, click-to-inspect wired |
| WHY goal was chosen (score comparison) | ✅ Implemented (LIGHT+) | TCK-20260619-E22A-TRACE-WRITER → `decision_trace.jsonl` |
| Goal score history over ticks | ❌ Missing | High gap |
| Entity state at tick N (reconstruction) | ✅ Implemented | TCK-20260619-E22-DECISION-EXPLAIN → `GET /api/v1/observability/cognition/{entity_id}/tick/{n}` |
| Route trace / navigation WHY | ✅ Implemented | TCK-20260619-E22-DECISION-EXPLAIN → decision trace includes route cost data |
| Cognition snapshots via REST API | ✅ Implemented | TCK-20260619-E22-DECISION-EXPLAIN → tick-indexed REST query surface |
| BehaviorTimeline via REST API | ✅ Implemented | `src/api/routes/behavior.py:54` `get_entity_behavior_timeline()` |

**Score: 12 present / 1 missing. Only "Goal score history over ticks" remains unimplemented (4 of 6 originally-missing items resolved by TCK-20260619-E22-DECISION-EXPLAIN + E22A-TRACE-WRITER).**

---

## Recommended Follow-Up Tickets

| Priority | Capability | Approach |
|---|---|---|
| **P0** | Expose goal scorer output in cognition snapshot | Retain top-3 goal scores (winner + alternatives) at tick commit; add to `EntityInspectionSnapshot.goal_scores` |
| **P1** | Add REST API for cognition snapshots | `GET /observability/search/cognition-snapshots?run_id=X&entity_id=Y&tick_start=N` |
| **P1** | Expand cognition capture to NORMAL mode | Extend `CognitionCapturePolicy.should_capture()` to include strategic-change triggers in NORMAL mode |
| **P1** | Preserve route trace per entity (last N) | Store last 10 route decisions in `NavigationComponent.route_trace_history` and surface via live inspector |
| P2 | Add REST endpoint for BehaviorTimeline | `GET /observability/live/entities/{id}/behavior-timeline` |
| P2 | Increase LIGHT-mode EntityTimeline retention | Raise default from 20 → 50 events; add `timeline_mode=debug` query param to live inspect endpoint |

---

## Related Dimensions

- **D10 (Test Coverage)** — `tests/integration/observability/test_cognition_snapshot_artifact.py` exists; coverage of gap-1 (score comparison) is zero.
- **D17 (Documentation Currency)** — `architecture_reference.md §8` references the observability pipeline; accuracy not re-verified in this audit.
- **D14 (Coupling Depth)** — `GET /api/v1/entities/{entity_id}` (server.py:149) returns raw entity state, which may violate the "do not expose raw domain models" architecture rule.
- **D01 (RPG Feature Impact)** — Decision Explanation Model flagged `[PARTIAL]` at score 15/25; confirmed route trace generated but not stored.
- Prior work: **TCK-20260520-SIM-OBS-PHASE5-M22** implemented `EntityInspectionSnapshot` + live inspector V1; **`docs/engine/architecture_reference.md` §8** is the observability architecture intent document.
