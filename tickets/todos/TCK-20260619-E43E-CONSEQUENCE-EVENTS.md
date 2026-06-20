---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43E-CONSEQUENCE-EVENTS
phase: open
date: 2026-06-20
tags: [social-memory, consequence-events, legendary-arrival, known-traitor, phase-4]
---

# TCK-20260619-E43E-CONSEQUENCE-EVENTS

## Title
Epic 4.3E · Social Memory Consequence Events

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Social memory has no runtime expression unless consequence events fire when relevant entities meet. This ticket adds `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED` events wired into the social encounter evaluation.

**Requires:** TCK-20260619-E43C-DECAY and TCK-20260619-E43D-FACTION-MEMORY

## Scope

Add to `src/observability/events.py`:
```python
LEGENDARY_ARRIVAL = "LEGENDARY_ARRIVAL"      # entity rep ≥ 0.9 enters faction territory
KNOWN_TRAITOR_SPOTTED = "KNOWN_TRAITOR_SPOTTED"  # traitor entity enters hostile faction territory
OLD_DEBT_COLLECTED = "OLD_DEBT_COLLECTED"    # entity fulfills prior-episode obligation
```

In the social encounter phase (find where entity-NPC encounter evaluations happen):
```python
def evaluate_social_consequence(entity: EntityState, faction_id: str, campaign_state: CampaignState) -> list[SimulationEvent]:
    events = []
    faction_mem = campaign_state.faction_social_memories.get(faction_id)
    if faction_mem and faction_mem.entity_hostility.get(entity.id, 0.0) > 3.0:
        events.append(SimulationEvent(kind="KNOWN_TRAITOR_SPOTTED", ...))
    # check reputation ≥ 0.9 for LEGENDARY_ARRIVAL
    ...
    return events
```

After E43E: create `docs/simulation/domains/social_memory_contract.md`. Update `docs/simulation/domains/social_systems_contract.md`. Update `docs/parity_ledger/social_narrative.yaml`. Run `make knowledge-index-update`.

## Acceptance Criteria
- `test_known_traitor_event_fires_on_encounter` passes
- `test_faction_memory_survives_episode_without_member_npcs` passes
- All 3 consequence event kinds importable from `src/observability/events.py`

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY (parent epic)
- TCK-20260619-E43C-DECAY (required)
- TCK-20260619-E43D-FACTION-MEMORY (required)

## Related Docs
- `docs/simulation/domains/social_memory_contract.md` (new — create after implementation)
- `docs/simulation/domains/social_systems_contract.md` (update)
- `docs/parity_ledger/social_narrative.yaml` (add cross-episode entries)

## Related Code Areas
- `src/observability/events.py` (add 3 event kinds)
- Social encounter phase in `src/engine/` or `src/systems/social_systems/`

## Test Summary
```bash
pytest tests/unit/social/test_social_memory.py -x -v
pytest tests/integration/scenarios/test_social_memory.py -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
