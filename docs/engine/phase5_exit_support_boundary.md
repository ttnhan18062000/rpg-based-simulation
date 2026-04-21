# Phase 5 Exit Support Boundary

## 1. Overview
This document formally defines the official support boundary for the `src_v2` engine at the conclusion of Phase 5. This boundary serves as the frozen baseline for the Phase 6 replacement ledger.

## 2. Officially Supported Slice (Phase 5 Recovery)

The following gameplay and runtime behaviors are **Officially Supported**, proven bit-identical in sequential execution, and regression-guarded.

### A. Grid Movement
- **Scope**: Cardinal and diagonal tile movement on a flat grid.
- **Contract**: Manhattan distance metric, 1.0 units per tick maximum.
- **Verification**: `tests_v2/parity/test_movement_parity.py`
- **Proof Level**: HARDENED (Gate 1 Completion).

### B. Resource Interaction
- **Scope**: Looting and harvesting from mapped resource nodes.
- **Contract**: Channeled interaction through `InteractionSystem`. Support for duration, interruption, and same-tick inventory resolution.
- **Verification**: `tests_v2/parity/test_resource_interaction_parity.py`
- **Proof Level**: HARDENED (Gate 2 Completion).

### C. Town Resolution (Blacksmith)
- **Scope**: Basic item crafting (Blacksmith only) and town-return logic.
- **Contract**: `RedirectionSystem` handles return-to-base; `BlacksmithSystem` handles resource-to-item conversion.
- **Verification**: [Town Resolution Parity Proof](../../tests_v2/parity/test_town_resolution_parity.py)
- **Evidence Index**: See [Phase 5 Proof Bundle](phase5_proof_bundle.md) for full evidence indexing.

### D. Autonomous Progression Loop
- **Scope**: Integrated Seek-Move-Harvest-Resolve-Craft loop for 100+ entities.
- **Verification**: `tests_v2/parity/test_progression_loop_parity.py`

## 3. Explicitly Unsupported / Divergent Remainder

### A. Intentional Divergences
- See [Divergence Log](divergence_log.md) for the full record of intentional parity shifts.
- Key items: Strict channeling, normalized registry keys, Tick 0 resolution.

### B. Unsupported Logic (Phase 6 Ledger Targets)
- See [Known Limitations](known_limitations.md) for the full record of unsupported features.
- Key items: Advanced pathfinding, combat AI, complex economy, tiered buildings.

## 4. Truth Baseline
This document is supported by the **[Phase 5 Truth Package](phase5_truth_package.md)**, which acts as the authoritative ledger for divergences and limitations.

## 4. Execution Mode Assumptions
- **Supported**: Sequential execution (Deterministic baseline).
- **Experimental**: Concurrency/Worker path (Thread-safety is implemented but parity equivalence is not yet fully ratified for the whole slice).

## 5. Certification Baseline
This boundary is linked to the **Class B Performance Profile** as defined in `docs/engine/performance_contract.md`.

---
*Created as part of Phase 6 Milestone 1 — Entry Gate Baseline.*
