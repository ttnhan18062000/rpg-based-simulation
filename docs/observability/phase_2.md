---
status: historical
layer: observability
authority: P2
audience: developer
---

# Phase 2 Semantic Observability & Post-Run Observatory

This document details the architectural specifications, components, and validation verification of **Phase 2 Semantic Observability and Post-Run Diagnostics** implemented for the V2 RPG Simulation Engine.

---

## 1. Decoupled Semantic Architecture

To preserve simulation purity and strict bit-identical determinism, Phase 2 separates the simulation loop and state changes from the event extraction, buffering, and bug diagnostic systems.

```
       [KERNEL STEP] -> Commit State
              |
              v
[Kernel._phase_observability]
              |
              +--> EventExtractor.extract(prior_state, current_state, update)
              |         |
              |         v (Produces curated SimulationEvents)
              |
              +--> EventRecorder.record(event) ---> writes to simulation_events.jsonl
              |
              +--> EntityTimelineStore.record(event) ---> stores in thread-safe external deques
```

---

## 2. Core Components

### 2.1 Standard Event Envelopes
Defined in [events.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/events.py), all events inherit from a standard Pydantic base `SimulationEvent` specifying:
- `event_id`: Unique string UUID.
- `event_type`: Dynamic type tag (e.g., `spawn`, `combat_damage`, `movement`).
- `event_category`: Category literal (`movement`, `combat`, `resource`, `quest`, `lifecycle`, `hard_law`, etc.).
- `tick`: The current tick index.
- `severity`: Standard severity literal (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- `source_system`: Producing sub-system tag.
- `message`: Human-readable summary.
- `payload`: Detailed dynamic context dictionary.

### 2.2 Decoupled Event Extractor
Implemented in [event_extractor.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/event_extractor.py), `EventExtractor.extract()` takes a prior state and current state delta comparison to produce curated, low-volume events. It enforces volume reduction rules:
- ROUTINE movement events and normal combat strike damage are ignored in `LIGHT` and `LONG_RUN` modes to prevent index bloat.
- Lethal combat hits, spawning, despawning, large transaction values, and quest transitions are always captured.

### 2.3 Bounded Event Recorder
Implemented in [event_recorder.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/event_recorder.py), `EventRecorder` operates an active 5000-event thread-safe buffer. If full, it evicts the oldest low-severity event (first checking `DEBUG`, then `INFO`, etc.) to prevent memory leaks while guaranteeing that all events are flushed safely to the `simulation_events.jsonl` output log file.

### 2.4 External Entity Timeline Store
Implemented in [entity_timeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/entity_timeline.py), `EntityTimelineStore` manages per-entity deques external to `EntityState`. This strictly protects `EntityState` attributes from dynamic mutation or hash contamination during canonical serialization and state replays.

---

## 3. Post-Run Diagnostics & Executive Reports

### 3.1 Post-Run Anomaly Analyzer
Implemented in [rules.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/rules.py) and [post_run_analyzer.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/anomaly/post_run_analyzer.py), this tool evaluates runs post-hoc against five specific behavioral rules:
1. **HardLawViolationRule**: Breached core laws (Critical).
2. **NavigationStuckRule**: Frost positions of active hero entities over multiple movement events (Error).
3. **QuestStalledRule**: Quests staying started or in progress for too long without completing (Warning).
4. **CombatNeverEndsRule**: Endless engagement between entities without lethal termination (Error).
5. **ResourceNodeCrowdingRule**: Crowded resource harvesting above safety capacity limits (Warning).

Results are exported to `anomalies.json` and a readable `anomaly_summary.md` markdown board.

### 3.2 Run Report Generator
Implemented in [run_report.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/run_report.py), this aggregates telemetry and computes a deterministic weighted **Health Score**:
- `Health Score` starts at 100.
- `-40` per Critical/Hard Law Violation.
- `-15` per Error (stuck, endless loop).
- `-5` per Warning (stalled quest, crowding).
- Outputs a gorgeous `run_report.md` executive dashboard and matching machine-readable `run_report.json`.

---

## 4. Verification Checklists & Certification
All components have been strictly certified through unit, integration, and parity test runs:
- **100% Exact Parity**: Confirmed via `test_state_hash_parity_across_observability_modes` that running the simulation under `OFF`, `LIGHT`, `DEBUG`, or `CERTIFICATION` modes results in 100% identical final authoritative hashes.
- **100% Automated Success**: Verify by running:
  `pytest tests/unit/observability/ tests/integration/observability/ tests/certification/test_event_observability_parity.py`
