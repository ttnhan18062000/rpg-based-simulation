# V2 Engine Support Matrix

## 1. Overview
This matrix provides a detailed view of supported features, their verification level, and their parity status against the legacy `src` system.

## 2. Core System Support
See [Phase 5 Truth Package](phase5_truth_package.md) for detailed divergences and [Phase 5 Proof Bundle](phase5_proof_bundle.md) for evidence.

| Subsystem | Feature | Status | Parity | Verification Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **Grid** | Tile Movement | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **Grid** | Cardinal Step | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **Grid** | Collision | **EXPERIMENTAL**| Divergent | [Divergence Log](divergence_log.md) |
| **Interaction**| Looting | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **Interaction**| Harvesting | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **Town** | Blacksmithing | **SUPPORTED**| Simplified | [Divergence Log](divergence_log.md) |
| **Town** | Redirection | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **AI** | Seek Loop | **OFFICIAL** | Bit-Identical | [Proof Bundle](phase5_proof_bundle.md) |
| **AI** | Combat Tactics | **SUPPORTED**| Divergent | [TCK-20260424-FIX-TEST-REGRESSIONS](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260424-FIX-TEST-REGRESSIONS.md) |
| **Social** | Recruitment | **SUPPORTED**| Contractual | [Walkthrough](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260424-PH9-FINAL-CLOSURE/walkthrough.md) |
| **Cognition** | Strategic Bias | **SUPPORTED**| Divergent | [Walkthrough](file:///home/vboxuser/Work/rpg-based-simulation/stored_artifacts/TCK-20260424-PH9-FINAL-CLOSURE/walkthrough.md) |

## 3. System Surface Support (Phase 10 Focus)

| Subsystem | Feature | Status | Parity | Gap |
| :--- | :--- | :--- | :--- | :--- |
| **CLI** | Unified Entry | **PARTIAL** | Functional | Full flag parity missing. |
| **Infra** | Broker Disabled | **OFFICIAL** | Bit-Identical | None. |
| **Observability**| Replay JSON-L | **SUPPORTED** | Bit-Identical | Flush-timing drift. |
| **Observability**| Structured Logs | **PARTIAL** | Divergent | Trace-ID missing. |
| **API** | REST Status | **PARTIAL** | Divergent | Metadata gaps. |
| **API** | WebSocket | **UNSUPPORTED** | N/A | Full recovery needed. |

## 3. Runtime Profile Support

| Profile | Hardware Class | Concurrency | Status | Benchmark Target |
| :--- | :--- | :--- | :--- | :--- |
| **Standard** | Class B | Disabled | **OFFICIAL** | 100 Entities / 180 TPS |
| **Standard** | Class B | Enabled | **EXPERIMENTAL** | Thread-safe, No parity proof |
| **Low-Perf** | Class C | Disabled | **UNTESTED** | N/A |

## 4. Manifest Alignment
This matrix is synchronized with `manifest_v2.md` and represents the "Hardened" baseline for Phase 5. Any feature not listed as **SUPPORTED** or **EXPERIMENTAL** is considered out-of-scope for the current V2 runtime.

---
*Verified for Phase 10 Entry — 2026-04-24*
