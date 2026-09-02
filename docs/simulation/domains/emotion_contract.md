---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-08-31
---

# Emotion Domain Contract

**Source:** `src/domains/emotion/` (emotion_service.py, habit_service.py, recovery_service.py, opportunity_cost.py)  
**Pipeline phase:** event-driven, NOT every-tick scheduled  
**Authoritative status:** Synchronous in-event callback pattern. Returns new immutable instances via `dataclasses.replace`. Does NOT produce `EntityUpdate` or route through the authoritative mutation pipeline — **except** the `combat_engagement` habit-bias write path (`HabitBiasService.record_outcome`), which as of `TCK-20260831-HABIT-BIAS-WIRING` is instead driven by a real pipeline phase (`HabitBiasUpdatePhase`, `src/domains/emotion/habit_phase.py`) that writes through `EntityUpdate.cognition_bundle_set` on the authoritative apply path, gated behind `ENABLE_HABIT_BIAS_ACTION_STYLE` (default OFF). All other emotion-domain services (`EmotionUpdateService`, `RecoveryReadinessService`, `OpportunityCostEvaluator`) remain the synchronous in-event callback pattern described above; see the event table below.

---

## Purpose

The emotion domain maintains each entity's **short-term emotional state** and **habit memory** — the subjective internal pressures that modulate how the entity scores routes, assesses risk, and responds to setbacks. Emotion outputs are consumed by perception salience scoring, adventure route evaluation, and commitment abandonment logic.

This domain does not schedule or initiate actions. It responds to events and produces updated state records that downstream domains read as inputs.

---

## What It Owns

- `EmotionalModel` — 7 emotion dimensions, each in [0.0, 1.0]
- `HabitMemory.patterns` — per-action bias floats accumulated from outcome history
- `RecoveryState` — near-death flag, forced recovery window, retry readiness
- Opportunity cost computation for competing actions (stateless utility, no owned state)

---

## Engine Pipeline Phase

**Event-driven** (not a scheduled per-tick stage)

Emotion updates are **not** driven by a scheduled per-tick phase runner. They are triggered by specific engine events via synchronous callbacks:

- `near_death` event → `EmotionUpdateService.update_on_event` + `RecoveryReadinessService.register_near_death`, called from `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py`) — the only event of this group with a confirmed production call site
- `easy_win` event → `EmotionUpdateService.update_on_event` (delta rule defined; no production call site wired yet)
- `repeated_failure` event → `EmotionUpdateService.update_on_event` (delta rule defined; no production call site wired yet)
- `new_unknown` event → `EmotionUpdateService.update_on_event` (delta rule defined; no production call site wired yet)
- `successful_goal` event → `EmotionUpdateService.update_on_event` (delta rule defined; no production call site wired yet)
- `stagnation` event → `EmotionUpdateService.update_on_event` (delta rule defined; no production call site wired yet)
- `combat_loss` trigger event → `HabitBiasUpdatePhase.apply()` (`src/domains/emotion/habit_phase.py`) → `HabitBiasService.record_outcome(habit, "combat_engagement", success=False)` — the domain's **only** habit-bias event with a confirmed production call site, wired as of `TCK-20260831-HABIT-BIAS-WIRING`, gated behind `ENABLE_HABIT_BIAS_ACTION_STYLE` (default OFF). No win/victory `WorldEventCategory` exists, so `record_outcome` can currently only ever be called with `success=False` — see the `HabitBiasService` section below for the resulting one-way-decay implication. Unlike the five event kinds above, this call site does **not** run as a synchronous in-event callback: it is a pipeline phase (see Authoritative status above)

The domain has no `phase.py` of its own for the five `EmotionUpdateService` event kinds above — those are invoked by event handlers in the engine, not by the phase scheduler. `HabitBiasUpdatePhase` (`src/domains/emotion/habit_phase.py`) is the one exception, living under `src/domains/emotion/` but running as a real pipeline phase in `AuthoritativeApplyPipeline.refine()`.

---

## Emotional Model

`EmotionalModel` holds 7 dimensions, all clamped to [0.0, 1.0]:

| Dimension | Role |
|---|---|
| `fear` | Amplifies threat salience in perception; modulates recovery readiness |
| `confidence` | Affects adventure route scoring; reduced by failure events |
| `frustration` | Signals repeated-failure pressure; cleared by successful_goal |
| `curiosity` | Amplifies novelty salience in perception; boosted by new_unknown |
| `satisfaction` | Positive feedback from goal completion; cleared indirectly by stagnation |
| `panic` | Acute distress spike from near_death; highest urgency signal |
| `boredom` | Pressure to seek new routes; accumulates from stagnation |

---

## Service Contracts

### EmotionUpdateService.update_on_event(model, event_kind) → EmotionalModel

Applies deterministic delta rules to the current `EmotionalModel`. All deltas are additive; all results are clamped to [0.0, 1.0]. No randomness.

| event_kind | Deltas applied |
|---|---|
| `near_death` | fear +0.4, panic +0.5, confidence −0.3 |
| `easy_win` | confidence +0.1, satisfaction +0.1, fear −0.2 |
| `repeated_failure` | frustration +0.3, confidence −0.1 |
| `new_unknown` | curiosity +0.2 |
| `successful_goal` | satisfaction +0.2, frustration −0.3 |
| `stagnation` | boredom +0.1 |

Returns a new `EmotionalModel` instance. The input model is never mutated.

### HabitBiasService

Maintains `HabitMemory.patterns`: a dict mapping `pattern_id` (action identifier string) to a bias float in [0.0, 1.0], where 0.5 is neutral.

**record_outcome(memory, pattern_id, success) → HabitMemory**

- Success: `bias = min(1.0, current_bias + 0.1)`
- Failure: `bias = max(0.0, current_bias - 0.1)`
- New patterns default to 0.5 before their first recorded outcome.
- Returns a new `HabitMemory` via `dataclasses.replace`.

**apply_habit_bias(memory, tags, base_score) → float**

For each `tag` in `tags` that exists in `memory.patterns`:

```
score += (memory.patterns[tag] - 0.5) × 0.4
```

A bias of 1.0 contributes +0.2; a bias of 0.0 contributes −0.2; neutral 0.5 contributes 0.0. Applied additively to `base_score` — no clamping at this layer (caller is responsible).

**Production call sites (`TCK-20260831-HABIT-BIAS-WIRING`, all gated behind `ENABLE_HABIT_BIAS_ACTION_STYLE`, default OFF):**

- **Write:** `HabitBiasUpdatePhase.apply()` (`src/domains/emotion/habit_phase.py`) calls `record_outcome(habit, "combat_engagement", success=False)` for every `combat_loss` trigger event, per tick, in the authoritative pipeline (placed after `memory_update`, before `self_model`). No code path currently calls `record_outcome` with `success=True` — no win/victory `WorldEventCategory` exists yet. **This means the `"combat_engagement"` pattern in practice is a one-way monotonic decay from its 0.5 neutral default toward the 0.0 floor as an entity loses combat encounters; there is currently no way for it to recover.** Do not assume symmetric reinforcement/decay behavior for this pattern until a win trigger is added.
- **Read:** `TacticalDecisionSystem.evaluate_entity_intent()` (`src/engine/tactical.py`, SKIRMISHER kiting-distance branch) and `MovementSystem.resolve_move()` (`src/engine/movement.py`, EVASIVE opportunity-attack suppression) both call `apply_habit_bias(habit, ["combat_engagement"], personality.bravery)`, clamp to `[0.0, 1.0]`, and re-derive `ActionStyle` from the result. The two read sites are wired together and must stay synchronized — see `docs/mechanics/04_strategic_cognition.md` §6.3 for the full mechanic and the `ActionStyle` threshold rule they both re-run.

### RecoveryReadinessService

Enforces a **30-tick forced recovery window** after a `near_death` event. During this window, the entity must not re-enter combat or high-risk routes.

**register_near_death(state, current_tick) → RecoveryState**

Sets `recent_near_death=True`, `recovery_until_tick = current_tick + 30`, `retry_readiness = 0.1`, `confidence_loss += 0.4`, appends `"near_death"` to `trauma_tags`. Returns a new `RecoveryState`.

**is_ready_to_retry(state, current_tick) → bool**

Returns `True` if:
- `recent_near_death` is False (no active recovery), OR
- `recovery_until_tick` is set and `current_tick >= recovery_until_tick`, OR
- `retry_readiness >= 0.8` (readiness threshold met before window expires)

Returns `False` if none of the above apply — caller must gate combat/high-risk route eligibility on this result.

### OpportunityCostEvaluator.evaluate_cost(action_kind, is_needed_for_upgrade, has_alternative) → float

Stateless utility returning an opportunity cost in [0.0, 1.0]. Consumed by adventure domain scoring to penalize actions that foreclose better alternatives.

| action_kind | Conditions | Cost |
|---|---|---|
| `sell_material` | needed for upgrade, no alternative | 0.9 (capped at 1.0) |
| `sell_material` | needed for upgrade, alternative exists | 0.6 |
| `sell_material` | not needed | 0.1 |
| `join_party` | conflicts with active solo goal | 0.5 |
| any other | — | 0.0 |

This service holds no state and owns no durable fields.

---

## What It Reads

| Source | Field |
|---|---|
| Triggering event | `event_kind` string |
| Entity cognition | current `EmotionalModel` |
| Entity cognition | current `HabitMemory` |
| Entity cognition | current `RecoveryState` |
| Adventure/combat context | `is_needed_for_upgrade`, `has_alternative`, `is_greed_driven` (passed in by caller) |

The domain does not read world state, entity identity, or inventory directly.

---

## What It Decides

- How to update emotion dimensions in response to a specific event kind
- Whether the forced recovery window is still active (blocking high-risk eligibility)
- How habit bias shifts based on action outcome history
- What opportunity cost to assign to a competing action

---

## What It May Mutate

`EmotionalModel`, `HabitMemory`, and `RecoveryState` — returned as new immutable instances via `dataclasses.replace`. The caller is responsible for writing these back into the entity's cognition state.

Updates are **not** routed through `EntityUpdate` or the authoritative mutation pipeline — this is the synchronous in-event callback pattern: the domain receives current state, computes the updated state, and returns the new record. **Exception:** the `combat_engagement` habit-bias write (`HabitBiasUpdatePhase`) does route through `EntityUpdate.cognition_bundle_set` on the authoritative apply path; see the Authoritative status note at the top of this doc.

---

## What It Must NOT Mutate

| Target | Reason |
|---|---|
| Entity identity, class, attributes | Emotion is a short-term modulator, not an identity owner |
| Inventory, gold, equipment | No economic ownership |
| Strategic projects or goals | Emotion constrains and modulates strategy but does not own it |
| Other entities' state | Emotion updates are strictly per-entity |
| World state | The domain is entirely internal to entity cognition |

---

## Domain Interactions

| Domain / System | Direction | Detail |
|---|---|---|
| **Perception domain** (Perception Update stage) | Reads emotion outputs | `fear` and `curiosity` from `EmotionalModel` are read by `SignalSalienceEvaluator` to modulate threat and novelty salience |
| **Adventure domain** | Reads emotion outputs | `confidence` affects route scoring; `RecoveryReadinessService.is_ready_to_retry()` gates combat/high-risk route eligibility |
| **Commitment domain** (inline utility, see commitment_contract.md) | Reads emotion outputs | Near-death emotion state (fear, panic) informs survival abandonment classification |
| **Engine event handlers** | Triggers | Engine fires event callbacks on specific game outcomes; emotion domain is called synchronously within those handlers. Confirmed production call site: `NearDeathHardeningPhase.apply()` (`src/engine/pipeline_phases/hardening.py`) for the `near_death` event — the other five event kinds (`easy_win`, `repeated_failure`, `new_unknown`, `successful_goal`, `stagnation`) have delta rules defined but no production call site yet |
| **Authoritative apply pipeline** (`AuthoritativeApplyPipeline.refine()`) | Triggers (habit-bias write only) | `HabitBiasUpdatePhase` (`src/domains/emotion/habit_phase.py`) runs as a real pipeline phase, not a synchronous event callback — the one exception to this domain's event-driven pattern (`TCK-20260831-HABIT-BIAS-WIRING`, behind `ENABLE_HABIT_BIAS_ACTION_STYLE`) |
| **Tactical/Movement domains** (`src/engine/tactical.py`, `src/engine/movement.py`) | Read emotion outputs | `HabitBiasService.apply_habit_bias()` re-derives live `ActionStyle` from habit-biased bravery for SKIRMISHER kiting distance and EVASIVE opportunity-attack suppression respectively, behind `ENABLE_HABIT_BIAS_ACTION_STYLE` (`TCK-20260831-HABIT-BIAS-WIRING`) |

---

## Test Protection

| Test file | What it covers |
|---|---|
| `tests/unit/domains/emotion/test_phase16_emotion_update_service.py` | Delta rules per event_kind; clamping to [0.0, 1.0]; no-mutation of input |
| `tests/unit/domains/emotion/test_phase16_habit_bias_service.py` | record_outcome shift ±0.1; apply_habit_bias additive formula; neutral baseline 0.5 |
| `tests/unit/domains/emotion/test_phase16_recovery_readiness_service.py` | register_near_death window assignment; is_ready_to_retry tick boundary; readiness threshold |
| `tests/unit/domains/emotion/test_phase16_emotional_model.py` | EmotionalModel schema; field clamping; immutability |
| `tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py` | Scenario-level: near_death cascade, habit reinforcement across multiple outcomes, stagnation boredom accumulation |
| `tests/integration/scenarios/test_phase17_decision_trace_scenarios.py` | Downstream: confidence affects route scoring; recovery window blocks route eligibility |
| `tests/unit/strategic/test_cognition_immediate_fixes.py` | Cognition model integration with emotion state |
| `tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py` | `HabitBiasUpdatePhase` writes through the authoritative pipeline on `combat_loss`; preserves prior same-tick `cognition_bundle_set` writes; flag gates the phase |
| `tests/unit/tactical/test_habit_bias_action_style_wiring.py` | `tactical.py`'s live habit-biased `ActionStyle` re-derivation, on and off the flag |
| `tests/unit/movement/test_tactical_movement.py` | `movement.py`'s live habit-biased `ActionStyle` re-derivation for EVASIVE opportunity-attack suppression, on and off the flag |
| `tests/architecture/test_habit_bias_personality_frozen.py` | `PersonalityComponent` stays frozen/immutable; no `PersonalityUpdate` type introduced; habit-bias wiring never constructs a `PersonalityComponent` |

---

## Extension Rules

- **New emotion dimension:** Add field to `EmotionalModel` with default 0.0; add delta rules in `EmotionUpdateService.update_on_event()`; update all downstream consumers that read `EmotionalModel` (at minimum: perception salience formula and this contract doc).
- **New event_kind:** Add a delta rule block in `EmotionUpdateService.update_on_event()` for the new event. Keep all deltas deterministic — no randomness permitted.
- **New action_kind in opportunity cost:** Add a branch in `OpportunityCostEvaluator.evaluate_cost()`. Document the cost rationale in the branch comment.
- **Recovery window duration:** The 30-tick window is a hardcoded constant in `RecoveryReadinessService.register_near_death()`. If it needs to be configurable, extract it as a parameter rather than altering the hardcoded value silently.
- **Determinism invariant:** All four services are fully deterministic. Do not introduce randomness. Event-driven updates must produce the same `EmotionalModel` given the same input model and event_kind.
