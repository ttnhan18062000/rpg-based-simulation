---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Self-Model Contract

**Source:** `src/cognition/self_model_phase.py`, `src/cognition/self_assessment.py`
**Related docs:** [README.md](README.md), [capability_and_knowledge_contract.md](capability_and_knowledge_contract.md), [need_interpretation_contract.md](need_interpretation_contract.md)

---

## Purpose

The self-model is the entity's internal representation of its own condition. It answers: "How healthy am I? What are my weaknesses? Am I confident?" This feeds need interpretation (what do I need?) and capability estimation (what can I do?).

---

## SelfAwarenessComponent — the core output

`SelfAssessmentService.assess()` produces a frozen `SelfAwarenessComponent`:

```python
SelfAwarenessComponent:
    perceived_condition: Dict[str, float]   # health, stamina, carrying_load, gear_quality (0.0–1.0)
    perceived_weaknesses: Tuple[str, ...]   # ordered list of active weakness labels
    perceived_strengths: Tuple[str, ...]    # ordered list of active strength labels
    confidence_level: float                 # 0.05–1.0
    stress_level: float                     # 0.0–1.0
    uncertainty_level: float                # 0.1 base (Phase 2); later phases modulate
    last_self_check_tick: int               # set by orchestrator after construction
```

---

## Assessment thresholds

| Property | Threshold | Weakness/strength label |
|---|---|---|
| HP fraction | < 0.35 | `low_health` weakness |
| HP fraction | ≥ 0.85 | `good_health` strength |
| HP fraction | < 0.20 | contributes +0.25 to stress |
| Stamina fraction | < 0.30 | `low_stamina` weakness |
| Stamina fraction | ≥ 0.85 | `high_stamina` strength |
| Hunger | > 60.0 | `hunger_pressure` weakness |
| Hunger | > 80.0 | contributes +0.25 to stress |
| Sleep debt | > 50.0 | `sleep_debt_pressure` weakness |
| Sleep debt | > 75.0 | contributes +0.25 to stress |
| Inventory load | ≥ 85% of max_slots | `inventory_pressure` weakness |
| Gear quality (avg durability) | < 0.50 | `gear_damaged` weakness |
| Gear quality | ≥ 0.90 | `good_gear` strength |
| ATK vs expected (level × 5) | ATK < expected | `weak_weapon` weakness |
| ATK vs expected | ATK ≥ expected × 1.5 | `strong_weapon` strength |

### Composite metrics

```python
stress_level    = min(1.0, severity_count × 0.15 + critical_conditions × 0.25)
confidence_level = max(0.05, min(1.0, 0.8 − severity_count × 0.12 + strength_count × 0.08))
```

Where `severity_count = len(weaknesses)`, `critical_conditions = count of HP<20% / hunger>80 / sleep_debt>75`.

---

## Dirty check

`SelfModelUpdatePhase.run()` skips steps 3–4 (need interpretation + capability estimation) if:
- This is not the first tick (`last_self_check_tick != 0`)
- No InformationResponse events arrived for this entity this tick
- `perceived_condition`, `perceived_weaknesses`, and `perceived_strengths` are unchanged

If dirty check passes (nothing changed): only knowledge is merged if updated; no other recomputation. This is a performance optimisation — it does not change the correctness guarantee.

---

## Phase lifecycle

`SelfModelUpdatePhase.apply()` runs for every `alive AND active` entity each tick:
1. Calls `SelfModelUpdatePhase.run()` per entity
2. Maps the returned `SelfModelBundle` back into `EntityUpdate(self_model_bundle_set=...)`
3. Returns the refined `StateUpdate`

The resulting `SelfModelBundle` is written to `entity.self_model` through the authoritative apply path.

---

## Edge cases

- **First tick:** `last_self_check_tick == 0` forces full assessment (dirty check always triggers on first tick)
- **Entity death mid-assessment:** Phase skips `not entity.lifecycle.active OR not entity.combat.alive` — no assessment runs for dead entities
- **Stale self-model after rapid attribute change:** Dirty check uses `perceived_condition` values, not raw entity stats. If raw stats change but assessed condition hasn't crossed a threshold, the dirty check will skip re-assessment. This is intentional — condition is categorical (low/good/etc), not continuous.

---

## Downstream consumers

| Consumer | What it reads |
|---|---|
| `NeedInterpretationService` | `perceived_condition`, `perceived_weaknesses` |
| `src/domains/motivation/` | `entity.self_model.needs.dominant_need` |
| `src/domains/perception/` | `entity.self_model.needs` (attention focus) |
| `src/systems/strategic_systems/intelligence.py` | full `entity.self_model` |

---

## Regression tests

- `tests/unit/cognition/test_phase2_self_assessment_service.py` — threshold boundary tests for each weakness/strength label
- `tests/unit/cognition/test_phase2_self_model_phase.py` — dirty check (skip on unchanged), first-tick full assessment, death skip

---

## Extension rules

1. To add a new weakness: add a threshold constant, add a detection block in `SelfAssessmentService.assess()`, update the stress/confidence composite formulas if the new weakness is critical-tier. Add it to `perceived_weaknesses` by label string (not enum — label strings are forward-compatible).
2. To add a new condition dimension: add to `perceived_condition` dict with a normalised 0.0–1.0 value. Update downstream consumers that read `perceived_condition` by key.
3. To modulate `uncertainty_level` beyond the 0.1 base: this is a Phase 3+ concern. Add the modifier in a new method on `SelfAssessmentService` rather than in `assess()`.
4. Never make `SelfAssessmentService` stateful — it must remain a pure function of entity state.
