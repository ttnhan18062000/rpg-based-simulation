---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
artifact_type: test_plan
tags: [cognition, strategy]
---

# Test Plan — TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Regression Surface

**Unit — adventure domain** (`tests/unit/domains/adventure/`):
- `test_abandonment_rate.py`
- `test_craft_upgrade_execution.py`
- `test_depletion_scoring.py`
- `test_hero_quest_scoring.py` (constructs HERO-role entities; scoring.py's own HERO checks are
  out of scope, but eligibility change must not alter its inputs)
- `test_phase3_adventure_decision_boundary.py`
- `test_phase3_adventure_decision_service.py`
- `test_phase3_objective_intent_resolver.py`
- `test_phase3_route_families.py`
- `test_phase3_route_generator.py`
- `test_phase3_route_scoring.py`
- `test_scoring_plan_bonus.py`

**Integration — adventure domain** (`tests/integration/domains/adventure/`):
- `test_harvest_to_event.py`
- `test_phase3_adventure_decision_phase.py` — most directly exercises
  `AdventureDecisionPhase.apply()`'s eligibility filter (`test_filters_out_locked_projects` and
  siblings). Fixtures build entities via bare `V2EntityBuilder` with no `identity.properties`,
  relying on the `role` int defaulting to `0` (HERO) — per investigation.md Risk 1, these fixtures
  will need `properties={"cognition_profile_id": ...}` added (or an equivalent role-default
  fallback in production code) to keep passing under the new check.

**Unit — systems (parity-ledger-linked)** (`tests/unit/systems/`):
- `test_spawn_lock_condition.py` — `STRAT-243`'s own `test_path`
  (`TestLockHeldWhenThreatActive::test_lock_held_when_hp_high_but_hostile_present` and
  `::test_lock_held_when_both_hp_low_and_hostile_present`). Its `_make_hostile` fixture already
  sets `role=EntityRole.MONSTER` explicitly (unaffected by role-check removal), but the *hero*
  fixture in the same file must still resolve as eligible post-fix.

**Unit — strategic cognition** (`tests/unit/strategic/`): full directory — `CapacityService` and
any goal/opportunity tests that construct entities relying on default role/HERO behavior.

**Unit — content / schema** (`tests/unit/content/`):
- `test_catalog.py`, `test_layered_catalog.py` — catalog loading with the new
  `supports_adventure_routing` field.
- `test_resolvers.py::TestLivingDefaultsResolver` — resolves `CognitionProfileDefinition` via
  `LivingDefaultsResolver`; must still pass with the new field present (default `False`, no
  existing assertion enumerates the full field set, so this is expected to be a clean pass, not a
  required edit).
- `test_content_usage_matrix.py` — if this test parses/validates the matrix doc's row structure,
  confirm it doesn't hard-fail on the `living/cognition_profiles` row text changing.

**Observability** (`tests/unit/observability/test_decision_trace.py`) —
`test_adventure_decision_phase_wires_writer` explicitly sets
`hero.identity.role = EntityRole.HERO` on a `MagicMock()`; will not have
`identity.properties["cognition_profile_id"]` set unless the mock is also updated — must be
checked, not assumed to still pass.

**Regression scenario** (`tests/integration/scenarios/test_balance_regression.py`) — flag-gated
economic baseline sentinel (`TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`'s guarding test);
confirm the global `ENABLE_ADVENTURE_ROUTING` default-off sentinel
(`test_adventure_routing_defaults_off`, per that ticket's Test Summary) still passes unchanged —
this ticket does not touch the flag default.

## New Tests Required

1. **`test_eligibility_resolves_via_cognition_profile_not_role`** — Category: unit. Verifies a
   non-HERO-role entity (e.g. `role=EntityRole.CITIZEN` or `GUARD`) whose
   `identity.properties["cognition_profile_id"]` resolves to a profile with
   `supports_adventure_routing=True` (e.g. `practical_humanoid`) IS included in
   `AdventureDecisionPhase.apply()`'s eligible-heroes set. Location:
   `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` (new file) or added to
   `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`.
2. **`test_hero_role_with_ineligible_profile_excluded`** — Category: unit. Verifies a
   `role=EntityRole.HERO` entity whose `cognition_profile_id` resolves to a profile with
   `supports_adventure_routing=False` (`instinctive_animal`) is EXCLUDED — the negative case named
   explicitly in the ticket's own AC ("instinctive_animal-profile entity with role artificially
   set to HERO is NOT included"), proving the axis change holds in both directions, not just
   "non-hero now included."
3. **`test_zero_regression_human_practical_humanoid_hero`** — Category: integration. Fixed
   seed/tick count, `human`/`practical_humanoid`/`hero` scenario (matching the archetype-native
   `adventurer_hero` shape, or the `hero_adventurers`-module-spawned shape per Risk 1 —
   **both** should be covered if the Risk 1 fallback decision affects only one of the two paths)
   produces an identical `StateUpdate`/outcome pre- and post-fix. Location:
   `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`.
4. **`test_cognition_profile_id_missing_does_not_crash`** — Category: unit, direct regression
   guard for investigation.md Risk 1. Entity with `role=EntityRole.HERO` and no
   `cognition_profile_id` key in `identity.properties` (matching the real
   `_spawn_legacy_guard`/`hero_adventurers`-module shape) must resolve to *some* deterministic,
   explicitly-decided outcome (not a `KeyError`/crash) — whatever Plan decides (role-default
   fallback expected to resolve to eligible, matching `hero`'s `default_cognition_profile:
   practical_humanoid`). This is the single highest-value new test given the real-corpus gap found
   in Investigate. Location: `tests/unit/domains/adventure/test_eligibility_cognition_profile.py`.
5. **`test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`** — Category:
   architecture guard / unit. Verifies the catalog lookup used to resolve
   `CognitionProfileDefinition` inside `apply()` is performed via a pre-warmed singleton (matching
   the `behavior_consumers.py` pattern), not a fresh `CatalogRepository(...).load_all()` call per
   hero per tick — e.g. by asserting call count on a mocked/spied accessor stays O(1) or O(unique
   profile IDs) across N heroes in one `apply()` call, directly closing the ticket's own AC bullet
   ("cognition_profile_id resolution is confirmed cheap/cached per-tick"). Location:
   `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` or
   `tests/unit/strategic/` if the new accessor lives closer to `cognition_capacity.py`.
6. **`test_schema_supports_adventure_routing_field`** — Category: unit. `CognitionProfileDefinition`
   accepts `supports_adventure_routing: bool` with default `False`, and all 7 authored profiles in
   `data/content/living/cognition_profiles.yaml` parse with their intended explicit values (no
   profile silently left at the `False` default by omission). Location:
   `tests/unit/content/test_catalog.py` or `test_resolvers.py`.

## Scoped Pytest Commands

```
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -q
pytest tests/unit/systems/test_spawn_lock_condition.py -q
pytest tests/unit/strategic/ -q
pytest tests/unit/content/ -q
pytest tests/unit/observability/test_decision_trace.py -q
pytest tests/integration/scenarios/test_balance_regression.py -q
```

Never: `pytest tests/` (full suite) — scoped to the adventure/strategic-cognition/content domains
actually touched, per project testing rule.

## Anti-Drift Test Guards

- **Scoring untouched**: no test in this ticket's new-tests list should assert on
  `AdventureRouteScorer.score()`'s QUEST_OPPORTUNITY capability-match ratio or the group
  class-synergy 1.10x multiplier (`scoring.py:161,252`) — those stay HERO-role-gated by design;
  a test that accidentally starts asserting eligibility-style behavior there is scope creep into
  the explicitly out-of-scope file.
- **Interruption-bypass untouched**: no test should exercise
  `StrategicIntelligenceSystem.evaluate_project_switch()`'s `"danger"`/`"detour"` bypass logic —
  that is C2's scope (`intelligence.py`), a separate ticket; a shared fixture accidentally pulling
  in that code path would blur the boundary.
- **Flag default untouched**: `test_adventure_routing_defaults_off` (or equivalent sentinel named
  in `TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`'s Test Summary) must still assert
  `ENABLE_ADVENTURE_ROUTING` defaults `OFF` — this ticket changes *who* is eligible once the flag
  is on, never the flag's own default.
- **Non-hero-race expansion is intentional, not a regression**: a test asserting "only HERO-role
  entities are ever routed" would now be *wrong* per Goal 1 — any such pre-existing assertion
  found during Implement should be updated deliberately (with a comment referencing this ticket),
  not treated as a break to silently work around.
- **`cognition_profile_id`-missing path must fail loud or resolve deterministically, never fail
  silent-and-wrong**: guard against an implementation that catches `KeyError`/`AttributeError`
  around the properties lookup and defaults to "eligible" or "ineligible" without that being the
  explicit, documented Plan decision from investigation.md Risk 1.
