---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, cognition-graph, observability, analytics, visualization, tuning, data-engineering, parquet, duckdb]
---

# Idea: Cognition Graph as a First-Class Analytics Object

> **Maturity: IDEA** — Not scheduled. Recommend before or alongside E12 Balance Baseline and E22 Decision Explanation.

> **Status review (2026-08-22):** re-investigated for staleness. The gap this doc describes (cognition
> artifacts never reach `AnalyticsDatasetBuilder`/Parquet/DuckDB) is confirmed still 100% open — zero
> references to "cognition" anywhere in `src/observability/analytics/{dataset,exporter,query}.py`. Two
> things changed since this doc was written, both load-bearing for a re-scope:
>
> 1. **New cost constraint, not accounted for below.** `TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`
>    (done) broadened `CognitionCapturePolicy.should_capture()` so NORMAL/FULL/RESEARCH modes now capture
>    cognition-graph state changes (previously DEBUG/CERTIFICATION only) — but it also measured real
>    corpus storage cost (5.9MB per 150-tick run, 143MB per 2000-tick run) and explicitly judged
>    corpus-wide capture too expensive for `tools/calibrate_simq.py`'s calibration harness, which was left
>    unchanged. Any ticket built from this idea needs a storage-cost budget for the proposed Parquet
>    tables — this doc has none today.
> 2. **"Relationship to Planned Tickets" below is written forward-looking about work that has since
>    shipped.** E22-DECISION-EXPLAIN, E12-BALANCE-BASELINE, and E11D-SCORING-CAL are all in
>    `tickets/done/` now. E22 shipped `decision_trace_writer.py` + a tick-index sidecar — matching this
>    doc's own anticipated shape, and its §3c prerequisite (`decision_trace.jsonl` existing) is genuinely
>    satisfied today, unlike at write time. But E12 already ran its measurement pass *without* cognition
>    data, so the doc's closing recommendation ("wire before E12 measurement begins") describes a window
>    that already closed — read §"E12-BALANCE-BASELINE" below as a missed-opportunity record, not a live
>    recommendation, and treat any real ticket as retroactive wiring rather than a pre-measurement gate.
>
> The core technical proposal (Layers 1-3 below) is otherwise still accurate and worth scoping — this is a
> rewrite-before-ticketing, not a superseded idea.

---

## Problem

The engine has a rich cognition observability stack that is almost entirely disconnected from its analytics pipeline:

**What exists and records data:**
- `CognitionGraphExporter` — per-entity structural snapshot (`cognition_e{id}.json`, `cognition_graph_snapshots.jsonl`)
- `CognitionGraphDiffBuilder` — deterministic tick-to-tick delta (`cognition_graph_diffs.jsonl`)
- `CognitionFeatureExtractor` — aggregated run-level features per entity: `graph_churn_rate`, `max_blocker_age`, `overload_count`, `project_switch_count`, `blocker_add/resolve_count`, `lead_exhaustion_count` → `cognition_features.jsonl`
- `CognitionPatternMiner` — detects 5 behavioral failure patterns: `ProjectChurn`, `DetourLoop`, `StaleBlocker`, `LeadExhaustionStorm`, `StrategicOverload` → `cognition_patterns.json`
- `viz_strategy.html` — drag-and-drop viewer for a single `cognition_e{id}.json`

**What the analytics pipeline handles (`AnalyticsDatasetBuilder`, `ArtifactExporter`, `DuckDBQueryService`):**
- `simulation_events.jsonl` → Parquet
- `metric_windows.jsonl` → Parquet
- `anomalies.json` → Parquet
- `run_manifest.json` → Parquet
- DuckDB queries: `worst-runs`, `anomaly-summary`

**The gap**: cognition artifacts (`cognition_graph_snapshots.jsonl`, `cognition_graph_diffs.jsonl`, `cognition_features.jsonl`, `cognition_patterns.json`) are written but never fed into `AnalyticsDatasetBuilder`, never converted to Parquet, never surfaced in `DuckDBQueryService`. `CognitionPatternMiner` output is written to a file that nothing reads. `viz_strategy.html` cannot play back a run, compare entities, or show temporal trajectory.

The result: to validate whether an entity's cognition is "going in the right direction," a developer today must manually open individual JSON files per entity, visually parse graph structure, and mentally correlate across ticks — with no query surface and no aggregate view.

---

## Idea

Close the gap between **what is recorded** and **what is queryable and renderable** across three layers:

### Layer 1 — Data Engineering: Wire Cognition into the Analytics Pipeline

**1a — Post-run pipeline integration**

After each run completes (in the `Persistence` phase post-run hook), automatically invoke:
```python
CognitionFeatureExtractor.extract_features(run_dir, spec_data)
CognitionPatternMiner.mine_patterns(run_dir, spec_data)
```
Currently these must be called explicitly outside the engine. They should be wired into the standard post-run finalization alongside `metric_windows.jsonl` and `anomalies.json`.

**1b — Parquet tables for cognition data**

Add two new artifact types to `ArtifactExporter` and `AnalyticsDatasetBuilder`:

```python
# cognition_features.parquet schema
("run_id", pa.string())
("entity_id", pa.int64())
("scenario_name", pa.string())
("project_switch_count", pa.int64())
("blocker_add_count", pa.int64())
("blocker_resolve_count", pa.int64())
("unresolved_blocker_count", pa.int64())
("lead_exhaustion_count", pa.int64())
("overload_count", pa.int64())
("max_project_age", pa.int64())
("max_blocker_age", pa.int64())
("graph_churn_rate", pa.float64())

# cognition_patterns.parquet schema
("run_id", pa.string())
("entity_id", pa.int64())
("pattern_type", pa.string())   # ProjectChurn | DetourLoop | StaleBlocker | ...
("severity", pa.string())       # CRITICAL | WARNING
("confidence", pa.float64())
("tick_start", pa.int64())
("tick_end", pa.int64())
("evidence_json", pa.string())  # JSON-encoded evidence dict
```

**1c — DuckDB query expansion**

Add cognition-aware predefined queries to `DuckDBQueryService`:

```sql
-- "churn-by-entity": entities ranked by project_switch_count descending
-- "overloaded-entities": entities with overload_count >= threshold
-- "stale-blockers": entities with max_blocker_age >= 200 ticks
-- "pattern-summary": count by pattern_type and severity across all entities in run
-- "entity-health": composite score = f(churn_rate, unresolved_blockers, overload_count)
```

**1d — CognitionHealthScore: scalar per entity per run**

Derive a single `cognition_health_score` (0.0–1.0, lower = worse) from features:

```
health = 1.0
health -= min(0.30, churn_rate * 10)       # heavy penalize rapid switching
health -= min(0.25, unresolved_blockers * 0.05)
health -= min(0.25, (max_blocker_age / 400) * 0.25)
health -= min(0.20, overload_count * 0.04)
```

Feed this into `run_manifest.json` as a per-entity summary alongside the run-level `health_score`. Enables DuckDB to filter "runs with at least one entity below 0.4 cognitive health."

---

### Layer 2 — Visualization: Temporal and Cross-Entity Views

**2a — Temporal playback in viz_strategy.html**

Extend the existing drag-and-drop tool to accept `cognition_graph_snapshots.jsonl` (not just single `cognition_e{id}.json`). Add a tick slider: scrubbing the slider replays the entity's mental state across ticks, with nodes appearing/disappearing as the diff stream dictates.

Key rendering cues from `bounded_cognition_ui_contract.md`:
- `is_overloaded = true` → red border on graph header
- `active_slice_used / active_slice_limit > 0.8` → yellow/red budget bar
- Diff-highlighted nodes: added nodes in green, removed in red, changed in orange

**2b — Run-level aggregate view**

A separate HTML report (generated post-run by `CognitionPatternMiner`) showing:
- Pattern summary table: pattern_type × severity × affected entity count
- Churn heatmap: tick × entity grid, color = project_switch activity per tick window
- Blocker age histogram: per entity, how long do blockers survive before resolution?

This is the "quick validation" view: one file, shows whether the run's entity population is healthy without opening per-entity snapshots.

**2c — Cross-entity comparison mode**

In the aggregate view, group entities by class_id (WARRIOR, MAGE, ROGUE, MERCHANT) and show side-by-side:
- Mean `graph_churn_rate` per class
- Mean `max_blocker_age` per class
- `overload_count` distribution per class

This is the **balancing view** — it reveals whether specific archetypes are systematically stuck, thrashing, or overloaded before any code change is made.

---

### Layer 3 — Tuning Integration

**3a — Cognition features as calibration input**

`CognitionFeatureExtractor` already computes `graph_churn_rate` per entity. This is the observable consequence of `switch_margin` being too low. With cognition features in Parquet, calibration becomes a query:

```sql
SELECT
  scenario_name,
  AVG(graph_churn_rate) as mean_churn,
  AVG(max_blocker_age) as mean_blocker_age,
  AVG(overload_count) as mean_overload
FROM cognition_features
GROUP BY scenario_name
ORDER BY mean_churn DESC
```

Compare before/after a `switch_margin` change: if `mean_churn` drops by >30% without `mean_blocker_age` rising, the adjustment improved strategy stability.

**3b — Pattern counts as regression gates**

Add `cognition_patterns` to the balance regression test suite:
```python
assert pattern_counts["ProjectChurn"] == 0  # no churn in stable runs
assert pattern_counts["StrategicOverload"] < 2  # at most 1 overload event per run
```
This makes `CognitionPatternMiner` output a CI gate, not just a diagnostic file.

**3c — Decision trace join** (requires E22)

Once `decision_trace.jsonl` exists (E22), join it with `cognition_features` at query time:
```sql
SELECT
  f.entity_id,
  f.graph_churn_rate,
  d.route_kind,
  d.personality_bias
FROM cognition_features f
JOIN decision_trace d USING (entity_id, run_id)
WHERE f.graph_churn_rate > 0.05
```
This closes the causal loop: which scoring terms coincide with high-churn entities? That's the calibration input for E11D and E12.

---

## Relationship to Planned Tickets

### E22-DECISION-EXPLAIN (additive — shared artifact pipeline) — historical, E22 shipped DONE, prerequisite now satisfied

E22 plans: *"Write snapshots to `decision_trace.jsonl` in LIGHT observability mode; Add tick-index sidecar mapping tick → byte offset for O(1) lookup."*

E22 produces `decision_trace.jsonl`. This idea adds it to `ArtifactExporter` mappings and `AnalyticsDatasetBuilder` Parquet tables — so the trace becomes queryable alongside `cognition_features` via DuckDB. Without this, `decision_trace.jsonl` stays a file that developers manually parse, which is the same problem E22 is trying to solve for the graph snapshots.

**Impact on E22**: additive. E22 should define the artifact type key (`"decision_trace"`) in its writer so `ArtifactExporter` can reference it by name. The Parquet conversion for `decision_trace.jsonl` is straightforward given the schema E22 defines.

### E12-BALANCE-BASELINE (gap — measurement without cognition data) — historical, E12 already shipped DONE, measured without this wiring; missed-opportunity record

E12 plans: *"Run D04 completion: 1000-tick `urban_political` runs measuring gold accumulation rate, harvesting frequency per entity-hour, quest completion rate; Audit `blocker_penalty = 2.0` in `src/domains/adventure/scoring.py`."*

Auditing `blocker_penalty = 2.0` requires knowing how often entities are blocked — which is exactly what `blocker_add_count`, `unresolved_blocker_count`, and `max_blocker_age` in `cognition_features` measure. Without cognition features in the analytics pipeline, the E12 measurement pass measures outcomes (gold accumulation, harvesting rate) but cannot attribute them to cognitive causes (blocker storms, churn, overload).

**Impact on E12**: gap. The measurement pass should query `cognition_features` alongside simulation events. The `StaleBlocker` pattern count across entities is direct evidence for or against whether `blocker_penalty = 2.0` is the right threshold. Recommend: wire `CognitionFeatureExtractor` into the post-run pipeline before E12 begins measurement.

**Impact on E11D**: same gap. Bravery calibration (recalibrated to a ≥1.5× differential — `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` found the original ≥2× target unreachable and re-measured a real ~1.74× ratio, attributed to `GoalRegistry`/`CombatEngageScorer`, not `AdventureRouteScorer`) is currently measured only by route-kind outcome rates (E11C harness). Adding `graph_churn_rate` and `overload_count` split by personality quartile would reveal whether high-bravery entities also have lower cognitive stress — a richer signal for calibration than outcome rates alone.

---

## Architecture Constraints

- `CognitionFeatureExtractor` and `CognitionPatternMiner` are already stateless and read-only over run artifacts — safe to call in post-run hook without touching authoritative state.
- Parquet conversion follows the existing pattern in `ParquetArtifactExporter` — each new artifact type is a `_convert_X_to_parquet()` method + a mapping entry.
- `viz_strategy.html` is a standalone HTML file — the temporal playback extension is pure JS over the existing Cytoscape rendering, no server required.
- `cognition_health_score` is a derived metric — deterministic from features, safe for replay.

---

## Open Questions

- Should `cognition_health_score` feed into the run-level `health_score` in `run_manifest.json` (aggregated), or be a separate per-entity field?
- What is the right threshold for pattern regression gates? `ProjectChurn ≥ 3` (current default) may be too permissive for a "healthy run" assertion.
- Should the temporal playback load `cognition_graph_snapshots.jsonl` directly, or consume a pre-processed diff stream? Direct JSONL is simpler but larger for long runs.
- Does the cross-entity comparison view need class_id from entity metadata, or can it be inferred from the cognition graph node kinds?

---

*Raised: 2026-06-20. Recommend wiring `CognitionFeatureExtractor` into post-run pipeline before E12 measurement begins.*
