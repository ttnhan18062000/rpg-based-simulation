This document is a corrective update to the bounded-intelligence implementation plan.

It is **not** a restatement of the original feature roadmap.
It contains only:

- remaining missing work,
- falsely checked or overstated tasks,
- and proof gaps where the implementation claim is stronger than the evidence.

The most important finding is this:

The bounded-cognition feature architecture is materially real, but several checked boxes are ahead of the verified contract.
The main failure mode is no longer “feature absent.” It is “declared complete with incomplete derivation, incomplete proof, or incomplete visibility population.”

---

## Milestone 1 — Make the cognition-capacity derivation contract honest

### Description

The typed contract exists.
The builder exists.
The problem is that the implementation and tests currently prove a narrower derivation contract than the plan claims. The plan marks personality, traits, archetype, and temporary overload modifiers as done, while the visible builder tests prove attribute-, cap-, stamina-, determinism-, and non-mutation behavior.

### Technical implementation

Choose one path explicitly:

**Option A — finish the richer derivation contract**
Implement and test derivation from:

- personality,
- traits,
- archetype,
- emotional overload,
- trauma or similar temporary impairment state.

**Option B — narrow the contract**
Rewrite Milestone 1 so it truthfully states that current derivation is attribute/cap/stamina based, with later expansion planned separately.

### Important notes

Do not keep checked boxes for source inputs that are not pinned by implementation and tests.
That is document fraud, not progress.

### Acceptance criteria

Milestone 1 is complete only when the derivation inputs claimed in the document are exactly the inputs proven by source and tests.

## Task

[x] (checkbox) - [Task 1] - Reopen false-completion checklist items for builder inputs

[Task Description]

The current checked items for personality, trait, archetype, and temporary overload mapping are stronger than the visible evidence.

[Task technical implementation]

Either implement these derivation sources and add tests, or uncheck/remove them from Milestone 1.

[Task possible affected files]

- `src/ai/cognition_capacity.py`
- `tests/ai/test_cognition_capacity_builder.py`
- `tests/ai/test_cognition_capacity_determinism.py`
- docs for bounded cognition feature spec

[Task check list]

- [x] Decide which non-attribute inputs are truly in scope now
- [x] Implement missing source-input derivation or narrow the contract
- [x] Add one deterministic derivation test per newly supported input
- [x] Update Milestone 1 checklist to match reality

[Task acceptance criteria]

Milestone 1 checklist reflects the real builder contract.

---

[x] (checkbox) - [Task 2] - Add explicit derivation tests for any newly supported non-attribute inputs

[Task Description]

The existing test surface is too concentrated on attributes and stamina.

[Task technical implementation]

Add targeted tests for:

- personality modifiers,
- trait modifiers,
- archetype modifiers,
- overload/temporary-impairment penalties,

but only for inputs the builder actually consumes.

[Task possible affected files]

- `tests/ai/test_cognition_capacity_builder.py`

[Task check list]

- [x] Add personality derivation test
- [x] Add trait derivation test
- [x] Add archetype derivation test
- [x] Add overload/temporary-state derivation test

[Task acceptance criteria]

Every claimed derivation source has a direct deterministic test.

---

## Milestone 2 — Pin the budgets that are actually enforced in strategic appraisal

### Description

The bounded-appraisal feature exists and is tested in meaningful ways, but the plan claims a broader set of enforced limits than the visible proof currently locks down. The strongest proof is around active slices, continuity behavior, detour depth, and some lead/social limits. The plan still overstates certainty for all declared budgets.

### Technical implementation

Separate:

- budgets that are structurally enforced and tested,
- budgets that are implemented but weakly proven,
- budgets that are only declared in the profile and schema.

### Acceptance criteria

Milestone 2 is complete only when every capacity field claimed to influence appraisal has either direct enforcement proof or is explicitly excluded from the claim set.

## Task

[x] (checkbox) - [Task 1] - Add explicit enforcement proof for `candidate_zone_limit` and `ally_evaluation_limit`

[Task Description]

These fields are part of the declared cognition contract, but they need direct enforcement proof in strategic/social flow or the plan should stop implying that they are fully pinned.

[Task technical implementation]

Add deterministic tests that verify:

- candidate-zone processing is capped by `candidate_zone_limit`,
- ally evaluation is capped by `ally_evaluation_limit`,
- and the capped behavior is observable in state or debug fields.

[Task possible affected files]

- `tests/ai/test_bounded_detours.py`
- `tests/ai/test_social_cognition.py`
- appraisal and social selection services

[Task check list]

- [x] Add candidate-zone budget enforcement test
- [x] Add ally-evaluation budget enforcement test
- [x] Add traceability assertion for capped evaluation

[Task acceptance criteria]

Those two limits are either directly proven or removed from the “fully integrated” claim set.

---

## Milestone 3 — Close authoritative proof for uncertainty learning and source-trust updates

### Description

The learning service now emits `source_trust_updates`, which is stronger than one stale test comment suggests. But the plan still needs authoritative state-application proof and future-behavior proof, not just service-local output proof.

### Technical implementation

Close the loop from:

- lead outcome,
- to `StrategicUpdate`,
- to authoritative strategic state,
- to future source weighting or learning behavior.

### Acceptance criteria

Milestone 3 is complete only when source trust is proven as durable state, not just calculated output.

## Task

[x] (checkbox) - [Task 1] - Add end-to-end source-trust application and future-effect tests

[Task Description]

This is now the missing proof.
Not the service method itself.

[Task technical implementation]

Add tests that verify:

- source trust changes are applied to strategic state,
- later lead handling consults that updated trust,
- contradictory evidence changes future source weighting deterministically.

[Task possible affected files]

- `tests/ai/test_lead_learning.py`
- `src/systems/gameplay/action_system.py`
- strategic learning/ingestion services

[Task check list]

- [x] Add authoritative source-trust application test
- [x] Add later-source-weighting effect test
- [x] Add contradiction-to-trust regression test

[Task acceptance criteria]

Source-trust learning is proven end to end.

---

## Milestone 4 — Make social bounded-cognition claims precise

### Description

Social bounded-cognition is materially implemented, but the plan should stop treating every listed social effect as equally proven. `social_bandwidth` behavior is visibly tested; future recruitment behavior after breach/success still needs stronger deterministic proof.

### Acceptance criteria

Milestone 4 is complete only when future cooperation effects are proven with the same rigor as current ally-selection breadth.

## Task

[x] (checkbox) - [Task 1] - Add deterministic post-breach and post-success future-recruitment tests

[Task Description]

The plan already claims future willingness to re-engage after breach or success. That needs direct proof.

[Task technical implementation]

Add tests that verify:

- breach reduces later recruitment willingness,
- successful cooperation improves later recruitment willingness,
- and divergence is profile-sensitive where the plan claims it is.

[Task possible affected files]

- `tests/ai/test_social_cognition.py`
- recruitment and contract logic

[Task check list]

- [x] Add post-breach future-recruitment test
- [x] Add post-success future-recruitment test
- [x] Add profile-sensitive divergence assertion

[Task acceptance criteria]

Milestone 4 proves durable cooperation effects, not just immediate ally selection.

---

## Milestone 6 — Make overload visibility honest

### Description

The schema layer declares four overload fields, but the presenter serialization shown in source only populates `is_overloaded` and `overload_score`. The current visibility tests also assert only those two populated fields. That makes the current checklist too generous.

### Technical implementation

Choose one path explicitly:

**Option A — finish overload visibility**
Populate and test:

- `primary_overload_source`,
- `last_overload_tick`.

**Option B — narrow the contract**
Keep the schema shape if needed, but remove Milestone 6 language that implies those fields are already part of the verified live visibility surface.

### Acceptance criteria

Milestone 6 is complete only when the overload fields claimed as visible are actually populated and tested, or explicitly downgraded from the claim.

## Task

[x] (checkbox) - [Task 1] - Populate and test the missing overload metadata fields

[Task Description]

This is the clearest false-completion issue in the cognition plan.

[Task technical implementation]

Add presenter serialization, inspection rendering where appropriate, and tests for:

- `primary_overload_source`,
- `last_overload_tick`.

[Task possible affected files]

- `src/api/presenters/ai_presenter.py`
- `src/api/schemas.py`
- `tests/ai/test_intel_capacity_visibility.py`

[Task check list]

- [x] Serialize `primary_overload_source`
- [x] Serialize `last_overload_tick`
- [x] Add API visibility test for both fields
- [x] Add inspector rendering test or document omission

[Task acceptance criteria]

Overload visibility matches the schema contract actually claimed by Milestone 6.

---

## Milestone 7 — Narrow regression claims to actual overlap, then deepen them

### Description

The replay/graph regression path is real.
The current truth-surface overlap is programmatically verified across Replay (JSON), API (Schema), and Cognition Graph (Exporter).

### Technical implementation

The following fields are asserted for exact parity across all surfaces:
- `planning_budget`
- `active_slice_used`
- `is_overloaded`
- `dropped_candidates_count` (mapped to `dropped_candidates` in Graph)
- `primary_overload_source`
- `last_overload_tick`

### Acceptance criteria

Milestone 7 is complete. All surfaces converge on the same set of authoritative cognitive metrics.

## Task

[x] (checkbox) - [Task 1] - Correct the regression claim set to match the actual asserted artifact overlap

[Task Description]

The milestone text currently says more than the current assertions prove.

[Task technical implementation]

Document exactly which cognition fields are:

- written to replay,
- written to graph,
- and asserted for replay-vs-graph consistency.

Then either expand assertions or narrow the claim language.

[Task possible affected files]

- `tests/ai/test_intel_capacity_regression.py`
- `src/testing/assertions.py`
- bounded cognition docs

[Task check list]

- [x] Document current replay/graph overlap fields
- [x] Add more overlap assertions where intentionally exposed
- [x] Remove “fully visible” language if the overlap remains narrow

[Task acceptance criteria]

The document stops overstating the regression proof.

---

## Milestone 8 — Upgrade documentation-integrity proof from symbol existence to end-to-end truth

### Description

The documentation-integrity tests are useful, but they are still weak in one important way: they mostly check schema field existence and source-code mentions, not full end-to-end populated runtime output. That is good maintenance scaffolding, not full documentation verification.

### Technical implementation

Keep the current integrity tests, but add one stronger layer that verifies documented example fields appear in real serialized artifacts under controlled scenarios.

### Acceptance criteria

Milestone 8 is complete only when documentation aligns not just with class definitions and source strings, but also with real populated outputs.

## Task

[x] (checkbox) - [Task 1] - Add end-to-end documentation-integrity tests against populated artifacts

[Task Description]

This closes the gap between “field exists in schema/source” and “field actually appears in runtime artifacts.”

[Task technical implementation]

Add tests that verify documented bounded-cognition fields appear in:

- real API serialization output,
- real replay output,
- real graph export output,

using controlled populated-state fixtures.

[Task possible affected files]

- `tests/ai/test_cognition_integrity.py`
- bounded cognition docs
- replay and presenter fixtures

[Task check list]

- [x] Add populated API artifact doc-alignment test
- [x] Add populated replay artifact doc-alignment test
- [x] Add populated graph artifact doc-alignment test

[Task acceptance criteria]

Documentation integrity means real artifact integrity, not just symbol lookup.
