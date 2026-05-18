# V2 Engine Support Matrix

## 1. Overview
This matrix provides a detailed view of supported features, their verification level, and their parity status against the legacy `src` system.

## 2. Core System Support
See [Phase 5 Truth Package](../engine/phase5_truth_package.md) for detailed divergences and [Phase 5 Proof Bundle](../engine/phase5_proof_bundle.md) for evidence.

| Subsystem | Feature | Status | Parity | Verification Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **Grid** | Tile Movement | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **Grid** | Cardinal Step | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **Grid** | Collision | **EXPERIMENTAL**| Divergent | [Divergence Log](../engine/divergence_log.md) |
| **Interaction**| Looting | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **Interaction**| Harvesting | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **Town** | Blacksmithing | **SUPPORTED**| Simplified | [Divergence Log](../engine/divergence_log.md) |
| **Town** | Redirection | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **AI** | Seek Loop | **OFFICIAL** | Bit-Identical | [Proof Bundle](../engine/phase5_proof_bundle.md) |
| **AI** | Combat Tactics | **SUPPORTED**| Divergent | [TCK-20260424-FIX-TEST-REGRESSIONS](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260424-FIX-TEST-REGRESSIONS.md) |
| **Social** | Recruitment | **OFFICIAL** | Contractual | `test_recruitment.py` |
| **Cognition** | Strategic Bias | **OFFICIAL** | Divergent | `test_resource_intelligence_contract.py` |
| **Combat** | Legal Moves | **OFFICIAL** | Divergent | `test_legality.py` |

## 3. System Surface Support (Phase 10 Focus)

| Subsystem | Feature | Status | Parity | Gap |
| :--- | :--- | :--- | :--- | :--- |
| **CLI** | Unified Entry | **OFFICIAL** | Parity | `test_entry_parity.py` |
| **Infra** | Broker Disabled | **OFFICIAL** | Bit-Identical | `test_infra_isolation.py` |
| **Observability**| Replay JSON-L | **OFFICIAL** | Bit-Identical | `test_observability.py` |
| **Observability**| Structured Logs | **OFFICIAL** | Parity | `test_observability.py` |
| **API** | REST Status | **OFFICIAL** | Parity | `test_rest_parity.py` |
| **API** | WebSocket | **OFFICIAL** | Protocol Parity | `test_ws_protocol.py` |

## 3. Runtime Profile Support

| Profile | Hardware Class | Concurrency | Status | Benchmark Target |
| :--- | :--- | :--- | :--- | :--- |
| **Standard** | Class B | Disabled | **OFFICIAL** | 100 Entities / 180 TPS |
| **Standard** | Class B | Enabled | **EXPERIMENTAL** | Thread-safe, No parity proof |
| **Low-Perf** | Class C | Disabled | **UNTESTED** | N/A |

## 4. Manifest Alignment
This matrix is synchronized with `manifest_v2.md` and represents the "Hardened" baseline for Phase 5. Any feature not listed as **SUPPORTED** or **EXPERIMENTAL** is considered out-of-scope for the current V2 runtime.

---
*Verified for Phase 11 Ratification — 2026-04-24*
