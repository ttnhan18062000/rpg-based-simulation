---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-09-01
---

# Perception Domain Contract

**Source:** `src/domains/perception/` (phase.py, filter.py, salience.py, service.py) + `src/world/perception/gate.py`  
**Pipeline phase:** the Perception Update stage (`PerceptionUpdatePhase`)  
**Authoritative status:** Read-phase direct update — NOT a StateUpdate producer. Uses `dataclasses.replace` to overwrite `entity.cognition.subjective.perception` in-place per entity.

**Note:** `PerceptionUpdatePhase` currently has zero call sites in `AuthoritativeApplyPipeline.refine()` and does not run in any production pipeline tick today, independent of the path fix below (see TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION; pipeline wiring is tracked as a separate, out-of-scope follow-up).

---

## Purpose

The perception domain computes **each entity's subjective perception model** for the current tick — which world signals the entity currently perceives, what it is biased to notice, and what it ignored due to capacity limits. Perception is the interface between raw world signals and entity cognition: it filters the world down to what an entity can and does attend to.

This domain does not decide what to do with percepts. Downstream consumers (adventure routing, strategy) act on the populated `PerceptionModel`.

---

## What It Owns

- `entity.cognition.subjective.perception` — the `PerceptionModel` written each tick for active entities
- Attention focus tag derivation (which signal kinds the entity is biased toward)
- Salience scoring for each candidate world signal
- Budget-clamped partitioning of signals into perceived and ignored sets

The domain does **not** own the world signals themselves, the sense gate, or the knowledge model. It consumes the post-gate signal list and produces the entity's perception snapshot.

---

## Engine Pipeline Phase

**Perception Update stage — `PerceptionUpdatePhase.run()`**

Entry point: `PerceptionUpdatePhase.run(entities, world_signals, tick)`.

- Operates directly on the entity list; does **not** consume or produce `StateUpdate` records.
- Skips entities where `entity.lifecycle.active is False` or `entity.combat.alive is False`.
- Returns a new list of `EntityState` instances with `cognition.subjective.perception` replaced.

**World-side prerequisite:** `PerceptionGate` (at `src/world/perception/gate.py`) runs **before** the Perception Update stage. The gate performs catalog-driven binary sense-channel gating — only signals that pass the gate reach `world_signals` for the Perception Update stage to score. The Perception Update stage never re-evaluates gate eligibility.

---

## Pipeline Per Entity

```
AttentionFocusService → SignalSalienceEvaluator (per signal) → PerceptionFilterService → PerceptionModel replace
```

### Step 1 — AttentionFocusService.get_attention_focus(entity)

Derives a tuple of attention focus tags from three sources, in priority order:

| Source | Tag examples |
|---|---|
| `dominant_need == "healing"` | `healing_resource`, `healer`, `safe_place` |
| `dominant_need == "food"` | `food_source`, `town_inn` |
| `dominant_need == "rest"` | `town_inn`, `safe_place` |
| `dominant_need == "gold"` | `gold_opportunity`, `shop_merchant`, `chest` |
| `dominant_need == "equipment"` | `blacksmith`, `crafting_material`, `weapon_upgrade` |
| `dominant_need == "information"` | `guild_intel`, `location_clue`, `rumor_source` |
| `active_project_id` present | `project_target_{active_project_id}` |
| `fear > 0.6` | `threat`, `escape_route`, `ally` |
| `curiosity > 0.6` | `clue`, `unknown_location`, `rumor` |

Returns a deduplicated ordered tuple of tags. Tags from all three sources may appear simultaneously.

### Step 2 — SignalSalienceEvaluator.evaluate(entity, signal, attention_focus)

Computes a scalar salience score for each candidate `WorldSignal`:

```
score = base_relevance
      + 0.3                              (if signal.kind in attention_focus)
      + danger_level × (1 + fear)        (if danger_level > 0)
      + 0.2 × (1 + curiosity)            (if signal.is_novel)
      − distance × 0.01
```

- `distance` is Euclidean distance between `entity.navigation.position` and `signal.position`.
- `fear` and `curiosity` are read from `entity.cognition.subjective.emotion`.
- Result is clamped to `max(0.0, score)`. Signals with score ≤ 0.0 are dropped entirely.

### Step 3 — PerceptionFilterService.filter(entity, candidate_signals, budget, tick)

Sorts all scored signals by salience descending. Then partitions under budget:

| Outcome | Condition | Budget |
|---|---|---|
| Perceived | salience > 0.0 and perceived_count < max_perceived | max_perceived = 10 |
| Ignored (recorded) | overflow, ignored_list not full | max_ignored_to_record = 5 |
| Ignored (dropped) | overflow, ignored_list full, or salience ≤ 0.0 | — |

Perceived signals are classified into typed containers by `signal.kind`:
- `entity` / `HERO` / `MONSTER` → `perceived_entities` (Dict[int, PerceivedEntity])
- `healing_resource` / `food_source` / `crafting_material` → `perceived_resources`
- `blacksmith` / `town_inn` / `guild_intel` / `shop_merchant` → `perceived_services`
- `threat` → `perceived_threats`
- all other kinds → `perceived_opportunities`

Ignored signals are recorded as `IgnoredSignal(signal_id, reason="capacity_limit", tick=tick)`.

### Step 4 — PerceptionModel replacement

```python
new_perception = PerceptionModel(attention_focus=focus, perceived_entities=..., ..., last_updated_tick=tick)
new_subjective = replace(entity.cognition.subjective, perception=new_perception)
new_cognition  = replace(entity.cognition, subjective=new_subjective)
new_entity     = replace(entity, cognition=new_cognition)
```

All replacements use `dataclasses.replace` — the original entity is never mutated.

---

## World-Side Backing: PerceptionGate

`src/world/perception/gate.py` — runs **before** the Perception Update stage in the engine loop.

| Property | Detail |
|---|---|
| Entry point | `PerceptionGate.can_perceive(source_entity, target_signals, context)` |
| Profile resolution | Reads `entity.identity.properties["sense_profile_id"]` from catalog; falls back to `baseline_humanoid` defaults |
| Sense channels | 7: `vision`, `hearing`, `smell`, `magic_sense`, `life_sense`, `vibration`, `social_reading` |
| Signal keys | `visibility`, `noise`, `scent`, `magic_signal`, `life_signal`, `vibration`, `social_signal` |
| Detection threshold | Score ≥ 0.2 on any channel → `perceived: True` |
| Score formula | `sense_strength × signal_strength × distance_factor × terrain_mod × (0.5 + alertness × 0.5)` |
| Output | `PerceptionResult(perceived, confidence, signals_used, profile_source)` |
| Mutation | None — read-only, deterministic |

The gate is a binary filter. The Perception Update stage never sees signals that the gate blocked.

---

## What It Reads

| Source | Field |
|---|---|
| World signals | post-gate `Sequence[WorldSignal]` (base_relevance, kind, position, danger_level, is_novel) |
| Entity cognition | `entity.cognition.subjective.perception` (previous tick state) |
| Entity self-model | `entity.self_model.needs.dominant_need` |
| Entity cognition | `entity.cognition.subjective.emotion.fear` |
| Entity cognition | `entity.cognition.subjective.emotion.curiosity` |
| Entity strategy | `entity.strategic.current_project_id` |
| Entity navigation | `entity.navigation.position` |
| Entity lifecycle | `entity.lifecycle.active`, `entity.combat.alive` |

---

## What It Decides

- Which world signals are salient enough to perceive (salience scoring)
- What the entity is currently biased to notice (attention focus tag derivation)
- How to classify each perceived signal into typed perception slots
- Which overflow signals to record as ignored vs. silently drop

---

## What It May Mutate

`entity.cognition.subjective.perception` — overwritten each tick for active entities via `dataclasses.replace`. The update is **not** routed through `EntityUpdate` or the authoritative mutation pipeline; it is a direct structural replacement in the returned entity list.

This is the **read-phase direct update pattern**: the phase owns a narrow, bounded slice of cognition state and replaces it synchronously.

---

## What It Must NOT Mutate

| Target | Reason |
|---|---|
| World state / world signals | Perception is read-only with respect to the world |
| `entity.identity` | Identity is not a perception output |
| `entity.cognition.knowledge` | Knowledge model updates happen in a separate phase |
| Other entities' perception | Each entity's perception is computed independently |
| `entity.strategic`, `entity.inventory` | Outside perception scope |
| `PerceptionGate` catalog | Gate is read-only; no catalog mutation allowed |

---

## Domain Interactions

| Domain / System | Direction | Detail |
|---|---|---|
| **PerceptionGate** (`src/world/perception/gate.py`) | Upstream prerequisite | Gate runs before the Perception Update stage; filters which signals reach the salience evaluator |
| **Emotion domain** (event-driven, see emotion_contract.md) | Reads emotion outputs | `fear` and `curiosity` from `EmotionalModel` modulate salience scores and attention focus thresholds |
| **Motivation / needs** | Reads motivation outputs | `dominant_need` drives attention focus tag selection |
| **Adventure domain** | Feeds downstream | `perceived_opportunities` and `perceived_threats` become route candidates for adventure scoring |
| **World emergence** | Feeds downstream | Aggregated entity percepts contribute to world pressure models |
| **Knowledge model** (`src/cognition/knowledge_model.py`) | Separate phase | Knowledge model is updated from percepts in a later phase; perception domain does not write to it |

---

## Test Protection

| Test file | What it covers |
|---|---|
| `tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py` | Salience formula, attention bonus, fear/curiosity scaling, distance penalty, zero-clamp |
| `tests/unit/domains/perception/test_phase12_attention_focus_service.py` | Focus tag derivation from need, project, fear, curiosity; deduplication |
| `tests/unit/domains/perception/test_phase12_perception_filter_service.py` | Budget clamping, signal classification by kind, ignored signal recording |
| `tests/integration/domains/perception/test_phase12_perception_phase.py` | Full phase run over entity list; dead/inactive skip; PerceptionModel construction |
| `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py` | Scenario-level: need-driven attention, fear-amplified threat salience, curiosity-novelty bonus |
| `tests/unit/world/test_sense_perception_gate.py` | PerceptionGate: sense channel scoring, profile fallback, threshold gating |
| `tests/unit/engine/test_pressure_perception_consumers.py` | Downstream consumers reading perception outputs |

---

## Extension Rules

- **New sense channel:** Add channel to the gate catalog and `_SENSE_TO_SIGNAL` mapping in `gate.py`; add a corresponding `sense_profile` schema field; update baseline defaults in `_BASELINE_SENSE`. The Perception Update stage does not need changes — it scores post-gate signals.
- **New attention bias factor:** Extend `AttentionFocusService.get_attention_focus()` with the new condition and tags; update `SignalSalienceEvaluator.evaluate()` if the factor affects the score formula; add test cases for the new bias path.
- **New signal kind:** Add a classification branch in `PerceptionFilterService.filter()` to route the new `signal.kind` into the appropriate typed container.
- **Budget change:** `PerceptionBudget` fields (`max_perceived`, `max_ignored_to_record`) are configurable at `PerceptionUpdatePhase` construction time. Changing the default requires updating the constructor default and relevant tests.
- **Emotion dimension added:** If a new emotion dimension should influence salience, add a read of the new field in `SignalSalienceEvaluator.evaluate()` and document the formula addend here.
- **Determinism:** All scoring is deterministic. Do not introduce randomness into salience evaluation or filter ordering.
