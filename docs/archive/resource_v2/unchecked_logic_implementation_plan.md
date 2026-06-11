---
status: archive
authority: P2
audience: historical
layer: observability
original_date: unknown
---

# Implementation Plan for Remaining Unchecked Logic

Use this as the next closure plan after the fresh re-audit. The remaining work is no longer “build big systems.” Most major systems exist. The unchecked work is now mostly:

```text
proof governance
legacy edge semantics
domain-specific parity tests
unsupported/divergence classification
infrastructure compatibility
serialization/default-state guarantees
```

---

# Domain 1 — Checklist Governance / Proof Ledger [COMPLETED]

## Goal

Make checklist completion mechanically enforceable instead of manually trusted.

## Missing logic

* Stable checklist IDs are still not fully enforced.
* Checked rows need source, test, and proof markers.
* Divergent / unsupported behavior needs explicit classification.
* CI should fail when a checked row has missing proof.

## Implementation plan

### Task 1.1 — Add stable checklist IDs
* [x] Assign every checklist row a stable ID such as `RPG-AUTH-001`, `RPG-COMBAT-014`, `RPG-WORLD-009`.
  This matters because rows cannot be tracked reliably if their identity depends on text position.
  Verify by running a script that fails on duplicate or missing IDs.

### Task 1.2 — Enforce structured proof markers
* [x] Require checked rows to use this format:
```md
<!-- ID: RPG-XXXX SOURCE: src/... TEST: tests/... PROOF: unit|integration|negative|race|replay|longrun|divergence -->
```
This matters because checklist proof must be machine-readable.
Verify with `scripts/ledger_validator.py`.

### Task 1.3 — Add divergence / unsupported registry
* [x] Create `docs/engine/divergence_register.md` and `docs/engine/unsupported_register.md`.
  This matters because not all legacy behavior should be copied, but every omission must be intentional.
  Verify that every `INTENTIONAL DIVERGENCE` or `UNSUPPORTED` row links to one registry entry.

### Task 1.4 — Add CI ledger gate
* [x] CI must fail when a checked row references missing source/test paths or an unknown proof type.
  This matters because checklist closure should not rot after refactors.
  Verify with negative tests for invalid markers.

---

# Domain 2 — Authoritative Reason / Decision / Rejection Model [COMPLETED]

## Goal

Close remaining authority gaps around structured reasons, bounded tactical decisions, mutation tripwires, and rejection audit.

## Missing logic

* Legacy reason strings are not fully coerced into structured models.
* Tactical choice needs stronger proof that every chosen action comes from a legal bounded set.
* Mutation tripwire during decision phase is still not fully proven.
* Rejection audit aggregation needs explicit certification/report proof.

## Implementation plan

### Task 2.1 — Structured reason model

* [x] 2.1: Replace remaining string-based rejections in `SocialAppraisalSystem` and `LegalityServiceV2` with `ReasonCode` constants.
* [x] 2.2: Refactor `CombatUpdate` results to use `ReasonCode` for all failure paths.
* [x] 2.3: Enforce `ReasonCode` for all rejections in `ResourceTransactionResolver` (e.g., `INSUFFICIENT_CAPACITY`, `TARGET_LOCKED`).
* [x] 2.4: Aggregate rejected actions into scenario reports with reason, actor, target, action kind, and tick.
* [x] 2.5: Verify with a scenario containing movement rejection, combat rejection, and resource rejection.

### Task 2.2 — Tactical decision legality envelope

* [x] Make the tactical decision layer return only actions from a validated legal-action set.
  This matters because tactical AI must not exploit geometry or bypass legality checks.
  Verify with a test where illegal movement/combat options are present but not selected.

### Task 2.3 — Decision-phase mutation tripwire

* [x] Add a read-only guard around decision/thought evaluation so direct entity mutation raises immediately.
  This matters because decision code must propose intent, not mutate authoritative state.
  Verify with a test that intentionally mutates during decision and expects failure.

---

# Domain 3 — Strategic Cognition / Bounded Intelligence / Memory [COMPLETED]

## Goal

Close remaining strategic gaps around bounded concern intake, failed lead suppression, routine priority, and narrative memory.

## Missing logic

* Failed/tested lead suppression needs stronger repeated-tick proof.
* Routine/life-rhythm behavior is under-covered.
* Emotional and narrative memory are still thin.

## Implementation plan

### Task 3.1 — Profile-specific concern intake

* [x] Limit concern intake based on cognition profile, entity capacity, and urgency.
  This matters because low-capacity actors should not process unlimited strategic concerns.
  Verify with low-profile vs high-profile entities receiving the same concern set.

### Task 3.2 — Bounded detour generation

* [x] Generate detours from blockers/leads under explicit breadth/depth limits.
  This matters because strategic planning must not explode or create unrealistic omniscience.
  Verify with blockers that produce multiple possible detours and assert only allowed candidates survive.

### Task 3.3 — Failed lead suppression

* [x] Suppress recently tested failed leads from immediate reuse.
  This matters because actors should learn from failed searches, routes, contracts, or resource attempts.
  Verify with repeated ticks where the actor chooses a different lead after a failed one.

### Task 3.4 — Routine priority and disruption

* [x] Add routine priority rules for archetype, life stage, hunger, fatigue, home, work, and danger interruption.
  This matters because actors should not behave like pure combat/resource bots.
  Verify routine priority changes under hunger/fatigue/night/danger.

### Task 3.5 — Emotional and narrative memory

* [x] Add utility modifiers from emotional state and narrative memory such as confidence, fear, trauma, victory, betrayal, or scars.
  This matters because past events should affect future choices.
  Verify victory increases confidence, betrayal increases avoidance/revenge, and trauma lowers risky choices.

---

# Domain 4 — Social Contracts / Party Cooperation / Goal Registry [COMPLETED]

## Goal

Close social persistence, contract consequences, goal registry completeness, and party coordination edge cases.

## Missing logic [RESOLVED]

* [x] Breaking/honoring contracts needs stronger persistent-consequence proof.
* [x] Goal registry still has unchecked legacy compatibility rows.
* [x] Shared target validity for party members needs explicit guard.
* [x] Some social/nemesis/place-attachment rows remain unclosed.

## Implementation plan [DONE]

### Task 4.1 — Persistent contract consequences

* [x] Ensure honoring, failing, betraying, and cancelling contracts persistently affect trust, reputation, future appraisal, and party behavior.
  This matters because social outcomes must change future decisions.
  Verify by running a second recruitment/contract appraisal after each outcome.

### Task 4.2 — Contract transition table

* [x] Enforce valid transitions with a `ContractStatus` enum and transition service.
  This matters because raw status strings allow invalid social state.
  Verify invalid transitions such as `FULFILLED -> ACTIVE` or `EXPIRED -> FULFILLED` are rejected.

### Task 4.3 — Party shared-target validity

* [x] Validate party shared targets before assignment and clear them when dead, missing, or invalid.
  This matters because stale group targets create broken coordination.
  Verify with target death/removal during a party fight.

### Task 4.4 — Goal registry contract

* [x] Ensure built-in goals are registered, unique, and map to valid AI states or explicitly documented replacements.
  This matters because strategy scoring depends on valid goal routing.
  Verify registry contains expected goals, rejects duplicates, and handles empty candidate lists safely.

### Task 4.5 — Social/nemesis/place attachment parity

* [x] Implement or classify remaining social legacy concepts: place attachment, nemesis milestones, home attachment, and hero trading.
  This matters because these are legacy RPG identity/social memory behaviors.
  Verify each is either implemented with tests or marked unsupported with reason.

---

# Domain 5 — Navigation / Flow Field / Terrain / Anchored Ecology [COMPLETED]

## Goal

Close specialized navigation and anchored-world behavior not covered by basic movement.

## Missing logic [RESOLVED]

* [x] Flow-field navigation to far town and world boss remains unchecked.
* [x] Tactical-mode integration handler is not fully proven.
* [x] Arena stop conditions and watchdog behavior remain open.
* [x] Leash/camp/home anchored behavior still has residual unchecked legacy cases.

## Implementation plan [DONE]

### Task 5.1 — Flow-field navigation for long-distance targets

* [x] Add flow-field or documented replacement pathing for far town and world boss destinations.
  This matters because local A* is not enough for large-map navigation.
  Verify far-town and world-boss navigation use the intended large-scale route mechanism.

### Task 5.2 — Tactical mode integration handler

* [x] Ensure combat/navigation handlers respect tactical target positions and movement modes.
  This matters because tactical decisions must survive integration into execution.
  Verify tactical mode changes the proposed target position and execution path.

### Task 5.3 — Arena stop conditions

* [x] Restore or replace arena stop conditions for wipe and timeout.
  This matters because combat scenarios need deterministic termination.
  Verify wipe ends when one side is eliminated and timeout ends at `max_ticks`.

### Task 5.4 — Watchdog behavior

* [x] Add tick watchdog tests for hung and fast ticks.
  This matters because long-running simulations must detect stalled ticks.
  Verify hung tick aborts and fast tick continues.

### Task 5.5 — Anchored ecology

* [x] Complete no-leash, within-leash, chase-within-leash, and leash-free hunting behaviors.
  This matters because mobs should not globally chase forever unless intentionally configured.
  Verify mobs wander/hunt differently based on leash/camp state.

---

# Domain 6 — Progression / Traits / Roles / Stat Math [COMPLETED]

## Goal

Close growth, trait, role, stat recomputation, and RPG math compatibility gaps.

## Missing logic

* Attribute ownership/scaling semantics need stronger proof.
* RPG math/synergy rules need stable contract tests.
* Trait assignment and unknown-trait safety are not fully closed.
* Role derivation and dynamic role transition need explicit tests.
* Derived-stat ceilings and stat recomputation remain unchecked.

## Implementation plan

### Task 6.1 — Attribute ownership and scaling

* [x] Define which system owns each attribute/stat mutation and how scaling is applied.
  This matters because progression, gear, wounds, buffs, and debuffs can otherwise conflict.
  Verify attribute changes from AP, equipment, wounds, and region debuffs compose correctly.

### Task 6.2 — RPG math contract suite

* [x] Add stable contract tests for stat synergy, derived stat ceilings, caps, floors, and recomputation.
  This matters because RPG math bugs silently break balance.
  Verify recomputation after level-up, equipment change, wound, buff, and debuff.

### Task 6.3 — Trait system closure

* [x] Implement or classify unknown trait handling, valid trait assignment, and trait effect application.
  This matters because traits affect AI, combat, social behavior, and progression.
  Verify unknown traits are ignored safely and all assigned traits are valid.

### Task 6.4 — Role derivation and transition

* [x] Restore or replace role derivation and dynamic role transition with hysteresis.
  This matters because tactical roles should not flicker every tick.
  Verify role changes only after sustained condition changes.

### Task 6.5 — Tactical role bias

* [x] Add role-aware tactical bias for vanguard, support, and protector behavior.
  This matters because party members should not all choose identical micro-objectives.
  Verify each role prefers different movement/combat support behavior.

---

# Domain 7 — Resource / Inventory / Item Registry / Serialization [COMPLETED]

## Goal

Close item identity, registry completeness, stackability, serialization, and near-full inventory edge cases.

## Missing logic

* Item contract tests remain unchecked.
* Registry identity/integrity rows are not fully closed.
* Stack merge and near-full inventory behavior need stronger proof.
* Item serialization / enchanted item serialization remain open.
* Resource state serialization and replay truth still need closure.

## Implementation plan

### Task 7.1 — Item registry completeness

* [x] Ensure all core items load with stable IDs, names, stackability, weight, value, and weapon range metadata.
  This matters because inventory, combat, shop, crafting, and loot depend on registry truth.
  Verify registry identity and weapon range contract tests.

### Task 7.2 — Stackability and near-full inventory

* [x] Handle stack merges before slot rejection.
  This matters because inventory can be “full” by slot count but still able to merge stackable items.
  Verify near-full inventory can accept stackable items but rejects non-stackable items.

### Task 7.3 — Item identity / quantity / weight preservation

* [x] Preserve item ID, quantity, metadata, and weight through transfer, stack, split, serialization, and replay.
  This matters because item loss or mutation can happen without obvious count changes.
  Verify round-trip item serialization and transfer tests.

### Task 7.4 — Resource state serialization

* [x] Serialize/deserialize nodes, ground items, corpses, shop stock, and home storage without losing gameplay state.
  This matters because replay/save/load must preserve resource truth.
  Verify round-trip state before and after resource transactions.

---

# Domain 8 — World / Entity / Snapshot / Determinism Defaults [COMPLETED]

## Goal

Close default-state, serialization, freeze/isolation, registry, and deterministic substrate assumptions.

## Missing logic

* Entity builder and serialization preservation remain under-proven.
* Many default/no-op assumptions remain unchecked.
* Freeze/deep-freeze and model isolation rows remain open.
* Registry completeness for biomes, regions, terrains, tiers, templates, and zones needs closure.
* Subsystem advancement on quiet ticks remains unproven in one legacy scenario.

## Implementation plan

### Task 8.1 — Entity builder and full-schema serialization

* [x] Ensure entity builder and serialization preserve all gameplay-relevant state.
  This matters because generated entities must survive API/replay/save boundaries.
  Verify full schema export, minimal schema export, and no-crash export.

### Task 8.2 — Default-state contract suite

* [x] Add explicit tests for default values, empty collections, no skills, no traits, no quests, and subsystem default rates.
  This matters because default state is where many simulations start.
  Verify every default assumption is intentional.

### Task 8.3 — No-op / empty-tick safety

* [x] Ensure empty ticks still advance passive systems but do not invent actions.
  This matters because quiet ticks should affect world lifecycle without corrupting actors.
  Verify effects tick, completed quests do not advance, unknown actions are ignored.

### Task 8.4 — Freeze and isolation

* [x] Validate deep-freeze, nested collection immutability, copied-grid isolation, and no mutation by exporters/profile builders.
  This matters because mutation leaks break determinism and replay.
  Verify freeze/isolation tests across dict, list, nested structures, and strategy export.

### Task 8.5 — Registry and map data completeness

* [x] Validate terrain names, race labels, biome features, region territories, difficulty zones, tiers, and name templates.
  This matters because world generation depends on complete data definitions.
  Verify registry completeness tests.

---

# Domain 9 — Infrastructure / API / CLI / Degraded Mode [COMPLETED]

## Goal

Close runtime compatibility and safe degraded execution assumptions.

## Missing logic

* Brokerless mode remains partially unchecked.
* RabbitMQ/Kafka/Redis disabled-mode compatibility is open.
* CLI default behavior and parser compatibility are open.
* Structured logging compatibility rows remain open.
* API transport compatibility and protocol behavior need final classification.

## Implementation plan

### Task 9.1 — Brokerless execution

* [x] Ensure action systems import and simulation steps run without RabbitMQ, Kafka, Redis, or broker services.
  This matters because local/dev/degraded mode must not crash.
  Verify disabled-mode tests for each broker dependency.

### Task 9.2 — Worker fallback

* [x] Ensure worker pool falls back to inline execution when infrastructure is unavailable.
  This matters because gameplay should remain correct without distributed execution.
  Verify worker-fallback and no-infrastructure regression runner tests.

### Task 9.3 — CLI compatibility

* [x] Preserve or document CLI behavior such as `python -m src` defaulting to server mode and parser command compatibility.
  This matters because tooling and automation may depend on entrypoint behavior.
  Verify CLI contract tests.

### Task 9.4 — Structured logging contract

* [x] Ensure structured logs include mandatory fields and preserve identifiable component names.
  This matters because operational debugging depends on consistent logs.
  Verify log format tests for main entrypoint, worker pool, engine, and rejection logs.

### Task 9.5 — API protocol compatibility

* [x] Classify old API/broker transport behavior as preserved, replaced, or unsupported.
  This matters because not all old infrastructure should be ported, but the boundary must be explicit.
  Verify API compatibility tests or unsupported registry entries.

---

# Domain 10 — Medical / Death / Succession / Hidden Discovery [COMPLETED]

## Goal

Close high-flavor RPG legacy semantics that are still not proven.

## Missing logic

* Hidden discovery by perception remains unchecked.
* Medical diagnosis by wisdom remains unchecked.
* Succession/heirloom/permadeath rows remain unchecked.
* Nemesis milestone behavior remains incomplete.
* Scar perception remains under-proven.

## Implementation plan

### Task 10.1 — Hidden discovery

* [x] Implement perception-based discovery of hidden loot, locations, clues, or threats.
  This matters because perception should produce RPG exploration value.
  Verify high-perception entities discover hidden content more reliably than low-perception ones.

### Task 10.2 — Medical diagnosis

* [x] Implement wisdom/intelligence-based diagnosis quality for wounds, illnesses, or status effects.
  This matters because support/healer roles need meaningful non-combat gameplay.
  Verify high-wisdom diagnosis is accurate and low-wisdom diagnosis can misdiagnose.

### Task 10.3 — Death succession and heirlooms

* [x] Decide whether permadeath succession/heirlooms are preserved, enhanced, or unsupported.
  This matters because death consequences are a major RPG lifecycle law.
  Verify successor/heirloom transfer or document unsupported scope.

### Task 10.4 — Nemesis lifecycle

* [x] Implement or classify nemesis milestone creation after meaningful hostile history.
  This matters because repeated conflict should affect narrative memory.
  Verify repeated enemy encounters create persistent nemesis state.

---

# Recommended Work Order

## P0 — Closure infrastructure

```text
1. Governance / proof ledger
2. Structured reason model
3. Rejection audit aggregation
4. Unsupported / divergence registry
```

Do this first. Otherwise the checklist will stay manually fragile.

## P1 — High-risk gameplay gaps

```text
5. Source/transaction edge cases and item registry
6. Tactical decision boundedness
7. Strategic failed-lead / detour / routine logic
8. Contract consequences and party target validity
```

These affect core simulation correctness.

## P2 — Legacy semantic parity gaps

```text
9. Flow-field navigation
10. Leash/camp/home/place attachment behavior
11. Traits/roles/stat recomputation
12. Hidden discovery / diagnosis / nemesis / succession
```

These are RPG depth and legacy parity items.

## P3 — Infrastructure and compatibility closure

```text
13. Brokerless/degraded-mode execution
14. CLI/logging/API compatibility
15. Serialization/default-state/freeze registry assumptions
```

These decide whether closure is production-grade, not just gameplay-complete.

---

# Priority Plan

## What must change

Stop treating unchecked rows as “missing features only.” Many are actually **classification tasks**:

```text
implement
enhance
intentionally diverge
unsupported
out of scope
```

## Immediate actions

Start with:

```text
Domain 1 — Checklist Governance
Domain 2 — Authoritative Reason / Rejection
Domain 7 — Resource / Inventory / Item Registry
Domain 8 — Default / Serialization / Freeze
```

These give the highest closure value and reduce false-green risk.
