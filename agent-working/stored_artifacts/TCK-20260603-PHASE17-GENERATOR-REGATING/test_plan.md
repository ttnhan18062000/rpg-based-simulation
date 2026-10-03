---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE17-GENERATOR-REGATING
artifact_type: test_plan
tags: [phase17, generator, regating]
---

# Test Plan - Phase 17 (Procedural Generator Re-gating)

This document outlines the testing strategy for verifying generator integration with the unified content catalog.

## Automated Verification

### 1. Schema & Validation Completeness
* Test `test_procedural_generator_valid_world`:
  * Generate a procedural world spec.
  * Verify that the generator outputs a `ResolvedWorldBundle` containing a valid `world_spec`, a non-empty `compile_context`, and a `validation_report` with no blocking errors.
  * Verify that region bounds, building types, and entity counts match the configured intent parameters.

### 2. Strict Determinism Verification
* Test `test_procedural_generator_determinism`:
  * Generate two worlds with the same seed and verify that their `world_spec` and `provenance_manifest.content_fingerprint` are identical.
  * Verify that generating a world with a different seed yields a different spec and content fingerprint.
  * Verify that dynamic timestamps (`created_at`) are allowed to vary without failing determinism checks.

### 3. Catalog-Seeded Smoke Simulation Run
* Test `test_generated_world_catalog_smoke_simulation`:
  * Seed legacy registries using the dynamic content catalog repository (`data/content`).
  * Generate a world with `WorldProceduralGenerator`.
  * Compile the generated world spec utilizing its resolved `compile_context`.
  * Execute a 5-tick simulation runner loop.
  * Assert no registry lookup errors or hard-law validation violations arise during execution.
