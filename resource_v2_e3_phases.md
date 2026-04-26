# Implementation Plan Enhance3 — Missing / Incorrect RPG Core Logic

Current checklist coverage is **32.42%**. The next target should be **~45–50%**, but only by closing real RPG laws, not by marking partial logic as complete.

The latest update fixed a major part of resource conservation by introducing `ResourceTransferIntent` / `ResourceTransactionResolver` and tests for full-inventory harvest, loot, corpse, crafting, shop, and quest reward cases. The remaining danger is that some reward/state transitions can still advance separately from successful reward delivery.

---

# Phase 1 — Authoritative Mutation Boundary Cleanup

## Phase description

Close remaining mutation bypasses.

## Phase technical

Classify all direct `InventoryUpdate`, `RewardUpdate`, `QuestUpdate`, `ResourceTransferIntent`, and source-removal paths.

## Phase important notes

The new transaction resolver is good, but direct update types still exist. They are not automatically wrong, but they must be explicitly allowed or blocked.

## Phase high-level checklist

- [ ] Gold/items never bypass `ResourceTransactionResolver`.
- [ ] XP/non-inventory progression path is explicitly separate.
- [ ] Quest status cannot advance independently from reward delivery.
- [ ] Direct inventory mutation is only allowed for safe internal cases.
- [ ] All resource-affecting updates have one authority.

## Tasks

### Task 1.1 — Define allowed mutation matrix

**Missing / incorrect logic:**

```text
Direct RewardUpdate / InventoryUpdate paths are not fully classified.
```

**Task checklist:**

- [ ] Define which update types may carry XP.
- [ ] Define which update types may carry gold.
- [ ] Define which update types may carry items.
- [ ] Block or refactor unsafe direct reward/item paths.
- [ ] Add tests proving blocked bypasses fail.

---

# Phase 2 — Determinism and Replay Stability Hardening

## Phase description

Make randomness and replay stable across execution order.

## Phase technical

Replace or wrap local `random.Random(seed + tick + entity)` usage with domain/entity/tick/sub-id deterministic calls, or prove equivalence.

## Phase important notes

Deterministic-looking code is not enough. The law is: scheduler order must not change gameplay outcome.

## Phase high-level checklist

- [ ] Same seed produces same result.
- [ ] Local and concurrent mode match.
- [ ] Resource transactions hash consistently.
- [ ] Movement recovery hash is stable.
- [ ] Combat reward application is stable.
- [ ] RNG is domain-separated or proven call-order-safe.

## Tasks

### Task 2.1 — Add deterministic RNG boundary

**Missing / incorrect logic:**

```text
Some gameplay randomness is deterministic by convention, not by enforced domain contract.
```

**Task checklist:**

- [ ] Add domain-specific RNG API.
- [ ] Refactor world dynamics/spawn/loot/combat random calls.
- [ ] Add same-seed repeated-run tests.
- [ ] Add local-vs-concurrent hash tests for resource + combat + movement.

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

- [ ] Quest cannot become `REWARDED` unless reward transaction succeeds.
- [ ] Combat loot/gold reward cannot partially disappear.
- [ ] Multiple transfers in one tick are all-or-nothing where required.
- [ ] Failed reward is either queued, rejected, or explicitly partial.
- [ ] Transaction rejection records reason.
- [ ] No source mutation occurs without destination success.

## Tasks

### Task 3.1 — Make quest reward status transactional

**Missing / incorrect logic:**

```text
Quest status and reward delivery can still be treated as separate outcomes.
```

**Task checklist:**

- [ ] Quest reward transaction resolves first.
- [ ] Quest status changes to `REWARDED` only after accepted transfer.
- [ ] Rejected reward keeps quest in `COMPLETED` or `REWARD_PENDING`.
- [ ] Add test: full inventory blocks quest reward and does not mark rewarded.
- [ ] Add test: after freeing inventory, pending reward can complete.

### Task 3.2 — Define multi-transfer semantics

**Missing / incorrect logic:**

```text
Multiple resource transfers in one tick do not yet have full rollback semantics.
```

**Task checklist:**

- [ ] Define independent vs atomic batch transfer.
- [ ] Add transaction group ID.
- [ ] Reject entire group if one required transfer fails.
- [ ] Add test: two rewards, second fails, first rolls back if grouped.
- [ ] Add test: independent transfers allow partial success only when explicitly marked.

---

# Phase 4 — Movement Congestion Completion

## Phase description

Complete tactical movement recovery.

## Phase technical

You already added sidestep/yield/HOLD/regroup-style behavior and tests for yielding/sidestepping. Now finish the missing parts: wait, reroute, replan, anti-stalemate, and threat-aware movement.

## Phase important notes

Blocked movement should not immediately fail, but it also should not create chaotic random sidesteps forever.

## Phase high-level checklist

- [x] Sidestep exists.
- [x] Yield exists.
- [x] HOLD refuses yielding.
- [x] REGROUP mode exists.
- [ ] Wait behavior exists.
- [ ] Reroute behavior exists.
- [ ] Replan behavior exists.
- [ ] Anti-oscillation / anti-stalemate exists.
- [ ] Threat-aware movement exists.
- [ ] Movement recovery has priority order.

## Tasks

### Task 4.1 — Add movement recovery decision ladder

**Missing / incorrect logic:**

```text
Movement recovery is still incomplete: sidestep/yield exists, but full wait/reroute/replan/anti-stalemate behavior is not proven.
```

**Task checklist:**

- [ ] Try direct step.
- [ ] Try safe sidestep.
- [ ] Try priority yield.
- [ ] Try wait.
- [ ] Try reroute.
- [ ] Try replan objective.
- [ ] Detect oscillation.
- [ ] Suppress repeated failed movement loop.

---

# Phase 5 — Combat Legality Matrix

## Phase description

Complete combat legality beyond selected regression cases.

## Phase technical

Current tests cover selected legality cases such as range/LOS/readiness, but the combat law needs a full matrix.

## Phase important notes

Damage must never happen before legality succeeds.

## Phase high-level checklist

- [ ] Melee legal/illegal matrix.
- [ ] Ranged legal/illegal matrix.
- [ ] AoE legal/illegal matrix.
- [ ] Friendly-fire rules.
- [ ] Dead target rejection.
- [ ] Dead attacker rejection.
- [ ] Cooldown/readiness rejection.
- [ ] Cover/LOS interaction.
- [ ] Death/reward exactly-once rule.
- [ ] Combat trace equals applied result.

## Tasks

### Task 5.1 — Add combat legality contract suite

**Missing / incorrect logic:**

```text
Combat has useful tests, but not a complete legality matrix.
```

**Task checklist:**

- [ ] Add melee adjacency tests.
- [ ] Add ranged range/LOS tests.
- [ ] Add AoE target/radius/friendly-fire tests.
- [ ] Add invalid attacker/target tests.
- [ ] Add exactly-once death reward tests.
- [ ] Add combat trace consistency tests.

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

- [ ] Project starts.
- [ ] Objective derives.
- [ ] Blocker is inferred.
- [ ] Lead is generated.
- [ ] Lead is tested.
- [ ] Failed lead is suppressed.
- [ ] Detour is created.
- [ ] Project resumes after detour.
- [ ] Project abandons after repeated failure.
- [ ] Strategic memory affects future decisions.

## Tasks

### Task 6.1 — Implement full strategic loop test scenario

**Missing / incorrect logic:**

```text
Strategic cognition is implemented in slices, not proven as an end-to-end loop.
```

**Task checklist:**

- [ ] Create blocked harvest/combat/travel scenario.
- [ ] Verify blocker creation.
- [ ] Verify lead/detour creation.
- [ ] Verify failed lead suppression.
- [ ] Verify resume after success.
- [ ] Verify abandon after repeated failure.

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
- [ ] Offer creation.
- [ ] Offer appraisal.
- [ ] Acceptance/rejection.
- [ ] Active obligation.
- [ ] Role assignment.
- [ ] Shared objective propagation.
- [ ] Success consequence.
- [ ] Failure consequence.
- [ ] Betrayal consequence.
- [ ] Party dissolution.
- [ ] Future trust/reputation effect.

## Tasks

### Task 7.1 — Complete social contract lifecycle

**Missing / incorrect logic:**

```text
Party formation is improved, but contract lifecycle is not complete.
```

**Task checklist:**

- [ ] Contract offer creates pending state.
- [ ] Appraisal uses trust, risk, greed, betrayal, reward.
- [ ] Accepted contract creates obligation.
- [ ] Obligation creates party.
- [ ] Success improves trust/reputation.
- [ ] Failure reduces trust/reputation.
- [ ] Betrayal creates persistent social consequence.
- [ ] Completed/failed contract dissolves party.

---

# Phase 8 — Progression / Equipment / Skill Loop

## Phase description

Unify reward, progression, skill, and equipment capability changes.

## Phase technical

Current tests prove selected quest and level-up behavior, but not the full RPG advancement loop.

## Phase important notes

Progression is incomplete unless future capability changes.

## Phase high-level checklist

- [ ] XP route is clearly separate from item/gold transaction route.
- [ ] Level-up grants valid attributes/caps.
- [ ] Skills unlock from class/progression.
- [ ] Skill cooldowns affect combat.
- [ ] Equipment stats affect combat/movement.
- [ ] Durability/repair affects equipment.
- [ ] Crafting gates use real materials.
- [ ] Reward distribution is exactly-once.

## Tasks

### Task 8.1 — Define reward/progression boundary

**Missing / incorrect logic:**

```text
XP, gold, items, equipment, and quest status still need a clean boundary.
```

**Task checklist:**

- [ ] XP uses progression update.
- [ ] Gold/items use resource transaction.
- [ ] Equipment changes capability.
- [ ] Skills change action result.
- [ ] Crafting consumes materials only when output succeeds.
- [ ] Level-up cannot exceed caps.

---

# Phase 9 — World Lifecycle / Spawn / Raid / Calamity

## Phase description

Make the world evolve consistently over long runs.

## Phase technical

Current world lifecycle has some regional/conquest/corpse coverage, but spawn ecology, raids, calamities, boss lifecycle, and resource regeneration are still not fully proven.

## Phase important notes

Quiet ticks must still change the world.

## Phase high-level checklist

- [ ] Resource regeneration lifecycle.
- [ ] Spawn lifecycle.
- [ ] Camp lifecycle.
- [ ] Raid lifecycle.
- [ ] Boss lifecycle.
- [ ] Calamity lifecycle.
- [ ] Corpse decay under load.
- [ ] Regional threat escalation/decay.
- [ ] Long-run cleanup stability.
- [ ] World metrics detect meaningful shifts.

## Tasks

### Task 9.1 — Add living-world scenario suite

**Missing / incorrect logic:**

```text
World lifecycle is still scenario-thin.
```

**Task checklist:**

- [ ] Long-run resource regeneration test.
- [ ] Spawn/despawn lifecycle test.
- [ ] Raid formation/resolution test.
- [ ] Calamity trigger/recovery test.
- [ ] Boss spawn/death consequence test.
- [ ] 1,000+ tick cleanup stability test.

---

# Phase 10 — External Truth and Replay Proof

## Phase description

Ensure API, inspector, replay, metrics, and degraded mode expose authoritative truth.

## Phase technical

API and certification tests exist, but after adding transactions and new lifecycle logic, replay and external views must prove they reflect the new authoritative state.

## Phase important notes

The API must not hide pending rewards, rejected transactions, or partial failures.

## Phase high-level checklist

- [ ] API exposes pending reward state.
- [ ] Inspector exposes rejected transaction reason.
- [ ] Replay records transaction accepted/rejected.
- [ ] Replay reproduces same transaction result.
- [ ] Metrics include resource conservation counters.
- [ ] Degraded mode does not skip authoritative laws.
- [ ] Errors are visible, not silently swallowed.

## Tasks

### Task 10.1 — Add transaction/reward truth to external views

**Missing / incorrect logic:**

```text
New transaction architecture is not fully reflected in replay/API/inspector truth.
```

**Task checklist:**

- [ ] Add transaction trace to replay.
- [ ] Add pending reward to inspector.
- [ ] Add rejected transfer reason to API/debug view.
- [ ] Add conservation metrics.
- [ ] Add replay test for rejected transaction.

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
