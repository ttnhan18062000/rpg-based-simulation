---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-BRANCH-B
artifact_type: test_plan
tags: [simulation-quality, information, cognition, self-model, bug]
---

# Test Plan — TCK-20260703-SIMQ-UPLIFT3-BRANCH-B

## Regression Surface

- `src/cognition/self_model_phase.py` — `SelfModelUpdatePhase.apply()`/`.run()`, the primary
  fix site (`events=[]` hardcoding).
- New durable-state plumbing (per investigation's Finding 3 recommendation): a new
  `WorldSpec`/`WorldCompositionSpec`/`NormalizedWorldComposition` field, `WorldCompiler.compile()`
  seeding logic, `WorldAssemblyResolver.assemble()` passthrough, and a new `AuthoritativeState`
  field — mirrors the exact surface touched by `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`
  (`src/worldbuilding/{schema,compiler}.py`, `src/worldassembly/{schema,resolver}.py`,
  `src/core/state.py`).
- Every entity processed by `SelfModelUpdatePhase.apply()` in every world where
  `ENABLE_SELF_MODEL_COGNITION` could ever be turned on (currently none in shipped profiles, but
  the phase's behavior for ALL alive/active entities changes if `events` is ever non-empty for any
  of them — regression risk is "what happens to entities that do NOT have a seeded event" as much
  as "what happens to the one that does").
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`) — NOT touched by this
  ticket's chosen scope, but its behavior interacts with the fix (Finding 4): any test that turns on
  both `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` together will surface the
  pre-existing update-clobbering defect. This must be tested for and documented, not silently
  passed over.
- `tests/unit/cognition/test_phase2_self_model_phase.py` — existing dirty-check/first-tick/event
  assimilation tests; must continue passing unchanged (the fix should not alter `.run()`'s own
  internal logic, only what `.apply()` passes as `events`).
- All calibration worlds under `data/worlds/` — Scope item 5 explicitly requires a full regression
  sweep since `self_model` is a shared-engine phase, not `urban_political`-scoped code.

## New Tests Required

1. **`SelfModelUpdatePhase.apply()` sources real events from the new field (unit/integration,
   isolated).** Construct an `AuthoritativeState` with one entity whose `entity.id` matches a
   compile-time-seeded event, `feature_flags={"ENABLE_SELF_MODEL_COGNITION": FeatureMode.ON}`,
   `ENABLE_BELIEF_ASSIMILATION` left OFF (isolates Step 1 from Finding 4's clobber). Call
   `AuthoritativeApplyPipeline.refine()` directly (a "direct-pipeline test," not just
   `SelfModelUpdatePhase.run()` called standalone). Assert:
   - `refined.entity_updates[entity_id].self_model_bundle_set.knowledge.unknowns` (or `.facts`,
     depending on the seeded `answer_kind`) is populated and non-empty/non-default.
   - Entities with no seeded event still get a valid `self_model_bundle_set` (no crash, no
     unintended mutation) — confirms the fix does not regress the dirty-check/no-op path for
     unrelated entities.

2. **`self_model.knowledge.unknowns` survives materialization across a tick boundary.** Using the
   same state as (1), call `ApplyPath.apply_generation(state, refined_update, next_tick=...)` and
   assert the *next* tick's `AuthoritativeState.entities[entity_id].self_model.knowledge.unknowns`
   reflects the assimilated event — proving durability, not just an in-flight `EntityUpdate`.

3. **Finding 4 regression/characterization test (required — do not skip even if out of this
   ticket's fix-scope).** With `ENABLE_SELF_MODEL_COGNITION=ON` AND `ENABLE_BELIEF_ASSIMILATION=ON`
   simultaneously (any entity/world), assert and document the *actual* current behavior:
   either (a) `self_model`'s contribution is still clobbered (if Finding 4 is left unfixed by this
   ticket — the test should assert this explicitly, as a known-blocked marker, not silently ignore
   it), or (b) if this ticket's implementation *does* choose to fix `InformationBeliefPhase.apply()`'s
   wiring too, assert that self_model's `self_model_bundle_set` for entities NOT touched by Belief
   survives, and that Branch A/Branch B's own effects also survive alongside it (merge, not
   replace).

4. **Branch B end-to-end reachability (only if Finding 4 is addressed as part of this ticket, or in
   a scoped test that patches around it).** Entity has a seeded Step-1 event (from tick N-1,
   materialized) producing an unresolved `UnknownFact`, no Branch-A pending response for this
   entity, `ENABLE_SELF_MODEL_COGNITION=ON`, `ENABLE_BELIEF_ASSIMILATION=ON`, valid
   `information_source_profiles` that route successfully (e.g. `town_notice_board`-style guide
   profile matching `common_resource_sources`/`regional_danger` scope). Assert
   `InformationBeliefPhase.apply()`'s Branch B fires: `entity_updates[entity_id].intent_results`
   contains a `MOVE_TO`/`ASK_INFORMATION` intent and `property_updates` includes
   `last_routed_query_subject`/`last_routed_query_tick`. If Finding 4 is NOT fixed, this test is
   expected to demonstrate the block (assert it does NOT fire / self_model's write is lost) rather
   than being omitted.

5. **Full calibration regression sweep (Scope item 5).** Run
   `tools/calibrate_simq.py` (or the equivalent direct-pipeline harness) across **all** worlds
   under `data/worlds/` (not just `urban_political`), with `ENABLE_SELF_MODEL_COGNITION` left at its
   shipped default (OFF) in every profile. Assert 0 unintended regressions — i.e. confirm the
   phase-skip path is unchanged for every world where the flag is off (the fix must be provably
   inert when the flag stays off, matching the ticket's Out-of-Scope constraint on not requiring the
   flag anywhere).

6. **Existing unit tests unchanged.** `tests/unit/cognition/test_phase2_self_model_phase.py` (all 5+
   existing tests) must pass unmodified — confirms `.run()`'s internal event-handling logic (already
   correct, per `test_phase2_update_phase_assimilates_info_event`) is untouched; only `.apply()`'s
   event-sourcing changes.

## Scoped Pytest Commands

```bash
# Cognition unit tests (existing + new isolated Step-1 sourcing tests)
pytest tests/unit/cognition/ -v

# Information domain (Branch A/B interaction, unchanged behavior check)
pytest tests/unit/domains/information/ -v

# Worldbuilding/worldassembly (new schema/compiler/resolver plumbing, if Finding 3's template is followed)
pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ -v

# Full-pipeline integration (Branch A/B, fused loop, phase interaction)
pytest tests/integration/domains/test_fused_loop.py -v
pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -v

# Not the entire suite — scope to domains touched, per repo testing rule
pytest tests/unit/cognition/ tests/unit/domains/information/ tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/integration/domains/test_fused_loop.py -v

# Calibration regression sweep across all worlds (Scope item 5)
make evaluate --dry-run   # AC requires this to exit 0
# followed by a real calibration run per world if quality_report.json needs regenerating, e.g.:
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political
python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name dungeon_crawl
# ...repeat for each world under data/worlds/ per Scope item 5's "not just urban_political"
```

## Anti-Drift Test Guards

- Any test exercising Step 1's fix must use
  `src.world.providers.information.InformationResponse` (lowercase `answer_kind`) — never
  `src.domains.information.schema.NormalizedInformationResponse` (uppercase `answer_kind`). Mixing
  these up would silently produce a passing-looking test that validates the wrong contract (see
  investigation Finding 2's type-shape table).
- Any test that turns on `ENABLE_SELF_MODEL_COGNITION` must do so via a **test-local**
  `state.feature_flags` or `state.pressure_signals` override — never by editing a shipped
  `config/simulation_quality/profiles/*.yaml` file. Editing a shipped profile would silently expand
  blast radius to every calibration run using that profile, which is explicitly Out of Scope.
- Any test asserting "Branch B reachable" must also assert on `entity_updates` for at least one
  *other*, unrelated entity in the same tick — this is the only way to catch a regression of
  Finding 4 (the clobbering defect) if it is reintroduced or only partially fixed later. A test that
  only checks the single target entity's outcome would not catch this class of regression.
- Do not regenerate `data/worlds/urban_political/resolved/world.resolved.yaml` by hand if a new
  compile-time seed field is added for Step 1 — always via
  `python -m src.worldbuilding.cli resolve urban_political`, then diff-review the regenerated file.
- The full regression sweep (Scope item 5) must include worlds that do **not** set
  `ENABLE_BELIEF_ASSIMILATION` at all (e.g. `dungeon_crawl`, `sandbox_world`) to confirm the fix is
  inert there too, not just worlds that already exercise `ENABLE_BELIEF_ASSIMILATION`.
- `make evaluate --dry-run` (AC's explicit gate) must be run **after** any new calibration data is
  generated for affected worlds, not against stale `data/calibration/` output — a dry-run against
  pre-fix calibration data would trivially "pass" without exercising the change at all.
