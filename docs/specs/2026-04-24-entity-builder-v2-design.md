---
status: archive
authority: P2
audience: historical
layer: core
original_date: 2026-04-24
---

# V2 Entity Builder Design Specification

## 1. Goal
To implement a construction contract for V2 entities that provides a fluent API for testing and initialization while strictly enforcing the immutability and architectural standards of the V2 substrate.

## 2. Requirements

### 2.1 Fluent API Parity
The `V2EntityBuilder` must support the following methods (matching the legacy `EntityBuilder` signature):
- `kind(k: str)`
- `role(r: int)`
- `at(pos: tuple[float, float])`
- `with_base_stats(hp, atk, def_stat, ...)`
- `with_randomized_stats(rng, seed)`
- `build() -> EntityState`

### 2.2 Immutability
The resulting `EntityState` (and all nested components: `IdentityComponent`, `CombatComponent`, etc.) must be `frozen=True`.

### 2.3 Determinism
Randomization methods must produce bit-identical results to the legacy implementation when provided with the same `DeterministicRNG` state.

## 3. Implementation Details

### 3.1 Mutable Accumulator Pattern
The builder will internally maintain a flat dictionary of values. The `.build()` method will handle the "disaggregation" of these values into the typed V2 components.

### 3.2 Component Mapping
| Legacy Field | V2 Component | V2 Field |
| :--- | :--- | :--- |
| `hp` | `CombatComponent` | `hp` |
| `atk` | `CombatComponent` | `atk` |
| `role` | `IdentityComponent` | `role` |
| `pos` | `EntityState` | `position` |

## 4. Verification Plan

### 4.1 Differential Parity Proof
A dedicated parity test `tests/parity/test_entity_construction.py` will:
1. Instantiate a legacy `EntityBuilder`.
2. Instantiate a `V2EntityBuilder`.
3. Apply identical sequences of fluent calls.
4. Compare the final state snapshots.
5. **Success Criteria**: 100% field parity for all core RPG attributes.

## 5. Metadata and Tracking
- **Ledger ID**: `SUB-002` (EntityBuilder construction law)
- **Status**: Implementation Pending
- **Priority**: P0
