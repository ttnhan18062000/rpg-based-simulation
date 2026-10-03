---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22A-TRACE-WRITER
artifact_type: plan
tags: [decision-trace, observability, plan]
---

# Plan: TCK-20260619-E22A-TRACE-WRITER — Decision Trace Writer (LIGHT Mode)

## Key Architecture Finding (from investigation)

`execute_brain()` does NOT return scored routes — it returns `EntityUpdate` only.
Route scoring lives in `AdventureDecisionService.decide()` called from
`AdventureDecisionPhase.apply()` in `pipeline.py:L170`.

The correct wiring point is `AdventureDecisionPhase.apply()`, not `executor.py:L145`.
This is a scope correction from the ticket's "Step 3" — the caller is `pipeline.py` not `executor.py`.

## Ordered Steps

### Step 1 — Extend `AdventureRouteOption` with intermediate score term fields
**File:** `src/domains/adventure/schema.py`

Add 6 optional fields to `AdventureRouteOption` (frozen dataclass, slots=True):
```python
urgency: float = 0.0
benefit_score: float = 0.0        # renamed from 'benefit' to avoid shadowing expected_benefit
personality_bias: float = 0.0
confidence_bonus: float = 0.0
risk_penalty: float = 0.0
blocker_penalty: float = 0.0
```
Note: `selected` is not a field on the route — it's determined by position in the
scored_routes list passed to the writer (first = selected). Will emit as boolean in writer.

**AC mapped:** "Each route entry has all 8 score-term fields"

**Scope guard:** Do NOT change `score` field or any existing field. Do NOT change frozen/slots.
Add fields at the END of the dataclass to preserve existing positional construction.

### Step 2 — Update `AdventureRouteScorer.score()` to populate new fields
**File:** `src/domains/adventure/scoring.py`

After computing all intermediate terms (urgency, benefit, personality_bias, confidence_bonus,
risk_penalty, blocker_penalty, final_score), populate the new fields via `dataclasses.replace`:
```python
return dataclasses.replace(route,
    score=final_score,
    urgency=round(urgency, 4),
    benefit_score=round(benefit, 4),
    personality_bias=round(personality_bias, 4),
    confidence_bonus=round(confidence_bonus, 4),
    risk_penalty=round(risk_penalty, 4),
    blocker_penalty=round(blocker_penalty, 4),
)
```

**AC mapped:** "Each route entry has all 8 score-term fields"

**Scope guard:** Do NOT change the scoring formula or result. Only add field population.

### Step 3 — Create `src/observability/cognition/decision_trace_writer.py`
**File:** `src/observability/cognition/decision_trace_writer.py` (new file)

```python
class DecisionTraceWriter:
    """Writes per-entity scored route traces to decision_trace.jsonl in LIGHT+ modes."""
    def __init__(self, run_dir: str): ...
    def write_trace(self, entity_id: int, tick: int, scored_routes: list) -> None: ...
    def close(self) -> None: ...
```

- Mode check: if `ObservabilityConfig.get_mode() == ObservabilityMode.OFF`, no-op
- Opens file in append mode (`"a"`) on first write (lazy open — avoids creating file if never called)
- JSON schema per entry:
  ```json
  {
    "entity_id": <int>,
    "tick": <int>,
    "routes": [
      {
        "route_kind": <str>,       // route.family.value
        "score": <float>,
        "urgency": <float>,
        "benefit": <float>,        // from benefit_score field
        "personality_bias": <float>,
        "confidence_bonus": <float>,
        "risk_penalty": <float>,
        "blocker_penalty": <float>,
        "selected": <bool>         // True for index 0
      }, ...
    ]
  }
  ```
- Caps at 5 routes
- Flush after each write
- `close()` closes the file handle if open
- No import of `execute_brain()` — only imports `json`, `os`, `ObservabilityConfig`, `ObservabilityMode`

**AC mapped:** "10-tick LIGHT-mode run produces decision_trace.jsonl", "each line valid JSON",
"entity_id/tick/routes", "routes ≤5", "all 8 score-term fields"

### Step 4 — Wire writer into `AdventureDecisionPhase.apply()`
**File:** `src/domains/adventure/phase.py`

Add optional `trace_writer=None` parameter to `AdventureDecisionPhase.apply()`:
```python
@staticmethod
def apply(state, context=None, trace_writer=None) -> StateUpdate:
```

After `result = AdventureDecisionService.decide(...)` and before entity_updates is assembled:
```python
if trace_writer is not None:
    all_scored = [result.selected] + [
        AdventureRouteOption(family=r.family, score=r.score, ...)
        for r in result.rejected
    ]
    trace_writer.write_trace(hero.id, tick, [result.selected] + _rejected_as_options(result.rejected))
```

Actually simpler: collect `scored_candidates` from inside `AdventureDecisionService.decide()`
by having it return them in `AdventureDecisionResult.trace` dict (already exists).

**Revised approach**: In `AdventureDecisionService.decide()`, add all `scored_candidates`
to the `trace` dict. Then in `AdventureDecisionPhase.apply()`, extract from result.trace
and call writer. This avoids touching `AdventureDecisionResult` schema.

**Even simpler**: Build the write data directly in `phase.py` from `result.selected`
and `result.rejected` (both are `AdventureRouteOption` / `RejectedRoute`).
`RejectedRoute` has `family`, `score` but not the extended fields.
So the cleanest: pass `scored_candidates` list out via `result.trace["scored_candidates"]`
from `service.py`, then write from `phase.py`.

**Final decision**: Add `"scored_candidates"` key to `trace` dict in `service.py:L143-148`.
In `phase.py`, after `result = ...`, call `trace_writer.write_trace(hero.id, tick, result.trace.get("scored_candidates", []))`.

**AC mapped:** "execute_brain() is NOT modified", "writer fires in LIGHT mode"

**Scope guard:** Do NOT modify the `execute_brain()` function. Do NOT change the StateUpdate return type.

### Step 5 — Update `AdventureDecisionService.decide()` to export scored_candidates
**File:** `src/domains/adventure/service.py`

In the `trace` dict at L143-148, add:
```python
"scored_candidates": scored_candidates,   # list[AdventureRouteOption] with all fields
```

**Scope guard:** No logic changes — only adds data to the already-existing trace dict.

### Step 6 — Wire `DecisionTraceWriter` into `pipeline.py`
**File:** `src/engine/pipeline.py`

Change line 170 to pass writer:
```python
update = run_phase(
    "adventure_decision", update,
    lambda u: AdventureDecisionPhase.apply(
        state,
        trace_writer=getattr(state, "_decision_trace_writer", None)
    ),
    "ENABLE_ADVENTURE_ROUTING"
)
```

This allows the Kernel to attach `_decision_trace_writer` to state before calling `refine()`,
OR the Kernel can use a module-level singleton (simpler).

**Revised approach**: Use a module-level registry in `decision_trace_writer.py`:
```python
_active_writer: Optional[DecisionTraceWriter] = None

def set_active_writer(writer): ...
def get_active_writer(): ...
```

Then in `phase.py`, call `get_active_writer()` without any parameter threading.
Kernel calls `set_active_writer(writer)` at run start and `set_active_writer(None)` at end.

**AC mapped:** "writer fires in LIGHT mode"

### Step 7 — Wire Kernel to create and manage `DecisionTraceWriter` lifecycle
**File:** `src/engine/kernel.py`

Parallel to `_cognition_recorder` wiring at L232-244:
```python
self._decision_trace_writer = None
if obs_mode != ObservabilityMode.OFF:
    from src.observability.cognition.decision_trace_writer import DecisionTraceWriter, set_active_writer
    self._decision_trace_writer = DecisionTraceWriter(run_dir=run_dir_str)
    set_active_writer(self._decision_trace_writer)
```

And in shutdown/cleanup, call `close()` and `set_active_writer(None)`.

### Step 8 — Add new flag `OBS_DECISION_TRACE` to `ObservabilityConfig`
**File:** `src/observability/config.py`

Add `OBS_DECISION_TRACE: True` to LIGHT, NORMAL, FULL, RESEARCH, DEBUG, CERTIFICATION, LONG_RUN
flag mappings (all except OFF).

Add convenience method:
```python
@classmethod
def is_decision_trace_enabled(cls) -> bool:
    return cls.get_flag("OBS_DECISION_TRACE")
```

Use this flag in `DecisionTraceWriter.write_trace()` as the mode gate.

### Step 9 — Author `docs/observability/decision_trace_contract.md`
**File:** `docs/observability/decision_trace_contract.md` (new file)

Document the schema of `decision_trace.jsonl`:
- File location: `data/runs/{run_id}/decision_trace.jsonl`
- Mode threshold: LIGHT and above
- JSON schema per line
- Field descriptions

### Step 10 — Update `docs/audits/D15_entity_decision_inspection.md`
Change Gap 1 status from "Missing" to "Partially implemented by TCK-20260619-E22A-TRACE-WRITER".

### Step 11 — Write tests
**File:** `tests/unit/observability/test_decision_trace.py` (new file)

All tests from test_plan.md.

## Dependency Map
- Step 1 → Step 2 (scorer needs extended fields first)
- Step 1, 2 → Step 3 (writer uses field names)
- Step 5 → Step 4 (phase needs scored_candidates in trace)
- Step 3, 4, 5, 6 → Step 7 (kernel wires it all together)
- Step 8 can be done in parallel with Steps 1-7
- Step 9, 10 after Step 7
- Step 11 after Steps 1-8

## Acceptance Criteria → Step Mapping
| AC | Steps |
|---|---|
| 10-tick LIGHT-mode run produces decision_trace.jsonl | 3, 6, 7, 8 |
| Each line valid JSON with entity_id/tick/routes | 3 |
| Routes ≤5 with all 8 score-term fields | 1, 2, 3 |
| execute_brain() NOT modified | constraint on Steps 4-7 |
| test_decision_trace_written_in_light_mode passes | 11 |
| test_decision_trace_schema_has_all_score_terms passes | 11 |

## Scope Guards (what NOT to touch)
- `src/engine/domain/cognition.py` — read-only reference only
- `src/engine/executor.py` — no changes
- `src/engine/worker_logic.py` — no changes
- `src/observability/trace.py` — no changes (Phase 17 contract, separate)
- `src/observability/validator.py` — no changes
- `AdventureDecisionResult` dataclass fields — only `trace` dict content

## Deviations
_(filled during implementation if actual steps differ from plan)_
