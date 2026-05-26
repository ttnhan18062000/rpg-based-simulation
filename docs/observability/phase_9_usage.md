# Phase 9: Simulation Mining & AI-Assisted Investigation — Developer Guide

This guide provides practical instructions, copy-pasteable code snippets, SQL query recipes, and diagnostic workflows to run, query, and utilize the **Phase 9 Simulation Mining & AI-Assisted Investigation Platform** in the V2 RPG Engine.

---

## 🚀 1. Asynchronous Parameter Sweeps

The mining platform runs matrix sweeps completely decoupled from the simulation hot path. To orchestrate a parameter grid sweep across scenarios, seeds, and execution models, use the `MiningExperimentController`.

### Python Execution Script
Save this script as `run_mining_sweep.py` in the workspace to launch a custom sweep:

```python
import asyncio
import logging
from src.observability.mining.controller import (
    MiningExperimentController,
    MiningExperimentConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    # 1. Configure the sweeping parameters matrix
    config = MiningExperimentConfig(
        experiment_id="quest_stability_sweep_2026",
        scenarios=["mixed_sandbox", "combat_heavy"],
        seeds=[42, 101, 2023],
        repeats=3,                     # Run each combination 3 times to audit state-drift
        ticks=200,                     # Run each simulation for 200 ticks
        max_workers=4,                 # Parallel thread execution pool
        storage_root="data/mining_experiments"
    )

    # 2. Initialize the sweep controller
    controller = MiningExperimentController(config)
    
    # 3. Launch the matrix sweep asynchronously
    logging.info("Starting large-scale simulation matrix sweep...")
    manifest = await controller.run_experiment()
    
    logging.info(f"Sweep Completed! Total runs executed: {len(manifest.runs)}")
    logging.info(f"Experiment Manifest saved at: {controller.experiment_dir}/experiment_manifest.json")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the script from your terminal:
```bash
python3 run_mining_sweep.py
```

---

## 📊 2. Querying Mined Datasets (SQL & Fallback)

Once a sweep finishes, the `MiningDatasetBuilder` automatically compiles the telemetry into a relational structure. You can query these tables using **DuckDB SQL** or using the **pure-Python fallback router** (which requires zero compiled binary dependencies).

### Python Query Service Broker

Here is how to load the query service and query the relational dataset:

```python
from src.observability.mining.dataset import DatasetQueryService

# Initialize the service pointing to your mined experiment folder
query_service = DatasetQueryService(
    experiment_dir="data/mining_experiments/quest_stability_sweep_2026"
)

# Load database tables
query_service.load_dataset()
```

### SQL Recipes for Simulation Mining

#### Recipe A: Locate Outlier Run Seeds
Identifies seeds experiencing abnormally high law violation densities:

```python
sql_outliers = """
SELECT r.seed, r.scenario_type, COUNT(f.violation_type) as violation_count, AVG(r.health_score) as avg_health
FROM runs r
JOIN hard_law_violations f ON r.run_id = f.run_id
GROUP BY r.seed, r.scenario_type
HAVING avg_health < 80.0
ORDER BY violation_count DESC
"""
outliers_df_or_list = query_service.query(sql_outliers)
print(outliers_df_or_list)
```

#### Recipe B: Temporal Anomaly Heatmap
Locates specific 10-tick simulation windows where anomalies occur most frequently:

```python
sql_temporal = """
SELECT (tick_start / 10) * 10 as tick_window, domain, COUNT(*) as anomaly_count
FROM anomalies
GROUP BY tick_window, domain
ORDER BY anomaly_count DESC, tick_window ASC
"""
temporal_patterns = query_service.query(sql_temporal)
```

#### Recipe C: Recurring Anomaly Domains
Finds repeating anomalies across different runs, highlighting systemic engine bugs:

```python
sql_recurring = """
SELECT domain, message, COUNT(DISTINCT run_id) as affected_runs
FROM anomalies
GROUP BY domain, message
HAVING affected_runs > 1
ORDER BY affected_runs DESC
"""
recurring_anomalies = query_service.query(sql_recurring)
```

---

## 🔒 3. Identifying State-Drift & Determinism Bugs

A core value of Phase 9 is automatically detecting non-deterministic behavior by comparing state hashes and event signatures across identical seeds.

### Running a Determinism Audit

```python
from src.observability.mining.dataset import DatasetQueryService
from src.observability.mining.auditor import DeterminismAuditor

query_service = DatasetQueryService("data/mining_experiments/quest_stability_sweep_2026")
query_service.load_dataset()

# Initialize determinism auditor
auditor = DeterminismAuditor(query_service)

# Audit all runs to detect seed-level divergences
drift_alerts = auditor.audit_determinism()

for alert in drift_alerts:
    print(f"⚠️ DETERMINISM DRIFT DETECTED!")
    print(f" - Seed: {alert.seed}")
    print(f" - Scenario: {alert.scenario_type}")
    print(f" - Drifting runs: {alert.run_a} vs {alert.run_b}")
    print(f" - Event Signature Divergence Index: {alert.divergence_index}")
```

---

## 🗂️ 4. Generating Reproducible Evidence Packs

When the `EngineeringBacklogGenerator` ranks a critical drift or law violation candidate, you can isolate it into a lightweight, self-contained **Evidence Pack** for offline reproduction.

```python
from src.observability.mining.evidence import EvidencePackBuilder

# Point to the experiment dataset broker
builder = EvidencePackBuilder(query_service)

# Build a self-contained evidence pack for the highest priority candidate
evidence_pack_path = builder.build_pack(
    run_id="run_sandbox_seed_42_repeat_1",
    candidate_id="CANDIDATE_QUEST_STALL_01"
)

print(f"📦 Evidence Pack archived at: {evidence_pack_path}")
```

### Examining an Evidence Pack Folder
Inside `data/mining_experiments/<experiment_id>/evidence_packs/CANDIDATE_QUEST_STALL_01/`, you will find:
1. `run_manifest.json`: Target run configuration and metadata.
2. `excerpt_metrics.json`: High-density tick-metric window (50 ticks before and after the failure).
3. `reproduce_command.sh`: A ready-to-run shell script to reproduce this exact seed locally:
   ```bash
   # content of reproduce_command.sh
   python3 -m src.cli.entry run-scenario --scenario mixed_sandbox --seed 42 --ticks 200 --observability-mode DEBUG
   ```

---

## 🤖 5. Orchestrating AI-Assisted Investigations

Once an Evidence Pack is created, run a structured LLM diagnostic investigation to pinpoint the bug and recommend code fixes.

```python
import asyncio
from src.observability.mining.orchestrator import AIAgentInvestigationRunner

async def run_ai_diagnostics():
    # 1. Point the runner to the isolated evidence pack directory
    runner = AIAgentInvestigationRunner(
        pack_dir="data/mining_experiments/quest_stability_sweep_2026/evidence_packs/CANDIDATE_QUEST_STALL_01"
    )

    # 2. Run the structured LLM diagnostic loop
    logging.info("Orchestrating LLM investigation agent...")
    report_path = await runner.run_investigation()
    
    logging.info(f"AI Diagnostics finalized! Report path: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_ai_diagnostics())
```

### Examining the AI Diagnostic Report
The generated `agent_investigation_report.md` will contain:
*   **Root-Cause Diagnosis**: Natural language explanation of the bug.
*   **Suspected Subsystems**: The target files and lines where the error originated.
*   **Traceability Assertions**: Citations of specific event hashes or database records proving the hypothesis.
*   **Remediation Recommendation**: A code diff recommendation to resolve the issue.

---

## 🚧 6. Continuous Integration (CI) Quality Gates

To prevent non-deterministic code or hard law violations from reaching production, integrate the `MiningQualityGate` into your Github Actions or CI pipeline scripts:

```python
from src.observability.mining.workflow import MiningQualityGate
from src.observability.mining.dataset import DatasetQueryService

# Initialize dataset broker
qs = DatasetQueryService("data/mining_experiments/quest_stability_sweep_2026")
qs.load_dataset()

# Check Quality Gate rules
gate = MiningQualityGate(qs)
gate_passed = gate.evaluate_gate()

if not gate_passed:
    print("❌ CI PIPELINE FAILED: Confirmed Non-Determinism or Critical Law Violations detected!")
    # Exit with code 1 to halt the CI/CD pipeline
    import sys
    sys.exit(1)
else:
    print("✅ CI PIPELINE PASSED: Zero-interference state is pristine!")
```
