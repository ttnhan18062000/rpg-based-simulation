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
  `DecisionTraceWriter.write_trace()` after each flush. Only the first occurrence of a tick is
  recorded. This keeps the sidecar valid after every write for crash recovery.
- **At run end (rebuild):** `DecisionTraceIndex.rebuild()` is called from
  `DecisionTraceWriter.close()` to produce a clean, complete index from the final file.
- The sidecar is **not authoritative state** — it can be rebuilt at any time via `rebuild()`.

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
