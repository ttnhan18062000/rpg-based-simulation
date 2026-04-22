# Investigation: Phase 7 Closure Conditions

## Reference Standards

In previous phases, "Closure" was often defined as a "Verification suite pass" or "Parity Oracle pass". For Phase 7 (Substrate Closure), we must elevate this to **Hardened Certification**.

## Target Closure Conditions

### 1. New Gaps (Substrate Recovery)

| ID | Item | Proposed Closure Condition | Proof Path |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-071** | Regional hazards | Authoritative `HazardSystem` implementation. Bit-identical trigger parity with legacy `regions.py`. | DIFFERENTIAL PARITY |
| **LEG-RPG-139** | Calamity consequences | Authoritative `CalamitySystem` extension. Verified deterministic scaling of regional pressure. | V2 CONTRACT |
| **LEG-RPG-143** | Entity Evolution | Authoritative `ArchetypeSystem`. Deterministic mutation in `PersistencePhase`. | V2 CONTRACT |

### 2. Hardening Rows (Authoritative Closure)

These rows are already "SUPPORTED" but require final certification of their deterministic integrity.

| ID | Item | Proposed Hardening Requirement | Proof Path |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-001** | Action intent conv. | Verification of bit-identical update shape across all 15 domains. | CERTIFICATION |
| **LEG-RPG-004** | World mutation sep. | 100% pass on `test_mutation_tripwire` under high-pressure concurrency. | CERTIFICATION |
| **LEG-RPG-006** | Conflict resolution | Proof of bit-identical resolution for 1000-tick randomized action sets. | CERTIFICATION |
| **LEG-RPG-066** | World gen det. | Bit-identical grid-state equality for 10 distinct seeds. | CERTIFICATION |
| **LEG-RPG-068** | Snapshot immut. | Verified recursive freeze on all `MindAspect` and `WorldAspect` records. | CERTIFICATION |
| **LEG-RPG-070** | Det. replay | Bit-identical state reconstruction from `.jsonl` stream for 5000 ticks. | CERTIFICATION |
| **LEG-RPG-073** | Engine phase order | Verified invariant enforcement at every phase boundary (0 to 5). | CERTIFICATION |
| **LEG-RPG-159** | Serialization Hard. | 100% round-trip parity for all `Entity` components including strategic state. | CERTIFICATION |

## Substrate Truth Standards

Phase 7 must enforce the following truth standards:
- **Bit-Identicality**: Mandatory for World Gen, Replay, and Conflict Resolution.
- **Structural Integrity**: Mandatory for Snapshots and Serialization.
- **Contract Safety**: Mandatory for Hazards and Calamity Scaling.

## Documentation Impact

The `docs/engine/phase7_backlog.md` must be updated to include a `Closure Condition` column that explicitly maps to these requirements.
