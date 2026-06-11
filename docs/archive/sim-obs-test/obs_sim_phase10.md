---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 10 — Cognition Graph Observability and Mining

Phase 10 should integrate the previous **strategic cognition graph export** into the Observatory.

The goal is not to log “AI thoughts” blindly. The goal is:

> When an entity behaves strangely, capture what it was trying to do, what blockers/leads/concerns/hypotheses it had, and how that cognition changed before the anomaly.

The existing foundation is useful: the current `CognitionGraphExporter` already exports persisted strategic state and has tests for empty/rich strategy, deterministic export, non-mutating behavior, metadata, and node kinds.

Also, the strategic update model already contains the right raw materials: blockers, leads, directives, projects, current project/objective, concerns, candidate zones, hypotheses, contracts, turning points, and overload fields.

---

# Phase 10 Main Objective

Build this flow:

```text
entity strategic state
  -> cognition graph snapshot
  -> cognition graph diff
  -> cognition event
  -> anomaly/evidence pack enrichment
  -> cognition mining
  -> better root-cause investigation
```

The final result should help answer:

```text
Why was this entity stuck?
Why did this quest stall?
Why did this worker keep targeting the same node?
Why did the entity keep changing projects?
Why did the economy freeze?
Why did strategic behavior become unstable?
```

---

# Important boundary

Do **not** turn this into a full “record every thought every tick” system.

That would be expensive, noisy, and misleading.

Phase 10 should capture cognition only when useful:

```text
anomaly-triggered
strategic-change-triggered
selected-entity debug mode
evidence-pack-triggered
certification-triggered
```

Not:

```text
every entity
every tick
full graph always
```

---

# Phase 10 Milestones

```text
Milestone 58 — Cognition Graph Artifact Schema
Milestone 59 — Cognition Snapshot Recorder
Milestone 60 — Cognition Diff Builder
Milestone 61 — Cognition Event Integration
Milestone 62 — Cognition Feature Extractor
Milestone 63 — Cognition Pattern Miner
Milestone 64 — Evidence Pack and Report Integration
Milestone 65 — Cognition Inspection API / CLI
Milestone 66 — Phase 10 Validation and Safety Tests
```

---

# Milestone 58 — Cognition Graph Artifact Schema

## Goal

Define stable artifacts before implementation spreads everywhere.

Phase 10 needs two main artifact files:

```text
cognition_graph_snapshots.jsonl
cognition_graph_diffs.jsonl
```

Optional later:

```text
cognition_features.parquet
cognition_patterns.json
```

---

## Snapshot record

A cognition snapshot is the strategic graph of one entity at one tick.

Minimum fields:

```text
schema_version
run_id
tick
entity_id
reason
trigger_event_id
trigger_anomaly_id
current_project_id
current_objective_id
overload_source
node_count
edge_count
graph_hash
graph
```

`reason` should be one of:

```text
ANOMALY_TRIGGERED
PROJECT_CHANGED
OBJECTIVE_CHANGED
BLOCKER_CHANGED
LEAD_CHANGED
CONCERN_CHANGED
OVERLOAD_CHANGED
DEBUG_SELECTED_ENTITY
CERTIFICATION_BOUNDARY
EVIDENCE_PACK_REQUEST
```

---

## Diff record

A cognition diff describes what changed between two snapshots.

Minimum fields:

```text
schema_version
run_id
tick
entity_id
previous_graph_hash
new_graph_hash
reason
added_nodes
removed_nodes
changed_nodes
added_edges
removed_edges
current_project_changed
current_objective_changed
blocker_delta_count
lead_delta_count
concern_delta_count
hypothesis_delta_count
project_delta_count
overload_changed
```

---

## Do not store huge raw objects blindly

Each graph node should be compact:

```text
node_id
kind
label
status
salience optional
score optional
severity optional
created_tick optional
metadata
```

Each edge should be compact:

```text
source_id
target_id
kind
metadata optional
```

---

## Tests for Milestone 58

Add these tests first, before recorder logic:

```text
tests/unit/observability/cognition/test_cognition_artifact_schema.py
```

Required tests:

```text
[x] Snapshot record serializes to JSON.
[x] Diff record serializes to JSON.
[x] Required fields cannot be missing.
[x] Unknown reason is rejected.
[x] Graph hash field is required.
[x] Empty graph snapshot is valid.
[x] Large metadata is rejected or truncated.
```

Important anti-misdirection test:

```text
[x] Schema test must not depend on real engine run.
```

Why: schema tests should fail only when the contract changes, not because simulation behavior changes.

---

# Milestone 59 — Cognition Snapshot Recorder

## Goal

Record cognition graph snapshots at controlled moments.

This should wrap the existing `CognitionGraphExporter`, not replace it.

Recommended component:

```text
ObservabilityCognitionRecorder
```

Keep the existing exporter pure:

```text
CognitionGraphExporter = read-only presenter
ObservabilityCognitionRecorder = artifact writer / policy owner
```

---

## Trigger policy

Snapshot should be recorded when:

```text
hard law violation affects entity
NavigationStuck affects entity
QuestStalled affects entity
ResourceProductionZero involves entity
project changes
objective changes
blocker added/removed
lead exhausted
concern added/removed
overload_source changes
entity selected for debug inspection
evidence pack requests it
```

Do not snapshot every cognition update.

---

## Mode behavior

| Mode            | Behavior                                                   |
| --------------- | ---------------------------------------------------------- |
| `OFF`           | no snapshots                                               |
| `LIGHT`         | anomaly-triggered snapshots only                           |
| `DEBUG`         | anomaly + strategic-change snapshots for selected entities |
| `CERTIFICATION` | deterministic boundary snapshots                           |
| `LONG_RUN`      | anomaly-triggered snapshots + compact summaries            |

The existing entity timeline already uses mode-based retention limits, so Phase 10 should follow the same design style.

---

## Snapshot selection policy

Add a component:

```text
CognitionCapturePolicy
```

Responsibilities:

```text
decide whether to snapshot
decide snapshot reason
decide full graph vs summary
decide max graph size
decide selected entities
```

---

## Output

Append to:

```text
data/runs/<run_id>/cognition_graph_snapshots.jsonl
```

---

## Tests for Milestone 59

Add:

```text
tests/unit/observability/cognition/test_cognition_capture_policy.py
tests/unit/observability/cognition/test_cognition_snapshot_recorder.py
tests/integration/observability/test_cognition_snapshot_artifact.py
```

Required tests:

```text
[x] OFF mode records nothing.
[x] LIGHT mode records anomaly-triggered snapshot.
[x] DEBUG mode records selected entity strategic change.
[x] LONG_RUN mode records compact snapshot only.
[x] Snapshot recorder uses CognitionGraphExporter.
[x] Snapshot recorder does not mutate entity.
[x] Snapshot file is valid JSONL.
[x] Snapshot includes run_id/tick/entity_id/reason.
[x] Snapshot includes graph_hash.
[x] Snapshot respects max graph size.
```

Critical anti-misdirection tests:

```text
[x] Non-anomalous entity is not snapshotted in LIGHT mode.
[x] Snapshot recorder does not call exporter for all entities every tick.
[x] Snapshot recorder does not affect final state hash.
```

These tests prevent the implementation from becoming noisy and expensive.

---

# Milestone 60 — Cognition Diff Builder

## Goal

Detect meaningful changes between cognition snapshots.

Snapshot alone answers:

```text
What did the entity know/try at this tick?
```

Diff answers:

```text
What changed?
```

That is more useful for mining.

---

## Component

```text
CognitionGraphDiffBuilder
```

Inputs:

```text
previous CognitionGraph
current CognitionGraph
```

Output:

```text
CognitionGraphDiffRecord
```

---

## Diff logic

Compare by stable IDs:

```text
node_id
edge source/target/kind
metadata fields
```

Detect:

```text
added nodes
removed nodes
changed nodes
added edges
removed edges
current_project changed
current_objective changed
overload changed
```

---

## Important rule

The diff must be deterministic.

Sort output by:

```text
node_id
edge key
field name
```

No unordered dict output.

---

## Tests for Milestone 60

Add:

```text
tests/unit/observability/cognition/test_cognition_graph_diff_builder.py
```

Required tests:

```text
[x] Same graph produces empty diff.
[x] Added blocker is detected.
[x] Removed lead is detected.
[x] Changed project status is detected.
[x] Changed current_project is detected.
[x] Changed overload_source is detected.
[x] Edge addition/removal is detected.
[x] Diff output order is deterministic.
[x] Diff does not mutate input graphs.
```

Golden-file test:

```text
[x] Rich graph A -> graph B produces exact expected diff JSON.
```

Why this matters: without a golden test, diff logic can silently drift and break mining.

---

# Milestone 61 — Cognition Event Integration

## Goal

Convert important cognition changes into semantic observability events.

Do **not** emit events for every tiny graph change.

Add curated events:

```text
StrategicProjectChanged
StrategicObjectiveChanged
StrategicBlockerAdded
StrategicBlockerResolved
StrategicLeadExhausted
StrategicConcernRaised
StrategicOverloadDetected
StrategicDetourCreated
StrategicDetourLoopSuspected
```

These should go through the existing `SimulationEvent` / `EventRecorder` pipeline.

---

## Event payload

Example:

```text
event_type = StrategicProjectChanged
event_category = strategy
entity_id = 42
tick = 1800
payload = {
  previous_project_id,
  new_project_id,
  reason,
  graph_diff_id
}
```

---

## Important boundary

Cognition events must be emitted **after authoritative state commit**, not during strategic decision logic.

The current engine already has an observability phase after state progression, so Phase 10 should hook there rather than inside low-level strategic mutation functions. The source shows cognition execution reads state and returns updates rather than mutating state directly, which supports this separation.

---

## Tests for Milestone 61

Add:

```text
tests/unit/observability/cognition/test_cognition_event_mapper.py
tests/integration/observability/test_cognition_events_recorded.py
tests/certification/test_cognition_observability_parity.py
```

Required tests:

```text
[x] Project change diff emits StrategicProjectChanged.
[x] Objective change diff emits StrategicObjectiveChanged.
[x] New blocker emits StrategicBlockerAdded.
[x] Resolved blocker emits StrategicBlockerResolved.
[x] Exhausted lead emits StrategicLeadExhausted.
[x] Overload change emits StrategicOverloadDetected.
[x] No meaningful diff emits no event.
[x] Events are recorded in simulation_events.jsonl.
[x] Enabling cognition events does not change final state hash.
[x] Enabling cognition events does not change replay hash.
```

Anti-misdirection test:

```text
[x] A metadata-only graph change does not emit high-severity strategy event.
```

This prevents noisy false positives.

---

# Milestone 62 — Cognition Feature Extractor

## Goal

Convert cognition snapshots/diffs/events into mining features.

Phase 9 mining should not read giant graphs directly.

It should use summarized cognition features.

---

## Output table

Add:

```text
cognition_features.parquet
```

or JSONL first:

```text
cognition_features.jsonl
```

One row per entity per run, or per entity per window.

Minimum fields:

```text
run_id
seed
entity_id
scenario_name
scenario_type
snapshot_count
diff_count
project_switch_count
objective_switch_count
blocker_add_count
blocker_resolve_count
unresolved_blocker_count
lead_exhaustion_count
concern_raise_count
hypothesis_change_count
detour_created_count
overload_count
max_project_age
max_blocker_age
graph_churn_rate
latest_current_project
latest_current_objective
```

---

## Derived features

Start with these:

```text
project_switch_count
blocker_count
unresolved_blocker_count
lead_exhaustion_count
detour_creation_count
overload_count
graph_churn_rate
```

Do not add all possible cognition features yet.

---

## Tests for Milestone 62

Add:

```text
tests/unit/observability/cognition/test_cognition_feature_extractor.py
tests/integration/observability/test_cognition_features_dataset.py
```

Required tests:

```text
[x] Project switches are counted correctly.
[x] Blocker add/remove counts are correct.
[x] Lead exhaustion count is correct.
[x] Overload count is correct.
[x] Empty cognition artifacts produce empty feature table, not crash.
[x] Feature output is deterministic.
[x] Feature table joins with run_id/entity_id.
```

Anti-misdirection test:

```text
[x] Feature extractor does not infer “root cause”; it only extracts features.
```

Root-cause logic belongs later.

---

# Milestone 63 — Cognition Pattern Miner

## Goal

Detect strategic/cognition behavior patterns across runs.

Add a new mining module:

```text
CognitionPatternMiner
```

---

## Initial cognition patterns

Only implement these first:

## 1. ProjectChurn

Entity changes projects too often.

Evidence:

```text
project_switch_count high
current_project changes repeatedly
no project completion
```

## 2. DetourLoop

Entity repeatedly creates detours without resolving the original blocker.

Evidence:

```text
detour_created_count high
same blocker remains active
main project remains stalled
```

## 3. StaleBlocker

A blocker remains unresolved too long while leads exist.

Evidence:

```text
blocker age > threshold
lead exists
current project unchanged
```

## 4. LeadExhaustionStorm

Many leads become exhausted in a short window.

Evidence:

```text
lead_exhaustion_count high
hypotheses collapse
entity cannot find useful targets
```

## 5. StrategicOverload

Entity repeatedly exceeds cognition profile limits.

Evidence:

```text
overload_count high
overload_source appears repeatedly
leads/concerns removed by bandwidth enforcement
```

---

## Pattern output

Write:

```text
cognition_patterns.json
```

Each pattern:

```text
pattern_id
pattern_type
severity
affected_runs
affected_entities
affected_seeds
tick_ranges
evidence
suspected_subsystems
confidence
recommended_investigation
```

---

## Tests for Milestone 63

Add:

```text
tests/unit/observability/cognition/test_cognition_pattern_miner.py
tests/integration/observability/test_cognition_pattern_mining_flow.py
```

Required tests:

```text
[x] ProjectChurn is detected from repeated project diffs.
[x] DetourLoop is detected from repeated detour diffs and same blocker.
[x] StaleBlocker is detected only when blocker age exceeds threshold.
[x] LeadExhaustionStorm is detected from lead exhaustion burst.
[x] StrategicOverload is detected from overload events.
[x] Missing cognition data returns SKIPPED_MISSING_SIGNAL.
[x] Pattern miner does not mark normal project progression as churn.
```

Critical negative tests:

```text
[x] One project switch is not ProjectChurn.
[x] One detour is not DetourLoop.
[x] Old blocker without available lead is not StaleBlocker.
[x] Lead exhaustion after successful exploration is not automatically failure.
```

These negative tests are essential to avoid misleading implementation.

---

# Milestone 64 — Evidence Pack and Report Integration

## Goal

Enrich Phase 9 evidence packs and Observatory reports with cognition evidence.

When an anomaly happens, include:

```text
cognition before
cognition after
cognition diff
cognition feature summary
cognition pattern matches
```

---

## Evidence pack additions

Add files:

```text
cognition_snapshot_before.json
cognition_snapshot_after.json
cognition_diff.json
cognition_feature_summary.json
cognition_pattern_summary.json
```

For many affected entities, add a compressed summary:

```text
affected_entities_cognition_summary.json
```

---

## Report additions

Add section:

```text
Strategic Cognition Evidence
```

Subsections:

```text
Current project/objective
Active blockers
Known leads
Concerns
Hypotheses
Overload status
Recent cognition changes
Potential cognition patterns
```

---

## AI Agent input

Do not feed full graphs by default.

Feed this:

```text
top affected entities
current project/objective
unresolved blockers
known leads
project switch count
detour count
overload count
graph diff summary
```

---

## Tests for Milestone 64

Add:

```text
tests/unit/observability/cognition/test_cognition_evidence_pack_builder.py
tests/integration/observability/test_cognition_evidence_pack_flow.py
tests/integration/observability/test_cognition_report_section.py
```

Required tests:

```text
[x] Evidence pack includes cognition snapshot before anomaly.
[x] Evidence pack includes cognition snapshot after anomaly.
[x] Evidence pack includes diff.
[x] Evidence pack includes compressed summary for many entities.
[x] Report includes cognition section when cognition data exists.
[x] Report clearly says cognition data missing when unavailable.
[x] AI input summary excludes huge raw graph by default.
```

Anti-misdirection test:

```text
[x] Evidence pack does not claim cognition root cause; it only provides evidence.
```

Root cause should be phrased as:

```text
likely related to unresolved blocker
```

not:

```text
definitely caused by unresolved blocker
```

---

# Milestone 65 — Cognition Inspection API / CLI

## Goal

Let developers inspect cognition graph data without opening raw files.

Keep it read-only.

---

## CLI commands

Add:

```text
rpg-observe cognition snapshot <run_id> <entity_id> --tick <tick>
rpg-observe cognition diff <run_id> <entity_id> --from <tick1> --to <tick2>
rpg-observe cognition features <run_id> <entity_id>
rpg-observe cognition patterns <run_id>
```

---

## API endpoints

Add read-only endpoints:

```text
GET /observability/history/runs/{run_id}/cognition/entities/{entity_id}/snapshots
GET /observability/history/runs/{run_id}/cognition/entities/{entity_id}/diffs
GET /observability/history/runs/{run_id}/cognition/entities/{entity_id}/features
GET /observability/history/runs/{run_id}/cognition/patterns
```

Optional live endpoint:

```text
GET /observability/live/entities/{entity_id}/cognition
```

Only return compact summary by default.

---

## Safety rules

```text
read-only
no arbitrary path access
limit result size
pagination required
full graph requires explicit flag
```

---

## Tests for Milestone 65

Add:

```text
tests/api/test_cognition_history_api.py
tests/cli/test_cognition_cli.py
```

Required tests:

```text
[x] Get cognition snapshots by entity.
[x] Get cognition diffs by entity.
[x] Get cognition features.
[x] Get cognition patterns.
[x] Missing cognition artifacts return clear response.
[x] Path traversal is blocked.
[x] Large graph response is paginated or rejected.
[x] Full graph requires explicit query flag.
```

Anti-misdirection test:

```text
[x] API summary endpoint does not return full graph by default.
```

---

# Milestone 66 — Phase 10 Validation and Safety Tests

## Goal

Prevent this feature from becoming noisy, expensive, or misleading.

This milestone is mandatory.

---

# Test group 1 — Exporter contract tests

Existing tests already verify important exporter behavior: empty/rich strategy, determinism, non-mutation, metadata, and node kinds. Keep those and extend them.

Add:

```text
tests/unit/strategic/test_cognition_graph_export_contract_v2.py
```

Required tests:

```text
[x] Export includes graph schema version.
[x] Export includes stable graph hash.
[x] Export node order is deterministic.
[x] Export edge order is deterministic.
[x] Export handles missing strategic component safely.
[x] Export handles unknown node metadata safely.
[x] Export does not include volatile runtime-only fields.
```

---

# Test group 2 — Determinism / parity tests

Add:

```text
tests/certification/test_cognition_observability_parity.py
```

Required tests:

```text
[x] Same scenario with cognition observability OFF.
[x] Same scenario with cognition observability LIGHT.
[x] Final state hash is identical.
[x] Replay hash is identical.
[x] Logical events are identical except cognition observability artifacts.
[x] Enabling snapshots does not change entity strategy.
```

This is the most important Phase 10 test group.

---

# Test group 3 — Performance tests

Add:

```text
tests/perf/test_cognition_observability_overhead.py
```

Required tests:

```text
[x] LIGHT mode overhead is under configured budget.
[x] LONG_RUN mode artifact size is under budget.
[x] DEBUG selected-entity mode does not export all entities.
[x] Snapshot trigger count is bounded.
[x] Graph size cap is enforced.
```

Important test:

```text
[x] 1,000 entities / N ticks does not create 1,000 * N graph snapshots.
```

This prevents accidental all-entity-per-tick export.

---

# Test group 4 — Negative semantic tests

Add:

```text
tests/unit/observability/cognition/test_cognition_false_positive_guards.py
```

Required tests:

```text
[x] Normal project completion is not ProjectChurn.
[x] Normal detour completion is not DetourLoop.
[x] Temporary blocker is not StaleBlocker.
[x] Single exhausted lead is not LeadExhaustionStorm.
[x] One overload event is not StrategicOverload.
```

These tests are critical because cognition mining can easily become noisy.

---

# Test group 5 — Real-flow integration test

Add:

```text
tests/integration/observability/test_cognition_observability_e2e.py
```

Flow:

```text
build scenario with strategic entity
run simulation
trigger strategic change
record cognition snapshot
record cognition diff
emit cognition event
generate analysis report
build evidence pack
mine cognition features
```

Assertions:

```text
[x] cognition_graph_snapshots.jsonl exists.
[x] cognition_graph_diffs.jsonl exists.
[x] simulation_events.jsonl includes cognition event.
[x] report includes cognition evidence.
[x] evidence pack includes cognition summary.
[x] final state hash unchanged by observability.
```

---

# Phase 10 End-to-End Flow

At the end of Phase 10:

```text
1. Strategic system updates entity cognition.
2. State commit happens.
3. Observability phase checks capture policy.
4. CognitionGraphExporter exports selected graph.
5. Snapshot recorder writes cognition_graph_snapshots.jsonl.
6. Diff builder compares previous/current graph.
7. Diff recorder writes cognition_graph_diffs.jsonl.
8. Event mapper emits curated cognition SimulationEvents.
9. Feature extractor produces cognition features.
10. Pattern miner detects strategic behavior patterns.
11. Evidence pack includes cognition evidence.
12. Reports and AI investigation use cognition summaries.
13. CLI/API allow read-only cognition inspection.
```

---

# Minimal Phase 10 Data Coverage

## Minimum snapshot triggers

```text
NavigationStuck
QuestStalled
ResourceProductionZero
project changed
blocker changed
lead exhausted
overload changed
```

## Minimum cognition events

```text
StrategicProjectChanged
StrategicBlockerAdded
StrategicBlockerResolved
StrategicLeadExhausted
StrategicOverloadDetected
StrategicDetourCreated
```

## Minimum cognition features

```text
project_switch_count
blocker_add_count
blocker_resolve_count
unresolved_blocker_count
lead_exhaustion_count
detour_created_count
overload_count
graph_churn_rate
```

## Minimum cognition patterns

```text
ProjectChurn
DetourLoop
StaleBlocker
LeadExhaustionStorm
StrategicOverload
```

---

# Implementation order

```text
1. Milestone 58 — Artifact schema
2. Milestone 59 — Snapshot recorder
3. Milestone 60 — Diff builder
4. Milestone 61 — Cognition events
5. Milestone 62 — Feature extractor
6. Milestone 63 — Pattern miner
7. Milestone 64 — Evidence/report integration
8. Milestone 65 — API/CLI
9. Milestone 66 — Validation and safety tests
```

Do not start mining before snapshots/diffs are stable.

Do not start report/AI integration before feature extraction is stable.

---

# Biggest implementation risks

| Risk                          | Prevention                          |
| ----------------------------- | ----------------------------------- |
| Exporting too much data       | Trigger policy + mode limits        |
| Changing simulation behavior  | Post-commit hook + parity tests     |
| Noisy false positives         | Negative semantic tests             |
| Misleading AI reports         | Evidence-only summaries             |
| Huge evidence packs           | Compact summaries by default        |
| Schema drift                  | Golden schema tests                 |
| Non-deterministic graph order | sorted nodes/edges + hash tests     |
| Expensive graph export        | selected entities only + perf tests |

---

# Final acceptance criteria

Phase 10 is complete when:

```text
[x] Cognition graph snapshot artifact exists.
[x] Cognition graph diff artifact exists.
[x] Snapshot capture is mode-based and trigger-based.
[x] Diff builder is deterministic.
[x] Curated cognition events are emitted.
[x] Cognition features are extracted.
[x] Cognition patterns are mined.
[x] Evidence packs include cognition summaries.
[x] Reports include cognition evidence.
[x] CLI/API can inspect cognition artifacts.
[x] No full-entity-per-tick graph export happens.
[x] Enabling cognition observability does not change final state hash.
[x] Negative tests prevent normal behavior from being flagged as anomalies.
```

# My recommendation

Phase 10 should be named:

```text
Cognition Graph Observability and Strategic Behavior Mining
```

This phase fills the missing layer between:

```text
what happened
```

and:

```text
what the entity believed / attempted / was blocked by
```

That is exactly what your Observatory needs for deep investigation of strategic entity behavior.
