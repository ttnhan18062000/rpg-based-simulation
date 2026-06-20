---
status: active
layer: observability
authority: P1
audience: agent
tags: [decision-trace, observability, schema, adventure-routing, phase-2]
---

# Decision Trace Contract — `decision_trace.jsonl`

**Implemented by:** TCK-20260619-E22A-TRACE-WRITER (Epic 2.2A)

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

## Related

- `docs/audits/D15_entity_decision_inspection.md` — Gap 1 addressed by this contract
- `docs/audits/D01_rpg_feature_impact.md` — Decision Explanation Model [PARTIAL] → now LIGHT mode
- TCK-20260619-E22B-TICK-INDEX — blocked on this; builds an index over this file
- `src/domains/adventure/schema.py:AdventureRouteOption` — source data schema
