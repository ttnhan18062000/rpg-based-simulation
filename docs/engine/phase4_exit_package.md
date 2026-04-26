# Phase 4 Exit Package: Core Truth & Parity Status

## 1. Executive Summary
Phase 4 concluded with the successful transition of the `src` Resource Engine into an authoritative resolution substrate. This package serves as the "frozen" reference for the engine's truth surfaces before entering Phase 5 expansion.

## 2. Supported Slices
| Layer | Verification | Status |
| :--- | :--- | :--- |
| **Grid Movement** | `test_movement_parity.py` | 100% Bit-Identical |
| **Interaction Core** | `test_resource_interaction_parity.py` | 100% Bit-Identical |
| **Replay Kernel** | `test_replay_order_preservation.py` | 100% Bit-Identical |

## 3. Support Boundary (Phase 4)
- **Movement**: 8-way grid movement with basic occupancy checking.
- **Interaction**: Bounded channeling for "ORE_VEIN" and "WOOD_NODE" types.
- **Inventory**: Authoritative slot counting and weight calculation.
- **Governor**: Bound-concurrency execution with deterministic lifecycle.

## 4. Known Limitations
- Pathfinding is restricted to local step-based proposal.
- Resource nodes do not yet support complex respawn cycles during tick 0.
- Town resolution is EXCLUDED from the Phase 4 support boundary.

## 5. Major Divergences
- **Readiness Cost**: V2 uses a fixed -50.0 readiness cost per move for deterministic consistency, replacing the variable original src cost.
- **Shutdown Semantics**: V2 enforces a pre-emptive bounded flush for the replay buffer to prevent disk-hang regressions.

## 6. Official Approval
> [!IMPORTANT]
> The Phase 4 branch is verified stable and bit-identical for the movement and interaction slices. This package closes Phase 4 truth debt.
