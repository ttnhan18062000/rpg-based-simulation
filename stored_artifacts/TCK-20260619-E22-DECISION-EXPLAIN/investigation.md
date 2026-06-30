---
ticket_id: TCK-20260619-E22-DECISION-EXPLAIN
phase: investigation
date: 2026-06-20
---

# Investigation: Decision Explanation Model

## Current State (verified 2026-06-20)

### execute_brain() — `src/engine/domain/cognition.py:L27`
Called via:
- `src/engine/executor.py:L145` — main tick loop
- `src/engine/worker_logic.py:L35` — worker packet path
- `src/engine/domain_logic.py:L32-39` — dispatcher

Route scoring trace is computed inside `execute_brain()` every tick for every entity, then discarded at tick boundary. The computed data (urgency/benefit/personality_bias/confidence_bonus/risk_penalty/blocker_penalty per route) is not written anywhere in LIGHT mode.

### cognition_graph_snapshots.jsonl — existing writer
- Written by `src/observability/cognition/recorder.py`
- `ObservabilityMode.LIGHT` → only anomalies captured (L41-42)
- `ObservabilityMode.DEBUG / CERTIFICATION` → entity state changes captured
- This is a graph-snapshot format (node/edge graph of cognitive state), NOT a scored route list
- Pattern to follow for `decision_trace.jsonl` writer

### ObservabilityMode — `src/observability/config.py`
Modes: OFF, LIGHT, LONG_RUN, DEBUG, CERTIFICATION
In LIGHT mode currently: cognition snapshots are skipped, only anomalies recorded.
E22A target: write `decision_trace.jsonl` in LIGHT mode (not DEBUG-only).

### API layer — `src/api/routes/`
Routes exist: `behavior.py`, `control.py`, `health.py`, `history.py`, `search.py`, `state.py`
No `decisions.py` or observability entity decisions endpoint.
`src/api/server.py` — root app, find where routes are registered before adding new one.

### decision_trace.jsonl — does not exist
No file, no writer, no index. Everything to be created fresh.

### `stored_artifacts/TCK-20260618-AUDIT-D15/`
D15 audit documented 8 present / 6 missing observability features. P0 gap: goal score comparison absent — execute_brain() scores transient and discarded.

## Architecture Constraint

Do NOT change `execute_brain()` logic. Only add a writer at the point where the route trace is currently discarded. This matches the design note in the epic: "Promoting existing computed data — do not change execute_brain() logic."

## Gap Summary

| Gap | Location | Size |
|---|---|---|
| `decision_trace.jsonl` writer missing | After execute_brain() in LIGHT mode | ~50 lines |
| Tick-index sidecar missing | New file alongside writer | ~30 lines |
| `/api/v1/observability/entities/{id}/decisions` endpoint missing | `src/api/routes/decisions.py` | ~80 lines |

## Risk

- Finding the exact return value of `execute_brain()` that carries the route trace is E22A's first step. The trace may be embedded in `EntityUpdate` or a separate return field.
- The tick-index byte-offset approach requires that `decision_trace.jsonl` entries are written atomically (one JSON line per flush). Verify the writer pattern from `cognition_graph_snapshots.jsonl` for the flush strategy.
- REST API: confirm `src/api/server.py` or equivalent registers routes so E22C knows where to add the new route.
