# Design: Strategic Knowledge Unification and Building-Surface Unification

## Goal
To eliminate architectural drift and "hybrid" logic in building handlers by standardizing on a single coherent strategic-knowledge pipeline. This shift ensures that all durable world-to-strategic translations are handled via typed `LeadRecord` and `BlockerRecord` objects, which in turn feed the centralized `DetourSuggestionService`.

## Problem Statement
The current simulation engine has buildings (Guild, Blacksmith, Inn, etc.) that produce a mix of:
1. **Typed Strategic records** (the new way).
2. **Legacy string-based goals** in `MindUpdate` (e.g., "Guild tip: iron_ore").
3. **Durable reasoning embedded in prose logs** (e.g., the `reason` field in `ActionProposal`).

This redundancy causes "strategic fragmentation" where detour logic must look at both typed state and unstructured string lists, leading to fragile AI behavior and debugging difficulty.

## Proposed Changes

### 1. Building Handler Unification (`src/ai/states/town.py`)
Each building handler will be refactored to strictly enforce the separation of Sensory Ingestion from Tactical Planning.

- **Adventurer Guild**: 
    - **Remove**: `MindUpdate(goals_add=["Guild tip: ..."])`.
    - **Remove**: Immediate revealed terrain memory for "hints" (except for direct verified map data).
    - **Add**: Rich `LeadRecord` and `CandidateZoneRecord` via `ingest_guild_intel`.
- **Blacksmith**: 
    - **Remove**: Constructing action `reason` strings as a vehicle for AI state tracking.
    - **Add**: Full `BlockerRecord` reporting for all missing Materials and Gold requirements.
- **Inn**:
    - **Add**: Convert rumors into `LeadRecord` with `kind=LeadKind.EVENT` or `LeadKind.LOCATION`.
- **Home**:
    - **Add**: Formalize `BlockerRecord` for maintenance/rebuild requirements.

### 2. Strategic Ingestion Service Refinement (`src/core/logic/strategic_knowledge_ingestion.py`)
- **Ingestion Contracts**: Standardize return types for all `ingest_*` methods.
- **Source Provenance**: Ensure every record carries a `source_type` (e.g., "blacksmith_demand", "guild_observation") for future trust/bias weight calculation.

### 3. Detour Logic Hardening (`src/ai/strategy/detour_suggestion.py`)
- **Input Source**: Ensure the service *only* looks at the typed records in `StrategicState`.
- **Lead Matching**: Implement a lookup for `BlockerKind.MATERIAL` that finds relevant `LeadRecord` by `subject` ID or semantic tags.
- **Goal Migration**: The `DetourSuggestionService` becomes the sole engine for deriving "Detour Objectives". This removes the need for handlers to ever propose specific goal text.

### 4. Deterministic Cleaning
- **Prose Audit**: Sweep [ActionProposal](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/base.py) usages to ensure `reason` is never used for hidden state retrieval.
- **AOA Enforcement**: No build-side handler is permitted to Proposal-inject a `CurrentProject` change directly; they must only emit the `Blocker` and let the reasoning loop decide on the pivot.

## Verification Plan

### Automated Tests
- **Purity Scan**: New tests in `tests/test_building_unification.py` to verify handlers NO LONGER emit `goals_add`.
- **End-to-End Detour**: Verify an entity visits the Blacksmith, gets a `Blocker`, then in the next tick, visits the Guild, gets a `Lead`, and then correctly pivots to a `COLLECT` objective for that material.
- **Snapshot Isolation**: Ensure these new strategic structures deep-copy correctly.

### Manual Verification
- **CLI Inspector**: Verify total absence of "Guild tip" or "Need: ..." strings in the `mind.decision.goals` list after visiting buildings.
- **Replay Logs**: Verify that `StrategicUpdate` intents are correctly captured and reflected in the strategy summary.
