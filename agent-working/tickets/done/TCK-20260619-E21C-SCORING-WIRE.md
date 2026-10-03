---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21C-SCORING-WIRE
phase: done
date: 2026-06-20
tags: [resource-ecology, adventure-scoring, cognition, phase-2]
---

# TCK-20260619-E21C-SCORING-WIRE

## Title
Epic 2.1C · Depletion-Aware Adventure Route Scoring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`AdventureRouteScorer.score()` computes `expected_benefit` independently of node charge state. Entities route toward depleted nodes as eagerly as full ones. This ticket adds a depletion fraction multiplier to `expected_benefit` for `GATHER_RESOURCE` routes.

**Requires:** TCK-20260619-E21B-REGEN-SERVICE (depletion state must exist in `ResourceNodeState`)

## Scope

### Change in `src/domains/adventure/scoring.py`

For `GATHER_RESOURCE` route family: before applying `benefit` in the scoring formula, multiply by a depletion fraction:

```python
# After identifying the target node_id for a GATHER_RESOURCE route:
target_node = state.resource_nodes.get(route.target_node_id)
if target_node is not None and target_node.max_charges > 0:
    depletion_fraction = target_node.remaining_charges / target_node.max_charges
    # Scale benefit: empty node → 0 benefit, full node → full benefit
    benefit = benefit * depletion_fraction
```

The scoring formula (per Mechanics Bible Chapter 04 §6) is:
```
score = urgency + benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty
```

`benefit` is the `expected_benefit` term. Multiplying by `depletion_fraction` linearly reduces it from full (charges == max) to zero (charges == 0).

**This must not affect other route families.** Only `GATHER_RESOURCE` routes read node charge state.

## Out of Scope
- Scoring changes for non-harvest routes
- Making entities proactively seek full nodes over depleted ones via a different mechanism

## Acceptance Criteria
- `AdventureRouteScorer.score()` for a `GATHER_RESOURCE` route to a depleted node (`remaining_charges=0`) returns score ≤ score for same route to full node of same type
- Specifically: depleted score ≤ 0.5 × full score when `remaining_charges = max_charges / 2`
- Non-harvest route scores are unchanged
- `tests/unit/domains/adventure/test_depletion_scoring.py` passes

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (parent epic)
- TCK-20260619-E21B-REGEN-SERVICE (required first — provides depletion state)
- TCK-20260619-E12C-BALANCE-TESTS (existing scoring tests must not regress)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §6 (scoring formula — add depletion_fraction note under §6.2)
- `docs/parity_ledger/strategic_cognition.yaml` (check STRAT-227 — update if benefit term semantics change)

## Related Code Areas
- `src/domains/adventure/scoring.py` (AdventureRouteScorer.score — modify benefit computation for GATHER_RESOURCE)
- `tests/unit/domains/adventure/test_phase3_route_scoring.py` (existing tests — must pass after change)
- `tests/unit/domains/adventure/test_depletion_scoring.py` (new test file)

## Assumptions / Open Questions
- Does `AdventureRouteScorer.score()` have access to `state.resource_nodes`, or does it receive a pre-computed route object? **RESOLVED:** scorer receives `resource_nodes` as an optional parameter threaded from `AdventureDecisionPhase`.
- Does the route object for `GATHER_RESOURCE` carry `target_node_id`? **RESOLVED:** added `target_node_id: Optional[int] = None` to `AdventureRouteOption`; set in generator from `opp.target_id`.

## Implementation Notes
- Added `target_node_id: Optional[int] = None` to `AdventureRouteOption` (schema.py) — backward-compatible frozen dataclass addition.
- Generator (`generator.py`) now sets `target_node_id = int(opp.target_id)` for `gather_resource` opportunities only.
- `AdventureRouteScorer.score()` accepts optional `resource_nodes: Optional[Dict[int, ResourceNodeState]] = None`; applies `benefit *= depletion_fraction` for GATHER_RESOURCE when node found and `max_charges > 0`.
- `AdventureDecisionService.decide()` gains matching optional `resource_nodes` parameter and threads it to scorer.
- `AdventureDecisionPhase.apply()` passes `state.resource_nodes` to `decide()`.
- All guards implemented: `resource_nodes is not None`, `node_id is not None`, `target_node is not None`, `max_charges > 0`.
- `docs/mechanics/04_strategic_cognition.md` §6.2 updated with depletion_fraction table and §6.2.1 subsection.
- STRAT-227 parity ledger updated with new v2_evidence and test_path.

## Test Summary
- 6 new tests in `tests/unit/domains/adventure/test_depletion_scoring.py` — all passing
- 7 existing tests in `tests/unit/domains/adventure/test_phase3_route_scoring.py` — all passing
- Full adventure domain: 32/32 passing

## Files Changed
- `src/domains/adventure/schema.py` — added `target_node_id: Optional[int] = None` to `AdventureRouteOption`
- `src/domains/adventure/generator.py` — set `target_node_id` from `opp.target_id` for `gather_resource`
- `src/domains/adventure/scoring.py` — added `resource_nodes` param; depletion_fraction logic for GATHER_RESOURCE
- `src/domains/adventure/service.py` — threaded `resource_nodes` through `decide()`
- `src/domains/adventure/phase.py` — passes `state.resource_nodes` to `decide()`
- `tests/unit/domains/adventure/test_depletion_scoring.py` — new test file (6 tests)
- `docs/mechanics/04_strategic_cognition.md` — §6.2 updated, §6.2.1 added
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 updated

## Completion Summary
Wired depletion-aware scoring into the adventure route pipeline. Added `target_node_id` to `AdventureRouteOption` schema and populated it in the generator for `gather_resource` opportunities. Extended `AdventureRouteScorer.score()` with an optional `resource_nodes` parameter that applies `benefit × (remaining_charges / max_charges)` for GATHER_RESOURCE routes, reducing routing attractiveness proportionally to node depletion. Threaded state through the phase→service→scorer call chain with backward-compatible defaults. All 6 AC tests pass; 32 adventure domain tests green; Mechanics Bible §6.2 and parity ledger STRAT-227 updated.
