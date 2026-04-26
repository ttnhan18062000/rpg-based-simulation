# RPG Core Missing Logic Implementation Plan

This plan implements the remaining RPG-core logic as semantic laws, not line-by-line legacy code.

Completion rule:

- Do not mark partial logic as complete.
- Do not mark logic complete if any active path bypasses the same law.
- Enhanced logic is acceptable if the RPG behavior is preserved or improved.
- Intentional divergence must be documented and tested.

---

# Phase 0 — Proof Governance and Completion Control

## Phase description

Create the control layer that defines when RPG logic is truly complete.

## Phase technical

Implement a machine-readable ledger that maps every checklist item to status, implementation evidence, test evidence, proof type, and divergence/enhancement note.
This is achieved by synchronizing `logic_checklist_exhaustive.md` with the YAML files in `docs/parity_ledger/` via a new verification tool.

## Phase important notes

Do this first. Without this phase, the project will keep producing false-green checklist items.

## Phase high-level checklist

- [x] Every RPG logic item has a stable ID.
- [x] Every completed item has implementation evidence.
- [x] Every completed item has test evidence.
- [x] Enhanced/divergent behavior is explicitly documented.
- [x] Partial implementation is blocked from being marked complete.
- [x] CI fails when a checked item has no proof.

## Tasks

### Task 0.1 — Build RPG Logic Ledger

**Task description:**
Create the proof system for all remaining RPG-core logic.

**Task technical:**
Add ledger validation script (`tools/parity/verify_checklist.py`), stable ID mapping in the markdown checklist, and automated CI-ready validation of proof evidence.

**Task checklist:**

- [x] Ledger exists.
- [x] Ledger validates statuses.
- [x] Missing proof fails validation.
- [x] Divergence without explanation fails validation.
- [x] Partial implementation cannot be marked complete.

---

# Phase 1 — Authoritative Mutation Pipeline

## Phase description

Ensure all gameplay mutation flows through one authoritative path.

## Phase technical

Implement or harden the intent-to-update-to-application pipeline in `src/engine/apply.py` and `src/engine/pipeline.py`. Ensure all systems (Combat, Interaction, Strategic) emit typed `StateUpdate` objects.

## Phase important notes

No AI, system, interaction, combat, or world lifecycle logic should directly mutate authoritative state outside the approved application path.

## Phase high-level checklist

- [x] AI produces intent, not direct mutation.
- [x] Systems produce typed updates, not direct mutation.
- [x] ApplyPath is the single mutation authority.
- [x] Invalid actions produce rejection results.
- [x] Partial rejection does not corrupt unrelated state.
- [x] No active gameplay bypass path exists.

## Tasks

### Task 1.1 — Harden Authoritative Mutation Boundary

**Task description:**
Make authoritative application the only trusted state mutation path.

**Task technical:**
Route action, interaction, combat, resource, progression, and world updates through a single validated application layer.

**Task checklist:**

- [x] All gameplay side effects use typed updates.
- [x] Direct world mutation is blocked or removed.
- [x] Rejection results are explicit.
- [x] Active bypasses are tested and prevented.

---

# Phase 2 — Determinism and Replay Stability

## Phase description

Guarantee stable simulation results under the same seed and scenario.

## Phase technical

Implement deterministic randomness and replay fingerprints that are stable across local and concurrent execution.

## Phase important notes

The exact legacy RNG API is not required. The RPG law is deterministic behavior, especially under concurrency.

## Phase high-level checklist

- [x] Same seed produces same result.
- [x] Different seed produces different valid result.
- [x] Local and concurrent modes produce equivalent results.
- [x] Replay reproduces authoritative outcomes.
- [x] Gameplay randomness is not scheduler-order dependent.
- [x] Canonical state hashing is stable.

## Tasks

### Task 2.1 — Implement Deterministic Execution Proof

**Task description:**
Prove that simulation output is stable across execution modes.

**Task technical:**
Add call-order-safe RNG strategy, state hashing, replay comparison, and local-vs-concurrent tests.

**Task checklist:**

- [x] Same-seed repeat test passes.
- [x] Local-vs-concurrent test passes.
- [x] Replay hash test passes.
- [x] RNG usage is isolated from global random.

---

# Phase 3 — Resource, Inventory, and Interaction Conservation

## Phase description

Prevent item loss, duplication, and invalid resource transformation.

## Phase technical

Make all resource transfer logic atomic and capacity-aware. Update `InventoryService` to handle atomic operations and ensure `HarvestSystem` and `LootSystem` verify capacity before source depletion.

## Phase important notes

This phase is incomplete if one path works but another active path bypasses capacity or conservation rules.

## Phase high-level checklist

- [x] Item cannot disappear unless inventory accepts it.
- [x] Resource charge cannot be consumed unless reward is received.
- [x] Corpse loot cannot vanish when inventory is full.
- [x] Ground item cannot be removed when pickup fails.
- [x] Crafting cannot consume materials unless output succeeds.
- [x] Shop buy/sell is atomic.
- [x] Quest/combat rewards obey inventory and state constraints.

## Tasks

### Task 3.1 — Unify Resource Transfer Laws

**Task description:**
Make harvest, loot, pickup, crafting, shop, and reward paths obey the same conservation law.

**Task technical:**
Apply capacity checks before removal/depletion and make transfer operations atomic. Implement a `ResourceConservationService` to unify these checks across all systems.

**Task checklist:**

- [x] Harvest capacity law implemented.
- [x] Loot capacity law implemented.
- [x] Ground pickup capacity law implemented.
- [x] Crafting consume/produce law implemented.
- [x] Shop transaction law implemented.
- [x] Reward distribution law implemented.

---

# Phase 4 — Movement and Spatial Behavior

## Phase description

Make movement believable, tactical, and occupancy-safe.

## Phase technical

Implement blocked-movement alternatives and spatial consistency. Define semantic movement modes in `src/core/movement_modes.py` and implement mode-aware resolution in `src/engine/movement.py`.

## Phase important notes

A blocked tile should not immediately mean failed movement. The actor should attempt reasonable tactical alternatives before final rejection.

## Phase high-level checklist

- [x] Occupied tiles are not silently overlapped.
- [x] Pathfinding avoids occupied tiles when appropriate.
- [x] Targeting occupied tiles remains possible when tactically valid.
- [x] Blocked movement can wait.
- [x] Blocked movement can yield.
- [x] Blocked movement can sidestep.
- [x] Blocked movement can reroute.
- [x] Blocked movement can replan.
- [x] Regroup movement exists.
- [x] Anti-stalemate movement exists.
- [x] Spatial index updates remain authoritative.

## Tasks

### Task 4.1 — Implement Tactical Movement Recovery

**Task description:**
Add movement recovery behavior before final movement rejection.

**Task technical:**
Implement movement intention handling, congestion recovery, spatial validation, and anti-stalemate rules. Add support for yielding to higher-priority entities and sidestepping.

**Task checklist:**

- [x] Pursue behavior works.
- [x] Retreat behavior works.
- [x] Hold behavior works.
- [x] Reposition behavior works.
- [x] Intercept behavior works.
- [x] Guard behavior works.
- [x] Regroup behavior works.
- [x] Congestion recovery works.

---

# Phase 5 — Combat and Tactical Legality

## Phase description

Ensure combat actions are legal, explainable, and authoritative.

## Phase technical

Implement complete combat legality and consequence application.

## Phase important notes

Damage must never happen before legality is proven.

## Phase high-level checklist

- [x] Melee legality is enforced.
- [x] Ranged legality is enforced.
- [x] AoE legality is enforced.
- [x] Line-of-sight legality is enforced.
- [x] Cooldown/readiness legality is enforced.
- [x] Target validity is enforced.
- [x] Damage calculation is explainable.
- [x] Critical/evasion/defense rules are stable.
- [x] Death consequences are authoritative.
- [x] Combat rewards are authoritative.
- [x] Combat trace matches actual applied result.

## Tasks

### Task 5.1 — Complete Combat Law Enforcement

**Task description:**
Make every combat result pass legality, resolution, and consequence rules.

**Task technical:**
Harden legality service, combat resolver, ApplyPath combat application, and combat trace output.

**Task checklist:**

- [x] Illegal melee causes no damage.
- [x] Illegal ranged attack causes no damage.
- [x] Illegal AoE causes no splash damage.
- [x] Dead/invalid targets are rejected.
- [x] Death/reward consequences are applied once.
- [x] Combat trace is truthful.

---

# Phase 6 — Strategic Cognition

## Phase description

Make actors pursue durable goals instead of only reacting tick-by-tick.

## Phase technical

Implement project, objective, blocker, lead, detour, and strategic learning loops.

## Phase important notes

The actor must remember what it is doing, why it is stuck, and what it already tried.

## Phase high-level checklist

- [x] Strategic state persists across ticks.
- [x] Projects have lifecycle rules.
- [x] Objectives derive from projects.
- [x] Blockers derive from objectives/state.
- [x] Leads guide uncertainty resolution.
- [x] Failed/tested leads are suppressed.
- [x] Detours are bounded by cognition capacity.
- [x] Project interruption uses margin/resistance logic.
- [x] Actors can resume suspended work.
- [ ] Actors can abandon work when cost is too high.
- [ ] Strategic learning affects future decisions.

## Tasks

### Task 6.1 — Complete Durable Goal Loop

**Task description:**
Implement the full goal-to-blocker-to-detour-to-resolution loop.

**Task technical:**
Harden strategic state, objective derivation, blocker inference, lead testing, interruption, and learning services.

**Task checklist:**

- [x] Start project works.
- [x] Derive objective works.
- [x] Detect blocker works.
- [x] Suggest detour works.
- [x] Test lead works.
- [x] Suppress failed lead works.
- [x] Resume project works.
- [ ] Abandon project works.

---

# Phase 7 — Social, Contracts, Reputation, and Party Cooperation

## Phase description

Make social history affect future gameplay decisions.

## Phase technical

Implement persistent social memory, contract consequences, reputation effects, and purpose-driven group formation.

## Phase important notes

Party formation must not be proximity-only. Proximity can help, but shared purpose must be the reason.

## Phase high-level checklist

- [x] Private trust affects decisions.
- [x] Public reputation affects decisions.
- [x] Betrayal affects future recruitment.
- [x] Social bonds persist.
- [x] Contracts create obligations.
- [x] Broken contracts create consequences.
- [x] Honored contracts create consequences.
- [x] Recruitment evaluates trust, greed, debt, trauma, and capability fit.
- [x] Party formation is purpose-driven.
- [x] Party leader/follower roles exist.
- [x] Shared objective propagation works.
- [x] Party dissolution works.

## Tasks

### Task 7.1 — Implement Purposeful Social Cooperation

**Task description:**
Make cooperation depend on social state, contracts, obligations, and shared objectives.

**Task technical:**
Harden social memory, contract lifecycle, recruitment logic, and group formation rules.

**Task checklist:**

- [x] Betrayal memory affects decisions.
- [x] Contract consequence affects future behavior.
- [x] Reputation and private trust are distinct.
- [x] Group forms from shared purpose.
- [x] Group does not form from proximity alone.
- [x] Group dissolves when purpose ends.

---

# Phase 8 — Progression, Skills, Equipment, and Rewards

## Phase description

Make RPG growth coherent and bounded.

## Phase technical

Implement progression loops that connect rewards to future capability.

## Phase important notes

Progression is not just stat storage. It must affect future combat, movement, strategy, crafting, and survival.

## Phase high-level checklist

- [x] XP gain works.
- [x] Level-up works.
- [x] Attribute point allocation works.
- [x] Attribute caps are enforced.
- [x] Aptitude modifiers work.
- [x] Class progression works.
- [x] Skill unlocks work.
- [x] Skill cooldowns work.
- [x] Skill effects affect gameplay.
- [x] Equipment stats affect gameplay.
- [x] Durability/repair works.
- [x] Crafting gates work.
- [x] Loot tables work.
- [x] Rewards are distributed once.

## Tasks

### Task 8.1 — Complete Advancement Loop

**Task description:**
Connect rewards, progression, skills, equipment, and future capability.

**Task technical:**
Harden XP, level, attributes, skills, gear, durability, crafting, loot tables, and reward application.

**Task checklist:**

- [x] Reward creates progression.
- [x] Progression changes capability.
- [x] Skills change action outcomes.
- [x] Equipment changes action outcomes.
- [x] Caps/gates prevent invalid growth.

---

# Phase 9 — World Lifecycle, Spawning, Raids, and Calamity

## Phase description

Make the world evolve through consistent rules over time.

## Phase technical

Implement passive tick consequences, spawning, resource regeneration, threat escalation, raids, and large-scale events.

## Phase important notes

Quiet ticks still matter. The world should not freeze when actors do not perform dramatic actions.

## Phase high-level checklist

- [x] Passive biological updates work.
- [x] Passive resource updates work.
- [x] Resource regeneration works.
- [x] Spawn rules are deterministic.
- [x] Camp behavior works.
- [x] Raid lifecycle works.
- [x] Boss/calamity lifecycle works.
- [x] Regional threat changes over time.
- [x] Town/world consequences persist.
- [x] Dead entity cleanup works.
- [x] Corpse decay works.
- [x] Long-run stability is tested.

## Tasks

### Task 9.1 — Implement Living World Loop

**Task description:**
Make the world change through passive and event-driven rules.

**Task technical:**
Harden world tick lifecycle, spawn systems, resource systems, regional threat, raids, calamities, and cleanup.

**Task checklist:**

- [x] Quiet tick consequences work.
- [x] Resource lifecycle works.
- [x] Spawn lifecycle works.
- [x] Raid lifecycle works.
- [x] Calamity lifecycle works.
- [x] Cleanup lifecycle works.

---

# Phase 10 — API, Inspector, Replay, and Degraded-Mode Truth

## Phase description

Ensure external systems expose authoritative truth without creating alternate gameplay truth.

## Phase technical

Make API, inspector, replay, debug traces, and degraded-mode behavior read from authoritative state.

## Phase important notes

API and inspector must never become parallel gameplay systems.

## Phase high-level checklist

- [x] API state matches authoritative state.
- [x] Inspector state matches authoritative state.
- [x] Replay records authoritative outcomes.
- [x] Replay load reproduces authoritative outcomes.
- [x] Debug traces are truthful.
- [x] Broker-disabled mode is safe.
- [x] Missing infrastructure degrades safely.
- [x] No-op behavior is explicit and safe.
- [x] Errors are visible, not silent.

## Tasks

### Task 10.1 — Expose Authoritative Truth

**Task description:**
Make every external view reflect the engine’s actual state.

**Task technical:**
Harden API serialization, inspector views, replay records, debug traces, degraded-mode paths, and error reporting.

**Task checklist:**

- [x] API truth verified.
- [x] Inspector truth verified.
- [x] Replay truth verified.
- [x] Degraded mode verified.
- [x] Safe no-op behavior verified.

---

# Implementation Order

```text
Phase 0  -> Proof governance
Phase 1  -> Authoritative mutation
Phase 2  -> Determinism
Phase 3  -> Resource conservation
Phase 4  -> Movement
Phase 5  -> Combat
Phase 6  -> Strategy
Phase 7  -> Social/contracts/groups
Phase 8  -> Progression
Phase 9  -> World lifecycle
Phase 10 -> External truth
```

---

# Phase 11 — Reconciliation and Cutover

## Phase description

Close the implementation-to-ratification boundary and formally declare the V2 engine authoritative.

## Phase technical

Perform a final audit of all RPG laws (Z1-Z16), implement missing spatial indexing (Z13), and synchronize the exhaustive checklist with machine-readable ledgers.

## Phase important notes

This is the final phase of the V2 engine recovery.

## Phase high-level checklist

- [x] All items in `logic_checklist_exhaustive.md` have stable IDs.
- [x] All checked items are backed by ledger evidence.
- [x] Spatial Index (Z13) is implemented and integrated.
- [x] Final verification tool passes with 0 errors.
- [x] Operational cutover documentation is complete.

## Tasks

### Task 11.1 — Governance Ledger Implementation

**Task checklist:**

- [x] All ledger IDs are unique.
- [x] All checklist items map to ledger IDs.
- [x] Evidence exists for all verified items.

### Task 11.2 — Spatial Index Hardening (Z13)

**Task checklist:**

- [x] `SpatialIndexV2` implemented.
- [x] Point query optimized to O(1).
- [x] Radius query optimized to O(K).
- [x] Integrated into `LegalityServiceV2`.

### Task 11.3 — Final Audit and Cutover

**Task checklist:**

- [x] `verify_checklist.py` passes.
- [x] `README.md` updated.
- [x] Project declared V2 authoritative.
 
---
 
# Phase 12 — Operational Hardening
 
## Phase description
 
Harden the V2 engine against remaining edge cases and parity violations identified during cutover.
 
## Phase technical
 
Implement strict resource conservation (Phase 3 restoration), resolve quest identity paradoxes, and ensure 100% logic parity with the legacy source of truth.
 
## Phase high-level checklist
 
- [x] Resource Conservation Law (TOWN-011/012) strictly enforced.
- [x] Authoritative Quest Reward pipeline implemented.
- [x] RPG Core Life-Loop and mortality laws verified.
- [x] 100% green status on all RPG verification tests.
 
---
 
# Phase 13 — Legacy Retirement (SKIPPED)
 
## Phase description
 
Retire the legacy engine and tests to minimize repository debt.
 
## Status
 
**SKIPPED** — The user has elected to keep `src_legacy` and `tests_legacy` for ongoing parity verification and reference.

