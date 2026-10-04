---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, architecture, engine]
---

# Authoritative Pipeline Phase Inventory

Generated from commit `262d7e57ba18a1ac17b66dffa7b0fa6f62d93e9e` by `tools/perf/phase_inventory.py`.
Regenerate with:

```
python3 tools/perf/phase_inventory.py --format md > docs/performance/phase_inventory.md
python3 tools/perf/phase_inventory.py --format json > docs/performance/phase_inventory.json
python3 tools/perf/phase_inventory.py --check docs/performance/phase_inventory.json
```

Evidence only (PA-05A, `TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT`). This report states
discrepancies; it does not decide which count is right (PERF-D6) and edits no document.
Counts below are measured, not asserted anywhere in a test: `refine()` changes on purpose.

## 1. Executable inventory (`src/engine/pipeline.py::AuthoritativeApplyPipeline.refine`)

- `run_phase()` calls: **44**; distinct literal names: **44**; duplicate names: none
- dynamic-name calls: 0; conditional/loop calls: 0; feature-flagged calls: 12
- direct operations on `update` (not through `run_phase`): 9; direct class-method calls outside `run_phase`: 5

### 1.1 `run_phase()` calls in source order

| # | Phase name | Line | Feature flag | Dispatch | Conditional/loop |
|---|---|---|---|---|---|
| 1 | `trust_boundary` | 135 | - | AuthoritativeApplyPipeline._strip_untrusted_world_effects | no |
| 2 | `actor_validity` | 136 | - | AuthoritativeApplyPipeline._resolve_actor_validity | no |
| 3 | `memory_update` | 154 | ENABLE_MEMORY_UPDATE | MemoryUpdatePhase.apply | no |
| 4 | `habit_bias_action_style` | 169 | ENABLE_HABIT_BIAS_ACTION_STYLE | HabitBiasUpdatePhase.apply | no |
| 5 | `role_model_selection` | 182 | ENABLE_ROLE_MODEL_IMITATION | RoleModelSelectionPhase.apply | no |
| 6 | `self_model` | 192 | ENABLE_SELF_MODEL_COGNITION | SelfModelUpdatePhase.apply | no |
| 7 | `information_belief` | 201 | ENABLE_BELIEF_ASSIMILATION | InformationBeliefPhase.apply | no |
| 8 | `information_intent_execution` | 207 | ENABLE_INFORMATION_INTENT_EXECUTION | InformationIntentExecutionPhase.execute | no |
| 9 | `cooperation` | 217 | ENABLE_SOCIAL_COOPERATION | CooperationPhase.execute | no |
| 10 | `contracts` | 222 | - | AuthoritativeApplyPipeline._resolve_contract_expirations | no |
| 11 | `blacksmith` | 223 | - | BlacksmithSystem.enforce | no |
| 12 | `faction_awareness` | 238 | - | _SU_fa | no |
| 13 | `information_propagation` | 248 | ENABLE_INFORMATION_HUB_ACCUMULATION | _SU_ip | no |
| 14 | `diplomatic_transitions` | 279 | - | _SU_dt | no |
| 15 | `military_conflict` | 289 | - | MilitaryConflictPhase.execute | no |
| 16 | `action_routing` | 297 | - | AuthoritativeApplyPipeline._route_action_intent | no |
| 17 | `position_swaps` | 298 | - | AuthoritativeApplyPipeline._resolve_position_swaps | no |
| 18 | `movement_routing` | 299 | - | AuthoritativeApplyPipeline._route_movement_intent | no |
| 19 | `combat_engagement` | 320 | ENABLE_COMBAT_ENGAGEMENT | CombatEngagementPhase.apply | no |
| 20 | `interaction_routing` | 332 | - | AuthoritativeApplyPipeline._route_interaction_intent | no |
| 21 | `interaction_enforcement` | 333 | - | InteractionSystem.enforce | no |
| 22 | `building_sabotage` | 334 | - | BuildingSabotageSystem.resolve | no |
| 23 | `town_resolution` | 339 | - | TownResolutionSystem.resolve | no |
| 24 | `gold_sink` | 344 | - | GoldSinkSystem.apply | no |
| 25 | `world_dynamics` | 348 | - | WorldDynamicsSystem.resolve_dynamics | no |
| 26 | `world_emergence` | 355 | ENABLE_WORLD_EMERGENCE | WorldEmergencePhase.execute | no |
| 27 | `quest_rewards` | 363 | - | AuthoritativeApplyPipeline._resolve_quest_rewards | no |
| 28 | `guild_visit` | 369 | ENABLE_GUILD_QUEST_GENERATION | GuildVisitPhase.resolve | no |
| 29 | `shop` | 371 | - | ShopSystem.enforce | no |
| 30 | `paid_information` | 375 | - | PaidInformationTransactionSystem.enforce | no |
| 31 | `resource_transactions` | 377 | - | AuthoritativeApplyPipeline._resolve_resource_transactions | no |
| 32 | `evolution` | 381 | - | EvolutionSystem.evaluate | no |
| 33 | `progression_conversion` | 387 | ENABLE_PROGRESSION_EVOLUTION | ProgressionConversionPhase.execute | no |
| 34 | `strategic_intelligence` | 398 | - | StrategicIntelligenceSystem.fused_strategic_pass | no |
| 35 | `belief_staleness_decay` | 408 | - | BeliefCycleSystem.resolve_lead_staleness | no |
| 36 | `lead_contradiction` | 409 | - | AuthoritativeApplyPipeline._enforce_lead_contradiction | no |
| 37 | `near_death_hardening` | 410 | - | AuthoritativeApplyPipeline._apply_near_death_hardening | no |
| 38 | `occupancy_resolution` | 412 | - | AuthoritativeApplyPipeline._resolve_occupancy_conflicts | no |
| 39 | `lifecycle` | 414 | - | LifecycleSystem.resolve_lifecycle | no |
| 40 | `groups` | 416 | - | AuthoritativeApplyPipeline._resolve_groups | no |
| 41 | `clan_lifecycle` | 418 | - | AuthoritativeApplyPipeline._resolve_clan_lifecycle | no |
| 42 | `expired_offers` | 425 | - | ContractService.reap_expired_offers | no |
| 43 | `capacity_enforcement` | 427 | - | CapacityEnforcementPhase.enforce | no |
| 44 | `faction_sentiment` | 441 | - | _SU_fs | no |

### 1.2 Direct operations on `update` that do not go through `run_phase()`

Every assignment to the name `update` inside `refine` whose value contains no `run_phase()` call.
These are a separate counted unit: they transform the update between phases.

| # | Line | Statement | Operation | Conditional/loop |
|---|---|---|---|---|
| 1 | 49 | assign | `replace` | if@L48 |
| 2 | 51 | assign | `replace` | if@L50 |
| 3 | 100 | assign | `replace` | no |
| 4 | 328 | assign | `update.replace` | no |
| 5 | 362 | assign | `update.replace` | no |
| 6 | 380 | assign | `update.replace` | no |
| 7 | 395 | assign | `update.replace` | no |
| 8 | 449 | assign | `update.replace` | no |
| 9 | 452 | assign | `update.replace` | if@L450 |

### 1.3 Direct class-method calls made by `refine()` outside `run_phase()`

Calls of the form `ClassName.method(...)` that sit outside every `run_phase()` call, lambda and
nested function. A structural heuristic: it finds services wired in directly, which a count of
`run_phase()` calls does not see. Not every hit is a phase.

| # | Line | Call | Conditional/loop |
|---|---|---|---|
| 1 | 64 | `OccupancySnapshot.from_state` | if@L63 |
| 2 | 96 | `StateUpdateCompactor.compact_with_metrics` | no |
| 3 | 230 | `FactionDecisionPhase.execute` | no |
| 4 | 439 | `FactionSentimentService.derive_from_bond_updates` | no |
| 5 | 440 | `FactionSentimentService.decay_stale_sentiments` | no |

## 2. Documented sources against the executable phases

| Source | Path | Stated count | Names listed | Executable phases with no entry | Entries matching no executable phase |
|---|---|---|---|---|---|
| authoritative_pipeline_md | `docs/engine/authoritative_pipeline.md` | - | 39 | `habit_bias_action_style`, `role_model_selection`, `information_propagation`, `belief_staleness_decay`, `clan_lifecycle`, `faction_sentiment` | `active_contracts` |
| d19_domain_phase_inventory | `docs/audits/D19_domain_phase_inventory.md` | 38 | 36 | `memory_update`, `habit_bias_action_style`, `role_model_selection`, `information_intent_execution`, `information_propagation`, `guild_visit`, `belief_staleness_decay`, `lead_contradiction`, `clan_lifecycle`, `faction_sentiment` | `adventure_decision`, `active_contracts` |
| codex_generator_note | `tools/agent_orchestration_codex_adapter/generator.py` | - | 0 | n/a (count only) | n/a (count only) |
| subphase_domain_contracts_epic | `docs/plans/design_enhancement/subphase_domain_contracts_epic.md` | - | 0 | n/a (count only) | n/a (count only) |

Notes:

- `authoritative_pipeline_md`: order differs from the executable order for the shared names: no; duplicate entries: none.
- `d19_domain_phase_inventory`: order differs from the executable order for the shared names: no; duplicate entries: none.
- `codex_generator_note`: states a count only; no phase names to compare.
- `subphase_domain_contracts_epic`: states a count only; no phase names to compare.

## 3. Declarations against the executable phases

### 3.1 `PhaseDependencyGraph.PHASES` (31 names)

- In the pipeline but not in the graph: `habit_bias_action_style`, `role_model_selection`, `faction_awareness`, `information_propagation`, `diplomatic_transitions`, `military_conflict`, `gold_sink`, `guild_visit`, `paid_information`, `belief_staleness_decay`, `lead_contradiction`, `clan_lifecycle`, `expired_offers`, `faction_sentiment`
- In the graph but not in the pipeline: `compactor`

### 3.2 `phase_domain_permissions.py`

- Granularity: TickPhase members (kernel phases), not refine() phases
- Keys: `INIT`, `SCHEDULING`, `COLLECTION`, `RESOLUTION`, `CLEANUP`, `ADVANCEMENT`, `PERSISTENCE`
- Pipeline phase names matching a key: none
- keys are kernel TickPhase members, a different counted unit from refine() phase names

