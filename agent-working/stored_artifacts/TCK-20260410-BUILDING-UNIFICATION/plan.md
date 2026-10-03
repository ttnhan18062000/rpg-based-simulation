---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260410-BUILDING-UNIFICATION
artifact_type: plan
tags: [building, unification]
---

# Implementation Plan: TCK-20260410-BUILDING-UNIFICATION

Execute [Improvement Phase 2] to standardize building handlers and decision logic. Unify all town-based detour navigation through the strategic stratum.

## User Review Required

> [!IMPORTANT]
> This refactor shifts building visit decisions from "Raw State Assessment" to "Strategic Blocker Resolution". It effectively deprecates ad-hoc goal strings in favor of `BlockerRecord` and `LeadRecord`.

## Proposed Changes

### Strategic Decision Logic

#### [MODIFY] [town.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/town.py)
Standardize `hero_should_visit_*` helpers to check the strategic state instead of raw inventory/identity flags.
- `hero_should_visit_blacksmith`: Check for active `BlockerKind.MATERIAL`.
- `hero_should_visit_guild`: Check for `BlockerKind.KNOWLEDGE` or missing map intel.
- `hero_should_visit_class_hall`: Check for `BlockerKind.CAPABILITY`.
- `hero_should_visit_home`: Check for `BlockerKind.ACCESS`.
- Ensure handlers return `StrategicUpdate` for all outcomes.

#### [MODIFY] [detour_suggestion.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategy/detour_suggestion.py)
Hardening Lead Matching and Objective Derivation.
- Unify objective labels and priority calculations.
- Ensure `evidence_refs` correctly links back to the matching `LeadRecord`.

---

### Ingestion Hardening

#### [MODIFY] [strategic_knowledge_ingestion.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/strategic_knowledge_ingestion.py)
Harden ingestion contracts for building failures and results.
- Standardize stable `blocker_id` generation across all building types to prevent duplicate blockers.

## Verification Plan

### Automated Tests
- `pytest tests/test_building_unification.py`
- Verify that `ActionProposal.updates` contains `StrategicUpdate` but zero `MindUpdate(goals_add)`.

### Manual Verification
- Use CLI Inspector to verify that an entity with a Material Blocker correctly matches a Material Lead and generates a detour objective.
