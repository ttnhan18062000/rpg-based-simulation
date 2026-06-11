---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: enhance-01
artifact_type: test_plan
tags: [enhance]
---

# Test Plan: Enhance 01 

## Scope
Validate that the introduction of the decoupled `EventBus` successfully generates cleanly formatted dictionaries in the final API JSON endpoints, and that no logic loops are broken during the refactor.

### 1. Engine Consistency Tests (Red Phase)
- **Objective:** Modify existing E2E simulation tests to assert that `EventLog` items correctly contain non-null `metadata` dictionaries during combat scenarios.
- **Verification:** Run `pytest tests/e2e/`.

### 2. Unit Testing the Pub/Sub Telemetry Bridge
- **Objective:** Directly instantiate the new `EventSystem`, manually publish artificial `CombatStruckEvents`, and assert that the Translator accurately formats the human-readable string using the entity registry.
- **Verification:** Asserts that `"Hero strikes Goblin for 15 damage"` works precisely when the exact inputs are provided.

### 3. API Schema Integrity
- **Objective:** Leverage `tests/e2e/test_production_stack.py` to pull `/api/world/state` after a tick and assert that the `GameEventSchema` successfully parses the new `metadata` payloads without Pydantic validation errors.
