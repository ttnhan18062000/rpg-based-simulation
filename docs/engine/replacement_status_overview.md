# Replacement Status Overview (`src_v2`)

## 1. Executive Summary
This document tracks the cumulative replacement progress of the V2 engine against the legacy `src` codebase. As of Phase 5, the engine has transitioned from "Exploratory Recovery" to a "Hardened Baseline" for core RPG loop components.

## 2. Replacement Status by Surface

### Core Engine Substrate
- **Status**: 100% (Hardened)
- **Status Detail**: Deterministic loop, authoritative apply path, and lifecycle management are fully implemented and verified.
- **Authority**: [Substrate Milestones 1-10](../../README.md#substrate-implementation-milestones-100-complete)

### Grid Movement & Spacials
- **Status**: ~90% (Hardened Slice)
- **Status Detail**: Cardinal/diagonal movement is bit-identical for supported scenarios. Complex pathfinding is unsupported.
- **Reference**: [Phase 5 Truth Package](phase5_truth_package.md)

### Resource & Economy
- **Status**: ~20% (Verified Baseline)
- **Status Detail**: Basic harvesting and Blacksmith crafting are recovered for the single-loop scenario.
- **Reference**: [Phase 5 Proof Bundle](phase5_proof_bundle.md)

### Combat & Action
- **Status**: 0% (Pending)
- **Status Detail**: All combat logic remains in legacy `src`. No combat attachment yet exists in `src_v2`.

### World & Spawning
- **Status**: ~5% (Structural)
- **Status Detail**: Authoritative entity representation exists. Spawning rules and world-level persistence remain in legacy `src`.

## 3. Phase 5 Certification Gate Summary
- **Truth Source**: [Phase 5 Truth Package](phase5_truth_package.md)
- **Evidence Source**: [Phase 5 Proof Bundle](phase5_proof_bundle.md)
- **Policy**: No implied parity; only verified behaviors are considered "SUPPORTED".

## 4. Next Milestone: Phase 6 Ledger
The current status is now frozen. All future progress is governed by the **Phase 6 Authoritative Replacement Ledger**, which will provide a row-by-row inventory of for replacement.

---
*Published on Phase 6 Entry — 2026-04-21*
