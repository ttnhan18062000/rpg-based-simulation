---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23A-QUEST-OPPORTUNITY
phase: open
date: 2026-06-20
tags: [quest-generation, pressure-driven, opportunity-type, world-emergence, phase-2]
---

# TCK-20260619-E23A-QUEST-OPPORTUNITY

## Title
Epic 2.3A · QuestOpportunity Model + Generator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`DynamicQuestSeedService` produces string-based opportunity kinds but no typed `QuestOpportunity` model exists. This ticket introduces the `QuestOpportunity` dataclass and `QuestOpportunityGenerator` that consumes world pressure signals (depletion, threat, unsatisfied needs) and emits typed opportunities.

**Blocks:** TCK-20260619-E23B-QUEST-LIFECYCLE, E23C, E23D

## Scope

### 1. Add `QuestOpportunity` dataclass to `src/core/models/quests.py`

```python
@dataclass(frozen=True, slots=True)
class QuestOpportunity:
    id: str                    # deterministic: f"{trigger_kind}_{source_id}_{tick}"
    kind: str                  # "resource_crisis" | "threat_response" | "diplomatic_errand"
    trigger_condition: str     # what caused this opportunity
    objective_chain: tuple     # ordered objective IDs (fetch X, eliminate Y, etc.)
    reward_spec: dict          # {"gold": int, "xp": int, "faction_rep": float}
    faction_source: str | None # faction offering the quest (None = world event)
    expiry_ticks: int          # tick at which this EXPIRES if not ACTIVE
    source_event_id: str | None  # RESOURCE_DEPLETED event that triggered this
```

### 2. Implement `QuestOpportunityGenerator` in `src/domains/world_emergence/services.py`

```python
class QuestOpportunityGenerator:
    """Converts world pressure signals into typed QuestOpportunity objects."""

    @staticmethod
    def from_resource_depleted(
        event: WorldEvent, tick: int, seed: int
    ) -> QuestOpportunity | None:
        """Generate a resource_crisis opportunity from a RESOURCE_DEPLETED event."""
        ...

    @staticmethod
    def from_threat_signal(
        threat_event: WorldEvent, tick: int, seed: int
    ) -> QuestOpportunity | None:
        """Generate a threat_response opportunity from a high-severity threat event."""
        ...

    @staticmethod
    def from_entity_need(
        entity_id: int, need_kind: str, ticks_unsatisfied: int, tick: int
    ) -> QuestOpportunity | None:
        """Generate a resource_crisis or diplomatic_errand from long-unsatisfied entity need."""
        ...
```

Three trigger families per epic:
- `resource_crisis`: triggered by `RESOURCE_DEPLETED` event (requires E21B)
- `threat_response`: triggered by high-severity combat/camp events
- `diplomatic_errand`: stub — generate but `reward_spec={"gold": 0, "xp": 0}` until Phase 5

### 3. Wire generator call into `WorldEmergencePhase`

In `src/domains/world_emergence/phase.py` (or `services.py`): after aggregating world events, call `QuestOpportunityGenerator` for each `RESOURCE_DEPLETED` event and append resulting `QuestOpportunity` to the phase output. Do not add to `quest_registry` here (that's E23B's job — read architecture rule: decision logic does not mutate durable state).

## Out of Scope
- quest_registry (E23B)
- Lifecycle state machine (E23B)
- Reward application (E23C)
- HERO routing (E23D)

## Acceptance Criteria
- `QuestOpportunity(id="rc_1_42", kind="resource_crisis", ...)` constructs without error
- Injecting a `RESOURCE_DEPLETED` event into `QuestOpportunityGenerator.from_resource_depleted()` returns a non-None `QuestOpportunity` with `kind="resource_crisis"`
- Same input + same seed → same `QuestOpportunity.id` (determinism)
- `test_resource_crisis_quest_generated_on_depletion` passes
- `test_quest_generation_determinism` passes

## Related Tickets
- TCK-20260619-E23-QUEST-GENERATION (parent epic)
- TCK-20260619-E21B-REGEN-SERVICE (prerequisite: provides RESOURCE_DEPLETED events)
- TCK-20260619-E23B-QUEST-LIFECYCLE (blocked on this)

## Related Code Areas
- `src/core/models/quests.py` (add QuestOpportunity dataclass)
- `src/domains/world_emergence/services.py` (add QuestOpportunityGenerator; DynamicQuestSeedService is reference pattern)
- `src/domains/world_emergence/phase.py` (wire generator into phase output)
- `tests/unit/quest/test_quest_generation.py` (extend with new tests)

## Assumptions / Open Questions
- Does `WorldEmergencePhase.run()` return typed outputs or mutation directly? Check `src/domains/world_emergence/phase.py` — if it returns typed outputs, `QuestOpportunity` can be part of that return. If it mutates, design needs to stay read-only here (pass opportunities up to the apply path).
- What fields does `DynamicQuestSeedService.produce()` actually return? Read the method before designing `QuestOpportunityGenerator`.
- Is there an existing `entity_need` pressure signal, or does the generator need to scan entity states for unsatisfied needs? Scope to resource + threat triggers for now; entity-need trigger is optional.

## Implementation Notes
- `QuestOpportunity.id` must be deterministic: `f"{kind}_{source_event_id}_{tick % 10000}"` or similar. Do not use `uuid()`.
- `objective_chain` is a tuple of strings for now (e.g. `("fetch:iron_ore:3",)` or `("eliminate:goblin:5",)`). Full structured objectives are Phase 4.
- `diplomatic_errand` stub: set `reward_spec={}` and `faction_source="stub"` — do not implement logic.
- Do NOT import `QuestOpportunity` inside `execute_brain()` or any hot-path simulation code.

## Test Summary
```bash
pytest tests/unit/quest/test_quest_generation.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
