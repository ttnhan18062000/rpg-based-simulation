---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260529-COG-PHASE12-PERCEPTION
phase: done
date: 2026-05-29
tags: [cog, phase12, perception]
---

# TCK-20260529-COG-PHASE12-PERCEPTION

## Title

Perception and Attention Domain Implementation

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the Phase 12 Perception and Attention Domain. This prevents entity omniscience by scoring world signals through salience and filtering them based on attention focus and bounded capacity.

## Scope

- Define the schemas: `PerceivedEntity`, `PerceivedResource`, `PerceivedService`, `PerceivedThreat`, `PerceivedOpportunity`, `IgnoredSignal`, and the full `PerceptionModel`.
- Implement `AttentionFocusService` to dynamically determine what an entity is biased to notice based on dominant need, active project, and emotions.
- Implement `SignalSalienceEvaluator` to score candidates based on relevance, danger, novelty, and distance.
- Implement `PerceptionFilterService` to apply capacity limits and perception budgets.
- Integrate into a simulation Perception Update Phase inside the authoritative pipeline loop.
- Establish comprehensive unit, integration, and scenario tests under `tests/`.

## Out of Scope

- Visional cone geometry, stealth/sneak systems, visual occlusion raycasting.

## Acceptance Criteria

- `PerceptionModel` fully defined under `src/core/cognition.py`.
- `AttentionFocusService`, `SignalSalienceEvaluator`, and `PerceptionFilterService` implemented and verified.
- Entities dynamically filter and prioritize signals based on condition (e.g. low HP focuses on healing).
- All unit, integration, and scenario tests pass.

## Related Tickets

- `TCK-20260529-COG-PHASE11-HIERARCHY`

## Related Docs

- `docs/entity/entity_base.md`

## Related Code Areas

- `src/domains/perception/` (created)
- `src/core/cognition.py`
- `tests/unit/entity/test_phase12_perception_model.py` (created)
- `tests/unit/domains/perception/` (created)
- `tests/integration/domains/perception/` (created)
- `tests/integration/scenarios/test_phase12_perception_attention_scenarios.py` (created)

