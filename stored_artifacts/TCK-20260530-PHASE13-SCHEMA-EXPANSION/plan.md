---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE13-SCHEMA-EXPANSION
artifact_type: plan
tags: [phase13, schema, expansion]
---

# Implementation Plan - Phase 13 Schema Expansion

## Overview
Expand catalog schema definitions to include items, enemies, recipes, and runtime regions.

## Proposed Changes

### Component 1: Pydantic Schema Definitions (`src/content/schema.py`)
- Add Pydantic classes:
  - `ItemDefinition`
  - `LootTableEntry`
  - `EnemyDefinition`
  - `RecipeIngredient`, `RecipeOutput`
  - `RecipeDefinition`
  - `RuntimeRegionDefinition`

### Component 2: CatalogRepository Loading (`src/content/repository.py`)
- Load and parse items, enemies, recipes, and runtime regions from Yaml files.
- Return fingerprints including these directories.

### Component 3: CatalogValidator Cross-References (`src/content/validator.py`)
- Add semantic validation checks verifying relational links across definitions.
