---
status: historical
layer: simulation
authority: P0
audience: agent
ticket_id: TCK-20260629-SIMQ-EVENT-TRANSLATE
phase: done
date: 2026-06-29
tags: [simq, observability, event-gap, calibration]
---

# TCK-20260629-SIMQ-EVENT-TRANSLATE

## Title
SimQ: Event Type Translation Table — Remap Engine Events to Contract Vocabulary

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P0

## Request Summary
The SimQ calibration run (E7) found 0 scored events because the engine emits event types
(`quest_event`, `StrategicConcernRaised`, `combat_kill`, etc.) that do not match the
contract §5 vocabulary (`quest_started`, `strategic_goal_changed`, `entity_killed`, etc.).

A translation table in `QualityHub.on_envelope()` can remap known engine types to contract
types before routing, unblocking calibration **without any engine changes**. This is a
pure adapter — no scorer logic changes, no engine changes.

## Scope
Add a `_TRANSLATION_TABLE: dict[str, str | Callable]` to `QualityHub` that normalizes
`ObservabilityEventEnvelope.event_type` before scorer dispatch. Implement as a pre-route
normalization step inside `on_envelope()`.

**Mappings to implement:**

| Engine event_type | Condition | Contract event_type |
|---|---|---|
| `quest_event` | `payload["status"] == "started"` or no status | `quest_started` |
| `quest_event` | `payload["status"] == "completed"` | `quest_completed` |
| `quest_event` | `payload["status"] == "failed"` | `quest_failed` |
| `combat_kill` | — | `entity_killed` |
| `gold_transaction` | — | `gold_transferred` |
| `lifecycle` | `payload["action"] == "level_up"` | `level_up` |
| `lifecycle` | `payload["action"] == "despawn"` | `entity_killed` (if entity was killed) |
| `StrategicProjectChanged` | `payload["reason"] == "completed"` | `project_completed` |
| `StrategicProjectChanged` | `payload["reason"] == "abandoned"` | `project_abandoned` |
| `StrategicProjectChanged` | otherwise | `project_started` |
| `StrategicObjectiveChanged` | — | `strategic_goal_changed` |
| `StrategicConcernRaised` | — | `strategic_goal_changed` |
| `StrategicDetourCreated` | — | `project_started` |
| `StrategicLeadExhausted` | — | `knowledge_default_fallback` |
| `InvariantViolation` | `payload.get("law_id","").startswith("COMBAT")` | `combat_hard_law_violation` |
| `InvariantViolation` | `payload.get("law_id","").startswith("CONSERVATION")` | `conservation_law_violated` |

Translation must produce a **new envelope** with the remapped `event_type` — never mutate
the input. Original `event_type` preserved in `payload["_original_event_type"]` for
traceability.

## Out of Scope
- Emitting new events from engine phases (see TCK-20260629-SIMQ-EMIT-STATE-DIFF)
- Changing scorer EVENT_TYPES registration
- Covering the ~73 contract event types with no engine equivalent (separate tickets)

## Acceptance Criteria
- [ ] `QualityHub._translate(envelope)` returns remapped envelope or original if no mapping
- [ ] All mappings in the table above are implemented and tested
- [ ] `on_envelope()` calls `_translate()` before routing to SCORER_REGISTRY
- [ ] Payload-conditional mappings (quest_event status, lifecycle action) work correctly
- [ ] Original event_type preserved in `payload["_original_event_type"]`
- [ ] `test_quality_hub_event_translation.py` covers all mappings in table
- [ ] Re-running `tools/calibrate_simq.py --ticks 100 --seed 42` shows non-zero events on
  NARRATIVE, COGNITION, COMBAT pillars (AGENCY partially)
- [ ] Parity entry SIMQ-CALIBRATED-001 updated: `status: verified` if calibration now runs

## Related Tickets
- TCK-20260628-SIMQ-E7-CALIBRATE (the ticket that discovered this gap)
- TCK-20260629-SIMQ-EMIT-STATE-DIFF (next step after this)
- SIMQ-CALIBRATED-001 parity entry in docs/parity_ledger/infrastructure.yaml

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 — contract vocabulary
- `docs/parity_ledger/infrastructure.yaml` — SIMQ-CALIBRATED-001

## Related Code Areas
- `src/simulation_quality/quality_hub.py` — `on_envelope()` method
- `src/observability/events.py` — engine event classes
- `src/observability/cognition/events.py` — StrategicCognitionEvent subclasses
- `src/observability/event_extractor.py` — EventExtractor.extract() output types
- `tests/simulation_quality/test_quality_hub_integration.py` — existing hub tests

## Assumptions / Open Questions
- Translation is pure adapter logic — it does NOT change what the engine emits
- Caller of `_translate()` owns the lifecycle of the new envelope; original is unchanged
- `quest_event` status comes from `SimulationEvent.payload["status"]` field per QuestEvent schema
- `lifecycle` payload action comes from `LifecycleEvent.details["action"]` serialized to payload

## Implementation Notes
- Implement as a classmethod or staticmethod `_translate(cls, env: ObservabilityEventEnvelope) -> ObservabilityEventEnvelope`
- Use `dataclasses.replace()` or `env.model_copy(update={...})` to produce new envelope
- The translation table should be a module-level constant `_TRANSLATE: dict[str, str | tuple[str, Callable]]`
- Conditional mappings (quest status, lifecycle action) require a two-step lookup:
  type → callable that takes env and returns contract type string
- No try/except around translation — if payload is malformed, fall through to original type

## Files Changed
- `src/simulation_quality/quality_hub.py` — added `_TRANSLATE_SIMPLE`, `_TRANSLATE_CONDITIONAL`, `_translate()` staticmethod; call in `on_envelope()`
- `tests/simulation_quality/test_quality_hub_event_translation.py` (new) — 34 tests for all mappings

## Completion Summary
Translation table implemented in QualityHub._translate(). All 16 engine→contract mappings covered. Calibration now scores NARRATIVE=A (16 events) and overall=B from 100-tick baseline. 34 tests passing. Parity entry SIMQ-CALIBRATED-001 updated with partial status and test_path.
