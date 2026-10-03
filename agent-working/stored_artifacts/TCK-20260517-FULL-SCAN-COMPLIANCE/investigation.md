---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-FULL-SCAN-COMPLIANCE
artifact_type: investigation
tags: [full, scan, compliance]
---

# Milestone 2: Full-Scan Phase Compliance Investigation

## 1. Background & Parity Contract

`StateUpdate` contains a `force_full_scan` boolean flag. In an authoritative simulation pipeline, when `force_full_scan=True` is enabled, or when `dirty_set` is empty/missing under full-scan mode, every simulation phase must fallback to scanning all active state entities rather than narrowing by `dirty_set`.

## 2. Existing Behavior Analysis

We investigated the codebase for all target phases:
1. `InteractionPhase.route_interaction_intent`: Calls `get_relevant_entity_ids(state, update, "interactions")`. When `force_full_scan=True`, `get_relevant_entity_ids` returns `set(state.entities.keys())`.
2. `MovementPhase`: Directly iterates `state.entities` and `refined_entity_updates` without querying `dirty_set`.
3. `StrategicIntelligenceSystem`: Iterates `state.entities`.
4. `ShopSystem.enforce`: Calls `get_relevant_entity_ids(state, update, "shop")`.
5. `CapacityEnforcementPhase.enforce`: Calls `get_relevant_entity_ids(state, update, "capacity")`.
6. `LifecycleSystem.resolve_lifecycle`: Iterates `state.entities`.

## 3. Findings

All 6 core phases already contain the architectural mechanisms to honor full-scan mode. However, there is no explicit integration test suite that proves this contract in isolation across all phases when `dirty_set=DirtySet()`. Creating this test suite will provide an immutable CI regression guard.
