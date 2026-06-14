---
status: active
layer: observability
authority: P1
audience: developer
tags: [observability, cli, simulation, sweep, worldbuilding, diagnostics]
---

# Running Simulations Headlessly with Full Observability

Practical developer reference for seeding, compiling, and running simulation worlds headlessly. Covers the full pipeline from world authoring through run analysis.

---

## 1. World Generation Pipeline

The engine decouples world authoring from the simulation loop. Worlds are authored as declarative YAML specs, compiled once, and then consumed by any number of simulation runs.

### CLI (worldbuilding — separate entry point)

```bash
# List all compiled worlds in the repository
python3 -m src.worldbuilding.cli list
# or: make world-list

# Validate a world spec against compile constraints
python3 -m src.worldbuilding.cli validate sandbox_world
# or: make world-validate WORLD=sandbox_world

# Compile a world spec into active state files
python3 -m src.worldbuilding.cli compile sandbox_world
# or: make world-compile WORLD=sandbox_world

# Resolve compositional specs into compiled assets
python3 -m src.worldbuilding.cli resolve sandbox_world
# or: make world-resolve WORLD=sandbox_world

# Inspect structural metrics of a world definition
python3 -m src.worldbuilding.cli inspect sandbox_world
# or: make world-inspect WORLD=sandbox_world

# Bootstrap a starter world template
python3 -m src.worldbuilding.cli create-template my_world
# or: make world-template WORLD=my_world
```

### Default sandbox world

`data/worlds/sandbox_world/world.yaml` — pre-compiled, always available:
- **Town District**: 15 citizens, 2 taverns, GRASS terrain
- **Woods Wilderness**: 5 monsters, 10 wood resource nodes, FOREST terrain

---

## 2. Running a Simulation

All simulation commands go through `python3 -m src cli` (or `make sim`).

### Basic run

```bash
python3 -m src cli --ticks 200 --seed 42
# or: make sim
```

### Custom world

```bash
python3 -m src cli --ticks 200 --seed 42 --world my_world
# or: make sim-world WORLD=my_world TICKS=200
```

### Log levels

`--log-level` controls Python logging verbosity. It does **not** affect the dynamic observability backpressure mode (see §3).

| Flag | When to use |
|---|---|
| `--log-level WARNING` | Quick smoke test — minimal output (`make sim-quick`) |
| `--log-level INFO` | Default for normal runs |
| `--log-level DEBUG` | Verbose phase-by-phase tracing (`make sim-debug`) |

```bash
# Verbose debug run
python3 -m src cli --ticks 100 --seed 42 --log-level DEBUG
# or: make sim-debug TICKS=100

# Quick 20-tick smoke test
make sim-quick
```

### Other flags

| Flag | Default | Description |
|---|---|---|
| `--ticks N` | 200 | Number of ticks to simulate |
| `--seed N` | 42 | World seed (deterministic) |
| `--entities N` | — | Override entity count |
| `--workers N` | — | Override worker thread count |
| `--replay` | — | Enable replay trace capture |
| `--world NAME` | sandbox_world | Custom world spec folder |

---

## 3. Dynamic Observability Backpressure

`EventRecorder` automatically adjusts its recording behaviour based on its queue fill ratio. This is **not a CLI flag** — it is adaptive and always active.

| Mode | Fill ratio | Behaviour |
|---|---|---|
| `NORMAL` | < 70% | All events recorded |
| `PRESSURE` | 70–90% | INFO/DEBUG sampled 1-in-5; WARNING+ always pass |
| `DEGRADED` | 90–100% | INFO/DEBUG dropped; WARNING+ pass |
| `SURVIVAL` | ≥ 100% | Counter-only — no queue push, no I/O overhead |

Mode transitions are logged once at INFO level. Check current pressure at any time:

```bash
python3 -m src diagnostics resources
# or: make check-resources
```

Exit code 0 = all subsystems OK or WARN. Exit code 1 = any subsystem DEGRADED (CI gate).

```bash
# JSON output for scripting
python3 -m src diagnostics resources --format json

# Offline mode — read from a completed run's artifacts
python3 -m src diagnostics resources --run-id <run_id>
```

---

## 4. Scenario Sweep (Run Matrix)

A sweep runs a parameterised matrix of scenarios and aggregates outcomes.

```bash
python3 -m src sweep path/to/sweep.json
# or: make sim-sweep CONFIG=path/to/sweep.json
```

Sweep config is a JSON file matching `ScenarioSweepConfig`. After the sweep:

```bash
# List all completed sweeps
python3 -m src list-sweeps

# Inspect a sweep summary
python3 -m src inspect-sweep <sweep_id>

# Compare sweep against baseline
python3 -m src compare-sweep <sweep_id> --baseline path/to/baseline.json

# CI gate — exit 1 if outcomes regressed
python3 -m src gate <sweep_id> --baseline path/to/baseline.json
```

---

## 5. Run Artifacts

After any run, artifacts land in `data/runs/<run_id>/`:

| File | Contents |
|---|---|
| `simulation_events.jsonl` | Raw behavioral event log |
| `metric_windows.jsonl` | Aggregated metric windows |
| `cognition_snapshots.jsonl` | Strategic cognition graphs |
| `hard_law_violations.jsonl` | Hard-law violation records |

### Export and analysis

```bash
# Export a run to Parquet
python3 -m src export <run_id> --format parquet
# or: make export-run RUN_ID=<run_id>

# Ingest into warehouse (SQLite/ClickHouse)
python3 -m src warehouse ingest-run <run_id>
# or: make warehouse-ingest RUN_ID=<run_id>

# SQL queries on the warehouse
python3 -m src warehouse query worst-runs --limit 10
python3 -m src warehouse query entity-events --entity-id 12 --limit 50

# Cognition inspection
python3 -m src cognition snapshot --entity-id 12 --run-id <run_id>
python3 -m src cognition patterns --run-id <run_id>
```

### Retention

```bash
# Dry-run scan of prunable files
python3 -m src retention plan
# or: make retention-plan

# Clean expired files (confirmation prompt)
python3 -m src retention clean
# or: make retention-clean
```

---

## 6. Crash Recovery

If the simulation crashes, `src/cli/entry.py` guarantees a `finally` block that:
1. Forces a final flush of the `EventRecorder` queue to disk
2. Forces `ReplayManager` to drain any pending chunks
3. Marks the run manifest as `FAILED` in the repository

No telemetry is lost on crash.
