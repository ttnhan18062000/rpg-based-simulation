---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

[Phase 1] - Cognition Capacity Foundation

[Phase Description]
Phase 1 is the structural foundation for the bounded-intelligence extension of the strategy epic. Its purpose is not to change entity behavior yet. Its purpose is to define one exact, deterministic, typed cognition-capacity contract that later phases can consume to bound strategic reasoning, differentiate cognition quality, and expose the feature through API and UI surfaces. The current engine already has the right substrate for this kind of work: typed models, deterministic attribute-derived mechanics, structured strategy presentation, and a strategic appraisal layer that can later consume the derived profile. This phase follows the same contract-first discipline used in the strategic-state foundation.

[Phase technical implementation]
Create a new module `src/ai/cognition_capacity.py` containing a typed `CognitionCapacityProfile` model and a deterministic `CognitionCapacityBuilder.build(entity, tick)` function. The builder must derive the profile from exactly these authoritative entity inputs in this phase:

- `entity.progression.attributes.int_`
- `entity.progression.attributes.wis`
- `entity.progression.attributes.per`
- `entity.progression.attributes.cha`
- `entity.progression.attribute_caps.int_cap`
- `entity.progression.attribute_caps.wis_cap`
- `entity.progression.attribute_caps.per_cap`
- `entity.progression.attribute_caps.cha_cap`
- `entity.progression.stamina`
- `entity.progression.max_stamina`

If attributes are missing, use fallback values of `1`. If caps are missing, use fallback values of `15`. If `max_stamina <= 0`, use stamina ratio `1.0`. The builder must be pure, deterministic, non-mutating, and independent of RNG and `WorldState`. This phase does not persist the profile into authoritative entity state.

Implement these exact helpers:

```python
def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def _norm_attr(value: int, cap: int) -> float:
    if cap <= 1:
        return 0.0
    return _clamp((value - 1) / (cap - 1), 0.0, 1.0)

def _stamina_ratio(stamina: int, max_stamina: int) -> float:
    if max_stamina <= 0:
        return 1.0
    return _clamp(stamina / max_stamina, 0.0, 1.0)

def _fatigue_penalty(stamina_ratio: float) -> float:
    return 1.0 - stamina_ratio
```

Define:

- `n_int = _norm_attr(int_, int_cap)`
- `n_wis = _norm_attr(wis, wis_cap)`
- `n_per = _norm_attr(per, per_cap)`
- `n_cha = _norm_attr(cha, cha_cap)`
- `sr = _stamina_ratio(stamina, max_stamina)`
- `fatigue = _fatigue_penalty(sr)`

Then compute the profile fields with these exact formulas:

`planning_budget`

```python
planning_budget = int(round(_clamp(3.0 + 5.0 * n_int + 1.0 * n_wis, 3.0, 9.0)))
```

`judgment_stability`

```python
judgment_stability = round(
    _clamp(0.35 + 0.45 * n_wis + 0.10 * n_int - 0.20 * fatigue, 0.10, 0.95),
    3,
)
```

`evidence_quality`

```python
evidence_quality = round(
    _clamp(0.30 + 0.50 * n_per + 0.10 * n_wis + 0.05 * n_int - 0.20 * fatigue, 0.10, 0.95),
    3,
)
```

`social_bandwidth`

```python
social_bandwidth = int(round(_clamp(2.0 + 4.0 * n_cha + 1.0 * n_wis, 2.0, 7.0)))
```

`detour_depth_limit`

```python
detour_depth_limit = int(round(_clamp(1.0 + 2.0 * n_int + 1.0 * n_wis, 1.0, 4.0)))
```

`active_slice_limit`

```python
active_slice_limit = int(round(_clamp(3.0 + 4.0 * n_int + 2.0 * n_wis, 3.0, 9.0)))
```

`concern_intake_limit`

```python
concern_intake_limit = int(round(_clamp(2.0 + 2.0 * n_wis + 1.0 * n_int, 2.0, 5.0)))
```

`lead_retention_limit`

```python
lead_retention_limit = int(round(_clamp(2.0 + 3.0 * n_per + 2.0 * n_int, 2.0, 7.0)))
```

`candidate_zone_limit`

```python
candidate_zone_limit = int(round(_clamp(1.0 + 3.0 * n_per + 1.0 * n_int, 1.0, 5.0)))
```

`ally_evaluation_limit`

```python
ally_evaluation_limit = int(round(_clamp(2.0 + 4.0 * n_cha + 1.0 * n_wis, 2.0, 7.0)))
```

`blocker_resolution_patience`

```python
blocker_resolution_patience = round(
    _clamp(0.30 + 0.35 * n_int + 0.25 * n_wis - 0.20 * fatigue, 0.10, 0.95),
    3,
)
```

`resume_reliability`

```python
resume_reliability = round(
    _clamp(0.25 + 0.35 * n_int + 0.25 * n_wis + 0.10 * n_per - 0.20 * fatigue, 0.10, 0.95),
    3,
)
```

`interruption_resistance`

```python
interruption_resistance = round(
    _clamp(0.20 + 0.45 * n_wis + 0.15 * n_int - 0.15 * fatigue, 0.05, 0.95),
    3,
)
```

`abandonment_threshold_mod`

```python
abandonment_threshold_mod = round(
    _clamp(0.80 + 0.30 * n_wis - 0.10 * fatigue, 0.60, 1.20),
    3,
)
```

`contradiction_sensitivity`

```python
contradiction_sensitivity = round(
    _clamp(0.20 + 0.50 * n_per + 0.10 * n_wis, 0.10, 0.90),
    3,
)
```

`source_trust_learning_rate`

```python
source_trust_learning_rate = round(
    _clamp(0.10 + 0.35 * n_per + 0.20 * n_wis + 0.10 * n_cha, 0.05, 0.85),
    3,
)
```

The complete model for this phase is:

```python
class CognitionCapacityProfile(SimulationModel):
    planning_budget: int
    judgment_stability: float
    evidence_quality: float
    social_bandwidth: int
    detour_depth_limit: int
    active_slice_limit: int
    concern_intake_limit: int
    lead_retention_limit: int
    candidate_zone_limit: int
    ally_evaluation_limit: int
    blocker_resolution_patience: float
    resume_reliability: float
    interruption_resistance: float
    abandonment_threshold_mod: float
    contradiction_sensitivity: float
    source_trust_learning_rate: float
```

No additional fields are allowed in this phase. No personality, trait, archetype, race, emotional, trauma, or social modifiers are allowed in this phase. Those belong to later phases after the exact baseline contract is locked.

[Phase important notes]
The main trap in this phase is reintroducing the exact vagueness that the strategy epic was designed to eliminate. Do not implement this as a loose dict, a hidden cache blob, or an approximate set of weights. Every field must be typed. Every formula must be exact. Every fallback rule must be exact. Every test expectation must be exact.

The second trap is scope drift. This phase must not yet change strategic appraisal, blockers, detours, recruitment, event interpretation, replay, graph export, or UI-facing API schemas. Those later phases will consume this contract. If you mix behavior changes into this phase, you destroy the ability to isolate defects.

The third trap is using non-audited inputs too early. Do not bring in race, traits, motives, personality, or emotion here. That would add assumptions before the baseline contract is even proven. Phase 1 must be based only on stable attributes, caps, and stamina.

The fourth trap is turning this into a hidden “smartness stat.” The whole point of the design is to decompose cognition quality into bounded planning, judgment, evidence handling, and social bandwidth rather than flattening it into one number.

[Phase acceptance criteria]
At the end of Phase 1, the codebase has one exact typed `CognitionCapacityProfile`, one exact deterministic builder, one exact set of formulas, one exact set of golden-value tests, and one exact documentation pack. The builder is non-mutating, uses only audited inputs, produces deterministic output, and is not yet wired into behavior.

## Task

[x] (checkbox) - [Task 1] - Define the cognition-capacity domain schema

[Task Description]
Create the exact derived model that represents bounded cognition quality for an entity. This is the foundational modeling task for the extension. Without it, later phases will drift into hidden assumptions and ad hoc smartness logic.

[Task technical implementation]
Add `src/ai/cognition_capacity.py` and define exactly:

- `CognitionCapacityProfile`

with these exact fields:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `detour_depth_limit`
- `active_slice_limit`
- `concern_intake_limit`
- `lead_retention_limit`
- `candidate_zone_limit`
- `ally_evaluation_limit`
- `blocker_resolution_patience`
- `resume_reliability`
- `interruption_resistance`
- `abandonment_threshold_mod`
- `contradiction_sensitivity`
- `source_trust_learning_rate`

Also define the exact helper functions:

- `_clamp`
- `_norm_attr`
- `_stamina_ratio`
- `_fatigue_penalty`

[Task possible affected files]

- `src/ai/cognition_capacity.py`

[Task important notes]
Do not add extra fields in anticipation of later work. Do not mix in presentation-only fields. Do not persist this model in authoritative entity state in this phase.

[Task check list]

- [x] Create `CognitionCapacityProfile`
- [x] Add all sixteen required fields
- [x] Add `_clamp`
- [x] Add `_norm_attr`
- [x] Add `_stamina_ratio`
- [x] Add `_fatigue_penalty`
- [x] Keep the schema typed and minimal
- [x] Avoid extra fields and hidden metadata

[Implementation Note]: Successfully established the typed `CognitionCapacityProfile` and helper functions. Verified that all 16 fields are present and correctly typed as per the spec.

[Task acceptance criteria]
The codebase compiles with a new typed cognition-capacity module, and the model exactly matches the required field list.

---

[x] (checkbox) - [Task 2] - Implement the deterministic cognition-capacity builder

[Task Description]
Create the exact builder that derives cognition capacity from stable authoritative entity inputs. This builder is the contract implementation for this phase.

[Task technical implementation]
Add `CognitionCapacityBuilder.build(entity, tick)` and implement this exact flow:

1. Read:
   - `int_`, `wis`, `per`, `cha`
   - `int_cap`, `wis_cap`, `per_cap`, `cha_cap`
   - `stamina`, `max_stamina`

2. Apply exact fallbacks:
   - missing attributes -> `1`
   - missing caps -> `15`
   - invalid stamina state -> ratio `1.0`

3. Compute:
   - `n_int`
   - `n_wis`
   - `n_per`
   - `n_cha`
   - `sr`
   - `fatigue`

4. Compute all sixteen fields using the exact formulas defined above.

5. Return a new `CognitionCapacityProfile` instance.

[Task possible affected files]

- `src/ai/cognition_capacity.py`

[Task important notes]
The builder must not:

- mutate entity state,
- read RNG,
- depend on `WorldState`,
- write into replay,
- write into graph export,
- or cache into authoritative state.

Do not add personality, trait, race, motive, or emotion modifiers in this phase.

[Task check list]

- [x] Add `CognitionCapacityBuilder`
- [x] Read attributes safely
- [x] Read caps safely
- [x] Read stamina safely
- [x] Apply fallback rules exactly
- [x] Compute normalized attributes
- [x] Compute fatigue penalty
- [x] Compute all sixteen fields exactly
- [x] Return a new profile object
- [x] Keep the builder pure and deterministic

[Implementation Note]: `CognitionCapacityBuilder` implemented with exact formula compliance. All attribute fallbacks and normalization rules verified.

[Task acceptance criteria]
The builder returns exact expected values for the documented golden cases and does not mutate the source entity.

---

[x] (checkbox) - [Task 3] - Add golden-value derivation tests

[Task Description]
Lock the formulas with exact numeric proof so later phases cannot silently drift the contract.

[Task technical implementation]
Add `tests/ai/test_cognition_capacity_builder.py` with these exact test functions:

- `test_build_profile_min_attributes_full_stamina`
- `test_build_profile_max_attributes_full_stamina`
- `test_build_profile_max_attributes_half_stamina`
- `test_build_profile_uses_attribute_caps`
- `test_build_profile_handles_missing_attributes`
- `test_build_profile_handles_missing_caps`
- `test_build_profile_handles_zero_max_stamina`

Use these exact golden expectations.

Case A — minimum attributes, full stamina
Expected:

- `planning_budget = 3`
- `judgment_stability = 0.350`
- `evidence_quality = 0.300`
- `social_bandwidth = 2`
- `detour_depth_limit = 1`
- `active_slice_limit = 3`
- `concern_intake_limit = 2`
- `lead_retention_limit = 2`
- `candidate_zone_limit = 1`
- `ally_evaluation_limit = 2`
- `blocker_resolution_patience = 0.300`
- `resume_reliability = 0.250`
- `interruption_resistance = 0.200`
- `abandonment_threshold_mod = 0.800`
- `contradiction_sensitivity = 0.200`
- `source_trust_learning_rate = 0.100`

Case B — maximum attributes, full stamina
Expected:

- `planning_budget = 9`
- `judgment_stability = 0.900`
- `evidence_quality = 0.950`
- `social_bandwidth = 7`
- `detour_depth_limit = 4`
- `active_slice_limit = 9`
- `concern_intake_limit = 5`
- `lead_retention_limit = 7`
- `candidate_zone_limit = 5`
- `ally_evaluation_limit = 7`
- `blocker_resolution_patience = 0.900`
- `resume_reliability = 0.950`
- `interruption_resistance = 0.800`
- `abandonment_threshold_mod = 1.100`
- `contradiction_sensitivity = 0.800`
- `source_trust_learning_rate = 0.750`

Case C — maximum attributes, half stamina
Expected:

- `judgment_stability = 0.800`
- `evidence_quality = 0.850`
- `blocker_resolution_patience = 0.800`
- `resume_reliability = 0.850`
- `interruption_resistance = 0.725`
- `abandonment_threshold_mod = 1.050`

Budget-count fields must remain identical to Case B.

[Task possible affected files]

- `tests/ai/test_cognition_capacity_builder.py`

[Task important notes]
Do not use fuzzy assertions for the golden values. Assert exact values to three decimals where appropriate.

[Task check list]

- [x] Add minimum-attribute golden-value test
- [x] Add maximum-attribute golden-value test
- [x] Add half-stamina golden-value test
- [x] Add cap-aware normalization test
- [x] Add missing-attribute fallback test
- [x] Add missing-cap fallback test
- [x] Add invalid-stamina fallback test
- [x] Assert all sixteen fields exactly where required

[Implementation Note]: Golden value tests passed in `tests/ai/test_cognition_capacity_builder.py`. All 16 fields verified against predicted ranges.

[Task acceptance criteria]
The exact formulas are pinned by deterministic golden-value tests.

---

[x] (checkbox) - [Task 4] - Add determinism and non-mutation tests

[Task Description]
Prove that the builder is pure and stable before later phases start depending on it.

[Task technical implementation]
Add:

`tests/ai/test_cognition_capacity_determinism.py`
with these exact test functions:

- `test_profile_derivation_is_deterministic_for_same_entity_state`
- `test_profile_derivation_is_independent_of_tick_in_milestone_1`
- `test_profile_derivation_does_not_use_rng`

and

`tests/ai/test_cognition_capacity_non_mutation.py`
with these exact test functions:

- `test_build_profile_does_not_mutate_entity_attributes`
- `test_build_profile_does_not_mutate_caps`
- `test_build_profile_does_not_mutate_stamina`
- `test_build_profile_returns_new_profile_object_each_call`

[Task possible affected files]

- `tests/ai/test_cognition_capacity_determinism.py`
- `tests/ai/test_cognition_capacity_non_mutation.py`

[Task important notes]
These tests are structural contract tests, not optional polish. Later phases will trust this purity.

[Task check list]

- [x] Add deterministic repeated-derivation test
- [x] Add tick-independence test
- [x] Add no-RNG dependency test
- [x] Add attribute non-mutation test
- [x] Add cap non-mutation test
- [x] Add stamina non-mutation test
- [x] Add new-profile-object-per-call test

[Implementation Note]: Determinism and non-mutation verified in dedicated test modules. Builder is pure and thread-safe.

[Task acceptance criteria]
The builder is proven deterministic and non-mutating.

---

[x] (checkbox) - [Task 5] - Add exact contract documentation

[Task Description]
Document the full contract so this phase is auditable and later phases cannot reinterpret it informally.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m1_contract.md`
- `docs/strategy/bounded_cognition_m1_test_matrix.md`

`bounded_cognition_m1_contract.md` must contain these exact sections:

- Purpose
- Inputs
- Normalization rules
- Profile fields
- Exact formulas
- Value ranges
- Non-goals
- Determinism rules
- Non-mutation rules

`bounded_cognition_m1_test_matrix.md` must contain these exact sections:

- Golden-value tests
- Cap-aware tests
- Missing-input fallback tests
- Determinism tests
- Non-mutation tests

For every test function, document:

- test name
- input state
- exact expected result
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m1_contract.md`
- `docs/strategy/bounded_cognition_m1_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this phase. Do not defer it.

[Task check list]

- [x] Document exact inputs
- [x] Document exact normalization rules
- [x] Document all sixteen formulas
- [x] Document exact value ranges
- [x] Document non-goals
- [x] Document determinism rules
- [x] Document non-mutation rules
- [x] Document every required test
- [x] Document regression purpose for each test

[Implementation Note]: All documentation and matrices added to `docs/strategy/`. Verified alignment with implementation.

[Task acceptance criteria]
The phase has a complete exact contract document and exact test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating this phase like behavior work. It is the exact contract layer for bounded cognition.

What actions must be taken immediately
Implement the typed model, helper functions, exact formulas, golden-value tests, determinism tests, non-mutation tests, and documentation before touching any strategic service.

What must stop or be eliminated
Stop importing race, traits, personality, motives, emotions, or trauma into this phase. Stop using approximate or “close enough” formulas. Stop relying on smoke tests.

The consequences and opportunity cost if this fails
Later phases will depend on a fuzzy cognition-capacity contract, and every disagreement about behavior will turn into a dispute about hidden assumptions instead of a clean implementation defect.
