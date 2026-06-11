---
status: active
layer: strategy
authority: P1
audience: developer
---

# Spec: Phase 1 — World Capability Foundation Design Document

This design document outlines the technical implementation strategy for **Phase 1 — World Capability Foundation**. The objective is to establish a robust, performant, and TDD-backed layer that exposes structured options (opportunities, query providers, requirements) so that entities can intelligently plan their lifepaths in subsequent phases.

---

## 1. Context Exploration & System Comparison

### 1.1 Existing Entity Aspect Mappings
We compare our planned Phase 1 components with the current architecture detailed in `docs/entity/entity_base.md` and `docs/entity/entity_aspect_relationship_diagram.mmd`:

*   **State Aggregates**: Currently, the `EntityState` includes `StrategicComponent` (active projects, objectives, leads, blockers) and `SocialComponent` (trust, debt, contracts). However, these are purely *local mental state representations*.
*   **The Mismatch**: Currently, the *World* (`AuthoritativeState`) does not expose structured options (e.g. "What resources can I harvest near me that will satisfy my blocker?"). The entity has to search the entire world manually or fall back to ad-hoc, hardcoded logic.
*   **The Bridge**: Phase 1 introduces read-only *World Registries* and *State-Free Providers* (Requirement, Information, and Opportunity Providers). This decouples the entity's mental state from direct world-state scanning, routing all options through structured interface objects.

---

## 2. Collaborative Design & Implementation Strategy

### Task 1 — Scenario-driven TDD Harness
*   **Goal**: Ensure we can prove high-level route-family behavior before implementing production logic.
*   **Design**:
    *   **Scenario Specification**: Define Pydantic models for `ScenarioSpec` loaded from YAML.
    *   **Deterministic Simulation Runner**: Execute ticks synchronously under exact seed constraints, capturing all state transitions.
    *   **Scorecard Generator**: Compare execution traces against `valid_route_families` and `forbidden_behavior` definitions, generating a `scenario_scorecard.json`.

### Task 2 & 3 — Content Pack & Data Registries
*   **Goal**: Define a compact but rich adventure data set (`wood`, `iron_ore`, `rusted_sword`, `wolf`, etc.) and register them cleanly.
*   **Design**:
    *   **Registry Classes**: Add `ItemRegistry`, `ResourceRegistry`, `EnemyRegistry`, `RecipeRegistry`, and `ServiceRegistry` as static, read-only caches.
    *   **Validation Rules**: Add startup asserts ensuring that all recipe ingredients, enemy loot items, and service locations refer to valid IDs in the registries.
    *   **Clean Code Application**: Group data structures into raw dataclasses (DTOs) under `src/core/registries.py` to keep data decoupled from logic.

### Task 4 — Requirement Evaluator
*   **Goal**: A generic, modular system to evaluate why actions are blocked, turning failures into structured `BlockerState` candidates.
*   **Design**:
    *   **Evaluator Logic**: Small, highly cohesive pure functions that accept `EntityState`, `AuthoritativeState`, and a typed `Requirement` object.
    *   **Evaluation Engine**: Evaluates constraints (`has_gold`, `has_item`, `knows_fact`, `near_service`, `inventory_space`, `target_alive`) and returns a structured `RequirementResult`.

### Task 5 — Scoped Information Provider
*   **Goal**: Entities must ask scoped information sources (guide, guild, blacksmith) rather than magically accessing global truth.
*   **Design**:
    *   **Guide Provider**: Exposes resource region locations based on active queries. Can return a partial answer (e.g., suggesting a research lead for secret materials like `moon_resin` instead of the exact coordinate).
    *   **Guild Provider**: Exposes active quest boards and danger limits.
    *   **Blacksmith Provider**: Exposes crafting recipe costs and item requirements.

### Task 6 & 7 — Opportunity Providers (Resource & Service)
*   **Goal**: Expose a bounded list of nearby visible node opportunities and service options relative to the entity's active blockers and goals.
*   **Design**:
    *   **Scope & Caps**: Cap returned options (e.g. maximum 5 opportunities per evaluation) to prevent full-world scanning.
    *   **Structure**: Return structured `Opportunity` objects detailing estimated rewards, risks, and required conditions.

### Task 8 — Action Intent Adapter
*   **Goal**: Adapt strategic options into the existing mechanical execution pipelines without refactoring `ActionRouter` or service loops.
*   **Design**:
    *   **Adapter Pattern**: Introduce `ActionIntent` representing actions like `MOVE_TO`, `BUY_ITEM`, `REQUEST_CRAFT`, and `HARVEST_RESOURCE`.
    *   **Execution Delegate**: Safely translate intents into corresponding `StateUpdate` or `ResourceTransferIntent` applications.

### Task 9 — Route-Family Classifier
*   **Goal**: Group raw mechanical actions into narrative-friendly "Route Families" (`buy_upgrade`, `craft_upgrade`, `defer_with_reason`) for scenario verification.
*   **Design**:
    *   Consumes the execution trace log and runs deterministic trace rule mappings to classify the active lifepaths followed by the adventurer.

### Task 10 — Performance Budget Gates
*   **Goal**: Protect the simulation loop from excessive provider call overhead.
*   **Design**:
    *   Add transaction-level metric counters (`provider_calls_total`, `requirements_evaluated_total`).
    *   Add scaling scenario benchmarks (10, 30, and 100 entities) asserting bounded tick latencies.

---

## 3. High-Level Recommendation

We recommend proceeding with a **TDD-First, highly modular approach**:
1. Implement the YAML loaders and TDD scenario runner first.
2. Define the exact registries and load our initial `phase1_adventure_seed` pack.
3. Write the 5 failing scenario YAML specifications.
4. Implement the `RequirementEvaluator` and opportunity providers to make the scenarios pass one by one.
