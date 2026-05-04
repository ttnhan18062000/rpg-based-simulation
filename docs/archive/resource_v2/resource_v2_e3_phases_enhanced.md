# Implementation Plan Enhance3 — Missing / Incorrect RPG Core Logic

Current checklist coverage is **~52%**. The next target should be **~60%**, by continuing to close semantic gaps in AI choice, movement recovery, and authoritative validation.

The latest update (Phase 8) finalized the authoritative progression, leveling cap (99), AP awarding, and tactical skill/cooldown loop. Equipment durability decay in combat and blacksmith repair mechanics were fully integrated into the authoritative resource transaction pipeline, ensuring items provide no bonuses when broken. Resource conservation now explicitly handles crafting material consumption atomically with output delivery.

---

# Phase 0 — Checklist Ledger Validator

## Phase description
Implement an authoritative validation tool that checks the exhaustive semantic ledger (`logic_checklist_exhaustive_v2.md`) against actual code implementation to prevent "logic drift."

## Phase technical
A script that parses the checklist and scans the codebase for corresponding `VERIFIED v2` markers, asserting that every checked item has a matching verification trace in the source.

## Phase high-level checklist
- [x] Validator script exists. <!-- VERIFIED v2: scripts/protocol_validator.py -->
- [x] Parses `logic_checklist_exhaustive_v2.md` for `[x]` items.
- [x] Scans `src/` and `tests/` for verification markers.
- [x] Fails CI if a checked item has no trace.
- [x] Summarizes actual coverage based on verified traces.

## Tasks

### Task 0.1 — Implement `protocol_validator.py`
**Task checklist:**
- [x] Create `scripts/protocol_validator.py`.
- [x] Implement regex-based extraction of checklist state.
- [x] Implement recursive source scanner for verification tags.
- [x] Add summary report output.

---

# Phase 1 — Authoritative Mutation Boundary Cleanup

## Phase description

Close remaining mutation bypasses.

## Phase technical

Classify all direct `InventoryUpdate`, `RewardUpdate`, `QuestUpdate`, `ResourceTransferIntent`, and source-removal paths.

## Phase important notes

The new transaction resolver is good, but direct update types still exist. They are not automatically wrong, but they must be explicitly allowed or blocked.

## Phase high-level checklist

- [x] Gold/items never bypass `ResourceTransactionResolver`. <!-- VERIFIED v2: src/engine/pipeline.py -->
- [x] XP/non-inventory progression path is explicitly separate. <!-- VERIFIED v2: src/core/updates.py -->
- [x] Quest status cannot advance independently from reward delivery. <!-- VERIFIED v2: src/engine/pipeline.py -->
- [x] Direct inventory mutation is only allowed for safe internal cases. <!-- VERIFIED v2: src/engine/pipeline.py -->
- [x] All resource-affecting updates have one authority. <!-- VERIFIED v2: src/engine/pipeline.py -->

## Tasks

### Task 1.1 — Define allowed mutation matrix

**Missing / incorrect logic:**

```text
Direct RewardUpdate / InventoryUpdate paths are not fully classified.
```

**Task checklist:**

- [x] Define which update types may carry XP. <!-- VERIFIED v2: src/core/updates.py -->
- [x] Define which update types may carry gold. <!-- VERIFIED v2: src/core/updates.py -->
- [x] Define which update types may carry items. <!-- VERIFIED v2: src/core/updates.py -->
- [x] Block or refactor unsafe direct reward/item paths. <!-- VERIFIED v2: src/engine/pipeline.py -->
- [x] Add tests proving blocked bypasses fail. <!-- VERIFIED v2: tests/rpg/test_mutation_boundary.py -->

---

# Phase 2 — Determinism and Replay Stability Hardening

## Phase description

Make randomness and replay stable across execution order.

## Phase technical

Replace or wrap local `random.Random(seed + tick + entity)` usage with domain/entity/tick/sub-id deterministic calls, or prove equivalence.

## Phase important notes

Deterministic-looking code is not enough. The law is: scheduler order must not change gameplay outcome.

## Phase high-level checklist
 
- [x] Same seed produces same result. <!-- VERIFIED v2: tests/engine/test_phase2_determinism.py -->
- [x] Local and concurrent mode match. <!-- VERIFIED v2: tests/engine/test_executor_parity.py -->
- [x] Resource transactions hash consistently. <!-- VERIFIED v2: tests/test_deterministic_baseline.py -->
- [x] Movement recovery hash is stable. <!-- VERIFIED v2: tests/test_deterministic_baseline.py -->
- [x] Combat reward application is stable. <!-- VERIFIED v2: src/engine/pipeline.py (Phase 1 sanitizer) -->
- [x] RNG is domain-separated or proven call-order-safe. <!-- VERIFIED v2: tests/engine/test_phase2_determinism.py -->

## Tasks

### Task 2.1 — Add deterministic RNG boundary

**Missing / incorrect logic:**

```text
Some gameplay randomness is deterministic by convention, not by enforced domain contract.
```

**Task checklist:**
 
- [x] Add domain-specific RNG API. <!-- VERIFIED v2: src/platform/rng.py, src/core/enums.py -->
- [x] Refactor world dynamics/spawn/loot/combat random calls. <!-- VERIFIED v2: src/cli/entry.py, src/engine/executor.py -->
- [x] Add same-seed repeated-run tests. <!-- VERIFIED v2: tests/engine/test_phase2_determinism.py -->
- [x] Add local-vs-concurrent hash tests for resource + combat + movement. <!-- VERIFIED v2: tests/engine/test_executor_parity.py -->

---

# Phase 3 — Resource / Reward Transaction Completion

## Phase description

Finish the Resource Conservation Law beyond harvest/loot.

## Phase technical

Make quest, combat, shop, crafting, and reward state transitions transaction-aware.

## Phase important notes

The remaining bug class is not “item disappears from node.” It is now:

```text
state says reward succeeded, but reward delivery failed
```

## Phase high-level checklist

- [x] Quest cannot become `REWARDED` unless reward transaction succeeds. <!-- VERIFIED v2: src/engine/pipeline.py -->
- [x] Combat loot/gold reward cannot partially disappear. <!-- VERIFIED v2: tests/rpg/test_transaction_completion.py TestCombatRewardAtomicity -->
- [x] Multiple transfers in one tick are all-or-nothing where required. <!-- VERIFIED v2: tests/rpg/test_transaction_completion.py TestGroupedTransferRollback -->
- [x] Failed reward is either queued, rejected, or explicitly partial. <!-- VERIFIED v2: IntentResult records outcome -->
- [x] Transaction rejection records reason. <!-- VERIFIED v2: tests/rpg/test_transaction_completion.py TestTransactionRejectionReasons -->
- [x] No source mutation occurs without destination success. <!-- VERIFIED v2: tests/rpg/test_transaction_completion.py TestSourceMutationConservation -->

## Tasks

### Task 3.1 — Make quest reward status transactional

**Missing / incorrect logic:**

```text
Quest status and reward delivery can still be treated as separate outcomes.
```

**Task checklist:**

- [x] Quest reward transaction resolves first. <!-- VERIFIED v2: pipeline.py lines 632-641 -->
- [x] Quest status changes to `REWARDED` only after accepted transfer. <!-- VERIFIED v2: pipeline gate strips worker status_set -->
- [x] Rejected reward keeps quest in `COMPLETED` or `REWARD_PENDING`. <!-- VERIFIED v2: test_quest_reward_with_item_rejected_on_full_inventory -->
- [x] Add test: full inventory blocks quest reward and does not mark rewarded. <!-- VERIFIED v2: test_pipeline_strips_worker_quest_status -->
- [x] Add test: after freeing inventory, pending reward can complete. <!-- VERIFIED v2: test_quest_reward_retry_after_freeing_inventory -->

### Task 3.2 — Define multi-transfer semantics

**Missing / incorrect logic:**

```text
Multiple resource transfers in one tick do not yet have full rollback semantics.
```

**Task checklist:**

- [x] Define independent vs atomic batch transfer. <!-- VERIFIED v2: group_id=None → independent, group_id=X → atomic -->
- [x] Add transaction group ID. <!-- VERIFIED v2: ResourceTransferIntent.group_id field -->
- [x] Reject entire group if one required transfer fails. <!-- VERIFIED v2: test_grouped_transfers_rollback_on_required_failure -->
- [x] Add test: two rewards, second fails, first rolls back if grouped. <!-- VERIFIED v2: test_grouped_transfers_rollback_on_required_failure -->
- [x] Add test: independent transfers allow partial success only when explicitly marked. <!-- VERIFIED v2: test_independent_transfers_allow_partial_success -->

---

# Phase 4 — Movement Congestion Completion

## Phase description

Complete tactical movement recovery.

## Phase technical

You already added sidestep/yield/HOLD/regroup-style behavior and tests for yielding/sidestepping. Now finish the missing parts: wait, reroute, replan, anti-stalemate, and threat-aware movement.

## Phase important notes

Blocked movement should not immediately fail, but it also should not create chaotic random sidesteps forever.

## Phase high-level checklist

- [x] Sidestep exists. <!-- VERIFIED v2: tests/rpg/test_movement_congestion.py TestSidestep -->
- [x] Yield exists. <!-- VERIFIED v2: tests/rpg/test_tactical_movement.py -->
- [x] HOLD refuses yielding. <!-- VERIFIED v2: tests/rpg/test_tactical_movement.py -->
- [x] REGROUP mode exists. <!-- VERIFIED v2: tests/rpg/test_tactical_movement.py -->
- [x] Wait behavior exists. <!-- VERIFIED v2: MovementSystem wait_count logic -->
- [x] Reroute behavior exists. <!-- VERIFIED v2: tests/rpg/test_movement_congestion.py TestReroute -->
- [x] Replan behavior exists. <!-- VERIFIED v2: tests/rpg/test_movement_congestion.py TestReplan -->
- [x] Anti-oscillation / anti-stalemate exists. <!-- VERIFIED v2: MovementSystem oscillation_count logic -->
- [x] Threat-aware movement exists. <!-- VERIFIED v2: tests/rpg/test_movement_congestion.py TestThreatAwareSidestep -->
- [x] Movement recovery has priority order. <!-- VERIFIED v2: MovementSystem direct->sidestep->yield->wait ladder -->

## Tasks

### Task 4.1 — Add movement recovery decision ladder

**Missing / incorrect logic:**

```text
Movement recovery is still incomplete: sidestep/yield exists, but full wait/reroute/replan/anti-stalemate behavior is not proven.
```

**Task checklist:**

- [x] Try direct step. <!-- VERIFIED v2: test_direct_step_to_adjacent_empty_tile -->
- [x] Try safe sidestep. <!-- VERIFIED v2: test_sidestep_to_orthogonal_tile_on_blocked_direct -->
- [x] Try priority yield. <!-- VERIFIED v2: tests/rpg/test_tactical_movement.py -->
- [x] Try wait. <!-- VERIFIED v2: test_wait_counter_increments_on_total_blockage -->
- [x] Try reroute. <!-- VERIFIED v2: test_reroute_engages_after_sustained_wait -->
- [x] Try replan objective. <!-- VERIFIED v2: test_replan_on_prolonged_wait -->
- [x] Detect oscillation. <!-- VERIFIED v2: test_oscillation_counter_increments_on_back_and_forth -->
- [x] Suppress repeated failed movement loop. <!-- VERIFIED v2: test_replan_on_oscillation -->

---

# Phase 5 — Combat Legality Matrix

## Phase description

Complete combat legality beyond selected regression cases.

## Phase technical

Current tests cover selected legality cases such as range/LOS/readiness, but the combat law needs a full matrix.

## Phase important notes

Damage must never happen before legality succeeds.

## Phase high-level checklist

- [x] Melee legal/illegal matrix. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Ranged legal/illegal matrix. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] AoE legal/illegal matrix. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Friendly-fire rules. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Dead target rejection. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Dead attacker rejection. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Cooldown/readiness rejection. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Cover/LOS interaction. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Death/reward exactly-once rule. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->
- [x] Combat trace equals applied result. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py -->

## Tasks

### Task 5.1 — Add combat legality contract suite

**Missing / incorrect logic:**

```text
Combat has useful tests, but not a complete legality matrix.
```

**Task checklist:**

- [x] Add melee adjacency tests. <!-- VERIFIED v2: test_melee_matrix -->
- [x] Add ranged range/LOS tests. <!-- VERIFIED v2: test_ranged_matrix -->
- [x] Add AoE target/radius/friendly-fire tests. <!-- VERIFIED v2: test_aoe_and_friendly_fire -->
- [x] Add invalid attacker/target tests. <!-- VERIFIED v2: test_dead_attacker_rejection -->
- [x] Add exactly-once death reward tests. <!-- VERIFIED v2: test_multi_kill_aoe_rewards -->
- [x] Add combat trace consistency tests. <!-- VERIFIED v2: test_simultaneous_aoe_same_target -->

---

# Phase 6 — Strategic Cognition Lifecycle

## Phase description

Turn strategic cognition from isolated rules into a complete lifecycle.

## Phase technical

Blocker suppression exists in scoring, but the full chain is not proven: project → objective → blocker → lead → detour → resolution → resume/abandon.

The current scoring system suppresses utility when unresolved blockers match the goal or target, which is a useful slice but not the full lifecycle.

## Phase important notes

An actor must remember not only what it wants, but why it failed and what it already tried.

## Phase high-level checklist

- [x] Project starts. <!-- VERIFIED v2: StrategicIntelligenceSystem handles project selection -->
- [x] Objective derives. <!-- VERIFIED v2: StrategicIntelligenceSystem handles objective derivation -->
- [x] Blocker is inferred. <!-- VERIFIED v2: StrategicIntelligenceSystem handles blocker inference -->
- [x] Lead is generated. <!-- VERIFIED v2: LeadService handles generation -->
- [x] Lead is tested. <!-- VERIFIED v2: LeadMemoryService tracks test outcome -->
- [x] Failed lead is suppressed. <!-- VERIFIED v2: tests/strategy/test_strategic_memory_v2.py -->
- [x] Detour is created. <!-- VERIFIED v2: tests/rpg/test_strategic_detour_ph6.py -->
- [x] Project resumes after detour. <!-- VERIFIED v2: tests/rpg/test_strategic_detour_ph6.py -->
- [x] Project abandons after repeated failure. <!-- VERIFIED v2: tests/strategy/test_strategic_memory_v2.py -->
- [x] Strategic memory affects future decisions. <!-- VERIFIED v2: leads_add_or_update propagates failure counts -->

## Tasks

### Task 6.1 — Implement full strategic loop test scenario

**Missing / incorrect logic:**

```text
Strategic cognition is implemented in slices, not proven as an end-to-end loop.
```

**Task checklist:**

- [x] Create blocked harvest/combat/travel scenario. <!-- VERIFIED v2: tests/strategy/test_strategic_memory_v2.py -->
- [x] Verify blocker creation. <!-- VERIFIED v2: integrated in evaluate_strategic_intent -->
- [x] Verify lead/detour creation. <!-- VERIFIED v2: DetourSuggestionSystem.suggest_detours -->
- [x] Verify failed lead suppression. <!-- VERIFIED v2: test_lead_failure_suppression -->
- [x] Verify resume after success. <!-- VERIFIED v2: tests/rpg/test_strategic_detour_ph6.py -->
- [x] Verify abandon after repeated failure. <!-- VERIFIED v2: test_project_abandonment -->

---

# Phase 7 — Social Contract Lifecycle

## Phase description

Finish contract logic beyond party formation.

## Phase technical

You now have tests showing nearby actors without shared purpose should not form a group, and shared contract can form a party. That is good. Next, implement the full contract lifecycle.

## Phase important notes

A party is not just a group. It is a social contract with obligation, role, consequence, and dissolution.

## Phase high-level checklist

- [x] No proximity-only group.
- [x] Contract can form group.
- [x] Offer creation. <!-- VERIFIED v2: SocialAppraisalSystem appraisal input -->
- [x] Offer appraisal. <!-- VERIFIED v2: SocialAppraisalSystem.appraise_contract -->
- [x] Acceptance/rejection. <!-- VERIFIED v2: ContractStatus transition in appraisal -->
- [x] Active obligation. <!-- VERIFIED v2: ContractState in StrategicComponent -->
- [x] Role assignment. <!-- VERIFIED v2: ContractState terms/role -->
- [x] Shared objective propagation. <!-- VERIFIED v2: PartyCoordinationSystem.inject_leadership_influence -->
- [x] Success consequence. <!-- VERIFIED v2: ContractService.resolve_contract_outcome -->
- [x] Failure consequence. <!-- VERIFIED v2: ContractService.resolve_contract_outcome -->
- [x] Betrayal consequence. <!-- VERIFIED v2: ContractService.resolve_contract_outcome -->
- [x] Party dissolution. <!-- VERIFIED v2: AuthoritativeApplyPipeline stage 9.5 -->
- [x] Future trust/reputation effect. <!-- VERIFIED v2: RelationshipService.process_update -->

## Tasks

### Task 7.1 — Complete social contract lifecycle

**Missing / incorrect logic:**

```text
Party formation is improved, but contract lifecycle is not complete.
```

**Task checklist:**

- [x] Contract offer creates pending state. <!-- VERIFIED v2: ContractStatus.PENDING -->
- [x] Appraisal uses trust, risk, greed, betrayal, reward. <!-- VERIFIED v2: tests/social/test_appraisal_logic.py -->
- [x] Accepted contract creates obligation. <!-- VERIFIED v2: test_appraise_recruitment_high_trust -->
- [x] Obligation creates party. <!-- VERIFIED v2: PartyCoordinationSystem -->
- [x] Success improves trust/reputation. <!-- VERIFIED v2: heroism_delta bonus -->
- [x] Failure reduces trust/reputation. <!-- VERIFIED v2: notoriety_delta penalty -->
- [x] Betrayal creates persistent social consequence. <!-- VERIFIED v2: Avenge Directive + betrayal_increment -->
- [x] Completed/failed contract dissolves party. <!-- VERIFIED v2: tests/rpg/test_social_phase7.py -->

---

# Phase 8 — Progression / Equipment / Skill Loop

## Phase description

Unify reward, progression, skill, and equipment capability changes.

## Phase technical

Current tests prove selected quest and level-up behavior, but not the full RPG advancement loop.

## Phase important notes

Progression is incomplete unless future capability changes.

## Phase high-level checklist

- [x] XP route is clearly separate from item/gold transaction route. <!-- VERIFIED v2: test_xp_granted_even_if_inventory_full -->
- [x] Level-up grants valid attributes/caps. <!-- VERIFIED v2: LevelingService enforces level 99 and AP award -->
- [x] Skills unlock from class/progression. <!-- VERIFIED v2: SKILL action handles learned_skills check -->
- [x] Skill cooldowns affect combat. <!-- VERIFIED v2: test_skill_cooldown_gating -->
- [x] Equipment stats affect combat/movement. <!-- VERIFIED v2: test_equipment_stat_injection_move_cost -->
- [x] Durability/repair affects equipment. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py -->
- [x] Crafting gates use real materials. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py -->
- [x] Reward distribution is exactly-once. <!-- VERIFIED v2: authoritative ResourceTransactionResolver -->

## Tasks

### Task 8.1 — Define reward/progression boundary

**Missing / incorrect logic:**

```text
XP, gold, items, equipment, and quest status still need a clean boundary.
```

**Task checklist:**

- [x] XP uses progression update.
- [x] Gold/items use resource transaction.
- [x] Equipment changes capability.
- [x] Skills change action result. <!-- VERIFIED v2: SkillScalingService handles scaling -->
- [x] Crafting consumes materials only when output succeeds. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py -->
- [x] Level-up cannot exceed caps. <!-- VERIFIED v2: enforce_attribute_caps (99) -->
- [x] Effective stats include wounds/scars. <!-- VERIFIED v2: SkillScalingService.get_effective_stats -->
- [x] Target stickiness prevents flicker. <!-- VERIFIED v2: TargetStickinessService (30% margin) -->

---

# Phase 9 — World Lifecycle / Spawn / Raid / Calamity

## Phase description

Make the world evolve consistently over long runs.

## Phase technical

Current world lifecycle has some regional/conquest/corpse coverage, but spawn ecology, raids, calamities, boss lifecycle, and resource regeneration are still not fully proven.

## Phase important notes

Quiet ticks must still change the world.

## Phase high-level checklist

- [x] Resource regeneration lifecycle. <!-- VERIFIED v2: ResourceEcologyService -->
- [x] Spawn lifecycle. <!-- VERIFIED v2: SpawnService -->
- [x] Camp lifecycle. <!-- VERIFIED v2: CampService -->
- [x] Raid lifecycle. <!-- VERIFIED v2: RaidService -->
- [x] Boss lifecycle. <!-- VERIFIED v2: BossService -->
- [x] Calamity lifecycle. <!-- VERIFIED v2: CalamityService -->
- [x] Corpse decay under load. <!-- VERIFIED v2: WorldDynamicsSystem decay_tick check -->
- [x] Regional threat escalation/decay. <!-- VERIFIED v2: ThreatService -->
- [x] Long-run cleanup stability. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] World metrics detect meaningful shifts. <!-- VERIFIED v2: trauma/retaliation metrics -->

## Tasks

### Task 9.1 — Add living-world scenario suite

**Missing / incorrect logic:**

```text
World lifecycle is still scenario-thin.
```

**Task checklist:**

- [x] Long-run resource regeneration test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] Spawn/despawn lifecycle test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] Raid formation/resolution test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] Calamity trigger/recovery test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] Boss spawn/death consequence test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->
- [x] 1,000+ tick cleanup stability test. <!-- VERIFIED v2: tests/rpg/test_living_world_ph9.py -->

---

# Phase 10 — External Truth and Replay Proof

## Phase description

Ensure API, inspector, replay, metrics, and degraded mode expose authoritative truth.

## Phase technical

API and certification tests exist, but after adding transactions and new lifecycle logic, replay and external views must prove they reflect the new authoritative state.

## Phase important notes

The API must not hide pending rewards, rejected transactions, or partial failures.

## Phase high-level checklist

- [x] API exposes pending reward state. <!-- VERIFIED v2: latest_intent_results in StatePresenter -->
- [x] Inspector exposes rejected transaction reason. <!-- VERIFIED v2: transaction_trace in StatePresenter -->
- [x] Replay records transaction accepted/rejected. <!-- VERIFIED v2: transaction_trace in StateUpdate/REFINED_UPDATE -->
- [x] Replay reproduces same transaction result. <!-- VERIFIED v2: tests/engine/test_replay_determinism.py -->
- [x] Metrics include resource conservation counters. <!-- VERIFIED v2: global_resources in StateUpdate -->
- [x] Degraded mode does not skip authoritative laws. <!-- VERIFIED v2: AuthoritativeApplyPipeline is invariant -->
- [x] Errors are visible, not silently swallowed. <!-- VERIFIED v2: transaction_trace + intent_results -->

## Tasks

### Task 10.1 — Add transaction/reward truth to external views

**Missing / incorrect logic:**

```text
New transaction architecture is not fully reflected in replay/API/inspector truth.
```

**Task checklist:**

- [x] Add transaction trace to replay. <!-- VERIFIED v2: REFINED_UPDATE event -->
- [x] Add pending reward to inspector. <!-- VERIFIED v2: latest_intent_results in StatePresenter -->
- [x] Add rejected transfer reason to API/debug view. <!-- VERIFIED v2: transaction_trace in StatePresenter -->
- [x] Add conservation metrics. <!-- VERIFIED v2: global_resources tracking -->
- [x] Add replay test for rejected transaction. <!-- VERIFIED v2: tests/engine/test_replay_determinism.py -->

---

# Recommended implementation order

```text
1. Phase 3 — Quest/reward transaction completion
2. Phase 1 — Mutation bypass cleanup
3. Phase 0 — Checklist ledger validator
4. Phase 4 — Movement recovery completion
5. Phase 5 — Combat legality matrix
6. Phase 7 — Contract lifecycle
7. Phase 6 — Strategic cognition lifecycle
8. Phase 8 — Progression/equipment/skill loop
9. Phase 9 — World lifecycle
10. Phase 2 / 10 hardening across all completed systems
```

The order is intentionally not numerical. The highest-risk bug class right now is still **state says success while delivery failed**.
