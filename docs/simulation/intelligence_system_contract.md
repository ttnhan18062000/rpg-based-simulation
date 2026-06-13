---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Intelligence System Contract

**Source:** `src/systems/strategic_systems/intelligence.py` (StrategicIntelligenceSystem, 1,332 lines)
**Related docs:** [belief_and_detour_contract.md](belief_and_detour_contract.md), [docs/simulation/domains/information_contract.md](domains/information_contract.md), [docs/strategy/bounded_cognition_contract.md](../strategy/bounded_cognition_contract.md)

---

## Purpose

`StrategicIntelligenceSystem` is the central strategic decision engine for entities. It does NOT store or retrieve world knowledge — that is `src/cognition/knowledge_model.py`. It orchestrates the **full strategic lifecycle**: evaluating concerns and intents, managing project switching, inferring blockers from failures, triggering detours, and enforcing the entity's cognition profile limits.

### Precise distinction: intelligence vs knowledge model

| Layer | File | What it does |
|---|---|---|
| **StrategicIntelligenceSystem** | `intelligence.py` | Strategic decision logic: project lifecycle, blocker inference, project switching with interruption resistance, detour suggestion, cognition profile enforcement |
| **KnowledgeModelService** | `src/cognition/knowledge_model.py` | Factual world knowledge: resource locations, region threats, entity positions — with freshness timestamps and capacity limits |
| **BeliefCycleSystem** | `belief.py` | Certainty lifecycle of individual beliefs: rumors vs observations, contradiction degradation, staleness decay |

An agent asking "what does an entity know about region X?" → knowledge_model.py.
An agent asking "why did an entity switch projects?" → intelligence.py.
An agent asking "how certain is the entity about a lead?" → belief.py.

---

## Core responsibilities

### 1. Blocker inference — `infer_blockers()`

Logic IDs: STRAT-191–STRAT-194

Produces `BlockerState` records from recent failures:
- Navigation failure → NAVIGATION_BLOCKED blocker (target region inaccessible)
- Task failure (craft/gather/combat) → RESOURCE_BLOCKED or SKILL_BLOCKED blocker
- Repeated failures (same task ≥ 3 times) → PERSISTENT_BLOCKED flag

Each blocker has: `kind`, `subject` (what is blocked), `reference` (failed target), `severity`, `origin` (project that spawned it).

### 2. Strategic intent evaluation — `evaluate_all_strategic_intents()`

Logic IDs: STRAT-148, STRAT-149

Evaluates all possible strategic objectives and projects against current entity state. Returns a scored list of intents. The highest-scoring intent that passes interruption resistance becomes the new project if project-switching is warranted.

### 3. Project switching — `evaluate_project_switch()`

Applies **interruption resistance**: the current project gets a retention priority bonus. Switching only happens if the alternative intent scores exceed the current project score by more than the interruption resistance margin (from `CognitionProfile.interruption_resistance`). This prevents constant project-flipping under volatile conditions.

### 4. Full strategic pass — `fused_strategic_pass()`

The primary entry point. Runs the full evaluation sequence:
1. Process recent outcomes (`process_project_outcome()`)
2. Resolve active objectives (`_resolve_active_objective()`)
3. Evaluate all concerns (`evaluate_all_concerns()`)
4. Evaluate strategic intents (`evaluate_all_strategic_intents()`)
5. Apply routine biasing (`apply_routine_biasing()`)
6. Trigger detour suggestions (via `DetourSuggestionSystem`)
7. Enforce belief cycle decay (via `BeliefCycleSystem.decay_stale_beliefs()`)

Returns a `StrategicUpdate` with the net result of all evaluations.

### 5. Project resumption — `resume_project()`

Resumes a previously paused project after a detour or interruption. Restores the project to active status and re-sets current_project_id.

### 6. Cognition profile enforcement — `derive_cognition_profile()`

Reads the entity's class and state to derive a `CognitionProfile` (from `src/core/strategic.py`). Profile fields cap strategic behavior:
- `interruption_resistance`: how hard it is to switch projects mid-execution
- `detour_breadth`: max detour suggestions considered
- `detour_depth`: max nesting level of detour-within-detour
- `lead_capacity`: max concurrent leads tracked

---

## Inputs

- `entity.strategic`: leads, blockers, hypotheses, beliefs, projects, objectives, concerns, profile
- `entity.identity`: class_id, level, attributes
- `state`: full `AuthoritativeState` (read-only view)
- Recent outcomes: last_task, last_payload, navigation_failure (from tick event log)

---

## Outputs

Returns `StrategicUpdate` carrying: leads_add_or_update, blockers_add_or_update, hypotheses_add_or_update, beliefs_add_or_update, projects_add_or_update, objectives_add_or_update, current_project_id_set.

Does NOT mutate state directly (Logic ID: STRAT-002).

---

## Relationship to other systems

- Calls `DetourSuggestionSystem` (detour.py) to generate detour candidates from blockers+leads
- Calls `BeliefCycleSystem` (belief.py) to decay stale beliefs
- Reads from `CapacityService` (`src/strategy/cognition_capacity.py`) to enforce lead/blocker capacity limits
- Reads from `GoalRegistry` (`src/ai/goals.py`) for goal scoring weights
- Reads from `ScoreModifierSystem` (`src/ai/score_modifiers.py`) for situational score adjustments
- Called by `StrategicRedirectionSystem` (redirection.py) for enforced project changes

---

## Regression tests

- `tests/integration/test_strategic_intelligence.py` — blocker inference, project switching with interruption resistance
- `tests/unit/test_strategic_blocker_inference.py` — blocker kind/severity/origin correctness
- `tests/unit/test_cognition_profile.py` — profile derivation, capacity enforcement

---

## Extension rules

1. To add a new blocker kind: add to `BlockerState.kind` enum, add inference logic in `infer_blockers()`, add tests verifying blocker attributes (STRAT-191–STRAT-194 compliance).
2. To add a new strategic intent type: add scoring in `evaluate_all_strategic_intents()`, add a project mapper for the new intent, add a test verifying it can outcompete the current project under appropriate conditions.
3. Never add world-knowledge storage here — any factual information the entity learns about the world goes into `src/cognition/knowledge_model.py`.
4. `fused_strategic_pass()` must remain the single entry point — do not add additional external callers that skip steps in the sequence.
