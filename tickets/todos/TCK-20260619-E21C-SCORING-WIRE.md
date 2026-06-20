---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21C-SCORING-WIRE
phase: open
date: 2026-06-20
tags: [resource-ecology, adventure-scoring, cognition, phase-2]
---

# TCK-20260619-E21C-SCORING-WIRE

## Title
Epic 2.1C · Depletion-Aware Adventure Route Scoring

## Status
OPEN

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
- Does `AdventureRouteScorer.score()` have access to `state.resource_nodes`, or does it receive a pre-computed route object? Inspect `src/domains/adventure/scoring.py` to find how `expected_benefit` is currently computed and what state is available.
- Does the route object for `GATHER_RESOURCE` carry `target_node_id`? Verify field name in `src/domains/adventure/` schemas.

## Implementation Notes
- If `state.resource_nodes` isn't directly available in `score()`, it may be passed as part of the `WorldSnapshot` or similar. Read the method signature before implementing.
- Guard against `max_charges == 0` (division by zero) with `if target_node.max_charges > 0`.
- Guard against missing node (`target_node is None`) — skip depletion scaling if node not found.
- After implementation: update `docs/mechanics/04_strategic_cognition.md` §6.2 to document `depletion_fraction` modifier. Update parity ledger `docs/parity_ledger/strategic_cognition.yaml` STRAT-227 if it describes the `benefit` term.
- Run `make knowledge-index-update` if docs/ changed.

## Test Summary
New file `tests/unit/domains/adventure/test_depletion_scoring.py`:
```bash
pytest tests/unit/domains/adventure/test_depletion_scoring.py -x -v
# Existing scoring tests must not regress
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
