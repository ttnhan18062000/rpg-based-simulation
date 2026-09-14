# Test Plan — TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

## New tests (all assert on the resolved entity's own population_id/behavior, not list length)

- `tests/unit/domains/campaigns/test_campaign_orchestrator.py::test_pending_information_responses_resolves_to_the_intended_campaign_entity`
  — real `frontier_living_world`, the ticket's own worked example.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py::test_pending_self_model_information_events_resolves_to_the_intended_campaign_entity`
  — real `unit_selfmodel_pilot` content, the ticket's other named field.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py::test_pending_information_responses_resolves_against_survivor_roster_in_later_episodes`
  — episode N>0, a fabricated survivor with the target population_id.
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py::test_campaign_built_state_fires_belief_assimilated_for_the_correct_entity`
  — full real-episode `AuthoritativeApplyPipeline.refine()` run proving `InformationBeliefPhase.apply()`
  actually assimilates the fact into the correct entity, the ticket's own explicit Scope bullet.

## Updated test

- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — the old
  `test_build_initial_state_does_not_thread_pending_information_responses_yet` negative assertion
  replaced with a comment pointing to the new positive coverage above (the premise it asserted is
  now resolved, not merely stale).

## Regression

Ran under `.venv313` (CI parity), `-m "not slow and not extra_slow"`:
- `tests/unit/worldbuilding/test_world_compiler.py` (extraction correctness, 8 pre-existing tests
  covering this exact resolution): green, unchanged behavior.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py`: 33 passed (30 pre-existing + 3 new).
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`: 9 passed (8 pre-existing
  + 1 new).
- Broader sweep (`tests/unit/worldbuilding/ tests/unit/domains/campaigns/ tests/unit/worldassembly/
  tests/integration/scenarios/test_phase5_information_belief_scenarios.py
  tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py tests/unit/cognition/
  tests/unit/engine/test_scenario_runtime_service.py tests/unit/engine/test_scenario_checkpointer.py`):
  **673 passed, 1 skipped**.
