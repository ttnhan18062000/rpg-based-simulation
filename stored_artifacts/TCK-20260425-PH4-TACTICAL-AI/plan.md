---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH4-TACTICAL-AI
artifact_type: plan
tags: [ph4, tactical, ai]
---

# Implementation Plan: Tactical AI and Capacity Hardening

## Goal
Restore role-based tactical behavior and enforce cognitive capacity limits in the V2 engine.

## Proposed Changes

### Core
- Add `tactical_role` to `CombatComponent`.
- Update `V2EntityBuilder` to support fluent role assignment.

### Engine
- Update `TacticalDecisionSystem` to support `SKIRMISHER` (kiting) and `VANGUARD` (closing) logic.

### Systems
- Update `StrategicIntelligenceSystem` to check `CognitionProfile` limits before proposing new projects.

## Verification
- `tests/parity/test_tactical_roles.py`
