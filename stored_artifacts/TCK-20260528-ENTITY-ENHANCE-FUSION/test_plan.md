# Test Plan - Integrating Enhanced Domain Cognitive / World Loop (Phases 1-10)

This document maps out the specific test targets to verify the correct integration of the cognitive and world emergence loop.

## Integration Tests
We will add `tests/integration/domains/test_fused_loop.py` to assert the following:

1. `test_full_pytest_collection_has_no_import_mismatch`
   - Assert that `pytest` can now collect the entire suite cleanly.
2. `test_feature_shadow_mode_preserves_authoritative_hash`
   - Run a 10-tick simulation with enhanced domain mode set to `OFF` and record the final state hash.
   - Run the same seed with enhanced domain mode set to `SHADOW`. Assert that the final state hash is identical.
3. `test_self_model_phase_runs_in_shadow_without_state_mutation`
   - Run in `SHADOW` mode and verify that while `SelfModelUpdatePhase` executes, the entity's live state does not undergo unauthorized mutations.
4. `test_adventure_phase_receives_nonempty_world_opportunities`
   - Verify that the `AdventureDecisionPhase` receives real, nonempty opportunities from the active world providers.
5. `test_resource_provider_uses_state_resource_nodes_and_depletion`
   - Verify that when a resource node is depleted, the `ResourceOpportunityProvider` stops yielding opportunities for it.
6. `test_information_belief_phase_persists_assimilated_knowledge`
   - Create a fact update, run `InformationBeliefPhase`, and verify the fact is readable in `entity.self_model.knowledge` on the next tick.
7. `test_combat_engagement_targets_considered_are_capped`
   - Spawn 100 hostiles, execute `CombatEngagementPhase`, and assert that the number of candidate targets considered per entity is capped (e.g., <= 8) and execution completes well under 5ms.
8. `test_scenario_runner_uses_real_kernel_not_fixed_defer`
   - Execute a scenario through `ScenarioRunner` and verify that the runner executes a real deterministic simulation kernel rather than hardcoded mock deferrals.
