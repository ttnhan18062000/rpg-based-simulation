# Event Bus Architecture & Dataclass Contract Telemetry

## Overview
As of **March 21, 2026** (Ticket `enhance-01`), the simulation engine's telemetry and logging mechanics have been fully decoupled from the core simulation mathematical logic. The architecture relies on an explicit Pub/Sub system managed by the generic `EventBus`.

## The Problem
Historically, discrete actions like Combat, Leveling Up, or Death manually parsed strings (e.g., `"Hero attacks Goblin for 12 damage!"`) and pushed them blindly into a ring buffer. This created a dual problem:
1. Hard-coupling mathematical algorithms (`combat.py`) with UI Presentation.
2. Inability to parse metrics out of strings seamlessly via Dashboards or Replay logs without executing blind Regex.

## The Solution

### 1. `DomainEvent` Dataclasses (`src/core/events.py`)
All actions now emit explicitly structured Python Domain Events holding the discrete variables of action context.
*Examples:* `CombatEvent`, `LootEvent`, `QuestEvent`, `LevelUpEvent`.

```python
# Combat modules no longer generate formatting strings!
world.event_bus.publish(CombatEvent(
    attacker_id=5, defender_id=10, damage=14, is_crit=True, skill_used="attack", attacker_hp=50, defender_hp=10...
))
```

### 2. The `TelemetryBridge` (`src/systems/event_system.py`)
The `EventBus` publishes the native raw Domain objects to a subscriber `TelemetryBridge`. The Bridge isolates the translation responsibility by injecting the `display_name` and converting the rigorous dataclass back into the localized API `/stream` formatted strings. 

Crucially, the raw dataclass variables are automatically dumped into the explicit JSON dictionary inside the `SimEvent.metadata` field. 

### Why? Event-Sourcing
This architecture ensures that the system is ready for **Database and Event-Sourcing**. When we switch from an in-memory GUI application to a cloud SaaS platform, the literal Domain Dataclasses can execute `.model_dump_json()` and sink directly into a PostgreSQL or Clickhouse event data bucket. The core logic of the game won't even realize a database exists.
