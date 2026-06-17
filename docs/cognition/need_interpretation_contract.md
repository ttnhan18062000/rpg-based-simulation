---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Need Interpretation Contract

**Source:** `src/cognition/need_interpretation.py`, `src/cognition/trace_events.py`
**Related docs:** [README.md](README.md), [self_model_contract.md](self_model_contract.md), [docs/simulation/domains/motivation_contract.md](../simulation/domains/motivation_contract.md), [docs/world/opportunity_providers_contract.md](../world/opportunity_providers_contract.md)

---

## Purpose

`NeedInterpretationService.interpret()` converts biological pressure signals and self-awareness weakness labels into **prioritised, named need signals** that the motivation and perception domains can act on. It answers: "Given what this entity knows about itself right now, what does it most urgently need?"

---

## Rule: survival needs outrank growth needs

The interpretation follows a strict priority hierarchy:
1. **Survival** (healing, food, rest) — always highest urgency when critical
2. **Maintenance** (equipment repair, stamina recovery, inventory space)
3. **Growth** (equipment improvement, gold)
4. **Information** (knowledge gaps) — always lowest

When a survival need is CRITICAL, growth needs are deflated to LOW urgency.

---

## Urgency constants

| Constant | Value |
|---|---|
| CRITICAL | 0.95 |
| HIGH | 0.75 |
| MEDIUM | 0.50 |
| LOW | 0.25 |

---

## Need generation rules

| Need key | Trigger condition | Urgency |
|---|---|---|
| `healing` | HP fraction < 0.35 (`low_health` weakness) | CRITICAL if HP < 0.20; HIGH if HP < 0.35 |
| `food` | hunger > 60.0 | CRITICAL if > 85; HIGH if > 70; MEDIUM if > 60 |
| `rest` | sleep_debt > 50.0 | HIGH if > 75; MEDIUM if > 50 |
| `stamina_recovery` | `low_stamina` weakness AND `rest` not already present | MEDIUM |
| `equipment_repair` | `gear_damaged` weakness | HIGH if gear_quality < 0.25; MEDIUM otherwise |
| `equipment_improvement` | `weak_weapon` weakness | MEDIUM; deflated to LOW if `healing` is CRITICAL |
| `inventory_space` | `inventory_pressure` weakness | HIGH if load ≥ 100%; MEDIUM otherwise |
| `gold` | gold < 30 | HIGH if gold < 10; LOW otherwise |
| `information` | knowledge_model has any unknowns | LOW (always lowest priority) |

---

## Dominant need

`dominant_need = argmax(need.urgency)` across all active needs. This is the single highest-urgency need key (string). If no needs are active, `dominant_need = None`.

The dominant need is read by:
- `src/domains/motivation/` → `MotivationBiasService` uses it to compute route bias multiplier
- `src/domains/perception/` → `AttentionFocusService` uses it to derive attention focus tags for salience scoring

---

## NeedInterpretationComponent

```python
NeedInterpretationComponent:
    active_needs: Dict[str, InterpretedNeed]  # need_key → InterpretedNeed
    dominant_need: Optional[str]              # key of highest-urgency need
    last_interpreted_tick: int               # set by orchestrator after construction

InterpretedNeed:
    key: str           # e.g. "healing", "food", "rest"
    urgency: float     # 0.0–1.0 (use urgency constants above)
    confidence: float  # how certain the entity is about this need
    reason: str        # e.g. "low_health", "hunger", "gear_damaged"
```

---

## Connection to world-side motivation pressure

`src/world/motivation/pressure_resolver.py` runs **before the cognition step** and produces a `MotivationPressureSet` (8 normalized pressure dimensions: survival, comfort, social, achievement, curiosity, safety, greed, purpose) from the entity's catalog `need_profile_id` and `drive_profile_id`.

These world-side pressures are NOT the same as interpreted needs. They are catalog-defined drive profiles, while interpreted needs are dynamically computed from the entity's current biological and equipment state. Both feed the motivation domain, which combines them into routing bias multipliers.

---

## Trace events — `trace_events.py`

Five frozen trace events are emitted during `SelfModelUpdatePhase`:

| Event | When emitted | Key fields |
|---|---|---|
| `SelfAwarenessUpdatedEvent` | After dirty check triggers (assessment changed) | weaknesses, strengths, confidence, stress |
| `NeedInterpretedEvent` | After need interpretation runs | dominant_need, needs_summary (key → urgency dict) |
| `CapabilityEstimateUpdatedEvent` | After capability estimation runs | estimates_summary |
| `KnowledgeFactLearnedEvent` | When a fact is new or updated | subject, fact_type, certainty |
| `KnowledgeUnknownRecordedEvent` | When a new unknown is recorded | subject, reason |

Events are collected in a `trace_events_collector` list during `SelfModelUpdatePhase.run()` and routed to the warehouse history API. They appear in the entity's `TICK_EVENT` stream, queryable by entity_id and tick range.

---

## Regression tests

- `tests/unit/cognition/test_phase2_need_interpretation_service.py` — each need's trigger conditions, urgency levels, survival-outranks-growth deflation, dominant_need selection
- `tests/integration/scenarios/test_phase2_self_model_scenarios.py` — event emission on dirty-check trigger, needs_summary format

---

## Extension rules

1. To add a new need type: add a trigger condition and urgency calculation block in `NeedInterpretationService.interpret()`. Follow the survival/maintenance/growth/information priority hierarchy — assign urgency constants accordingly. Add a test for the trigger condition boundary.
2. To add a new trace event: add a frozen dataclass in `trace_events.py`, emit it in the appropriate step of `SelfModelUpdatePhase.run()`, add it to the collector.
3. Never add action-selection logic here — `NeedInterpretationService` only produces need signals. The motivation domain decides what to do with them.
4. Need keys are strings (not enums) for forward compatibility. New need keys must be documented here to ensure downstream consumers can handle them.
