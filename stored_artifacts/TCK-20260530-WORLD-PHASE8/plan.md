# Plan: Simple Procedural Generation Foundation (Phase 8)

## Overview

This plan details the implementation of a deterministic, budget-bounded procedural generation framework in `src/worldgeneration/`. The generator consumes a high-level `GenerationIntentSpec` and deterministic seed, building a fully validated `WorldSpec` (worldspec.v1) containing generated regions, terrain assignments, buildings, resources, and populations.

## 1. Schema Definitions (`src/worldgeneration/schema.py`)

We will define:
- `GenerationIntentSpec`: Specifies seed, target sizes, density factors, required modules, and constraints.

## 2. Generator Core (`src/worldgeneration/generator.py`)

We will implement the procedural generator:
- Deterministic initialization via seed-specific RNG (`random.Random`).
- Region Layout: Placement of centered settlements and surrounding wilderness regions.
- Asset Placement: Distance/bounds checks placing buildings in settlements, and resources in wilderness.
- Population Seeding: Spawning appropriate populations (workers, guards, monsters) in spawn-safe areas.
- Provenance Integration: Populating generator metadata (seed, generator version) inside `ProvenanceManifest` sidecars.

## 3. Gating Validation

The generated spec is passed to `WorldValidator` using `ValidationContext.GENERATED_WORLD` to guarantee that all generated assets are structurally sound.
