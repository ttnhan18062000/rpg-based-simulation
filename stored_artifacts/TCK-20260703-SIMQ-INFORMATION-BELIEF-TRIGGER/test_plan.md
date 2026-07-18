---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER
artifact_type: test_plan
tags: [simulation-quality, information, belief, cognition, self-model]
---

# Test Plan — TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER

Scope assumed: the recommended fix (compile-time seed of one
`AuthoritativeState.pending_information_responses` entry for `urban_political`, via the same
schema/compiler/resolver plumbing pattern already used for `information_source_profiles`).
No changes to `src/cognition/self_model_phase.py`, `SelfModelUpdatePhase`,
`InformationNeedDetector`, `CognitionDomain.execute_brain()`, or `ENABLE_SELF_MODEL_COGNITION`
are in scope — regression coverage below reflects that boundary.

## Regression Surface (existing tests that must pass)

Branch A logic itself (unchanged by this ticket, must keep passing):
- `tests/unit/domains/information/test_phase5_information_assimilation.py` —
  `InformationAssimilationService.assimilate()` capacity/dedup/merge behavior
- `tests/unit/domains/information/test_phase5_information_response_normalizer.py` —
  `InformationResponseNormalizer.normalize()` answer_kind branching
- `tests/integration/domains/information/test_phase5_information_belief_phase.py` — both Branch
  A and Branch B unit-level phase behavior (`test_phase_routes_query_for_active_unknowns` and
  any Branch A test in this file)
- `tests/integration/domains/test_fused_loop.py` — full-pipeline Branch A assimilation
  (`pending_information_responses` set via `dataclass_replace`, asserts
  `self_model_bundle_set is not None` after `AuthoritativeApplyPipeline.refine()`) — this is the
  closest existing analog to the new compile-time-seeded behavior; must not regress

Compiler/schema/resolver plumbing precedent (pattern being mirrored, must keep passing
unchanged since this ticket does not touch `information_source_profiles` plumbing):
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_seeds_information_source_profiles_from_spec`
- `tests/unit/worldbuilding/test_world_compiler.py::test_compiler_no_information_sources_declared_yields_empty_list`
- `tests/unit/worldbuilding/test_world_compiler.py::test_urban_political_resolved_world_seeds_two_information_sources`
- `tests/unit/worldassembly/test_assembly.py::test_resolver_passes_information_source_profiles_from_composition`
- `tests/unit/worldassembly/test_assembly.py::test_resolver_no_information_source_profiles_declared_yields_empty_list`

Unaffected-but-adjacent (confirm no accidental coupling):
- `tests/unit/domains/information/test_phase5_information_query_router.py`,
  `test_phase5_information_intent_resolver.py`, `test_phase5_information_source_profile.py`
  (Branch B / router path — untouched by this ticket, must show zero behavior change)
- `tests/unit/cognition/test_phase2_self_model_phase.py`,
  `tests/unit/cognition/test_phase2_knowledge_model_service.py` (cognition subsystem — untouched,
  `events=[]` hardcoding is explicitly NOT fixed by this ticket; these tests must show no
  behavior change)
- `tests/simulation_quality/test_information_scorer.py` (InformationScorer — reads emitted
  events, not compile plumbing; should start reflecting non-zero `belief_assimilated` inputs
  once the world content lands, but the scorer's own unit logic must not need code changes)
- `tests/perf/test_phase5_information_belief_budget.py` — perf budget for
  `information_belief` phase; confirm the new seeded entry does not push per-tick cost over
  budget (single static dict, expected negligible)

## New Tests Required (per AC)

1. **Compiler seeds `pending_information_responses` from `WorldSpec`** (mirrors
   `test_compiler_seeds_information_source_profiles_from_spec`): given a `WorldSpec` with a
   `pending_information_responses` entry (subject/query_kind/source_id/raw_response/actor_id),
   `WorldCompiler.compile()` produces `AuthoritativeState.pending_information_responses` with
   that entry present, contents unchanged. Add to `tests/unit/worldbuilding/test_world_compiler.py`.
2. **No-entries-declared yields empty list** (mirrors
   `test_compiler_no_information_sources_declared_yields_empty_list`): absence of the field in
   `WorldSpec` compiles to `state.pending_information_responses == []`. Add to the same file.
3. **`urban_political` resolved world seeds the expected entry** (mirrors
   `test_urban_political_resolved_world_seeds_two_information_sources`): after
   `python -m src.worldbuilding.cli resolve urban_political`, the resolved `WorldSpec` and
   compiled `AuthoritativeState` both carry the one seeded pending response for the chosen actor.
4. **Resolver mirrors composition-level `pending_information_responses`** (mirrors
   `test_resolver_passes_information_source_profiles_from_composition`): a `world.yaml`
   composition declaring a `pending_information_responses` entry round-trips unchanged through
   `WorldAssemblyResolver.assemble()` onto the resolved `WorldSpec`. Add to
   `tests/unit/worldassembly/test_assembly.py`.
5. **No-declaration composition yields empty list through resolver** (mirrors
   `test_resolver_no_information_source_profiles_declared_yields_empty_list`): same file.
6. **End-to-end: `belief_assimilated` calibration hit** — build (or extend) an integration test
   modeled on `test_fused_loop.py:186-200` but sourcing `pending_information_responses` from the
   **compiled `urban_political` state** (not a manually-constructed test state) to prove the
   full compile→pipeline path, not just the hand-wired unit path. Assert
   `event_extractor`'s emitted events for that tick include `belief_assimilated` with the
   expected `subject`. Place under `tests/integration/scenarios/` (mirrors
   `test_phase5_information_belief_scenarios.py`'s existing style) or extend that file directly.
7. **Repeat-fire is safe/idempotent** — run the compiled `urban_political` world for >=2 ticks
   with `ENABLE_BELIEF_ASSIMILATION=ON` and assert no error/exception and no unbounded growth in
   `entity.self_model.knowledge` (facts dict does not grow every tick from the same static
   response — capacity-bounded per `InformationAssimilationService`'s `max_facts=10` /
   `max_unknowns=5`). Documents the accepted repeat-fire behavior noted in the investigation's
   Risks section.
8. **Parity ledger entry test path** — if `INFRA-257` (or whatever id is assigned) requires a
   `test_path` per the parity ledger schema (P0 entries require one; confirm priority chosen),
   point it at test #6 above.

## Scoped Pytest Commands

```bash
# Unit: compiler/schema plumbing
pytest tests/unit/worldbuilding/test_world_compiler.py -v

# Unit: worldassembly resolver plumbing
pytest tests/unit/worldassembly/test_assembly.py -v

# Unit/integration: information domain (Branch A/B, normalizer, assimilation, router — regression)
pytest tests/unit/domains/information/ tests/integration/domains/information/ -v

# Integration: fused loop / cross-phase behavior (Branch A pipeline regression)
pytest tests/integration/domains/test_fused_loop.py -v

# Integration: information belief scenarios (new end-to-end calibration-hit test)
pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -v

# Cognition subsystem — confirm zero behavior change (events=[] intentionally untouched)
pytest tests/unit/cognition/ -v

# Simulation quality scorer — confirm scorer logic unaffected, only inputs change
pytest tests/simulation_quality/test_information_scorer.py -v

# Perf budget sanity check
pytest tests/perf/test_phase5_information_belief_budget.py -v

# Full targeted sweep before calling it done (excludes slow/full-suite runs per project rule)
pytest tests/unit/domains/information tests/unit/worldbuilding tests/unit/worldassembly \
       tests/unit/cognition tests/integration/domains/information \
       tests/integration/domains/test_fused_loop.py \
       tests/integration/scenarios/test_phase5_information_belief_scenarios.py \
       tests/simulation_quality/test_information_scorer.py -v

# Calibration / regression across all worlds (required by AC)
make evaluate --dry-run
```

## Anti-Drift Test Guards

- Any new test touching `SelfModelUpdatePhase`, `KnowledgeModelService`, or
  `CognitionDomain.execute_brain()` is **out of scope** for this ticket and should not appear in
  the diff — if implementation drifts into fixing `events=[]` or wiring
  `InformationNeedDetector`, that is scope creep beyond the resolved UQ-1 recommendation and
  should be flagged back to planning, not silently tested-and-shipped.
- Do not assert on `lead_certainty_updated` or `paid_information_transaction` calibration hits
  as a requirement of this ticket's tests — only `belief_assimilated` is the target event under
  the recommended Branch A path; the AC only requires at least one of the three, and Branch A is
  the chosen one.
- `make evaluate --dry-run` must show **0 regressions across all worlds**, not just
  `urban_political` — even though the recommended fix is compiler/schema/resolver-only, other
  worlds' `WorldSpec`s must still compile with `pending_information_responses` defaulting to
  `[]` (test #2/#5 above cover this directly).
- Do not hand-edit `data/worlds/urban_political/resolved/world.resolved.yaml` to add the test
  fixture content — regenerate via `python -m src.worldbuilding.cli resolve urban_political`
  after editing `data/worlds/urban_political/world.yaml`, per existing precedent enforced by
  `test_urban_political_resolved_world_seeds_two_information_sources`'s equivalent for
  `information_source_profiles`.
- Confirm `grade_anchors.json` (`tests/simulation_quality/fixtures/grade_anchors.json`) is
  updated only after the real calibration run confirms `belief_assimilated calibration_hits > 0`
  — do not hand-edit anchor values speculatively ahead of an actual measured run.
