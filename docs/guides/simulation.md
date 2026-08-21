---
title: Simulation — Getting Started Guide
layer: simulation
authority: P1
audience: developer
tags: [simulation, cli, world, artifacts, engine]
---

# Simulation — Getting Started Guide

How to author worlds, run simulations, and read their output.
Full CLI reference: [`docs/observability/how_to_run_simulation.md`](../observability/how_to_run_simulation.md).
Engine contracts: [`docs/engine/kernel.md`](../engine/kernel.md).

---

## How the engine works

Every simulation run is a deterministic 7-phase loop (Init → Scheduling →
Collection → Resolution → Cleanup → Advancement → Persistence) repeated per tick. Given the same seed and world,
two runs always produce identical output. All durable state changes go through the
**authoritative mutation pipeline** — nothing writes world state directly.

Key entry points:
- `src/engine/kernel.py` — the 7-phase loop
- `src/engine/pipeline.py` — the 17-phase mutation sequence
- `src/cli/entry.py` — CLI wrapper, crash recovery, event flush on exit

---

## World authoring

Worlds are declared as YAML specs and compiled once before any simulation run.

```bash
# Bootstrap a starter worldcomposition.v1 stub (populate module_refs afterward)
python3 -m src.worldbuilding.cli create-template "My World" my_world

# Validate before compiling
python3 -m src.worldbuilding.cli validate my_world

# Compile (required before running)
python3 -m src.worldbuilding.cli compile my_world

# Inspect structural metrics
python3 -m src.worldbuilding.cli inspect my_world
```

The **default sandbox world** (`data/worlds/sandbox_world/`) is pre-compiled and always
available — use it for quick experiments without authoring a world first.

World specs live in `data/worlds/<name>/world.yaml`. Composition specs reference modules
from `content/world_modules/`. See [`docs/world/assembly_contract.md`](../world/assembly_contract.md)
for the authoring schema.

---

## Running a simulation

```bash
# Default 200-tick run on sandbox world (seed 42)
python3 -m src cli --ticks 200 --seed 42
# or: make sim

# Quick 20-tick smoke test
make sim-quick

# Debug run — verbose phase-by-phase tracing
make sim-debug TICKS=100

# Custom world
python3 -m src cli --ticks 200 --seed 42 --world my_world
```

### Key flags

| Flag | Default | Description |
|---|---|---|
| `--ticks N` | 200 | Number of ticks to simulate |
| `--seed N` | 42 | Deterministic world seed |
| `--world NAME` | `sandbox_world` | World spec folder under `data/worlds/` |
| `--entities N` | — | Override entity count |
| `--workers N` | — | Override worker thread count |
| `--replay` | off | Enable replay trace capture |
| `--log-level` | `INFO` | `WARNING` / `INFO` / `DEBUG` |

### Scenario sweep (run matrix)

```bash
# Run a parameterised sweep matrix
python3 -m src sweep path/to/sweep.json

# Inspect results
python3 -m src list-sweeps
python3 -m src inspect-sweep <sweep_id>

# CI gate — exit 1 if outcomes regressed vs baseline
python3 -m src gate <sweep_id> --baseline docs/observability/baselines/latest.json
```

---

## Run artifacts

All artifacts land in `data/runs/<run_id>/` after each run.

| File | Contents |
|---|---|
| `simulation_events.jsonl` | Raw behavioral event log (all `SimulationEvent` records) |
| `metric_windows.jsonl` | Aggregated metric windows per tick |
| `cognition_snapshots.jsonl` | Strategic cognition graph snapshots |
| `hard_law_violations.jsonl` | Any hard-law violations caught by the monitor |

### Querying artifacts

```bash
# Export to Parquet
python3 -m src export <run_id> --format parquet

# Ingest into warehouse (SQLite or ClickHouse)
python3 -m src warehouse ingest-run <run_id>

# Query the warehouse
python3 -m src warehouse query worst-runs --limit 10
python3 -m src warehouse query entity-events --entity-id 12 --limit 50

# Inspect cognition for a specific entity
python3 -m src cognition snapshot --entity-id 12 --run-id <run_id>
python3 -m src cognition patterns --run-id <run_id>
```

Artifacts in `data/runs/` are **temporary** and excluded from version control. Clean them
with `rm -rf data/runs/*` (always done at ticket close per repo workflow).

---

## Determinism guarantee

The same `--seed` and `--world` always produce bit-identical output. If two runs diverge,
that is a P0 regression. Tests that protect this:

```bash
pytest tests/integration/kernel/test_determinism_suite.py -v
pytest tests/certification/test_world_compile_determinism.py -v
```

Do not introduce threading or random calls in logic paths that run per-tick.
See [`docs/engine/kernel.md`](../engine/kernel.md) for the determinism contract.

---

## Crash recovery

On crash, `src/cli/entry.py` guarantees:
1. Final flush of the `EventRecorder` queue to disk
2. `ReplayManager` drain of any pending chunks
3. Run manifest marked `FAILED`

No events are lost on crash.

---

## Further reading

- [`docs/mechanics/`](../mechanics/) — simulation laws (damage formulas, conservation laws, etc.)
- [`docs/engine/authoritative_pipeline.md`](../engine/authoritative_pipeline.md) — mutation rules
- [`docs/guides/observability.md`](observability.md) — how to read events and traces
- [`docs/guides/simulation_quality.md`](simulation_quality.md) — how to score run health
