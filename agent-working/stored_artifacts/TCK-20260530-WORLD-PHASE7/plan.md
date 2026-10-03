---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-WORLD-PHASE7
artifact_type: plan
tags: [world, phase7]
---

# Plan: Provenance Manifest and Report Integration (Phase 7)

## Overview

This plan details the implementation of a sidecar provenance manifest and compiler report integration in the `rpg-based-simulation` world assembly pipeline. We will ensure all structural modifications and resolutions are completely traceable, serializing JSON sidecar files alongside the resolved WorldSpecs.

## 1. Schema Definitions (`src/worldassembly/schema.py`)

We will define:
- `ProvenanceRecord`: Holds single-element attributes:
  - `element_id`: str
  - `element_type`: str
  - `source_module`: Optional[str]
  - `recipe_type`: Optional[str]
  - `parameters`: dict[str, Any]
  - `profiles`: dict[str, Any]
  - `details`: dict[str, Any]
- `ProvenanceManifest`: Top-level structure:
  - `manifest_id`: str
  - `world_id`: str
  - `source_schema_version`: str = "provenancemanifest.v1"
  - `catalog_fingerprint`: str
  - `module_fingerprints`: dict[str, str]
  - `composition_fingerprint`: str
  - `resolver_version`: str = "1.0.0"
  - `generator_version`: Optional[str] = None
  - `seed`: Optional[int] = None
  - `created_at`: str
  - `records`: dict[str, ProvenanceRecord]

## 2. Resolver Integration (`src/worldassembly/resolver.py`)

`WorldAssemblyResolver.assemble` will populate the manifest:
- For regions: map to source module, recipes, grid bounds, terrain.
- For populations: map to source module, role, faction, default/explicit stats profiles.
- For resources & buildings: map to source module, type, defaults.
- For factions: map alignments, vaults.

## 3. Storage & Compile Report Integration

We will write `provenance_manifest.json` and a structured `compile_report.json` beside the resolved `world.resolved.yaml` bundle to make compilation 100% auditable.
