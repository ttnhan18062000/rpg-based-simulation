---
status: historical
layer: engine
authority: P2
audience: developer
---

# Replacement Status Overview (`src`)

## 1. Executive Summary
This document tracks the cumulative replacement progress of the V2 engine against the legacy `src` codebase. As of Phase 11, the engine has achieved **Ratified Replacement Status** for the primary simulation surface, backed by a comprehensive proof bundle and a formal project verdict.

## 2. Replacement Status by Surface

### Core Engine Substrate
- **Status**: 100% (Hardened & Ratified)
- **Status Detail**: Deterministic loop, authoritative apply path, and lifecycle management are fully verified.
- **Authority**: [Substrate Milestones 1-10](../../README.md#substrate-implementation-milestones-100-complete)

### Grid Movement & Spacials
- **Status**: 100% (Ratified)
- **Status Detail**: Cardinal movement, congestion handling, and spatial hashing are verified for parity.
- **Reference**: [Final Replacement Boundary](../engine/final_replacement_boundary.md)

### Resource & Economy
- **Status**: ~40% (Verified Baseline)
- **Status Detail**: Harvesting, looting, and basic town resolution are recovered. Economy overhaul deferred.
- **Reference**: [Final Proof Bundle](../engine/phase11_proof_bundle.md)

### Combat & Action
- **Status**: ~85% (Hardened)
- **Status Detail**: Basic combat resolution, legality enforcement (LoS), and action convergence are fully recovered.
- **Reference**: [Final Replacement Verdict](../engine/final_replacement_verdict.md)

### Strategic & Social
- **Status**: 100% (Ratified)
- **Status Detail**: Bounded cognition, social trust, and project-based AI are fully recovered and hardened.
- **Reference**: [Strategic Cognition Baseline](../engine/phase11_preserved_review.md)

## 3. Phase 11 Ratification Summary
- **Replacement Coverage**: 80.4% (152/189 behaviors).
- **Parity Proof**: 140/152 supported rows satisfy parity; 12/152 are intentionally divergent.
- **Verdict**: [Final Replacement Verdict](../engine/final_replacement_verdict.md) — RATIFIED.
- **Policy**: No implied parity; only verified behaviors in the [Legacy Replacement Ledger](../engine/legacy_replacement_ledger.md) are supported.

## 4. Next Phase: Phase 12 Cutover
The ratification phase is now closed. All future work is governed by the **Phase 12 Cutover and Retirement Plan**, which defines the schedule for switching production traffic to the `src` engine.

---
*Published on Phase 11 Close — 2026-04-24*
