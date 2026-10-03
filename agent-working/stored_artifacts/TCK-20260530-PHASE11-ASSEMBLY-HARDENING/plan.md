---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE11-ASSEMBLY-HARDENING
artifact_type: plan
tags: [phase11, assembly, hardening]
---

# Implementation Plan - Phase 11 Assembly Hardening

## Overview
This plan specifies how Phase 11 will be implemented in accordance with `world_phases_11_19.md`.

## Proposed Changes

### Component 1: `ResolvedWorldBundle` and `CompileContext` integration
- Modify `ResolvedWorldBundle` in `src/worldassembly/resolver.py` to include `compile_context: CompileContext`.
- Add `validation_report` parameter to `ResolvedWorldBundle`.

### Component 2: Stage Decoupling
- Extract Validator logic into `WorldAssemblyValidator`.
- Extract Report Builder logic into `WorldAssemblyReportBuilder`.
- Ensure `WorldAssemblyResolver` orchestrates these stages cleanly.

### Component 3: Explicit Profile Preservation
- In `WorldAssemblyResolver.assemble()`, when traversing population recipes, resolve their profiles and populate `compile_context` using `self.profile_resolver`.
- Ensure explicit `stats_profile`, `inventory_profile`, and `cognition_profile` are registered correctly.

### Component 4: Provenance Determinism
- Separate `created_at` from `content_fingerprint` in assertions and avoid byte-identical hacks.
