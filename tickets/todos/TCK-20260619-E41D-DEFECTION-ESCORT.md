---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41D-DEFECTION-ESCORT
phase: open
date: 2026-06-20
tags: [party, defection, betrayal, escort, route-scoring, phase-4]
---

# TCK-20260619-E41D-DEFECTION-ESCORT

## Title
Epic 4.1D · Defection Mechanics + Escort Behavior

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No defection or escort mechanics exist. This ticket implements `betrayal_desertion` events when entity grievance exceeds threshold, and escort route-scoring adjustments for entities protecting an ESCORT_TARGET group member.

**Requires:** TCK-20260619-E41C-REWARD-DIST

## Scope

### Defection

In `PartyLifecycleService.check_defection()`:
- Threshold: `GroupRecord.grievance_log` length ≥ 3 (3 unresolved grievances)
- On defection: emit `betrayal_desertion` SimulationEvent; remove entity from group.member_ids via `GroupUpdate`; apply `SocialUpdate(reputation_delta={entity_id: -2.0})`

### Escort Behavior

In `src/domains/adventure/scoring.py` (`AdventureRouteScorer`):
```python
# In score() method, after base score computed:
if entity_group and entity_group.escort_target_id and entity_id != entity_group.escort_target_id:
    if route.family == RouteFamily.PROTECT_TARGET:
        score += 3.0   # urgency bonus
    elif route.family == RouteFamily.OWN_SURVIVAL:
        score -= 1.0   # deprioritize own survival vs. protecting target
```

Add `PROTECT_TARGET` to `RouteFamily` enum if not already present (check `src/domains/adventure/scoring.py` for enum definition before adding).

After E41D: create `docs/simulation/domains/party_contract.md`. Run `make knowledge-index-update`.

## Acceptance Criteria
- `test_betrayal_desertion_fires_on_high_grievance` passes
- `test_escort_target_route_scores_above_survival` passes
- Integration: 600-tick run produces ≥1 party event in NarrativeLedger

## Related Tickets
- TCK-20260619-E41-PARTY-LOOP (parent epic)
- TCK-20260619-E41C-REWARD-DIST (required)

## Related Docs
- `docs/simulation/domains/party_contract.md` (new — create after implementation)
- `docs/mechanics/04_strategic_cognition.md` (update route scoring terms)

## Related Code Areas
- `src/systems/social_systems/party_lifecycle.py` (add check_defection)
- `src/domains/adventure/scoring.py` (add PROTECT_TARGET scoring)
- `src/observability/events.py` (add betrayal_desertion event kind)

## Test Summary
```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
pytest tests/integration/scenarios/test_party_lifecycle.py -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
