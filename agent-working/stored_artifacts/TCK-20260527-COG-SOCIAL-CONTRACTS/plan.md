---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-SOCIAL-CONTRACTS
artifact_type: plan
tags: [cog, social, contracts]
---

# Implementation Plan: TCK-20260527-COG-SOCIAL-CONTRACTS

## Goal
Integrate social contracts (Loan and Recruitment) into the authoritative simulation pipeline and strategic projects.

## Proposed Changes

### 1. `src/engine/pipeline.py`
- Import `ContractService` and wire `process_active_contracts` and `reap_expired_offers` into Phase 7 (final integrity and cognitive resolution).

### 2. `src/systems/social_systems/contracts.py`
- Modify `ContractService.accept_contract` to construct a corresponding `ProjectState` and `ObjectiveState` for active contracts (`RECRUITMENT` / `LOAN`) and add them to the strategic update.

### 3. `tests/unit/strategic/test_social_contracts.py`
- Write a test suite verifying that contract acceptance correctly spawns active projects/objectives, failed outcomes degrade trust, and betrayal history blocks future contract acceptance.
