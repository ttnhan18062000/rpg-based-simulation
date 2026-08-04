---
status: active
layer: observability
authority: P1
audience: agent
tags: [decision-trace, observability, schema, adventure-routing, phase-2]
---

# Decision Trace Contract — `decision_trace.jsonl`

**Implemented by:** TCK-20260619-E22A-TRACE-WRITER (Epic 2.2A)
**Extended by:** TCK-20260627-P1H-GOAL-RUNNERUP — runner-up scores and goal-score cache

## Overview

`decision_trace.jsonl` captures the scored adventure route breakdown for every
eligible hero on every tick where `AdventureDecisionPhase` runs. It addresses
D15 audit Gap 1: "No goal score comparison (WHY goal X was chosen)."

The file is written in LIGHT mode and above (all modes except OFF). It is the
primary artifact for explaining why an entity chose a particular strategy route
over alternatives.

## File Location

```
data/runs/{run_id}/decision_trace.jsonl
```

One JSON object per line (JSONL). Append mode — partial runs do not lose prior entries.

## Mode Threshold

| Mode | Written |
|---|---|
| OFF | No |
| LIGHT (default) | **Yes** |
| NORMAL | Yes |
| FULL | Yes |
| RESEARCH | Yes |
| DEBUG | Yes |
| CERTIFICATION | Yes |
| LONG_RUN | Yes |

Controlled by `OBS_DECISION_TRACE` flag in `ObservabilityConfig`.

## JSON Schema

```json
{
  "entity_id": <int>,
  "tick": <int>,
  "source_goal_score": <float|null>,   // Winner's score (rank 1); null if no candidates
  "runner_up_scores": [                // Ranks 2 and 3 (empty if fewer than 2 candidates)
    {
      "goal_id": <string>,             // RouteFamily value of the alternative route
      "score": <float>,                // Its computed score
      "rank": <int>                    // 2 or 3
    },
    ...
  ],
  "routes": [
    {
      "route_kind": <string>,        // RouteFamily value, e.g. "gather_resource"
      "score": <float>,              // Final computed score (≥0.0)
      "urgency": <float>,            // Active need urgency contribution
      "benefit": <float>,            // Expected benefit (depletion-adjusted)
      "personality_bias": <float>,   // Personality trait bias for this family
      "confidence_bonus": <float>,   // Confidence contribution (route.confidence * 0.15)
      "risk_penalty": <float>,       // Risk penalty (risk × multiplier × 0.5)
      "blocker_penalty": <float>,    // Blocker penalty (2.0 if blocked, else 0.0)
      "selected": <bool>             // true for the winning route (index 0)
    },
    ...
  ]
}
```

- `routes` contains at most 5 entries, sorted by descending score (winner first).
- `selected: true` marks the route actually committed to a strategic project.
- `runner_up_scores` gives a compact summary of why the winner was chosen over alternatives.
- All float fields are rounded to 4 decimal places.

## Score Formula

```
score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty
```

Defined in `src/domains/adventure/scoring.py:AdventureRouteScorer.score()`.

## Implementation Notes

- **Writer:** `src/observability/cognition/decision_trace_writer.py:DecisionTraceWriter`
- **Wired at:** `src/domains/adventure/phase.py:AdventureDecisionPhase.apply()`
- **Lifecycle managed by:** `src/engine/kernel.py` (parallel to cognition recorder)
- **execute_brain() is NOT touched** — route scoring is in the strategic pipeline phase,
  not the tactical cognition domain.
- **Async write path (TCK-20260702-OBSISO-TRACE-ASYNC):** `write_trace()` is a bounded
  in-memory enqueue only — no file I/O runs on the phase call path
  (`docs/architecture/observability_hot_path_safety_contract.md` §3). Each call builds the
  scored-route `entry` dict (unchanged shape/logic), updates the in-memory
  `_latest_goal_scores` cache synchronously, then pushes a `_DecisionTraceQueueItem` onto a
  private `BoundedObservabilityQueue`. A private `QueueDrainWorker`, owned by the
  `DecisionTraceWriter` instance (the same per-instance pattern `EventRecorder` uses, not the
  global observability queue singleton), drains the queue on its own cadence and performs the
  actual `decision_trace.jsonl` write **and** the `DecisionTraceIndex.append_entry()` call
  off-path, via `_write_entry_to_file`. `close()` stops the worker, synchronously drains and
  writes any remaining queued entries, closes the file, then rebuilds the tick-index sidecar.
  See "Accepted Crash-Loss and Overflow-Drop Windows" below.

## Tick Index Sidecar

**Implemented by:** TCK-20260619-E22B-TICK-INDEX (Epic 2.2B)

A sidecar file `decision_trace_index.json` is written alongside `decision_trace.jsonl` to
enable O(1) random-access reads by tick number.

### File Location

```
data/runs/{run_id}/decision_trace_index.json
```

### Format

```json
{"<tick>": <byte_offset>, ...}
```

- Keys are string representations of tick numbers (JSON requires string keys).
- Values are integer byte offsets into `decision_trace.jsonl`.
- Each offset points to the **first** line for that tick (index 0 of all entities at that tick).
- Subsequent entities at the same tick are contiguous in the file and are traversed by
  `lookup()` until the tick changes.

Example:

```json
{"1": 0, "2": 234, "3": 512}
```

### Lifecycle

- **During run (incremental):** `DecisionTraceIndex.append_entry(tick, offset)` is called from
  `DecisionTraceWriter`'s private async drain worker (`_write_entry_to_file`), once per queued
  entry actually written to `decision_trace.jsonl` — not synchronously from `write_trace()`.
  Only the first occurrence of a tick is recorded. This keeps the sidecar valid after every
  **drained** write, at the worker's drain cadence, not synchronously per hot-path call.
- **At run end (rebuild):** `DecisionTraceIndex.rebuild()` is called from
  `DecisionTraceWriter.close()` to produce a clean, complete index from the final file.
- The sidecar is **not authoritative state** — it can be rebuilt at any time via `rebuild()`.

### Accepted Crash-Loss and Overflow-Drop Windows

Moving the file write and index update off the hot path (TCK-20260702-OBSISO-TRACE-ASYNC)
introduces two bounded, accepted windows where an enqueued trace record may never reach disk:

- **Crash-loss window**: entries still sitting in the queue (not yet drained) at the moment of
  an unclean process kill are lost. Bounded by the drain worker's `interval_sec=0.01s` default
  cadence, not unbounded.
- **Queue-overflow-drop window**: under sustained queue saturation (occupancy at
  `ObservabilityConfig.get_max_queue_size()`), new entries are silently dropped rather than
  blocking the hot path.

Both windows mirror the already-accepted precedent set by `EventRecorder`/
`simulation_events.jsonl` on the identical `BoundedObservabilityQueue`/`QueueDrainWorker`
primitive. See `docs/guidelines/intentional_divergences.md` §2.31 for the full rationale and
verification paths.

### Implementation

- **Class:** `src/observability/cognition/tick_index.py::DecisionTraceIndex`
- **Wired by:** `src/observability/cognition/decision_trace_writer.py::DecisionTraceWriter`
- **Lookup:** `DecisionTraceIndex.lookup(tick)` — used by REST API (E22C)
- All I/O is non-fatal: exceptions are caught and logged; the run continues.

## Goal Score Cache (EntityInspector integration)

`DecisionTraceWriter` maintains an in-memory cache of the top-3 goal scores per entity
(the last tick written). `EntityInspectionSnapshot.goal_scores` is populated from this
cache via `get_active_writer().get_latest_goal_scores(entity_id)`.

Each `goal_scores` entry: `{"goal_id": str, "score": float, "rank": int}`.

The cache is non-durable and non-authoritative — it holds the **most recent tick's** data
only. The full history is in `decision_trace.jsonl`.

## Related

- `docs/audits/D15_entity_decision_inspection.md` — Gap 1 addressed by this contract
- `docs/audits/D01_rpg_feature_impact.md` — Decision Explanation Model [PARTIAL] → now LIGHT mode
- TCK-20260619-E22B-TICK-INDEX — builds the tick index sidecar (implemented)
- TCK-20260619-E22C-REST-API — REST API that uses `lookup()` to serve per-tick queries
- `src/domains/adventure/schema.py:AdventureRouteOption` — source data schema
- `src/observability/live/entity_inspector.py:EntityInspectionSnapshot` — `goal_scores` field
