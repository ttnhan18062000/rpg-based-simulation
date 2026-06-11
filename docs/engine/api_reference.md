---
status: active
layer: engine
authority: P1
audience: developer
---

# API Reference: The Presentation Layer

The WorldLoop RPG provides a gzipped JSON API designed for low-latency state synchronization. Following the AOA pivot, the API layer is decoupled from the simulation via a "Presenter" pattern.

---

## 1. REST Endpoints

### `GET /api/v1/state`
Returns the full current `Snapshot` of the world.
- **Query Params**:
  - `selected_id` (optional): Returns extra detailed cognitive data for a specific entity.
- **Response**: `WorldStateResponse` (JSON).

### `GET /api/v1/stream`
A **Server-Sent Events (SSE)** stream delivering per-tick deltas.
- **Event**: `message`
- **Data**: `JSON Delta` (Changed entities, Removed IDs, Events).

---

## 2. JSON Schemas

The AOA model uses two levels of entity representation to save bandwidth.

### `EntitySlimSchema` (Standard)
Streamed every tick for all alive entities.
- `id`: Entity ID.
- `kind`: Archetype string.
- `x`, `y`: Position.
- `hp`, `max_hp`: Combat health.
- `state`: Current `AIState` enum (e.g., "COMBAT", "HUNT").
- `action`: Last verb and reason string.

### `EntityFullSchema` (Detailed)
Returned only for the `selected_id`.
- **Everything in Slim**, plus:
- **`Mind`**: Full `goal_scores`, `emotion` values, and `memory_log`.
- **`Combat`**: Detailed `traces` (ring buffer of damage dealt/taken).
- **`Progression`**: Full `attributes`, `skills` cooldowns, and `aptitudes`.
- **`Inventory`**: List of items in equipment and bag.

---

## 3. Cognitive Introspection

Developers can peek into the AI's "thought process" via the `Mind` section of the `FullSchema`.

### Goal Scores
```json
"mind": {
  "decision": {
    "goal_scores": {
      "COMBAT": 0.85,
      "LOOT": 0.12,
      "REST": 0.05
    },
    "last_goal": "COMBAT",
    "last_reason": "[AGGRESSIVE] Hunting nearby Goblin #402"
  }
}
```

### Emotion Spikes
```json
"emotion": {
  "panic": 0.12,
  "stuck": 0.0,
  "bravery": 0.95
}
```

---

## 4. Event Categories

SSE Streams deliver `SimEvent` records categorized into domains:

- **`combat`**: Attacks, crits, kills, and damage numbers.
- **`progression`**: Level-ups, attribute increases, and evolution.
- **`world`**: Weather changes, region discoveries, and world-boss spawns.
- **`ai`**: Significant state changes (e.g., "Entity 40 is fleeing due to panic").

---

## 5. Performance Note: The Delta Engine

The SSE stream (`/api/v1/stream`) does not send full entities. It computes a **structural diff** between the current tick and the previous tick.
- If an entity only moves, only its `x` and `y` are sent.
- If an entity is identical to the previous tick, its ID is omitted entirely.
- This results in a **90% reduction in bandwidth** for a standard simulation loop.
