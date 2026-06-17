---
status: archive
authority: P2
audience: historical
layer: misc
original_date: 2026-05-01
---

# RPG Core Migration Design: Phases 6 & 7

**Date**: 2026-05-01
**Topic**: Strategic Cognition & Social Contract Lifecycle
**Status**: APPROVED

## Overview
This spec outlines the migration of legacy RPG core logic for **Strategic Cognition (Phase 6)** and **Social Contracts (Phase 7)** into the authoritative V2 engine. The goal is to enable complex social interactions (recruitment, parties, negotiation) and intelligent strategic behavior (learning from failure, project abandonment) while maintaining the V2 engine's principles of determinism and typed state updates.

## 1. Social Contract Lifecycle (Phase 7)

### 1.1 Model: Individual Agency with Leadership Influence
Characters retain their autonomy but are influenced by group goals.

### 1.2 Components
- **`ContractAppraisalSystem`**:
    - **Purpose**: Evaluate `OFFERED` contracts.
    - **Inputs**: Personality (Greed, Courage), Social Bonds (Trust, Loyalty, Debt), and Biological state (HP, Hunger).
    - **Logic**: Calculate an `AcceptanceScore`. If score > threshold, status becomes `ACCEPTED`.
- **`ContractNegotiationSystem`**:
    - **Purpose**: Manage `COUNTERED` offers.
    - **Logic**: Recruiter evaluates counter-offers using project urgency and relationship quality. Max 2 rounds of negotiation.
- **`PartyCoordinationSystem`**:
    - **Approach**: Weighted Goal Scoring.
    - **Logic**: In `evaluate_strategic_intent`, if an entity is in a group, the Leader's active objective is injected as a goal candidate with a `Leadership_Weight` boost (+25 utility).
    - **Overrides**: Survival needs (HP < 20%) or critical personal concerns can still override the party objective if their utility exceeds the boosted party score.

## 2. Strategic Cognition Lifecycle (Phase 6)

### 2.1 Strategic Memory (Lead Suppression)
- **Mechanism**: Leads track a `failure_count`.
- **Suppression**: If a lead fails repeatedly, it is marked with a `suppression_until_tick` timestamp.
- **Evaluation**: `evaluate_strategic_intent` ignores suppressed leads during candidate selection.

### 2.2 Project Abandonment
- **Mechanism**: Projects track failed attempts.
- **Transition**: After 3 failures, project status becomes `ABANDONED`.
- **Penalty**: Generates a "Frustration" penalty for that project kind, reducing its future utility for a set duration.

### 2.3 Enhanced Blocker Inference
- **Social Blockers**: Identify when an objective requires additional party members (e.g., "Missing Specialist").
- **Trigger**: Social blockers trigger the **Recruitment Loop** in the next strategic pass.

## 3. Data Flow & Integration
- **State Updates**: All contract changes and strategic shifts are emitted as `StrategicUpdate` objects.
- **Social Bonds**: Contract outcomes (success/failure/betrayal) emit `SocialBondUpdate` records to `RelationshipService`.
- **Authoritative Gate**: The `AuthoritativeApplyPipeline` remains the singular point of application for these updates.

## 4. Verification Plan
### 4.1 Unit Tests
- `tests/social/test_appraisal.py`: Prove trust/greed affects acceptance.
- `tests/strategy/test_memory.py`: Prove failed leads are suppressed.

### 4.2 Integration Tests
- `tests/systems/test_social_contract_lifecycle.py`: End-to-end recruitment -> execution -> reward.
- `tests/systems/test_strategic_loop_complex.py`: Proves project abandonment and detour recursion.
