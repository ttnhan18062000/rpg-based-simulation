# Test Coverage Audit: Phase 8 — World Emergence / Population-Level Consequences

This document outlines the test coverage partition for population-level and world emergence feedback mechanics, ensuring Phase 8 tests are high-fidelity, focused on macro-loops, and non-redundant with existing world-dynamics.

## 1. Existing Coverage (Non-Goals for Phase 8 Duplication)

The current test suites in the repository already cover:
- **Regional trauma/stability passive recovery**: Formally ticking down trauma scores or recovering stability values over time.
- **Deterministic spawning**: Spawn systems spawning entities precisely based on region attributes and seed definitions.
- **Camp maturity and spawn**: Formula-driven evolution of camp tier levels and monsters spawned by active camps.
- **Camp clearing reward**: XP and gold dispersal logic upon monster camp destruction.
- **Calamity intensity**: Scaling trauma multipliers or calamity severity based on death clusters.
- **Boss spawn caps**: Preventing excessive bosses or catastrophic threats beyond predefined parameters.
- **Resource node caps**: Ensuring nodes do not duplicate or over-generate yields beyond strict bounds.
- **Long-run stability & population stability**: Multi-thousand tick simulation bounds checking for system drift.

## 2. Phase 8 Test Scope (Macro Feedback Loop)

Phase 8 introduces the missing world-emergence feedback loop, proving that entity actions reshape the world and that reshaped worlds change future entities.

Key partitions:
- **Entity Event Aggregation**: Bounding raw event streams (deaths, depleted resources, raids) into tiny windowed aggregates.
- **Regional & Resource Scarcity Pressures**: Bounding dynamic scarcity and regional danger pressures without raw global mutations.
- **Opportunity & Service Pressures**: Translating environmental pressures into clear demand indicators (blacksmith shortages, guild warnings).
- **Seed Generation**: Producing deterministic, capped quest and rumor seeds to bridge world emergence to information networks.
- **Subjective / Imperfect Signal Exposure**: Guaranteeing that far-away entities remain unaffected while hometown/local entities adapt their risk profiles.
- **Behavior Modification**: Verifying route diversifications, detours, party formations, and active quest selections derived from local exposure.

## 3. Test Cases Audit Matrix

| Test Module / File | Test Category | Target Mechanics Verified |
|:---|:---|:---|
| `test_phase8_world_emergence_boundary.py` | Unit | Immutable boundary execution, deterministic outputs, zero raw live-state mutations |
| `test_phase8_world_event_aggregator.py` | Unit | Windows and bins event streams cleanly, ignores low-salience spams |
| `test_phase8_regional_pressure_model.py` | Unit | Bounded danger/quest pressures from death/failure events |
| `test_phase8_scarcity_model.py` | Unit | Resource scarcity indexing, replenishment decays, spatial isolation |
| `test_phase8_world_opportunity_pressure.py` | Unit | Translating pressures into clear clear-threat or gather opportunities |
| `test_phase8_dynamic_quest_seed_service.py` | Unit | Deterministic quest seeds generated from opportunity pressures |
| `test_phase8_rumor_seed_service.py` | Unit | Lower-certainty, region-scoped information rumor generation |
| `test_phase8_service_state_pressure.py` | Unit | Blacksmith stocks, healers, and guilds responding to scarcity & trauma |
| `test_phase8_world_to_entity_signal_bridge.py` | Unit | Direct observation vs rumor certainty, local spatial filtering vs far-away ignorance |
| `test_phase8_world_emergence_events.py` | Unit | Verification of typed emergence events, reason tracking, trace validity |
| `test_phase8_world_emergence_phase.py` | Integration | Feature flags, cadence gates, state-update merge logic |
| `test_phase8_world_emergence_scenarios.py` | Integration | End-to-end stories (iron scarcity crafting, death danger avoidance, camp clearing reduction, rumor locality) |
| `test_phase8_world_emergence_budget.py` | Performance | Bounded window aggregation, execution time < 5.0ms for 100+ entities and 1000+ events |
