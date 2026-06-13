---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Regional Sovereignty Runtime Contract

**Source:** `src/world/regional_sovereignty.py`, `src/world/regions.py`
**Related docs:** [docs/mechanics/regional_sovereignty.md](../mechanics/regional_sovereignty.md) (topology/build-time), [threat_and_consequences_contract.md](threat_and_consequences_contract.md) (influence thresholds), [docs/simulation/domains/adventure_contract.md](../simulation/domains/adventure_contract.md) (routing decisions)

---

## Purpose

Regional sovereignty governs faction control at runtime — who owns a region, what that ownership means for entities in the region, and how control changes. This document covers **runtime behavior only**. For the build-time topology (how region borders are defined, which regions can be adjacent, declarative sovereignty setup), see `docs/mechanics/regional_sovereignty.md`.

---

## What sovereignty means at runtime

A region is under faction sovereignty when one faction's influence ≥ +50 (player/hero faction) or ≤ −50 (monster/enemy faction). See [threat_and_consequences_contract.md](threat_and_consequences_contract.md) for the influence threshold mechanics.

Sovereignty has three runtime effects:

| Effect | Who it applies to | Mechanism |
|---|---|---|
| Taxation | All entities that earn gold in the region | Every 100 ticks |
| Sovereignty debuffs | Entities in a monster-controlled region | Per-tick stat modifiers |
| Town access lock | Entities of opposing faction | Structural gate on service opportunities |

---

## Taxation — `regional_sovereignty.py`

Taxation runs every **100 ticks**.

| Entity type | Amount paid | Recipient |
|---|---|---|
| Hero/adventurer | 2.0 gold | Owning faction treasury |
| Functional building | 10.0 gold | Owning faction treasury |

Taxation is applied via `ResourceTransferIntent` (mandatory for gold changes). Entities with insufficient gold pay what they have (no debt).

---

## Sovereignty debuffs

When a region is monster-controlled (influence ≤ −50), entities of non-monster faction in that region receive debuffs:

| Stat | Modifier |
|---|---|
| ATK | × 0.8 |
| DEF | × 0.8 |
| SPD | × 0.9 |

**Current implementation status:** The debuff constants and `apply_sovereignty_debuffs()` function are defined in `regional_sovereignty.py`, but the function returns an `EntityUpdate` without populating the debuff fields. The apply-path dependency is incomplete — debuffs are declared but not fully applied in the current codebase.

Agents should not assume debuffs are active. Verify in source before relying on this mechanic.

---

## Movement and borders

**There is no runtime movement-blocking border gate.** Sovereignty does not prevent entities from crossing region borders at the movement level.

Hostile-region avoidance is a **routing decision** — entities avoid monster-controlled regions because:
1. `RegionThreatClassifier` labels them HIGH or EXTREME threat
2. The adventure domain applies a −2.0 blocker penalty to routes through high-threat regions
3. The entity may choose a different route based on its personality (caution bias)

An entity CAN cross into a hostile region if its routing scores it as worthwhile (e.g., a combat-seeking warrior with high bravery bias). Sovereignty does not hard-block this.

---

## Town access lock

When a region is conquered (influence ≤ −50):
- A stronghold structure is spawned at the region centre
- Town service opportunities are faction-filtered by `RequirementsFilter` (see [opportunity_providers_contract.md](opportunity_providers_contract.md))
- Entities of the opposing faction see no service opportunities in that region

Liberation (influence ≥ +50) removes the stronghold and restores open town access.

---

## Cross-region movement rules — `regions.py`

`regions.py` provides the runtime adjacency graph (which regions are reachable from which). Key rules:
- Movement between non-adjacent regions is not permitted (checked before movement resolution)
- Adjacency is symmetric (if A→B is valid, B→A is valid)
- Region graph is static at runtime (built at world generation, not modified during simulation)

---

## Regression tests

- `tests/integration/test_sovereignty.py` — taxation cadence, gold transfer correctness, faction lock
- `tests/unit/test_regions.py` — adjacency graph validity, cross-region movement gate
- Note: sovereignty debuff tests are pending (incomplete implementation)

---

## Extension rules

1. To fix sovereignty debuffs: populate the EntityUpdate fields in `apply_sovereignty_debuffs()` and add tests. Do not change the constants — they are already correct.
2. To add a new faction type: extend the faction alignment check in taxation and town access lock. The influence threshold (±50) is configurable per-region in the build config.
3. To add runtime border gating: add a movement pre-check in the movement resolution phase. This would be a significant behavior change — document in v2_intentional_divergences.md and update the adventure routing contract.
4. Taxation amount (2.0 gold / 10.0 gold) is currently hardcoded. If configurable taxation is needed, move these constants to world config.
