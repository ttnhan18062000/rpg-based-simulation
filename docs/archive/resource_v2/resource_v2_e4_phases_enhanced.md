---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# Implementation Plan Enhance4 — System-Wide Semantic Coverage

Target checklist coverage after E4: **~75–85%**. This phase moves beyond individual subsystem fixes to establish a provable, machine-readable truth baseline and complete the missing high-level RPG loops (Determinism, Combat Matrix, Strategic Cognition, Social Contracts, Progression, World Lifecycle, and Observability).

---

# Phase E4.0 — Coverage Ledger Completion (Truth Baseline)

## Phase description
Turn the exhaustive checklist into a machine-readable "Truth Ledger" where every checked item is mapped to a `VERIFIED v2` marker in the source.

## Phase technical
Standardize Verification IDs across the ledger and source. Update `protocol_validator.py` to enforce strict ID matching. Uncheck unproven items to establish an "honest baseline."

## Phase high-level checklist
- [ ] Each checked item has a stable ID matching a `VERIFIED v2` marker. <!-- VERIFIED v2: scripts/protocol_validator.py -->
- [ ] No "NO TRACE" failures in the validator for checked items.
- [ ] Verified Coverage reflects the actual state of the implementation (~15-20% truthfully mapped).

## Tasks

### Task 0.1 — Standardize Checklist IDs
**Missing / incorrect logic:**
```text
Checklist IDs (e.g. strategic_state_persistence) do not always match source markers (e.g. StrategicComponent).
```
**Task checklist:**
- [ ] Audit all `[x]` items in `logic_checklist_exhaustive_v2.md`.
- [ ] Align checklist IDs with source markers or vice-versa.
- [ ] Add `<!-- VERIFIED v2: ID -->` comments to every checked row.

### Task 0.2 — Inject Missing Core Markers
**Task checklist:**
- [ ] Inject markers for `authoritative_mutation_boundary` in `pipeline.py`.
- [ ] Inject markers for `xp_vs_resource_separation` in `pipeline.py`.
- [ ] Inject markers for `quest_reward_transaction_safety` in `pipeline.py`.

---

# Phase E4.1 — Determinism and Replay Completion

## Phase description
Prove that the engine is bit-identical across runs, execution modes (local/concurrent), and replays.

## Phase technical
Harden RNG domain separation and ensure the canonical state hash captures all gameplay-relevant state.

## Phase high-level checklist
- [ ] All gameplay randomness uses `DeterministicRNG` domain APIs. <!-- VERIFIED v2: src/platform/rng.py -->
- [ ] Canonical state hash matches between Local and Concurrent modes.
- [ ] Replay reproduces rejected transactions and reward pending states exactly.

## Tasks

### Task 1.1 — Enforce RNG Domain Separation
**Task checklist:**
- [ ] Refactor `CombatSystem` to use `RNG.get_float(Domain.COMBAT, ...)`.
- [ ] Refactor `SpawnService` to use `RNG.get_float(Domain.SPAWN, ...)`.
- [ ] Refactor `LootSystem` to use `RNG.get_float(Domain.LOOT, ...)`.

---

# Phase E4.2 — Full Combat Legality and Consequence Matrix

## Phase description
Complete the combat law matrix covering Melee, Ranged, AoE, Status, and Death consequences.

## Phase high-level checklist
- [ ] Melee, Ranged, and AoE attacks obey the same `LegalityServiceV2` boundary. <!-- VERIFIED v2: src/engine/legality.py -->
- [ ] Friendly-fire and dead-target rules are invariant.
- [ ] Combat trace perfectly describes the applied state change.

---

# Phase E4.3 — Complete Strategic Cognition Lifecycle

## Phase description
Close the strategic loop: Project → Objective → Blocker → Lead → Detour → Success/Abandon.

## Phase high-level checklist
- [ ] Concerns generated from real world state (Hunger, Fatigue, Full Inventory, Threats).
- [ ] Blockers correctly diagnosed (Missing Resource, Path Blocked, Full Inventory).
- [ ] Detours suggested and tested for all blocker types.
- [ ] Strategic learning suppresses failed leads.

---

# Phase E4.4 — Complete Social Contract and Party Lifecycle

## Phase description
Make social contracts the authoritative source of group formation and social history.

## Phase high-level checklist
- [ ] Parties formed only from shared Purpose/Contract/Quest.
- [ ] Contract outcome affects trust, reputation, and future appraisal.
- [ ] Betrayal logic implemented with persistent social consequences.

---

# Phase E4.5 — Progression, Skills, and Equipment Completion

## Phase description
Finalize the RPG advancement loop including Skill Unlocking, Stat Scaling, and Equipment Burden.

## Phase high-level checklist
- [ ] Skill unlocks tied to Class/Level progression.
- [ ] Equipment stats and weight affect Movement and Combat.
- [ ] Durability and Repair fully transactional.

---

# Phase E4.6 — World Lifecycle and Long-Run Stability

## Phase description
Ensure the world evolves (Raids, Calamities, Resource Regeneration) and stays clean (Corpse Decay) over 1,000+ ticks.

## Phase high-level checklist
- [ ] Passive updates (Biological, World) run on every quiet tick.
- [ ] Regional dynamics (Influence, Hazards) propagate to strategy.
- [ ] 1,000-tick stress test with zero stale object leaks.

---

# Phase E4.7 — External Truth and Observability

## Phase description
Expose the new authoritative states (Pending Rewards, Blockers, Contracts) to API and Replay.

## Phase high-level checklist
- [ ] API exposes `latest_intent_results` (Rejections, Successes).
- [ ] Replay includes `transaction_trace` for all resource movements.
- [ ] Inspector shows active Strategic Blockers and Detours.

---

# Implementation Order
1. **Phase E4.0** — Establish truthful baseline (ID Reconciliation).
2. **Phase E4.1** — Enforce RNG Purity (Foundation for Replay).
3. **Phase E4.2** — Harden Combat Matrix.
4. **Phase E4.3 / E4.4** — Strategic and Social Loops.
5. **Phase E4.5 / E4.6** — Progression and World Dynamics.
6. **Phase E4.7** — Final Observability and Certification.
