# Enhance 01: Enrich Event Information

## Summary

Add more contextual data to simulation events so the event log and future replay tools have richer information to display. Balance detail level — enough to understand what happened, not so much it floods the log.

## Current State

Events are `SimEvent(tick, category, message)` where `message` is a plain string like `"Hero attacks Goblin for 12 damage"`. No structured metadata is attached.

## Proposed Changes

### Structured Event Metadata

Add an optional `metadata: dict | None` field to `SimEvent`:

```python
SimEvent(
    tick=42,
    category="combat",
    message="Hero attacks Goblin for 12 damage (crit!)",
    metadata={
        "attacker_id": 1,
        "defender_id": 5,
        "damage": 12,
        "is_crit": True,
        "skill_used": "power_strike",
        "attacker_hp_after": 35,
        "defender_hp_after": 3
    }
)
```

### Event Categories to Enrich

| Category | Additional Metadata |
|----------|-------------------|
| `combat` | attacker_id, defender_id, damage, is_crit, skill_used, hp_after |
| `death` | entity_id, killer_id, position, level_at_death |
| `loot` | entity_id, item_id, item_name, source (ground/chest/drop) |
| `level_up` | entity_id, old_level, new_level, attribute_gains |
| `trade` | entity_id, action (buy/sell), item_id, gold_change |
| `craft` | entity_id, recipe_id, output_item |
| `quest` | entity_id, quest_type, status (accepted/completed/failed) |

### Guidelines

- Keep message strings human-readable (unchanged)
- Metadata is optional — not all events need it
- Don't log every tick's movement or idle state (too noisy)
- Frontend can use metadata for click-to-inspect on events (future)

## Affected Code

- `src/utils/event_log.py` — `SimEvent` dataclass, add metadata field
- `src/api/schemas.py` — `GameEventSchema` response model
- `src/engine/world_loop.py` — enrich events during Phase 4
- `src/actions/combat.py` — attach combat metadata
- `src/ai/states.py` — attach metadata in relevant state handlers
- `frontend/src/types/api.ts` — update `GameEvent` type

## Notes

> This is a prerequisite for epic-11 (Replay & Observation Tools) — structured events enable click-to-rewind and battle replay features.

## Labels

`enhance`, `events`, `backend`, `frontend`
