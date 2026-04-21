# Canonical `src_v2` Surface Inventory

This document tracks the current state of the `src_v2` implementation. It is used as the current-state mirror to the Legacy Replacement Ledger.

## Schema Reference

See [replacement_ledger_schema.md](replacement_ledger_schema.md) for detailed maturity dimension and column definitions.

## Inventory Ledger

| ID | Area | Atomic Item | V2 Source | V2 Test | Proof Artifact | Maturity Status | Ambiguity Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **LEG-RPG-008** | RPG-CORE | Replay/Observability consume results | `src_v2/engine/` | `tests_v2/` | `test_authoritative_apply.py`| SUPPORTED | Verified in M7. |
| **LEG-RPG-009** | RPG-CORE | Manhattan distance (Move/Combat) | `src_v2/engine/legality.py`| `tests_v2/parity/`| `test_movement_parity.py` | SUPPORTED | Bit-identical parity. |
| **LEG-RPG-010** | RPG-CORE | Cardinal/tile movement legality | `src_v2/engine/movement.py`| `tests_v2/parity/`| `test_movement_parity.py` | SUPPORTED | Explicit tile rules. |
| **LEG-RPG-011** | RPG-CORE | Occupied-tile movement rejection | `src_v2/engine/legality.py`| `tests_v2/parity/`| `test_movement_parity.py` | SUPPORTED | Prevents silent overlap. |
| **LEG-RPG-012** | RPG-CORE | Melee legality (Adjacency) | `src_v2/engine/legality.py`| `tests_v2/parity/`| `test_interaction_parity.py`| SUPPORTED | Hardened engagement rules.|
| **LEG-RPG-013** | RPG-CORE | Ranged legality (Range + LOS) | `src_v2/engine/legality.py`| `tests_v2/parity/`| `test_interaction_parity.py`| SUPPORTED | Explicit LoS check in v2.|
| **LEG-RPG-014** | RPG-CORE | AoE legality (Center/Radius) | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_interaction_parity.py`| SUPPORTED | Unified AoE system. |
| **LEG-RPG-015** | RPG-CORE | World-time vs readiness cadence | `src_v2/engine/kernel.py` | `tests_v2/verify/`| `test_quiet_tick_integrity.py`| SUPPORTED | Decoupled tick semantics.|
| **LEG-RPG-016** | RPG-CORE | Quiet ticks advance consequences | `src_v2/engine/kernel.py` | `tests_v2/verify/`| `test_quiet_tick_integrity.py`| SUPPORTED | Background progression. |
| **LEG-RPG-017** | RPG-CORE | Disengagement/OA consequences | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_interaction_oracle` | PARTIAL | OA contracts pending. |
| **LEG-RPG-018** | RPG-CORE | Anti-stalemate logic (Cycle det.) | `src_v2/systems/` | `tests_v2/` | `test_anti_stalemate.py` | SUPPORTED | Cycle-detection v2. |
| **LEG-RPG-019** | RPG-CORE | Movement intent semantic modes | `src_v2/engine/movement.py`| `tests_v2/parity/`| `test_movement_parity.py` | SUPPORTED | Seven intent modes. |
| **LEG-RPG-020** | RPG-CORE | Congestion handling (Yield/Sidestep) | `src_v2/systems/redirection.py`| `tests_v2/parity/`| `test_movement_parity.py` | SUPPORTED | Redirection system. |
| **LEG-RPG-022** | RPG-CORE | Looting as channeled state | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_resource_interaction_parity.py`| SUPPORTED | Exact state-machine. |
| **LEG-RPG-023** | RPG-CORE | Harvesting as channeled state | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_resource_interaction_parity.py`| SUPPORTED | Contract-hardened timing.|
| **LEG-RPG-024** | RPG-CORE | Loot/harvest abort (Slot pressure) | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_resource_interaction_parity.py`| SUPPORTED | Capacity enforcement. |
| **LEG-RPG-025** | RPG-CORE | Loot/harvest abort (Weight pressure) | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_resource_interaction_parity.py`| SUPPORTED | Carry burden logic. |
| **LEG-RPG-026** | RPG-CORE | Inventory tracks Slots + Weight | `src_v2/core/state.py` | `tests_v2/` | `test_item_contracts.py` | SUPPORTED | Disaggregated metrics. |
| **LEG-RPG-027** | RPG-CORE | Node yields as side effects | `src_v2/engine/interaction.py`| `tests_v2/parity/`| `test_resource_interaction_parity.py`| SUPPORTED | Authoritative emission. |
| **LEG-RPG-028** | RPG-CORE | Town return as real state | `src_v2/engine/town_resolution.py`| `tests_v2/parity/`| `test_town_resolution_parity.py`| SUPPORTED | No cosmetic teleports. |
| **LEG-RPG-029** | RPG-CORE | Shop visits (Buy/Sell) | `src_v2/engine/shop.py` | `tests_v2/parity/`| `test_town_resolution_parity.py`| SUPPORTED | Gold/Inventory truth. |
| **LEG-RPG-030** | RPG-CORE | Blacksmith visits (Crafting/Gating) | `src_v2/engine/blacksmith.py` | `tests_v2/` | `test_town_resolution_parity.py`| SUPPORTED | Explicit crafting res. |
| **LEG-RPG-032** | RPG-CORE | Inn/Home visits (Recovery) | `src_v2/engine/town_resolution.py`| `tests_v2/unit/`| `test_town_resolution_parity.py`| SUPPORTED | Distinct recovery states. |
| **LEG-RPG-034** | RPG-CORE | Near-death hardening (Stat growth) | `src_v2/systems/strategic.py`| `tests_v2/` | `test_near_death_hardening.py`| SUPPORTED | Restoration from Part 5. |
| **LEG-RPG-035** | RPG-CORE | Strategic state (Directives etc.) | `src_v2/core/strategic.py` | `tests_v2/` | `test_resource_intelligence_contract.py`| SUPPORTED | Persistent across ticks. |
| **LEG-RPG-038** | RPG-CORE | Blocker inference | `src_v2/systems/strategic.py`| `tests_v2/` | `test_resource_intelligence_contract.py`| SUPPORTED | Bounded cognition. |
| **LEG-RPG-047** | RPG-CORE | Blocker material resolution | `src_v2/systems/strategic.py`| `tests_v2/` | `test_resource_intelligence_contract.py`| SUPPORTED | Restoration from Part 5. |
| **LEG-RPG-164** | RPG-CORE | Building-to-Strategy Pipeline | `src_v2/engine/blacksmith.py` | `tests_v2/` | `test_resource_intelligence_contract.py`| SUPPORTED | Context markers. |
| **LEG-SYS-001** | SYS-COMPAT | CLI Mode / Argparse support | `src_v2/certification/harness.py`| `tests_v2/` | `verify_v2_baseline.py` | SUPPORTED | Unified entry gate. |
| **LEG-SYS-002** | SYS-COMPAT | Environment/Config Precedence | `src_v2/config/validator.py`| `tests_v2/config/`| `verify_v2_baseline.py` | SUPPORTED | Profile-driven truth. |
| **LEG-SYS-003** | SYS-COMPAT | Broker-fallback (Sequential) | `src_v2/engine/worker_manager.py`| `tests_v2/` | `test_concurrency_bounds.py`| SUPPORTED | Auto-downgrade logic.|
| **LEG-SYS-004** | SYS-COMPAT | Single-process semantic truth | `src_v2/engine/kernel.py` | `tests_v2/` | `test_concurrency_bounds.py`| SUPPORTED | M10 Sequential Base. |
| **LEG-SYS-005** | SYS-COMPAT | Worker-node protocol parity | `src_v2/core/worker_protocol.py`| `tests_v2/` | `test_concurrency_bounds.py`| SUPPORTED | Match with Milestone C.|
| **LEG-SYS-006** | SYS-COMPAT | Graceful signal propagation | `src_v2/engine/kernel.py` | `tests_v2/` | `test_shutdown_integrity.py`| SUPPORTED | Bounded flush budget. |
| **LEG-SYS-007** | SYS-COMPAT | Hardware-bound CPU ceiling | `src_v2/engine/worker_manager.py`| `tests_v2/` | `test_concurrency_bounds.py`| SUPPORTED | Throttled execution. |
| **LEG-SYS-008** | SYS-COMPAT | Hardware-bound RAM floor | `src_v2/config/validator.py`| `tests_v2/` | `verify_v2_baseline.py` | SUPPORTED | Configured sanity check.|
| **LEG-SYS-009** | SYS-COMPAT | JSON-L Replay Tracing | `src_v2/engine/replay_manager.py`| `tests_v2/` | `test_replay_determinism.py`| SUPPORTED | Verifiable trace output.|
| **LEG-SYS-010** | SYS-COMPAT | Streaming Replay Buffer | `src_v2/engine/replay_manager.py`| `tests_v2/` | `test_replay_determinism.py`| SUPPORTED | Non-blocking persistence.|
| **LEG-SYS-011** | SYS-COMPAT | Relative-path release manifest | `src_v2/certification/harness.py`| `tests_v2/` | `verify_v2_baseline.py` | SUPPORTED | Atomic index mapping. |
| **LEG-SYS-017** | SYS-COMPAT | Global concurrency limiter | `src_v2/engine/worker_manager.py`| `tests_v2/` | `test_concurrency_bounds.py`| SUPPORTED | Adaptive cap logic. |
| **LEG-SYS-018** | SYS-COMPAT | Deterministic seed enforcement | `src_v2/platform/rng.py` | `tests_v2/` | `test_determinism_oracle.py`| SUPPORTED | Bit-identical output. |
| **LEG-SYS-019** | SYS-COMPAT | Scenario-driven CLI args | `src_v2/certification/harness.py`| `tests_v2/` | `verify_v2_baseline.py` | SUPPORTED | Profile/Scenario flags. |
| **LEG-SYS-020** | SYS-COMPAT | Headless operation support | `src_v2/engine/kernel.py` | `tests_v2/` | `verify_v2_baseline.py` | SUPPORTED | CI/CD Compatibility. |

---

## Maturity Totals

| Dimension | Count |
| :--- | :--- |
| IMPLEMENTED | 44 |
| TESTED | 44 |
| PROOF-BACKED | 44 |
| SUPPORTED | 43 |

## Audit Log

- **2026-04-21**: Initial V2 inventory scan started. Population of Action/Engine items.
- **2026-04-21**: Completed scan of Combat, Movement, Resources, Town, and System surfaces. 44 items mapped.
