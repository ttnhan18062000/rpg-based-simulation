---
status: active
layer: engine
authority: P1
audience: developer
---

# Supported Gameplay Surface

## 1. Purpose
This document defines the official support boundary for gameplay logic within `src`. It distinguishes between verified authoritative behaviors and excluded or experimental systems.

## 2. Support Matrix

| Gameplay Slice | Support Level | Path | Determinism Proof | Concurrency Proof |
| :--- | :--- | :--- | :--- | :--- |
| **Grid Movement** | OFFICIAL | Authoritative Apply | HASH_MATCH | EQUIVALENT |
| **Resource Interaction**| OFFICIAL | InteractionSystem | HASH_MATCH | EQUIVALENT |
| **Inventory (Bounded)** | OFFICIAL | InventoryComponent | HASH_MATCH | PROTECTED |
| **Blacksmithing** | SUPPORTED | BlacksmithSystem | EQUIVALENT | PROTECTED |
| **Progression Loop** | OFFICIAL | RedirectionSystem | HASH_MATCH | PROTECTED |
| **Combat** | EXCLUDED | N/A | N/A | N/A |

## 3. Support Definitions

### OFFICIAL
- **Guarantee**: Bit-identical results between sequential and supported concurrent modes.
- **Verification**: Certified via `INTEG_RESOURCE_LOOP` scenarios.
- **Regression**: Any divergence blocks the release gate.

### EXPERIMENTAL
- **Guarantee**: Best-effort. May have non-deterministic edge cases.
- **Usage**: Only enabled via specific `RuntimeProfile` flags.

### EXCLUDED
- **Guarantee**: NONE. The engine substrate explicitly ignores or errors on these intents.

## 4. Intentional Divergences from Legacy (src)

| Feature | Legacy Behavior | V2 Behavior | Reasoning |
| :--- | :--- | :--- | :--- |
| **Harvesting** | Instant (Engine Bug) | Channeled (3+ Ticks) | **Operation Honesty**: Channeled tasks must obey time progression. |
| **Looting** | Ad-hoc Position | Authoritative Proximity | **Safety**: Prevents "teleport-looting" via parallel updates. |
| **Inventory** | Unbounded Dict | Bounded Slots/Weight | **Resource Budgeting**: Prevents OOM via infinite item storage. |

## 5. Known Limitations
- Movement is currently limited to 1x1 grid resolution (no advanced pathfinding).
- Only the "Blacksmith" building is supported for town resolution.
- Only "Material" blockers and "Location" leads are supported in the strategic loop.
- Multi-actor contention is resolved by authoritative resolution order.
