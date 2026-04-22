# Legacy Checklist Coverage Report

**Generated**: 2026-04-23  
**Scope**: All 5 legacy checklist parts (Parts 1–5), updated through **Phase 9**  
**Engine**: `src_v2` — Strategic & Social Cognition Complete

---

## Executive Summary

| Metric | Value |
| :--- | :--- |
| **Total checklist items** | **602** |
| **Checked ([x])** | **188** |
| **Unchecked ([ ])** | **414** |
| **Overall coverage** | **31.2%** |

> [!NOTE]
> Parts 1–4 cover **RPG-core gameplay logic** (497 items, 35.0% covered).
> Part 5 covers **infrastructure/system compatibility** (105 items, 13.3% covered) — largely out-of-scope for the gameplay engine transition.

---

## Coverage by Checklist Part

| Part | Description | Checked | Total | Coverage | Bar |
| :--- | :--- | ---: | ---: | ---: | :--- |
| Part 1 | RPG-Core Atomic Logic (Section A + B tests) | 75 | 167 | **44.9%** | █████████░░░░░░░░░░░ |
| Part 2 | Strategic / Social / Cognition Tests | 48 | 152 | **31.6%** | ██████░░░░░░░░░░░░░░ |
| Part 3 | Progression / World / Snapshot Tests | 29 | 56 | **51.8%** | ██████████░░░░░░░░░░ |
| Part 4 | Unclassified RPG-Core Tests | 22 | 122 | **18.0%** | ████░░░░░░░░░░░░░░░░ |
| Part 5 | System Compatibility Add-On | 14 | 105 | **13.3%** | ███░░░░░░░░░░░░░░░░░ |
| **TOTAL** | | **188** | **602** | **31.2%** | ██████░░░░░░░░░░░░░░ |

---

## Part 1: Section A — Source Logic Inventory (Subsystem Contracts)

These are the high-level atomic behavior contracts per subsystem.

| Subsystem | Checked | Total | Coverage |
| :--- | ---: | ---: | ---: |
| Authoritative action and update model | 8 | 8 | **100.0%** ✅ |
| Combat / movement / legality / tactics | 13 | 13 | **100.0%** ✅ |
| Resource interaction / inventory / buildings / town loop | 12 | 13 | **92.3%** 🟡 |
| Strategic mind / projects / blockers / leads / cognition | 13 | 13 | **100.0%** ✅ |
| Social / contracts / relationships / reputation | 6 | 8 | **75.0%** 🟡 |
| Progression / classes / skills / attributes / entity growth | 0 | 8 | **0.0%** ❌ |
| World / entities / regions / spawning / determinism | 8 | 8 | **100.0%** ✅ |

### Part 1, Section A Unsupported Items

| Subsystem | Unsupported Item |
| :--- | :--- |
| Resource interaction | Guild visits produce intel, quests, and resource hints |
| Social | Public reputation is distinct from private narrative meaning |
| Social | Party/group cooperation is purpose-driven |
| Progression | All 8 items: attribute ownership, class choice, skill scaling contracts, rewards, item contracts, NPC contracts, specialization, RPG math |

---

## Part 1: Section B — Test-Derived Checklist (Combat/Movement/Resource)

| Test File | ✓ | Total | Cov. | Status |
| :--- | ---: | ---: | ---: | :--- |
| `ai/test_tactical_milestone_4.py` | 4 | 4 | 100% | ✅ |
| `combat/test_combat_context_milestone_2.py` | 4 | 4 | 100% | ✅ |
| `combat/test_combat_movement_rulebook.py` | 8 | 8 | 100% | ✅ |
| `arena/test_arena_harness_contract.py` | 0 | 5 | 0% | ❌ |
| `arena/test_arena_minimal.py` | 0 | 1 | 0% | ❌ |
| `arena/test_arena_watchdog.py` | 0 | 2 | 0% | ❌ |
| `arena/test_core_scenario_regression.py` | 0 | 3 | 0% | ❌ |
| `arena/test_observability_audit.py` | 0 | 2 | 0% | ❌ |
| `arena/test_resource_isolation.py` | 0 | 1 | 0% | ❌ |
| `combat/test_anti_stalemate.py` | 0 | 2 | 0% | ❌ |
| `combat/test_anti_stalemate_milestone_2.py` | 0 | 1 | 0% | ❌ |
| `combat/test_engagement_contract.py` | 0 | 3 | 0% | ❌ |
| `combat/test_opportunity_attacks.py` | 0 | 2 | 0% | ❌ |
| `combat/test_target_stickiness.py` | 0 | 1 | 0% | ❌ |
| `combat/test_world_time_progression.py` | 0 | 2 | 0% | ❌ |
| `engine/test_quiet_tick_integrity.py` | 0 | 4 | 0% | ❌ |
| `integration/ai/test_wind_pillar_navigation.py` | 0 | 3 | 0% | ❌ |
| `test_party_tactics.py` | 0 | 3 | 0% | ❌ |
| `unit/ai/test_skirmish.py` | 0 | 2 | 0% | ❌ |
| `unit/ai/test_tactical_behavior_contract.py` | 0 | 6 | 0% | ❌ |
| `unit/core/logic/test_movement_model.py` | 0 | 3 | 0% | ❌ |
| `integration/gameplay/test_toughness_decay.py` | 0 | 3 | 0% | ❌ |
| `test_building_unification.py` | 0 | 7 | 0% | ❌ |
| `unit/ai/test_routine_cycle.py` | 0 | 3 | 0% | ❌ |
| `unit/ai/test_routine_needs.py` | 0 | 4 | 0% | ❌ |
| `unit/core/gameplay/test_item_contracts.py` | 0 | 3 | 0% | ❌ |
| `unit/systems/test_difficulty_scaling.py` | 0 | 13 | 0% | ❌ |
| `unit/systems/test_toughness_decay.py` | 0 | 2 | 0% | ❌ |

---

## Part 2: Strategic / Social / Cognition Tests

### Fully Covered (Phase 9) ✅

| Test File | Items |
| :--- | :--- |
| `ai/test_bounded_detours.py` | 3/3 |
| `ai/test_bounded_project_continuity.py` | 3/3 |
| `ai/test_lead_learning.py` | 2/2 |
| `ai/test_source_trust_learning_loop.py` | 1/1 |
| `core/test_cognition_graph_exporter.py` | 4/4 |
| `unit/ai/strategy/test_strategic_uncertainty.py` | 2/2 |
| `unit/ai/strategy/test_blocker_resolution.py` | 3/3 |
| `ai/test_betrayal_social_consequence.py` | 1/1 |
| `unit/systems/test_familiarity_scaling.py` | 1/1 |

### Partially Covered 🟡

| Test File | ✓ | Total | Phase 9 Additions |
| :--- | ---: | ---: | :--- |
| `ai/test_event_interpretation.py` | 4 | 6 | +4 (concern gen, interruption resistance) |
| `ai/test_bounded_strategic_slice.py` | 2 | 5 | +2 (concern/lead caps) |
| `integration/strategy/test_strategic_brain_integration.py` | 5 | 6 | +5 (pivot, scar, betrayal, recruitment) |
| `integration/strategy/test_strategic_continuity.py` | 2 | 2 | +2 (directive mutation/strengthening) |
| `integration/strategy/test_strategic_persistence.py` | 3 | 6 | +3 (lock, threat override, resume) |
| `unit/strategy/test_strategic_services.py` | 4 | 8 | +4 (belief decay, concern/directive/project mutation) |
| `ai/test_learning_social.py` | 1 | 2 | +1 (refutation by exhaustion) |
| `ai/test_cognition_capacity_determinism.py` | 1 | 3 | +1 (deterministic profile) |

### Uncovered ❌

| Test File | Items | Notes |
| :--- | ---: | :--- |
| `ai/test_bounded_blockers.py` | 2 | Diagnosis accuracy by wisdom |
| `ai/test_bounded_objective_continuity.py` | 3 | Objective derivation precedence |
| `ai/test_cognition_capacity_non_mutation.py` | 4 | Profile build non-mutation |
| `ai/test_cognition_explainability.py` | 3 | Overload metadata, personality |
| `ai/test_cognition_integrity.py` | 7 | UI contract, spec alignment |
| `ai/test_directive_mutation_thresholds.py` | 1 | Repeated threshold |
| `ai/test_social_cognition.py` | 3 | Social blocker detection |
| `ai/test_uncertainty_resolution_loop.py` | 1 | Zone resolution |
| `core/test_strategy_models.py` | 4 | Pydantic model rebuild |
| `core/test_lived_models.py` | 5 | Phase 3 model instantiation |
| `integration/strategy/*` (6 files) | 18 | Various integration tests |
| `unit/ai/strategy/test_strategic_biasing.py` | 3 | Biological bias, directive flow |
| `unit/systems/test_strategy.py` | 5 | Influence/war/conquest |
| `unit/systems/test_strategy_system.py` | 3 | War/territory systems |
| Social tests (6 files) | 14 | Social meaning, contracts, trading |

---

## Part 3: Progression / World / Snapshot

| Test File | ✓ | Total | Status |
| :--- | ---: | ---: | :--- |
| `unit/core/aspects/test_skill_scaling.py` | 3 | 3 | ✅ (Phase 9) |
| `core/test_snapshot_integrity.py` | 3 | 3 | ✅ |
| `integration/engine/test_determinism.py` | 2 | 2 | ✅ |
| `integration/engine/test_mutation_purity.py` | 1 | 1 | ✅ |
| `unit/core/gameplay/items/test_inventory_resolution.py` | 4 | 4 | ✅ |
| `unit/core/models/test_snapshot_purity.py` | 5 | 5 | ✅ |
| `unit/systems/test_town_service.py` | 3 | 3 | ✅ |
| `unit/core/test_deep_freeze.py` | 2 | 2 | ✅ |
| `unit/systems/test_calamity_evolution.py` | 1 | 1 | ✅ |
| `unit/ai/test_legend_legacy.py` | 2 | 3 | 🟡 |
| `unit/core/aspects/test_progression.py` | 1 | 5 | 🟡 |
| `integration/engine/test_snapshot_safety.py` | 2 | 4 | 🟡 |
| Others (5 files) | 0 | 20 | ❌ |

---

## Part 4: Unclassified RPG-Core Tests

### Fully Covered ✅
`movement/test_congestion_milestone_3.py` (4/4), `unit/ai/test_belief_cycle.py` (3/3, Phase 9), `unit/core/aspects/test_evolution.py` (2/2), `unit/systems/test_evolution.py` (2/2)

### Partially Covered 🟡
`unit/ai/test_narrative_memory.py` (2/4, Phase 9), `unit/systems/test_dynamic_quests.py` (1/2, Phase 9), `unit/combat/test_building_sabotage.py` (1/2), `unit/core/aspects/test_aoa_integrity.py` (3/4), `unit/core/test_performance_optimizations.py` (2/4)

### Uncovered (30 files, 82 items) ❌
Includes: AI pipeline, emotions, personality, flow fields, action styles, combat consequences, exhaustion, serialization, phase 4 models, routine service, recruitment negotiation, etc.

---

## Part 5: System Compatibility

| Section | ✓ | Total | Coverage |
| :--- | ---: | ---: | ---: |
| A: CLI / Headless Runner | 1 | 16 | 6.3% |
| B: Broker disabled-mode | 0 | 10 | 0.0% |
| C: Worker Fallback & Scaling | 3 | 16 | 18.8% |
| D: Chaos & Resilience | 3 | 7 | 42.9% |
| E: Replay Compatibility | 4 | 8 | 50.0% |
| F: Logging | 4 | 12 | 33.3% |
| G: Metrics & Monitoring | 0 | 7 | 0.0% |
| H: API Protocol & Transport | 0 | 11 | 0.0% |
| I: Headless Execution | 0 | 7 | 0.0% |
| J: Unhappy Path | 0 | 10 | 0.0% |
| **TOTAL** | **14** | **105** | **13.3%** |

> [!IMPORTANT]
> Part 5 covers **infrastructure/transport/CLI** compatibility. These items are intentionally **out-of-scope** for the RPG-core gameplay engine transition (Phases 5–9). They represent a future workstream if full CLI/API parity is desired.

---

## Phase 9 Impact Summary

Phase 9 flipped **~45 items** from unchecked to checked across Parts 1–4:

| Area | Items Gained | Key Systems |
| :--- | ---: | :--- |
| Strategic cognition (Part 1 §A + Part 2) | ~25 | Interruption, bandwidth, detour, event interpretation, cognition export |
| Social narrative (Part 1 §A + Part 2) | ~10 | Betrayal, trust, contracts, familiarity, recruitment |
| Belief & knowledge (Part 2 + Part 4) | ~6 | Belief cycle, contradiction, uncertainty |
| Progression (Part 3) | ~4 | Skill scaling, narrative memory, quests |

---

## Coverage Trendline (Phases 5–9)

| Phase | Approximate Coverage | Delta |
| :--- | ---: | ---: |
| Phase 5 (baseline) | ~20% | — |
| Phase 6 | ~22% | +2% |
| Phase 7 | ~24% | +2% |
| Phase 8 | ~27% | +3% |
| **Phase 9** | **31.2%** | **+4.2%** |

---

## Largest Uncovered Areas (Prioritization Guide)

| Area | Unchecked Items | Files | Notes |
| :--- | ---: | ---: | :--- |
| Arena harness & scenarios | 14 | 5 | Arena regression, watchdog, resource isolation |
| Difficulty scaling | 13 | 1 | Tier HP/ATK/gold/boss scaling |
| Combat depth (stalemate, engagement, OA) | 9 | 5 | Anti-stalemate, engagement, opportunity attacks |
| Tactical AI (party, skirmish, behavior) | 11 | 4 | Party roles, kiting, retreat |
| Strategic integration tests | 18 | 6 | Pipeline, transport, world integration |
| Social integration | 14 | 6 | Meaning, trading, milestones, recruitment |
| Routine / biological | 7 | 2 | Sleep, eat, biological decay |
| Building unification | 7 | 1 | Guild/blacksmith/class-hall resolution |
| RPG math / progression | 12 | 4 | Attributes, breakthroughs, gear, class |
| Infrastructure (Part 5) | 91 | — | CLI, brokers, API, logging |
