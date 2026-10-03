---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
artifact_type: test_plan
tags: [economy, cognition]
---

# Test Plan — TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Regression Surface

This ticket makes no `src/` changes (it is scope-only and BLOCKED). There is therefore no
behavior-change regression surface to protect. The only meaningful "regression surface" is a
sanity check that the code this ticket's dead-on-arrival claim rests on still behaves exactly as
described in `investigation.md` — i.e. that nothing about `ValuePreferenceProfile` defaults or
`compute_bias_multiplier`'s formula shape has silently drifted since this investigation was written.

Existing tests covering that surface, grouped by category (all must keep passing unmodified,
since this ticket touches none of them):

- **unit**
  - `tests/unit/domains/motivation/test_phase14_bias_service.py` — exercises
    `MotivationBiasService.compute_bias_multiplier` directly, including a non-default
    `ValuePreferenceProfile(values=values)` construction (line 24-28) confirming the delta formula
    shape.
  - `tests/unit/domains/motivation/test_phase14_motivation_models.py` — schema/default tests for
    `ValuePreferenceProfile`/`MotivationModel`.
  - `tests/unit/motivation/test_motivation_bias_culture.py` — cultural overlay branch tests
    (`CulturalBiasApplicator` integration via `compute_bias_multiplier`'s `culture_values` param).
  - `tests/unit/entity/test_phase11_cognition_model_schema.py` — `CognitionModel` schema-level
    tests, covers the `motivation` field's default-factory chain that produces
    `src/core/builder.py:111`'s zero-arg construction path.
  - `tests/unit/domains/culture/test_culture_applicator.py` — `CulturalBiasApplicator` unit tests
    (relevant to `WORLD-CULT-002` parity entry, unaffected by this ticket).

- **integration**
  - `tests/integration/scenarios/test_phase14_motivation_doctrine_scenarios.py` — doctrine + values
    scenario tests with non-default `ValuePreferenceProfile` construction (test-only, confirming
    the ticket's "zero production, test-only" finding).
  - `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` — end-to-end cognition
    hierarchy smoke test, includes a non-default `ValuePreferenceProfile(survival=0.8)` construction
    (test-only).

- **arena-combat**
  - None. This subsystem (`MotivationBiasService`) is not part of the combat-resolution/arena
    surface; no arena-combat tests reference it.

## New Tests Required

None apply to this ticket's own scope. Every Acceptance Criterion in this ticket's `## Acceptance
Criteria` section is a documentation/scoping criterion (ticket created in scoping-only/BLOCKED
state; foundation ticket named as a hard blocking dependency; dead-on-arrival fact stated with
file:line evidence; eventual ACs stated as conditional/deferred; no `src/` changes made) — none of
these are testable by an automated test, since none of them assert runtime behavior. There is
nothing for a new pytest test to verify at this ticket's scope.

The ticket's own **Conditional / Deferred Implementation Acceptance Criteria** section already
specifies what the *future*, unblocked implementation ticket will require, once the foundation
ticket lands:

- A test asserting `MotivationBiasService.compute_bias_multiplier` produces non-zero,
  entity-differentiated deltas for the new `material_ambition` axis using concrete non-default
  entity data (mirroring the existing pattern in
  `tests/unit/domains/motivation/test_phase14_bias_service.py:24-28`) — this is explicitly named in
  the ticket body as a Deferred AC, not something to write now.
- A parity ledger `test_path` entry for whatever `docs/parity_ledger/strategic_cognition.yaml` entry
  the future implementation ticket adds — also deferred.

These deferred items are recorded here for traceability but are explicitly **not** created as part
of this ticket; creating them now would violate this ticket's own "no `src/` changes while BLOCKED"
constraint (a test asserting non-zero deltas for a not-yet-existing field would either fail today or
require adding the field, both out of scope).

## Scoped Pytest Commands

None required for this ticket's own scope — no code changed, nothing to regression-test as a result
of this ticket.

As an optional sanity check only (not required for this ticket's Definition of Done, since no
`src/`/`tests/` files were touched), the existing tests the investigation's dead-on-arrival claim
rests on should already pass unmodified:

```
pytest tests/unit/domains/motivation/test_phase14_bias_service.py \
       tests/unit/motivation/test_motivation_bias_culture.py \
       tests/unit/domains/motivation/test_phase14_motivation_models.py \
       -v
```

Never `pytest tests/` (unscoped) for this ticket — there is no changed domain to scope to.

## Anti-Drift Test Guards

- If a future session is tempted to "just quickly" add a test asserting non-zero
  `material_ambition` deltas under this ticket, that is a scope violation: this ticket is BLOCKED
  and explicitly forbids `src/` changes; a test for a field that doesn't exist yet either fails or
  requires adding the field first — either outcome belongs to the deferred foundation/implementation
  tickets, not this one.
- If a future session touches `src/core/cognition.py` or `src/domains/motivation/service.py` under
  this ticket ID, that is itself the signal this ticket's own AC ("No src/ changes are made under
  this ticket while blocked") was violated — no test is needed to catch this; it's a direct
  Definition-of-Done violation to flag at Verify.
- `tests/unit/domains/culture/test_culture_applicator.py` and the `WORLD-CULT-002` parity entry
  guard the *adjacent* transient cultural-overlay system (`CulturalBiasApplicator`) staying
  non-durable — if a future foundation/implementation ticket for `MotivationModel.values`
  accidentally starts writing culture data into durable `ValuePreferenceProfile` state instead of
  keeping the overlay transient, this existing test/parity-entry pair is what would catch that
  regression. Not exercised by this ticket, but worth naming as the guard that already exists for
  the adjacent system this ticket's design sketch must not blur into.
