---
status: active
layer: observability
authority: P1
audience: developer
---

# Running Simulations Headlessly with Full Observability

This guide provides simple, practical developer instructions to seed, compile, and run simulation worlds headlessly with maximum behavior observation enabled under the **Phase 19–28 Observability & Behavior Profiling** guidelines.

---

## 🚀 Seeding & Compiling the World

The RPG V2 Engine completely decouples world creation from the simulation loop. Before running a simulation, the world spec must be parsed and compiled into an active state by the `WorldCompiler` and `WorldRepository`.

### Default Sandbox World
By default, the CLI uses the `sandbox_world` specification stored under `data/worlds/sandbox_world/world.yaml`. 
This template dynamically spawns:
- **Town District**: Spawns **15 citizens**, **2 taverns**, and GRASS terrain.
- **Woods Wilderness**: Spawns **5 monsters**, **10 wood resource nodes**, and FOREST terrain with high hazards.

### Custom World Setup
To list all available compiled worlds in the repository index, run:
```bash
python3 -m src.worldbuilding.cli list
```

---

## 💻 Headless Simulation CLI Run Commands

### 1. Default Sandbox Simulation (With DEBUG Observability)
To launch a simulation of **100 ticks** using the default compiled `sandbox_world` under the highest behavioral profiling mode (`DEBUG`), run:

```bash
# Activate the virtual environment
source /home/vboxuser/Work/venv/bin/activate

# Execute headlessly with full behavior tracking enabled
OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42 --log-level INFO
```

### 2. Custom World Simulation (With DEBUG Observability)
To launch a simulation on a custom compiled world specification folder (e.g. `another_world`), run:

```bash
SIM_OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42 --world another_world --log-level INFO
```

---

## 📁 3. Locating and Processing Mined Data

Once your run completes, the telemetry datasets are persisted inside `data/runs/<run_id>/`. You can query, extract, and analyze this data using standard tools:

### Raw Artifact Paths
*   **Behavior Event Logs**: `data/runs/<run_id>/simulation_events.jsonl`
*   **Metric Windows**: `data/runs/<run_id>/metric_windows.jsonl`
*   **Strategic Cognition Graphs**: `data/runs/<run_id>/cognition_snapshots.jsonl`
*   **Hard Law Violations**: `data/runs/<run_id>/hard_law_violations.jsonl`

### Command-Line Dataset Processing

#### A. Export to Parquet
To convert a raw run's JSONL telemetry into high-performance, compressed Parquet files under `data/exports/`, run:
```bash
python3 -m src export <run_id> --format parquet
```

#### B. DB Warehouse Ingestion (SQLite/ClickHouse)
To ingest a completed run's behavior scorecard, timeline episodes, and findings into your SQL warehouse repository:
```bash
python3 -m src warehouse ingest-run <run_id>
```

#### C. SQL Predefined Analytical Queries
To execute deep analytical checks (e.g. finding the worst runs by health or fetching an entity's event log) on the database:
```bash
# Query the worst runs
python3 -m src warehouse query worst-runs --limit 10

# Fetch a detailed event history for entity 12
python3 -m src warehouse query entity-events --entity-id 12 --limit 50
```

---

## 🛡️ 4. Crash Recovery & Durability Guarantees

> [!IMPORTANT]
> **Zero Telemetry Loss on Engine Crashes**: 
> The simulation runner implements a strict `try...finally` boundary in `src/cli/entry.py`. If the simulation encounters an uncaught exception, a `HardLawViolationError`, or a system crash:
> 1. The engine catches the error, outputs the diagnostic trace to logs, and triggers the `finally` block.
> 2. The `finally` block **synchronously forces a final queue flush** inside the `EventRecorder` and `ReplayManager`.
> 3. All buffered in-flight behavioral events are safely written out to `simulation_events.jsonl` before the process exits.
> 4. The run manifest status is updated as `FAILED` in the repository, making it fully troubleshooting-ready for offline analysis.
