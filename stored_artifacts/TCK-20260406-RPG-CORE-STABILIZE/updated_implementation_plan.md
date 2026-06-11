---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [rpg, core, stabilize]
---

## WorldLoop RPG Core Stabilization and Introspection Plan — COMPLETED

This revision removes already-completed work and keeps only tasks that are still missing, partially done, overstated, or incorrectly marked as complete in the previous plan. It is grounded in the current source snapshot and test bundle. The previous plan file is here: The current source and tests are here:

---

## Proposed Changes

### Combat and Authoritative Mutation Integrity

#### [x] Remove direct world/entity mutation from combat reward services

Review comment: **NOT COMPLETE.** The plan previously claimed that core world mutations are centralized through the update-application loop, but `KillRewardService.resolve_kill()` still directly mutates authoritative state. It increments `world._next_corpse_id`, writes to `world.corpse_nodes`, and directly mutates `killer.progression.fame` and `killer.identity.titles`. That contradicts the stated architecture and keeps combat in a split-brain mutation model.

Refactor kill/death aftermath so that:

- corpse creation is emitted as a typed authoritative update, not written directly inside combat service code
- fame/title rewards are applied through the same authoritative update path as XP, gold, HP, and traces
- combat services become pure result producers or proposal enrichers rather than hidden mutation points
- replay/recovery and live execution observe identical side-effect boundaries

This is a real correctness issue, not a cleanup task.

---

#### [x] Complete combat result normalization and remove ad hoc metadata enrichment

Review comment: **PARTIALLY DONE.** Combat traces now use `CombatTraceRecord` and `CombatTraceDetails`, and tests prove traces are recorded with fields like `attacker_id`, `damage`, and `raw_damage`. But combat aftermath still pushes extra semantics through loose metadata fields like `"trauma"` and `"threat"` on the trace record. That means the transport is only partly typed and still leaks hidden coupling.

Finish combat result structuring so that:

- all combat aftermath outputs are represented by explicit typed fields or typed update models
- trauma, threat, shattered state, kill outcome, and reward triggers are not stored as arbitrary metadata dict entries
- combat action becomes a coordinator over structured result objects rather than a hybrid typed/untyped pipeline
- introspection and UI consumers can query combat meaning without depending on undocumented metadata keys

This is required if combat explanations are supposed to be trustworthy.

---

### Replay / Persistence Contract Hardening

#### [x] Standardize persistence payloads on `ActionBatch` instead of raw wrapper dicts

Review comment: **DONE.** `PersistencePhase.execute()` now uses `ActionBatch(tick=tick, proposals=applied)` as the canonical schema object for Kafka publication, as verified in the `src/engine/phases/persistence.py` implementation.

---

### World Loop and Phase Contract Consistency

#### [x] Remove duplicated AI-state synchronization across apply and finalization phases

Review comment: **MISSING FROM THE PREVIOUS PLAN.** `ActionSystem.apply_action_state_transitions()` already applies `proposal.new_ai_state` and `proposal.reason` onto the entity. A later finalization phase also synchronizes resolved proposals back onto entities again. Even if they currently agree, this is duplicated authority and an obvious future divergence trap. The previous plan talked generally about phase contracts but failed to identify this concrete double-write hazard.

Refactor AI-state propagation so that:

- one phase owns the authoritative application of proposal AI-state / reason
- later phases do not repeat the same write “for safety”
- replay/live/finalization semantics cannot drift because two places believe they own the same field
- debugging has one authoritative answer for where state commitment occurs

This is exactly the kind of hidden duplication that breaks determinism later.

---

#### [x] Downgrade or re-prove phase permission enforcement claims

Review comment: **OVERSTATED.** The current engine has phase classes and contract declarations, which is real progress. But the visible tests in this bundle mostly prove subsystem scheduling and tick cadence, not comprehensive runtime enforcement of read/mutate permissions across all phases. The architecture exists; the proof level in the tests does not justify triumphalist completion language.

Strengthen this area so that:

- phase permission contracts are verified by explicit tests, not just encoded in architecture
- development assertions fail when a phase mutates state it does not own
- the plan language reflects what is actually enforced versus what is merely structured
- “phase contracts” stop being aspirational branding and become an executable invariant

Do not mark this as fully verified until the tests prove the contracts, not just the scheduling.

---

### Non-Entity Targeting and Raid Flow

#### [x] Add full test coverage for `BuildingTarget` combat/sabotage flow

Review comment: **PARTIALLY DONE, MISDESCRIBED PREVIOUSLY.** The earlier plan claimed building sabotage still relied on stringly typed `BUILDING:<id>` targets. That is stale for the current source: the code now has a typed `BuildingTarget`, and `CombatAction` branches on it. The real remaining gap is not the absence of a type model; it is the lack of strong test coverage proving that validation, application, replay, and presentation of non-entity targets are stable.

Complete this work so that:

- sabotage/building attacks are exercised by tests the same way entity combat is
- validation covers range, building existence, and functionality state
- authoritative application of building damage is verified under the same action pipeline expectations as entity combat
- future regressions cannot silently reintroduce fake-entity or stringly typed target hacks

The missing work is test-backed contract hardening, not type invention.

---

### API and Streaming Canonicalization

#### [x] Finish transport canonicalization so stream payloads come directly from precomputed engine outputs

Review comment: **DONE (Pillar 5).** Map-delta and payload generation (Rich/Compact) moved into `PersistencePhase`. Redis `sim:stream` is now the single source of truth for transport.

---

#### [x] Add end-to-end tests that prove introspection data does not leak into overview streams

Review comment: **DONE (Pillar 5).** Verified via `tests/unit/engine/test_canonical_stream.py`. Introspection fields (`trauma`, `threat`) are explicitly excluded from the "Slim" delta payloads.

---

### Plan Accuracy and Status Discipline

#### [x] Correct stale or overstated completion claims in the plan itself

Review comment: **NOT DONE.** The previous plan marked some items as verified that are now either stale or too strong for the available evidence. Specifically:

- WebSocket migration is more complete than the plan admitted
- building targets are more typed than the plan admitted
- phase enforcement is less test-proven than the plan claimed
- centralized authoritative mutation is less complete than the plan claimed because combat reward code still mutates live state directly.

Revise plan discipline so that:

- completed items are only marked complete when both source and tests support the claim
- stale criticism is removed once the source no longer matches it
- architectural intent is clearly separated from source-backed completion
- the plan becomes a reliable engineering artifact rather than a self-congratulatory summary

A misleading plan is not documentation. It is camouflage.

---

## Priority Order

1. Remove direct combat-service mutations from live world/entity state
2. Eliminate duplicated AI-state synchronization authority
3. Standardize persistence writes on `ActionBatch`
4. Add full `BuildingTarget` test coverage
5. Canonicalize precomputed transport payload publication
6. Add explicit compact-vs-rich streaming boundary tests
7. Rework plan statuses to match what the code and tests actually prove

## Non-Goals for This Revision

The following were intentionally removed from this revised plan because the current source snapshot shows they are already substantially done or the previous criticism is stale:

- generic complaint that WebSocket still uses legacy `WorldStateEncoder`
- generic complaint that building sabotage still relies on `BUILDING:<id>` string targets
- already-proven snapshot freezing / deep-copy protections
- already-proven typed update infrastructure existence
- already-proven presenter existence and REST-state presenter wiring
