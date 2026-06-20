---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22A-TRACE-WRITER
artifact_type: investigation
tags: [decision-trace, observability, adventure-routing, cognition]
---

# Investigation: TCK-20260619-E22A-TRACE-WRITER — Decision Trace Writer (LIGHT Mode)

## Current Behavior

### execute_brain() return value (CRITICAL FINDING)
`src/engine/domain/cognition.py:L27-L75` — `CognitionDomain.execute_brain()` returns
`Dict[int, EntityUpdate]`. It does NOT return scored routes. Internally it calls:
1. `SensoryFilter.filter_saliency()` → neighbor list
2. `AppraisalSystem.evaluate_emotional_state()` → emotion state
3. `TacticalDecisionSystem.evaluate_entity_intent()` → `EntityUpdate`

No route scoring occurs inside `execute_brain()`. The ticket's assumption about wiring
at `executor.py:L145` is **incorrect** — there are no scored routes to capture there.

### Where route scoring actually happens
Route scoring is in the STRATEGIC pipeline, not the tactical brain:
- `src/domains/adventure/phase.py:AdventureDecisionPhase.apply()` — runs during
  `StrategicIntelligenceSystem.fused_strategic_pass()` at `pipeline.py:L244`
- `src/domains/adventure/service.py:AdventureDecisionService.decide()` — scores all
  candidates via `AdventureRouteScorer.score()`, returns `AdventureDecisionResult`
  containing `selected` (winner) and `rejected` tuple

### AdventureRouteOption fields (the actual scored data)
`src/domains/adventure/schema.py:L34-L59`:
- `family: RouteFamily` — route kind (RECOVER, GATHER_RESOURCE, etc.)
- `score: float` — computed final score (urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty)
- `confidence: float` — subjective success confidence (0.0–1.0)
- `expected_benefit: float` — subjective reward expectation (0.0–1.0)
- `expected_risk: float` — subjective danger expectation (0.0–1.0)
- `blockers: Tuple[str, ...]` — blocker reasons if route is blocked
- `reason: Optional[str]` — short descriptive reason

Score formula in `src/domains/adventure/scoring.py:L33`:
    score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty

### Ticket schema vs actual fields
The ticket schema references: `urgency`, `benefit`, `personality_bias`, `confidence_bonus`,
`risk_penalty`, `blocker_penalty`, `score`, `selected`. These are **intermediate** scoring
terms computed inside `AdventureRouteScorer.score()` — only the final `score` field is
stored on `AdventureRouteOption`. The intermediate terms are local variables (L149).

Resolution: The writer must capture the top-5 scored routes with available fields.
We can reconstruct intermediate terms by adding them to `AdventureRouteOption` OR
write the writer to emit what is available (`family`, `score`, `confidence`,
`expected_benefit`, `expected_risk`, `blockers`, `selected`).

The cleanest approach per the ticket's AC is to add the intermediate score terms to
`AdventureRouteOption` and have the scorer populate them — this is a small extension
to an immutable dataclass.

### Existing recorder pattern
`src/observability/cognition/recorder.py:ObservabilityCognitionRecorder`:
- Initialized with `run_id` and `run_dir`
- Called `record_tick()` post-commit
- Writes to append-mode JSONL files in `run_dir/`
- Mode-gated via `ObservabilityConfig.get_mode()`
- Does NOT use a persistent open file handle — writes per-tick atomically

### ObservabilityConfig
`src/observability/config.py`: `ObservabilityMode` enum — OFF, LIGHT, NORMAL, FULL,
RESEARCH, DEBUG, CERTIFICATION, LONG_RUN. Default is LIGHT.
No existing flag for decision trace — we add a new flag `OBS_DECISION_TRACE` enabled
in LIGHT+ modes (all modes except OFF).

### Existing trace types
`src/observability/trace.py`: `DecisionTrace`, `DecisionOptionTrace`, `RejectedOptionTrace`
— these are Phase 17 structures for a different purpose (general decision trace contract).
The new `DecisionTraceWriter` produces a different, simpler JSONL schema for route scoring.

### Wiring point
The correct wiring point is `src/domains/adventure/phase.py:AdventureDecisionPhase.apply()`
after `result = AdventureDecisionService.decide(...)` returns. The `scored_candidates`
list is available inside `AdventureDecisionService.decide()` at `service.py:L69-72`.

The cleanest approach: pass an optional `trace_writer` to `AdventureDecisionService.decide()`
or call the writer from `AdventureDecisionPhase.apply()` using data from `result`.

Since `AdventureDecisionResult.trace` already has partial info and `result.selected` +
`result.rejected` have the scored routes, we can write the trace from `phase.py` without
touching `service.py`.

### Lifecycle management
`ObservabilityCognitionRecorder` is instantiated in the Kernel or run-level setup.
The `DecisionTraceWriter` should follow the same pattern — instantiated once per run
and passed to `AdventureDecisionPhase.apply()` via an optional parameter.

The AdventureDecisionPhase is called from `StrategicIntelligenceSystem.fused_strategic_pass()`
which is called from `pipeline.py:L244`. The Kernel owns the pipeline. The writer instance
needs to be created at Kernel/run setup and injected here.

### Kernel setup for cognition recorder
Need to find how `ObservabilityCognitionRecorder` is wired to understand the injection pattern.

## Mechanics / Engine Constraints
- `execute_brain()` is read-only — must not be modified (AC requirement and architecture rule)
- Decision logic reads state only; all durable changes through authoritative path
- The writer writes to a file (observability artifact) — not durable state — so it can be
  called from the domain phase without violating the architecture rule
- The write must be post-computation (after `decide()` returns) and non-blocking

## Parity Ledger Overlap
`docs/parity_ledger/infrastructure.yaml`:
- INFRA-005: strategy observability consistency — this ticket adds a new surface, should be noted
- INFRA-006: strategic decision driver traceability — adjacent; new INFRA-211 entry warranted
- Last entry is INFRA-210

## Prior Work
- TCK-20260523-COGNITION-FINAL-CERTIFICATION: Phase 10 cognition graph observability complete
- TCK-20260527-COG-AUTHORITATIVE-PATH: execute_brain() established as read-only tactical evaluator
- D15 audit identifies "No goal score comparison" as Gap 1 (15/15 impact) — this ticket directly addresses it
- D01 audit: "Decision Explanation Model [PARTIAL] — trace generated every tick but not stored durably"
- E22 epic parent (done) established the E22A/B/C child ticket breakdown

## Risks and Open Questions
1. **RESOLVED**: Route scoring is in AdventureDecisionPhase, not execute_brain(). Wire writer at phase.py, not executor.py.
2. **RESOLVED**: ScoredRoute type does not exist — use AdventureRouteOption fields.
3. **RISK**: Intermediate score terms (urgency, benefit, personality_bias, confidence_bonus, risk_penalty, blocker_penalty) are NOT on AdventureRouteOption — only the final `score` is. AC requires "all 8 score-term fields". Two options:
   a. Add fields to AdventureRouteOption (dataclass extension — minor but touches schema.py)
   b. Write partial schema (6 available fields) and document the gap
   **Decision**: Option (a) — extend AdventureRouteOption with the 6 intermediate terms; AdventureRouteScorer populates them. This is minimal and matches the AC exactly.
4. **RISK**: Kernel injection point for writer lifecycle. Need to confirm how to pass writer to AdventureDecisionPhase.
5. No performance risk — LIGHT mode with flush-per-write is consistent with the recorder pattern.

## Anti-Drift Hazards
- Do NOT modify `execute_brain()` in any way — AC explicitly prohibits this
- Do NOT add import of `DecisionTraceWriter` inside `execute_brain()`
- The file must be opened in append mode — partial runs must not lose prior entries
- Flush after each write — the tick index in E22B depends on complete lines
