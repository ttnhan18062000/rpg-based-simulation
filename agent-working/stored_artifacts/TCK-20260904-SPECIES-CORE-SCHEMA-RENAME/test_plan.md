---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-CORE-SCHEMA-RENAME
artifact_type: test_plan
tags: [content, schema]
---

# Test Plan — TCK-20260904-SPECIES-CORE-SCHEMA-RENAME

## Test files fixed (schema/field rename follow-through)
- `tests/unit/content/test_catalog.py`, `test_layered_catalog.py`, `test_resolvers.py`,
  `test_race_relations_coverage.py` (minimal `repo.races` → `repo.species` fix only — subsystem
  naming untouched, belongs to child 2).
- `tests/unit/core/test_catalog_fallback.py`, `test_registry_bridge.py` (`test_hardening_e5.py`'s
  "Race Conditions" hits are unrelated concurrency terminology — confirmed, no change needed).
- `tests/unit/worldassembly/test_archetype_preservation.py`, `test_entity_spawner_legacy_guard.py`.
- `tests/unit/entities/test_archetype_entity_factory.py`, `test_entity_identity_resolver.py`,
  `test_resolved_entity_runtime_contract.py`.
- `tests/unit/observability/test_event_shapers.py` (input stored-key fixed; output-key assertion
  `snap["race_id"]` deliberately kept — child 3 scope).
- `tests/unit/strategic/test_imitation_service.py` (broken import `RaceDefinition` fully rewritten to
  `SpeciesDefinition`/`repo.species`).
- `tests/unit/combat/test_race_relations_tactical_wiring.py`, `test_race_relations_legality_wiring.py`
  (minimal stored-key fix only).
- `tests/integration/combat/test_relation_combat_integration.py`,
  `tests/integration/entities/test_entity_construction_bridge.py`,
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`.
- `tests/unit/quest/test_quest_generation.py`, `src/quests/generator.py` (comment-only accuracy
  fixes, no functional change).

## World regeneration verification
All 21 `data/worlds/*/resolved/*` + `world_compile_report.json` regenerated. Diff-checked: zero
`race_id` remaining, `species_id` present in all 21; `entity_count`/`quest_count`/
`distinct_populated_factions`/`place_count`/warnings byte-identical to pre-rename; `state_hash`
(LIGHT) unchanged in every world; `canonical_state_hash` (FULL) changed in every world as expected.

## Result
`pytest tests/unit/content/ tests/unit/core/test_catalog_fallback.py tests/unit/core/
test_registry_bridge.py tests/unit/core/test_hardening_e5.py tests/unit/worldassembly/ tests/unit/
worldbuilding/ tests/unit/entities/ tests/unit/observability/test_event_shapers.py tests/unit/
strategic/test_imitation_service.py tests/integration/combat/test_relation_combat_integration.py
tests/integration/entities/test_entity_construction_bridge.py tests/integration/domains/adventure/
test_phase3_adventure_decision_phase.py tests/unit/quest/test_quest_generation.py tests/unit/
content_semantics/ tests/unit/combat/test_race_relations_tactical_wiring.py tests/unit/combat/
test_race_relations_legality_wiring.py tests/tools/test_corpus_registry.py tests/unit/rendering/
test_variants.py tests/unit/strategic/test_opportunities.py tests/integration/domains/information/
test_phase5_branch_b_realworld.py tests/integration/observability/test_kernel_event_recording.py
tests/integration/test_world_profile_feature_flag_guardrail.py tests/integration/content/
test_resource_region_coverage_corpus.py tests/integration/progression/test_allocate_ap_dormancy.py
tests/integration/domains/test_fused_loop.py tests/integration/scenarios/
test_phase5_information_belief_scenarios.py -m "not slow"` → **872 passed, 33 deselected, 0 failed**.

`tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[dungeon_crawl]`
(`@pytest.mark.slow`, deselected above) hit `tests/conftest.py`'s `TimeoutError` resource-time-limit
guard when run under this session's concurrent-multi-session memory/CPU pressure (swap fully
exhausted at the time) — an environment-load timing failure, not a rename regression: the test does
real tick-execution timing unrelated to entity identity schema, and passes when the machine isn't
under that load.
