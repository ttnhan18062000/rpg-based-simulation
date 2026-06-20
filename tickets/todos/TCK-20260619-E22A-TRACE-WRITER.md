---
status: open
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22A-TRACE-WRITER
phase: open
date: 2026-06-20
tags: [decision-explanation, observability, trace-writer, cognition, phase-2]
---

# TCK-20260619-E22A-TRACE-WRITER

## Title
Epic 2.2A · Decision Trace Writer (LIGHT Mode)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`execute_brain()` scores top-5 routes per entity per tick and discards them at tick boundary. D15 audit (P0 gap): "goal score comparison absent — execute_brain() scores transient and discarded." This ticket adds a writer that captures the score breakdown to `decision_trace.jsonl` in LIGHT observability mode, without changing any `execute_brain()` logic.

**Blocks:** TCK-20260619-E22B-TICK-INDEX

## Scope

### Step 1 — Understand execute_brain() return value

Read `src/engine/domain/cognition.py` (the full `execute_brain()` method). Find:
- What does it return? Does the return value carry scored routes, or are they written internally?
- If routes are returned in the `EntityUpdate`, which field? If they're computed internally, find where the trace data lives before it's discarded.

This is the most critical first step. The writer must insert **after** execute_brain() completes without modifying it.

### Step 2 — Create `src/observability/cognition/decision_trace_writer.py`

New writer class following the pattern of `src/observability/cognition/recorder.py`:

```python
class DecisionTraceWriter:
    """Writes per-entity scored route traces to decision_trace.jsonl in LIGHT+ modes."""

    def __init__(self, run_dir: str):
        self._path = os.path.join(run_dir, "decision_trace.jsonl")
        self._file = open(self._path, "a")

    def write_trace(self, entity_id: int, tick: int, scored_routes: list[ScoredRoute]) -> None:
        """Write top-5 scored routes for one entity at one tick."""
        entry = {
            "entity_id": entity_id,
            "tick": tick,
            "routes": [
                {
                    "route_kind": r.route_kind,
                    "score": r.score,
                    "urgency": r.urgency,
                    "benefit": r.benefit,
                    "personality_bias": r.personality_bias,
                    "confidence_bonus": r.confidence_bonus,
                    "risk_penalty": r.risk_penalty,
                    "blocker_penalty": r.blocker_penalty,
                    "selected": r.selected,
                }
                for r in scored_routes[:5]
            ]
        }
        self._file.write(json.dumps(entry) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()
```

### Step 3 — Wire writer into execute_brain() caller (not execute_brain() itself)

In `src/engine/executor.py:L145` (or `worker_logic.py:L35`, whichever calls `execute_brain()`):
- If `ObservabilityMode` is LIGHT or higher: after `execute_brain()` returns, call `writer.write_trace(entity_id, tick, routes)`
- The writer instance should be created once per run and passed in (not instantiated per call)

### Step 4 — Update `ObservabilityMode` threshold check

In `src/observability/config.py` or the caller: ensure `DecisionTraceWriter.write_trace()` fires in LIGHT mode (the existing `cognition_graph_snapshots.jsonl` is DEBUG-only; `decision_trace.jsonl` should be LIGHT and above).

## Out of Scope
- Tick index (E22B)
- REST API (E22C)

## Acceptance Criteria
- 10-tick LIGHT-mode run produces `decision_trace.jsonl` in the run directory
- Each line is valid JSON with `entity_id`, `tick`, `routes` (≤5 items)
- Each route entry has all 8 score-term fields (`urgency`, `benefit`, `personality_bias`, `confidence_bonus`, `risk_penalty`, `blocker_penalty`, `score`, `selected`)
- `execute_brain()` in `src/engine/domain/cognition.py` is NOT modified
- `test_decision_trace_written_in_light_mode` passes
- `test_decision_trace_schema_has_all_score_terms` passes

## Related Tickets
- TCK-20260619-E22-DECISION-EXPLAIN (parent epic)
- TCK-20260619-E22B-TICK-INDEX (blocked on this)

## Related Docs
- `docs/audits/D15_entity_decision_inspection.md` (update status from gap to implemented)
- New doc: `docs/observability/decision_trace_contract.md` (schema — author this ticket's output section)

## Related Code Areas
- `src/engine/domain/cognition.py` (execute_brain — read-only reference)
- `src/engine/executor.py:L145` (wire writer here)
- `src/observability/cognition/recorder.py` (pattern reference)
- `src/observability/config.py` (ObservabilityMode)
- `src/observability/cognition/decision_trace_writer.py` (new file)

## Assumptions / Open Questions
- Does execute_brain() return scored routes in its return value, or are they only accessible as an internal intermediate? Read `src/engine/domain/cognition.py` in full before implementing.
- Is there a `ScoredRoute` typed model, or is the route list a dict? Find the type used inside execute_brain() before designing the writer schema.
- Where is the `DecisionTraceWriter` instance lifecycle managed? Likely in the `Kernel` or run-level setup — find the equivalent for `cognition_graph_snapshots.jsonl` recorder.

## Implementation Notes
- File must be opened in append mode (`"a"`) so partial runs don't lose prior entries.
- Flush after each write so the index in E22B sees complete lines.
- Do not import `DecisionTraceWriter` inside execute_brain() — wire it in the caller layer.
- Run `graphify update src/` after implementation.
- Run `make knowledge-index-update` if docs/ changed.

## Test Summary
```bash
pytest tests/unit/observability/test_decision_trace.py::test_decision_trace_written_in_light_mode -x -v
pytest tests/unit/observability/test_decision_trace.py::test_decision_trace_schema_has_all_score_terms -x -v
pytest tests/unit/observability/ -x -v -q  # regression
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
