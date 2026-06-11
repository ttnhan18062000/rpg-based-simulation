---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: enhance-01
artifact_type: plan
tags: [enhance]
---

# Implementation Plan: Event Enrichment & Extensible Event Bus

## Overview
Pursuant to the `enhance-01` requirements and the `architecture` skill directives, we are implementing **Option C: The Domain Event Bus**. 
This separates the act of *detecting a simulation action* from the act of *formatting text and pushing telemetry*. 

By building standard data contracts now, we guarantee that when the project expands into persistent database storage (Event Sourcing) in the future, the exact same backend Domain Events can be instantly serialized and dropped into a SQL table or Kafka topic.

## Component Architecture

### 1. Domain Event DataContracts
#### [NEW] `src/core/events.py`
We will establish strict, database-ready Python `dataclass` definitions for the critical lifecycle events.
**Examples:**
- `CombatStruckEvent(attacker_id: int, defender_id: int, damage: int, is_crit: bool, skill: str)`
- `DeathEvent(entity_id: int, killer_id: int, pos: tuple, level: int)`
- `LootEvent(entity_id: int, item_id: str, source: str)`

### 2. The Centralized Event Bus
#### [NEW] `src/systems/event_system.py`
A decoupled `EventBus` singleton or world-attached component.
- Contains a `publish(event: Any)` method.
- Systems will fire raw data into this bus instead of manipulating strings.

### 3. The Telemetry Bridge (Translation Layer)
#### [MODIFY] `src/systems/event_system.py`
This module will also contain a subscriber (e.g., `TelemetryBridge`) listening to the EventBus. 
When it receives a `CombatStruckEvent`, it will:
1. Lookup the `Entity` objects to fetch their `display_name` (e.g., "Hero" and "Goblin").
2. Construct the localized human-readable string: `"Hero attacks Goblin for 12 damage!"`.
3. Construct the `metadata` dictionary matching the event's data.
4. Pass the final formulated `SimEvent` to the legacy `src/utils/event_log.py` ring buffer so the frontend API doesn't break.

### 4. Logic Decoupling (Refactoring)
#### [MODIFY] `src/actions/combat.py`
#### [MODIFY] `src/engine/world_loop.py`
#### [MODIFY] `src/actions/loot.py`
We will surgically strip out all string-formatting logic from these action files. They will now exclusively push raw `CombatStruckEvent` and `DeathEvent` objects to the bus.

## Future Proofing
Because the `EventBus` receives explicit python dataclasses, adding a Database or PostgreSQL Sink later simply requires writing a new Subscriber (`DatabaseSink`) that executes `INSERT INTO events VALUES (event.attacker_id...)` without touching the simulation logic.
