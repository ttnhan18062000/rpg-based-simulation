---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260831-ROLE-MODEL-IMITATION
phase: done
date: 2026-08-31
tags: [strategy, cognition]
---

# TCK-20260831-ROLE-MODEL-IMITATION

## Title
Learning by Watching & Choosing Role Models

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Learning by Watching & Choosing Role Models. Investigation found the epic's "standalone, no cross-idea dependency" grouping for this idea is wrong — a hard dependency on idea 14 (species classification / intelligence_tier) was discovered during a Milestone-2 cross-cutting trace, because the imitation-sophistication scaling integration point cites intelligence_tier, a field idea 14 hasn't built yet. This idea is independently rated the weakest implementability fit of its ideation batch and needs genuinely new durable per-entity state (who a character watches/admires) — a prior atlas revision wrongly said no new state was needed; that was later corrected.

## Scope
- Do not start this ticket until TCK-20260831-SPECIES-INTELLIGENCE-TIER has landed and merged.
- Add a new typed role-model/imitation state on EntityState (who a character watches/admires) with a defined lifecycle, round-trip tested via serialize/deserialize — not a free-form field.
- Wire imitation-sophistication scaling to read intelligence_tier (landed by TCK-20260831-SPECIES-INTELLIGENCE-TIER) to modulate behavior.
- If this ticket must ship before intelligence_tier work completes for any reason, explicitly stub/defer the scaling with a documented known-limitation rather than silently coupling to a nonexistent field.
- Consider pairing with idea 22 (Relationship Roles, already shipped in M1) to make the role-model relationship visible — a suggested pairing, not a hard dependency.

## Out of Scope
- Any change to idea 14/intelligence_tier's own field definition or race classifications — consumed read-only here.
- Building idea 22's Relationship Roles system — already shipped, only optionally referenced.

## Acceptance Criteria
- [x] This ticket's related_tickets MUST list TCK-20260831-SPECIES-INTELLIGENCE-TIER as a hard prerequisite — do not schedule/start before it lands.
- [x] A new typed role-model/imitation state exists on EntityState with a defined lifecycle (who is watched/admired), not a free-form field, round-trip tested via serialize/deserialize.
- [x] Imitation-sophistication scaling reads intelligence_tier (from the now-landed idea 14 ticket) to modulate behavior.
- [x] If this ticket must ship before intelligence_tier work completes for any reason, the scaling is explicitly stubbed/deferred with a documented known-limitation, never silently coupled to a nonexistent field. (Moot in practice — the dependency was already landed — but the defensive `getattr`/`.get()` fail-safe path is implemented and tested regardless.)

## Related Tickets
- TCK-20260831-SPECIES-INTELLIGENCE-TIER (hard prerequisite — must land first)

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html
- docs/mechanics/04_strategic_cognition.md (new "Role-Model Watching & Imitation Fidelity"
  subsection, added under §4 during Implement)
- docs/parity_ledger/strategic_cognition.yaml (new `STRAT-264` entry, added during Implement)
- docs/architecture/cognition_domain_ownership.md (new `RoleModelBundle` row added during
  Document-Update — this ticket's `CognitionModel.role_model` sub-component was missing from the
  ownership map)

## Related Stored Artifacts
None.

## Related Code Areas
- src/strategy/cognition_capacity.py
- src/core/cognition.py (Scope-confirmed gap: this is where the new role-model/imitation state
  most likely nests — `CognitionModel` and its `MotivationModel`/`RelationshipModel` sub-components
  already live here, imported into `EntityState.cognition` in `src/core/state.py`; the original
  Related Code Areas list omitted this file even though Scope requires new EntityState-reachable
  state)
- src/core/state.py (read/reference only, if the chosen design nests under the existing `cognition`
  field per the precedent below — no `EntityState` field list or `to_canonical_dict()`/`to_readonly()`
  change needed in that case; only touch this file directly if a new top-level `EntityState` field
  is chosen instead of nesting)

## Assumptions / Open Questions
- Rated "the weakest implementability fit of the twelve" in its ideation batch, "medium at best" visible impact.
- This ticket must not be scheduled or started before idea 14 (TCK-20260831-SPECIES-INTELLIGENCE-TIER) lands — hard code-confirmed dependency (zero intelligence_tier concept anywhere in src/strategy/cognition_capacity.py today).
- Dependency confirmed satisfied: TCK-20260831-SPECIES-INTELLIGENCE-TIER is genuinely landed — `tickets/done/TCK-20260831-SPECIES-INTELLIGENCE-TIER.md` exists with all 4 AC checked, a full Completion Summary, `tickets/working_log.csv` row (2026-09-01T10:10:13Z, DONE), and commit `2a62c248` on this branch. Note: its own body `## Status` field still literally reads `INPROGRESS` and frontmatter `status: active`/`phase: open` were never flipped — a stale Finalize-bookkeeping gap shared by at least one other done M2 sibling this session (`ITEM-INSTANCE-HISTORY`; `CLAN-STATE-SCHEMA`/`CREATURE-TERRITORY-LIFECYCLE` sampled clean with `DONE`), not unique to this dependency and not evidence the work itself is incomplete. Non-blocking for this ticket; worth its own hotfix ticket to correct the batch's stale Status fields.
- Recommended (not mandated) implementation shape, found while checking for a collision with the batch's 4 recurring silent-drop instances (`_fast_replace_identity`, PH8 `replace()`, etc.): nest the new role-model/imitation state as a new sub-component under the existing `EntityState.cognition` field (`CognitionModel` in `src/core/cognition.py`, e.g. alongside `MotivationModel`/`RelationshipModel`) rather than adding a new top-level `EntityState` field. `src/engine/apply.py` lines 610-611 already pass `self_model`/`cognition` through generically (`changes.get("cognition", getattr(entity, "cognition", None))`), unlike `IdentityComponent`/`CombatComponent`'s explicit per-field reconstruction (where `territory_maturity`/`readiness_speed` had to be added by hand). Nesting under `cognition` means this ticket would NOT need a 5th silent-drop-pattern fix in `apply.py` at all — a new top-level field would reopen that risk. `SelfModelBundle`'s own docstring records the same reasoning precedent ("grouped ... so EntityState gains exactly one new top-level field instead of four").
- No field-name or schema collision found against the 4 EntityState/AuthoritativeState-touching M2 siblings this session: `CLAN-STATE-SCHEMA` added a standalone `ClanState` class (not an `EntityState` field); `ITEM-INSTANCE-HISTORY` added `item_instances` to `AuthoritativeState` (not `EntityState`); `POPULATION-COHORT-SEEDING` added `population_cohorts` to `RegionState` (not `EntityState`); `CREATURE-TERRITORY-LIFECYCLE` added `territory_maturity` to `IdentityComponent` (a different `EntityState` sub-component than where role-model state should nest). `SPECIES-INTELLIGENCE-TIER` touched only the `RaceDefinition` content schema, never `EntityState`.

## Implementation Notes

Implemented all 9 steps of `staging_artifacts/TCK-20260831-ROLE-MODEL-IMITATION/plan.md` exactly, no deviations:

1. **`RoleModelBundle`** (`src/core/cognition.py`): new frozen dataclass with 4 scalar fields
   (`admired_entity_id`, `admired_since_tick`, `last_reconsidered_tick`, `imitation_fidelity`,
   default `0.5`), nested as the 6th field (`role_model`) on `CognitionModel`. All fields are
   scalars so `to_canonical_dict()` needed no sorted-iteration logic. `SelfModelBundle` was
   deliberately left untouched (confirmed wrong target by investigation.md).
2. Added 2 new schema/determinism tests to `tests/unit/entity/test_phase11_cognition_model_schema.py`
   (`test_entity_state_cognition_has_role_model_subcomponent`,
   `test_role_model_state_canonical_dict_deterministic`); the 2 pre-existing self-model-decision
   regression tests in that file were re-run unmodified and still pass.
   `tests/unit/entity/test_phase2_self_model_components.py` was not touched and all 12 of its
   tests still pass.
3. **`RoleModelImitationService`** (new `src/strategy/role_model_imitation.py`): a deliberately
   separate service from `CapacityService.derive_profile` (fork decision (b) from plan.md — kept
   `CognitionProfile`'s 11 fields free of any content-catalog coupling). Reads
   `entity.identity.properties.get("race_id")` →
   `get_faction_semantics_service().repo.get_race(race_id)` → `RaceDefinition.intelligence_tier`,
   mapping `"high"` → `HIGH_TIER_FIDELITY=1.0`, `"low"`/unresolved → `LOW_TIER_FIDELITY`/
   `DEFAULT_FIDELITY=0.5`. Never raises — missing `race_id`, unresolved race, or missing
   `intelligence_tier` all fall through to the default.
4. New `tests/unit/strategic/test_imitation_service.py` (3 tests): high-vs-low tier scaling using
   an in-memory `CatalogRepository` fixture (no on-disk YAML load — `repo.races` assigned
   directly, mirroring the pattern in `tests/unit/world/test_regional_consequences.py`), the
   fail-safe path for missing race/unresolved race, and a `CognitionProfile` 11-field regression
   guard proving the fork didn't touch it. `tests/unit/strategic/test_cognition_capacity.py` was
   not touched and all 4 of its tests still pass.
5. **`RoleModelSelectionPhase`** (new `src/strategy/role_model_phase.py`): read-through-then-replace
   shape matching `HabitBiasUpdatePhase.apply()` exactly. Uses `SpatialQueryService.nearby_entities`
   (radius=10.0) + `entity.identity.evolution_level` comparison as the selection signal — nearest
   strictly-higher-`evolution_level` neighbor becomes the admired entity, `sorted(nearby_ids)`
   deterministic tie-break. Cadence: `SystemCadence().social_memory` (10 ticks) via `should_run`
   per-entity staggering, no new `SystemCadence` field added. Every cadence tick recomputes fresh
   (no "keep unless a strictly-better candidate exists" carve-out) — an admired entity that leaves
   the world/radius is implicitly cleared to `None` on the next reconsideration.
6. Registered `ENABLE_ROLE_MODEL_IMITATION` (default `FeatureMode.OFF`) in
   `src/domains/optimization/feature_flags.py`, and wired `RoleModelSelectionPhase` into
   `src/engine/pipeline.py`'s `refine()` immediately after the `habit_bias_action_style` block
   (before `self_model`), via the same sequential `run_phase(...)` threading `HabitBiasUpdatePhase`
   uses — never `.merge()` — so it participates in the safe (non-last-write-wins) composition
   path. Not registered in `PhaseDependencyGraph.PHASES`, matching `HabitBiasUpdatePhase`'s own
   precedent of omission.
7. New `tests/unit/strategic/test_role_model_state.py` (3 tests): lifecycle add-then-implicit-clear
   across two calls, cadence-gating (a non-`should_run` tick produces no `entity_updates` entry at
   all), and imitation-fidelity wiring between the phase and the service.
8. Extended `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` with 2 new tests
   (the pre-existing `test_cognition_hierarchy_e2e_smoke` was left unmodified):
   `test_cognition_bundle_set_apply_round_trip_includes_role_model` drives a `CognitionModel` with
   a populated `role_model` through `ApplyPath.apply_generation()` end-to-end and asserts the
   reconstructed entity's `cognition.role_model` matches exactly — concrete proof that
   `apply.py`/`patches.py` needed zero changes (the wholesale `cognition` passthrough at
   `apply.py:611` carries the new sub-field through opaquely). Investigation via a research
   sub-agent confirmed the plan's literal "5 existing sub-component apply-path assertions already
   in this file" description does not match this file's actual pre-existing content (it has one
   smoke test, not five per-sub-component apply-path assertions); the closest real analog pattern
   (`tests/integration/optimization/test_component_patch_apply_parity.py`'s
   `test_self_model_patch_apply_parity_durable_materialization`) was used instead to build a
   correct, real `apply_generation()`-driven round trip. `test_role_model_imitation_flag_defaults_off_and_phase_does_not_run`
   asserts the flag defaults OFF (phase produces no role_model change through the real pipeline)
   and, with the flag explicitly set to `ON`, that the phase does wire through correctly —
   mirroring `test_habit_bias_pipeline_wiring.py`'s own ON/OFF sentinel pattern.
9. Added a new `### Role-Model Watching & Imitation Fidelity (TCK-20260831-ROLE-MODEL-IMITATION)`
   subsection to `docs/mechanics/04_strategic_cognition.md` (inserted as the last subsection of §4,
   immediately before `## 5. Perception & Salience`). Added `STRAT-264` to
   `docs/parity_ledger/strategic_cognition.yaml` via `tools/parity_ledger_writer.py`'s
   schema-validating `write_entry()` (not raw Edit) — the writer also rebuilt
   `tools/parity_index.py`'s derived SQLite index in-process as part of the write. No new
   `docs/guidelines/intentional_divergences.md` entry was added — DEV-002 already covers this case,
   matching the `HABIT-BIAS-WIRING`/`CREATURE-TERRITORY-LIFECYCLE` precedent cited by plan.md.

All Scope Guards from plan.md were honored: `src/engine/apply.py`, `src/engine/patches.py`,
`src/core/updates.py` were not touched (confirmed via `git status`); `CapacityService.derive_profile`'s
signature and `CognitionProfile`'s 11 fields are unchanged; no new `SystemCadence` field was added;
`PhaseDependencyGraph.PHASES` was not touched; idea 22's `RelationshipRole` pairing was not built;
no new `intentional_divergences.md` entry was added.

## Test Summary

New/updated test files, all passing:
- `tests/unit/entity/test_phase11_cognition_model_schema.py` (8 tests, 2 new) — pass
- `tests/unit/strategic/test_imitation_service.py` (3 tests, new file) — pass
- `tests/unit/strategic/test_role_model_state.py` (3 tests, new file) — pass
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` (3 tests, 2 new) — pass

Regression guards confirmed unmodified and still passing:
- `tests/unit/strategic/test_cognition_capacity.py` (4/4 pass)
- `tests/unit/entity/test_phase2_self_model_components.py` (12/12 pass)

Regression sweep run beyond the ticket's own new tests (venv:
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`):
- `pytest tests/unit/entity/ tests/unit/strategic/ -m "not slow"` → 337 passed
- `pytest tests/integration/scenarios/ -m "not slow and not extra_slow"` → 151 passed, 1 skipped
  (one `extra_slow`-marked 24-seed aggregate test, `test_bravery_quartile_combat_rate_2x`, timed
  out under `-m "not slow"` alone due to its own pre-existing compute weight — unrelated to this
  ticket; its per-tick `role_model_selection` phase cost in that run's watchdog telemetry was
  ~0.0015ms, i.e. just the OFF-flag short-circuit check, confirming the new phase adds negligible
  overhead and is not the cause. Re-run excluding `extra_slow` passed cleanly.)
- `pytest tests/integration/domains/emotion/test_habit_bias_pipeline_wiring.py
  tests/integration/domains/memory/ tests/unit/domains/optimization/` → 130 passed (confirms the
  `pipeline.py` insertion did not disturb neighboring phases)

## Files Changed
- `src/core/cognition.py` — added `RoleModelBundle`, nested as `CognitionModel.role_model` (6th field)
- `src/strategy/role_model_imitation.py` (new) — `RoleModelImitationService`
- `src/strategy/role_model_phase.py` (new) — `RoleModelSelectionPhase`
- `src/domains/optimization/feature_flags.py` — added `ENABLE_ROLE_MODEL_IMITATION` (default OFF)
- `src/engine/pipeline.py` — registered `role_model_selection` phase after `habit_bias_action_style`
- `tests/unit/entity/test_phase11_cognition_model_schema.py` — 2 new tests
- `tests/unit/strategic/test_imitation_service.py` (new)
- `tests/unit/strategic/test_role_model_state.py` (new)
- `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` — 2 new tests
- `docs/mechanics/04_strategic_cognition.md` — new subsection
- `docs/parity_ledger/strategic_cognition.yaml` — new entry `STRAT-264` (Implement phase); `v2_evidence`
  extended by Parity phase to also cite `src/engine/pipeline.py`/`src/domains/optimization/feature_flags.py`,
  which turned out to be pre-existing candidate shards in this file with no citation touch this run —
  the same recurring "shared god-file" gap class this batch hit repeatedly (e.g. ticket 9's `state.py`).
- `docs/architecture/cognition_domain_ownership.md` — added a `RoleModelBundle` row (`cognition.role_model`
  → `src/strategy/`) to the CognitionModel sub-component ownership table (Document-Update phase, after
  Implement) — this doc enumerates all `CognitionModel` siblings and was missing the new 6th one.
- `staging_artifacts/TCK-20260831-ROLE-MODEL-IMITATION/investigation.md` (created this run's
  Investigate phase)
- `staging_artifacts/TCK-20260831-ROLE-MODEL-IMITATION/plan.md` (created this run's Plan phase)
- `staging_artifacts/TCK-20260831-ROLE-MODEL-IMITATION/test_plan.md` (created this run's Plan phase)
- `tickets/inprogress/TCK-20260831-ROLE-MODEL-IMITATION.md` (this file)

## Completion Summary

Added a new `RoleModelBundle` sub-component (4 scalar fields: who an entity currently admires,
since when, when last reconsidered, and an imitation-fidelity multiplier) nested under the
existing `EntityState.cognition` field, exactly matching `RelationshipModel`'s precedent — no new
top-level `EntityState` field and zero changes needed to `apply.py`/`patches.py`/`updates.py`
(the round-trip integration test proves this concretely). A new `RoleModelSelectionPhase`
periodically (per-entity staggered `social_memory` 10-tick cadence) scans nearby entities via
`SpatialQueryService.nearby_entities(radius=10.0)` and picks the nearest strictly-higher-
`evolution_level` neighbor as the admired role model, storing an `intelligence_tier`-derived
imitation-fidelity value (via the new, deliberately separate `RoleModelImitationService`)
alongside it. The phase is wired into `AuthoritativeApplyPipeline.refine()` right after
`habit_bias_action_style`, using the same safe sequential-threading (never `.merge()`) pattern,
and ships fully OFF by default behind `ENABLE_ROLE_MODEL_IMITATION` per DEV-002 — confirmed via a
dedicated sentinel test that the phase produces no state change through the real pipeline unless
the flag is explicitly turned on. All 4 acceptance criteria are satisfied; all 9 plan steps landed
with no deviations from `plan.md`.
