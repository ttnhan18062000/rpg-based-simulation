# Epic 11: Replay & Observation Tools

## Summary

Build a full replay recording and playback system that leverages the engine's deterministic architecture. Add observation tools for analyzing simulation runs: timeline scrubbing, entity tracking, stat graphs, and battle replay.

Inspired by: StarCraft replay system, League of Legends spectator mode, Factorio replay, Dwarf Fortress Legends mode.

---

## Motivation

- The engine is already deterministic — replay is architecturally "free" but not implemented beyond basic `ReplayRecorder`
- No way to rewind or analyze past events after they happen
- Observation tools help understand emergent AI behavior and debug decision-making
- Replay files enable sharing interesting simulation runs
- Aligns with "fully automated world" — the world is worth rewatching and studying

---

## Features

### F1: Replay Recording
- `ReplayRecorder` (partially exists) captures: world_seed, config, and per-tick action proposals
- Recording format: compact binary or JSON-lines (one object per tick)
- Record only actions — world state is reconstructed via deterministic replay
- Configurable: record every tick vs every N ticks (for long simulations)
- **Extensibility:** Recorder is a pluggable interface — swap formats without changing engine

### F2: Replay Playback
- New API endpoint: `POST /api/v1/replay/load` — load a replay file
- Replay mode replays recorded actions through WorldLoop without running AI workers
- Playback speed: configurable (1×, 2×, 4×, 0.5×, pause)
- Seek: jump to any tick in the replay (re-simulate from start to target tick)
- **Extensibility:** Replay source is an interface — could load from file, network, or database

### F3: Timeline Scrubbing (Frontend)
- Horizontal timeline bar showing tick range (0 to max recorded tick)
- Drag scrubber to jump to any point in the replay
- Key events marked on timeline: deaths, level-ups, boss kills, invasions
- Play/pause/speed controls integrated with timeline
- **Extensibility:** Event markers on timeline are filterable by category

### F4: Entity Tracking
- Select an entity and see its complete history: position path, HP over time, XP curve, gold
- Entity path drawn on canvas as a colored trail (fading over time)
- Side panel shows: actions taken at each tick, goals evaluated, state transitions
- Compare two entities side-by-side (hero vs a specific enemy)
- **Extensibility:** Tracked stats defined in a `TrackableMetric` registry

### F5: Stat Graphs
- Time-series charts for key metrics:
  - Hero: HP, XP, gold, items, attribute growth
  - Global: alive entity count, total deaths, faction territory sizes
- Graphs use a lightweight chart library (or canvas-based rendering)
- Hover on graph shows exact values at that tick
- **Extensibility:** New metrics added by registering in the tracker — no chart code changes

### F6: Battle Replay
- When clicking a combat event in the event log, jump to that tick and highlight the combatants
- Show damage numbers, crit indicators, and evasion misses as overlay text
- Step through combat tick-by-tick with detailed action breakdown
- **Extensibility:** Combat event detail stored in SimEvent metadata

### F7: Heatmaps
- Overlay canvas mode showing heatmaps:
  - Entity density over time (where do entities cluster?)
  - Death locations (where are the dangerous spots?)
  - Resource harvest frequency (which nodes are most visited?)
  - Hero movement patterns (which paths are most traveled?)
- Heatmap data accumulated during replay playback
- **Extensibility:** Heatmap types defined as accumulator functions

---

## Design Principles

- Replay reconstructs world state from seed + actions — no state snapshots needed
- All replay logic runs through the existing WorldLoop (minus worker threads)
- Frontend replay mode reuses all existing canvas/panel components
- Recording overhead is minimal (actions are small dataclasses)
- Seek is implemented via fast-forward (no random access) — acceptable for <10k ticks

---

## Dependencies

- Deterministic RNG system (already exists)
- ReplayRecorder stub (already exists)
- Event log system (already exists)
- WorldLoop tick cycle (already exists)

---

## Estimated Scope

- Backend: ~6 files new/modified (replay recorder, playback endpoint, replay WorldLoop mode)
- Frontend: ~8 files new/modified (timeline, graphs, heatmaps, tracking panel)
- Config: Recording toggle, replay file path, playback speed

---

## Dev Notes (from dev_noted_features)

> **[EPIC] rewind time to specific event:** InspectPanel > Events > click on event will rewind the world state into that event. The world is stopped at that moment, and user can:
> - Continue from that point, reset all the world state to that point
> - Back to the current time, exit the history view

This maps to **F3 (Timeline Scrubbing)** + **F6 (Battle Replay)** but with a specific UX: clicking an event in the InspectPanel events tab triggers the rewind. This is a more integrated approach than a standalone timeline bar — the event log itself becomes the navigation. Consider implementing this specific flow as the MVP before the full timeline UI.
