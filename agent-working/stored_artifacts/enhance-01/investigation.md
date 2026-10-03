---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: enhance-01
artifact_type: investigation
tags: [enhance]
---

# Investigation: Enhance 01 - Enrich Event Information

## Context Map
The goal is to inject structured JSON metadata into the `SimEvent(metadata=dict...)` pipeline for 7 critical lifecycle events so that UI dashboards and replay logs aren't blindly regex-parsing text strings.

### Source Files & Injection Points
1. **Combat Events** (`src/actions/combat.py` or `action_system.py`)
   - Requires: `attacker_id`, `defender_id`, `damage`, `is_crit`, `hp_after` etc.
2. **Death Events** (`src/engine/world_loop.py` & `src/actions/combat.py`)
   - Requires: `entity_id`, `killer_id`, `pos`, `level_at_death`
3. **Loot Events** (`src/systems/action_system.py`)
   - Requires: `entity_id`, `item_id`, `item_name`, `source`
4. **Level Up** (`src/engine/world_loop.py`)
   - Requires: `entity_id`, `old_level`, `new_level`, `attribute_gains`
5. **Trade/Craft** (`src/systems/action_system.py` or dedicated `trade.py`/`craft.py`)
   - Requires: `entity_id`, `action`, `item_id`, `gold_change`
6. **Quest** (`src/systems/quest_system.py`)
   - Requires: `entity_id`, `quest_type`, `status`

### Current Infrastructure
- The schema structure `metadata: dict | None` is **already natively supported** within:
  - `src/utils/event_log.py: SimEvent`
  - `src/api/schemas.py: EventSchema`
- Therefore, no database or REST schema migrations are necessary. The work is purely backend Python logic instrumentation.

## Risks & Constraints
- We must enforce strict standard structures for the `dict`. A generic `dict` can easily diverge into random key names (e.g., `attacker.id` vs `attacker_id`).
- We need a strategy to ensure all metadata strictly implements the required Contract/Schema so that front-end parsing does not face random `KeyError` exceptions.
