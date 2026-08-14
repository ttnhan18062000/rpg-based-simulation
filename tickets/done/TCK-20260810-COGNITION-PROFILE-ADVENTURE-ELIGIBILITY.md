---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
phase: done
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Title
Cognition-driven adventure eligibility replacing hardcoded HERO role gate

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User requested a full fix making adventure-routing eligibility general rather than blindly bound to the HERO role: "generalize is a must-do... you should make it general, then provide maybe configuration to what kind of race/faction to have adventure logics." This ticket replaces the hardcoded `entity.identity.role == EntityRole.HERO` check in `AdventureDecisionPhase.apply()` with a `supports_adventure_routing` flag on `CognitionProfileDefinition`, so any sufficiently cognitively-capable race/faction (elf, human, dwarf, ...) becomes adventure-eligible regardless of role, while instinctive/simple races (wolf, slime, ...) never are, and the existing human/practical_humanoid hero behavior is preserved exactly (zero-regression).

## Scope
- Add `supports_adventure_routing: bool = False` field to `CognitionProfileDefinition` (`src/content/schema.py`)
- Author explicit `supports_adventure_routing` values for all 7 cognition profiles in `data/content/living/cognition_profiles.yaml`, based on real cross-referencing of `disciplined_guard`/`trade_pragmatist` usage in `data/content/social/roles.yaml` and `data/content/entities/entity_archetypes.yaml` — a deliberate evidence-based decision, not a default-False guess
- Replace the hardcoded `entity.identity.role == EntityRole.HERO` check in `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py` line 76) with a check against the entity's resolved `cognition_profile.supports_adventure_routing`
- Verify the `cognition_profile_id` resolution path (`src/content/resolver.py`, `src/entities/archetype_factory.py`) is cheap/cached per-tick, consistent with `phase.py`'s existing "resolve once before loop" pattern, to avoid a per-tick per-hero performance regression
- Add a zero-regression test: human/practical_humanoid hero scenario produces identical outcome pre/post fix for a fixed seed/tick count
- Add a negative-case test: an instinctive_animal-profile entity with role artificially set to HERO is NOT included in adventure routing
- **(Discovered during Verify, not originally planned)** Resolve a real `PARITY_INCOMPLETE` gate hit: `src/content/matrix.py` (edited in Step 11) maps to `docs/parity_ledger/substrate.yaml`/`infrastructure.yaml` via 2 prior, unrelated existing citations (`SUB-373`, `INFRA-328`) — neither of which covers this ticket's own real change (editing an already-hand-registered row's text values, not the auto-discovery mechanism `SUB-373` documents, nor a new-file registration like `INFRA-328`). Resolved by extending `SUB-373`'s `support_boundary` field to document this scope distinction, citing this ticket's own diff as the concrete example — a real, substance-level clarification, not a forced/stretch-fit new entry.

## Out of Scope
- The 2 other `EntityRole.HERO` checks in `src/domains/adventure/scoring.py` (lines 161, 252) that affect QUEST_OPPORTUNITY scoring — a different concern (scoring, not eligibility), explicitly out of scope per design non-goals
- C2's interruption-bypass generalization (`evaluate_project_switch`) in `src/systems/strategic_systems/intelligence.py`
- Documentation updates to `docs/mechanics/04_strategic_cognition.md`, `docs/simulation/domains/adventure_contract.md`, and `docs/parity_ledger/strategic_cognition.yaml` — tracked in sibling ticket TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS (C3), not this ticket
- `docs/audits/D22_dormant_content_wiring.md` — tracked in TCK-20260810-D22-DORMANT-WIRING-AUDIT (C4)

## Acceptance Criteria
- [x] `CognitionProfileDefinition` gains `supports_adventure_routing: bool = False`; all 7 profiles in `data/content/living/cognition_profiles.yaml` get explicit authored values after real cross-referencing of `disciplined_guard`/`trade_pragmatist` usage
- [x] `AdventureDecisionPhase.apply()`'s eligibility filter (`src/domains/adventure/phase.py:76`) no longer references `EntityRole.HERO` — a non-hero entity with `supports_adventure_routing=True` is included, and a HERO-role entity whose profile has `supports_adventure_routing=False` is excluded
- [x] Zero-regression: human/practical_humanoid hero scenario produces identical outcome pre/post fix for a fixed seed/tick count
- [x] Negative case: an instinctive_animal-profile entity with role artificially set to HERO is NOT included — proves "regardless of role" holds in both directions
- [x] `cognition_profile_id` resolution is confirmed cheap/cached per-tick (not a new per-entity catalog lookup cost) consistent with `phase.py`'s existing resolve-once pattern

## Related Tickets
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml
- docs/parity_ledger/substrate.yaml (SUB-373 `support_boundary` extended — see Scope's own
  PARITY_INCOMPLETE-resolution bullet; discovered during Verify, not originally scoped)

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/phase.py
- src/content/schema.py
- data/content/living/cognition_profiles.yaml
- data/content/living/races.yaml
- data/content/social/roles.yaml
- data/content/entities/entity_archetypes.yaml
- src/entities/archetype_factory.py
- src/content/resolver.py
- src/strategy/cognition_capacity.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- disciplined_guard/trade_pragmatist need a deliberate evidence-based `supports_adventure_routing` decision — no test currently targets these two roles
- scoring.py's 2 other HERO checks are explicitly out of scope but share the same file family — real risk of scope creep or reviewer confusion
- the negative-case test (HERO-role instinctive_animal) requires direct test-only entity construction since this combination doesn't occur in real content
- cognition_profile_id resolution must be confirmed cheap/cached, not assumed, before landing

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/plan.md`'s
12 steps, in order:

- **Step 1**: Added `supports_adventure_routing: bool = Field(False)` to
  `CognitionProfileDefinition` (`src/content/schema.py`).
- **Step 2**: Authored `supports_adventure_routing` on all 7 profiles in
  `data/content/living/cognition_profiles.yaml`: `practical_humanoid`,
  `opportunistic_humanoid`, `disciplined_guard`, `trade_pragmatist`, `arcane_scholar` = `true`;
  `instinctive_animal`, `undead_fixated` = `false` — exactly as specified in the plan.
- **Step 3**: Added `get_cognition_profile_definition()` / `get_role_definition()` accessors to
  `src/engine/behavior_consumers.py`, following the existing `get_perception_gate()` /
  `_auto_init()` singleton pattern (no new warmup wiring, no new `_catalog` writer).
- **Step 4**: Added `_resolve_cognition_profile_id()` (3-tier fallback: explicit
  `cognition_profile_id` → `role_id` → `RoleDefinition.default_cognition_profile` → legacy
  `EntityRole.HERO` → `"hero"` role's own default) and `_supports_adventure_routing()`
  (cache-backed eligibility predicate) as module-level functions in
  `src/domains/adventure/phase.py`, exactly as specified in the plan.
- **Step 4a (Ch04 consistency check)**: Read `docs/mechanics/04_strategic_cognition.md` §§1-2
  (Goal Hierarchy & Prioritization, Interruption Resistance) in full before writing Step 5.
  **Confirmation**: neither section documents role- or cognition-profile-based *eligibility for
  a routing subsystem* (they cover goal scoring and interruption resistance, a distinct concern
  from "which entities `AdventureDecisionPhase` evaluates in the first place"), so this ticket's
  new eligibility axis is additive/orthogonal to Ch04's documented laws, not a divergence — no
  conflict found.
- **Step 5**: Replaced the `e.identity.role == EntityRole.HERO` filter in
  `AdventureDecisionPhase.apply()` with `_supports_adventure_routing(e, _profile_eligibility_cache)`
  and updated the method's docstring's eligibility bullet list accordingly.
- **Steps 6-9 (tests)**: Added `test_zero_regression_human_practical_humanoid_hero_archetype_native`
  and `test_zero_regression_human_practical_humanoid_hero_legacy_guard_shape` to
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` (both zero-
  regression shapes, per implementer's choice to keep both in the integration file). Added
  `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` (new file) with
  `test_eligibility_resolves_via_cognition_profile_not_role`,
  `test_hero_role_with_ineligible_profile_excluded`,
  `test_cognition_profile_id_missing_does_not_crash`, and
  `test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`. Added
  `test_schema_supports_adventure_routing_field` to `tests/unit/content/test_resolvers.py`.
- **Step 10**: Ran the full scoped regression suite from `test_plan.md`. All pass except two
  pre-existing failures confirmed unrelated to this change by diffing against an unmodified
  working tree (`test_harvest_to_event.py`'s two full-pipeline event tests, and
  `test_balance_regression.py::test_scoring_formula_constants_stable`) — all three fail
  identically with zero ticket changes applied. Two real, in-scope fixture updates were required
  and made deliberately (see Deviations in plan.md): `test_decision_trace.py`'s
  `test_adventure_decision_phase_wires_writer` mock hero needed a real
  `identity.properties` dict instead of a bare `MagicMock()` (predicted by test_plan.md's own
  Regression Surface section); `test_content_usage_matrix.py`'s
  `test_living_family_marked_resolved_partially_until_runtime_consumer` needed
  `living/cognition_profiles` split out of its "no runtime consumer yet" guard group, per the
  Step 11 deviation below.
- **Step 11**: Discovered `docs/mechanics/content_usage_matrix.md` is generator-backed
  (`tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` regenerates
  it from `src/content/matrix.py`'s `CONTENT_USAGE_MATRIX` on every `tests/unit/content/` run) —
  the plan's own sanctioned fallback for this case. Edited the `living/cognition_profiles` entry
  in `src/content/matrix.py` instead of hand-editing the markdown, then regenerated the `.md` via
  the real generator and reattached its pre-existing frontmatter block (the generator itself
  never emits frontmatter — confirmed pre-existing, unrelated to this ticket). See plan.md
  Deviations for full detail.
- **Step 12**: Replaced `STRAT-243`'s full `text` and `v2_evidence` fields in
  `docs/parity_ledger/strategic_cognition.yaml` per the plan's exact replacement text (both
  sentences), updated `v2_evidence` to cite the final `phase.py` line numbers/helper names, and
  added the two new Step 8 tests to `test_path` alongside the existing lock-gating test
  reference. `status` stays `verified`.
- **Step 12b (unplanned, found at Verify)**: The Parity phase's `cross_reference_touched()` gate
  hard-failed on `src/content/matrix.py` (Step 11's own file) — it maps to
  `docs/parity_ledger/substrate.yaml`/`infrastructure.yaml` via 2 prior, unrelated existing
  citations (`SUB-373`'s auto-discovery mechanism claim, `INFRA-328`'s new-file-registration
  claim), neither of which covers this ticket's real change (a manual text-field edit on an
  already-hand-registered row). Resolved with real substance, not a gate-dodge: extended
  `SUB-373`'s own `support_boundary` field (a schema field designed exactly for this — scoping/
  qualifying an existing claim, not asserting a new one) to state that its auto-discovery claim
  does not cover hand-registered-row maintenance, citing this ticket's own diff as the concrete
  example. Confirmed via `cross_reference_touched()` re-run (all 4 files PASS, ANY-of-candidates
  semantics) and `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index.py`
  (37 passed). User explicitly confirmed this was the correct substance-level fix, not a stretch
  fit, before it was applied.

All deviations from the plan (all pre-authorized by the plan/test_plan's own contingency clauses)
are recorded in `staging_artifacts/TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY/plan.md`'s
new "Deviations" section.

**Known pre-existing gotcha for downstream phases**: `docs/mechanics/content_usage_matrix.md`'s
generator (`generate_matrix_report()`, `src/content/matrix.py`) does not emit the file's YAML
frontmatter block, so every run of `pytest tests/unit/content/` (which includes
`test_generate_and_save_report`) strips it from the working tree again — this is pre-existing
behavior, unrelated to this ticket's own change, and would happen to any ticket touching this
file or merely running this test directory. If Test/Parity/Verify re-run `tests/unit/content/`,
re-check `docs/mechanics/content_usage_matrix.md` for a missing frontmatter block before Finalize
and reattach it (frontmatter block reproduced in this ticket's Files Changed commit) — do not
treat a missing block as a new regression to investigate.

## Test Summary

Scoped regression suite (per `test_plan.md`), all run against the finished code:

- `pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -q` — 69 passed, 2
  failed (`test_harvest_to_event.py`'s two full-pipeline tests — confirmed pre-existing/unrelated
  via `git stash` diff against an unmodified working tree).
- `pytest tests/unit/systems/test_spawn_lock_condition.py -q` — 6 passed.
- `pytest tests/unit/strategic/ -q` — 197 passed.
- `pytest tests/unit/content/ -q` — 233 passed (including the new
  `test_schema_supports_adventure_routing_field` and the updated
  `test_living_family_marked_resolved_partially_until_runtime_consumer`).
- `pytest tests/unit/observability/test_decision_trace.py -q` — 28 passed (including the fixed
  `test_adventure_decision_phase_wires_writer`).
- `pytest tests/integration/scenarios/test_balance_regression.py -q` — 2 passed, 1 failed
  (`test_scoring_formula_constants_stable` — confirmed pre-existing/unrelated), 1 skipped.
- `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index.py -q` — 37 passed
  (STRAT-243 edit integrity).
- `pytest "tests/tools/test_validate_frontmatter.py::TestPreviouslyFrontmatterMissingDocs::test_all_previously_frontmatter_missing_docs_now_pass_validation[docs/mechanics/content_usage_matrix.md]" -q` — 1 passed (frontmatter reattached after regeneration).
- `pytest tests/integration/test_scenario_feature_flag_defaults.py -k adventure_routing -q` — 25
  passed (`ENABLE_ADVENTURE_ROUTING` default-off sentinel untouched).

New tests added: `test_zero_regression_human_practical_humanoid_hero_archetype_native`,
`test_zero_regression_human_practical_humanoid_hero_legacy_guard_shape`,
`test_eligibility_resolves_via_cognition_profile_not_role`,
`test_hero_role_with_ineligible_profile_excluded`,
`test_cognition_profile_id_missing_does_not_crash`,
`test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`,
`test_schema_supports_adventure_routing_field`.

## Files Changed

- `src/content/schema.py` — added `supports_adventure_routing` field.
- `data/content/living/cognition_profiles.yaml` — authored the 7 profile values.
- `src/engine/behavior_consumers.py` — added the two catalog accessors.
- `src/domains/adventure/phase.py` — added the resolution/eligibility helpers, replaced the
  eligibility filter, updated the docstring.
- `src/content/matrix.py` — updated the `living/cognition_profiles` matrix entry (deviation; the
  real generator source for `content_usage_matrix.md`).
- `docs/mechanics/content_usage_matrix.md` — regenerated via the real generator, with the new
  `AdventureDecisionPhase` consumer row.
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-243` full-text correction.
- `docs/parity_ledger/substrate.yaml` — `SUB-373`'s `support_boundary` field extended to scope
  its auto-discovery claim away from hand-registered-row maintenance (unplanned; resolves a real
  `PARITY_INCOMPLETE` gate hit found at Verify — see Implementation Notes Step 12b).
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — 2 new
  zero-regression tests.
- `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` — new file, 4 new tests.
- `tests/unit/content/test_resolvers.py` — 1 new test (`test_schema_supports_adventure_routing_field`).
- `tests/unit/content/test_content_usage_matrix.py` — updated
  `test_living_family_marked_resolved_partially_until_runtime_consumer` (deviation).
- `tests/unit/observability/test_decision_trace.py` — updated
  `test_adventure_decision_phase_wires_writer`'s mock fixture (deviation).

## Completion Summary

Replaced the hardcoded `entity.identity.role == EntityRole.HERO` eligibility gate in
`AdventureDecisionPhase.apply()` with a check against the entity's resolved
`CognitionProfileDefinition.supports_adventure_routing`, resolved via a 3-tier fallback
(explicit `cognition_profile_id` → role default → legacy `EntityRole.HERO` → `"hero"` role
default) that is cached per-`apply()`-call so the catalog is looked up at most once per distinct
profile id per tick, not once per entity. All 7 cognition profiles were authored with explicit,
evidence-based `supports_adventure_routing` values, zero-regression is proven for both real
hero-spawn shapes in the corpus (archetype-native and the `hero_adventurers`-module legacy-guard
shape), and a negative case proves a HERO-role entity with an ineligible profile is correctly
excluded. The content usage matrix and `STRAT-243` parity ledger entry were updated in the same
session to stay factually accurate to the new logic.
