---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PHASE3-M9
artifact_type: investigation
tags: [sim, obs, phase3, m9]
---

# Investigation - Run Artifact Contract & Existing Recorders

## 1. File Writing Analysis

Currently, our new components write to hardcoded paths or directory paths passed in:
*   `EventRecorder`: Writes `simulation_events.jsonl` in the folder path passed to `EventRecorder(run_dir, ...)`.
*   `PostRunAnomalyAnalyzer`: Reads `simulation_events.jsonl` from `run_dir` and writes `anomalies.json` / `anomaly_summary.md` inside `run_dir`.
*   `RunReportGenerator`: Reads `anomalies.json` and writes `run_report.json` / `run_report.md` inside `run_dir`.

### Analysis:
By introducing `RunArtifactRepository`, we will centralize all of this. Instead of components managing their own paths, we will pass a `RunArtifactRepository` (or use it to resolve paths) to these components.
For example:
```python
repo = RunArtifactRepository(base_dir="data/runs")
events_path = repo.resolve_path(run_id, "events")
# returns "data/runs/<run_id>/simulation_events.jsonl"
```

---

## 2. Kernel Integration Investigation

The `Kernel` currently sets up observability buffers. We should:
- Introduce `run_id` to the `Kernel` (e.g. through the runtime profile or configuration, or dynamic parameter during instantiation/run).
- In V2 `Kernel`, `profile` is a `RuntimeProfile` which has a `name`. We can use a generated `run_id` or map it.
- Let's check `src/engine/kernel.py` using `view_file` to see how it can best receive a `run_id`.
  Wait, the `Kernel` class can simply take an optional `run_id` string during `__init__`, or generate one (e.g., `f"run_{int(time.time())}"`) if none is provided. This is extremely robust and backward-compatible!
- When observability mode is not `OFF`, the kernel will instantiate a `RunArtifactRepository` (or we pass it), create the run directory, write the initial manifest status as `RUNNING`, and configure the recorders to save inside this repository's resolved folder.
- When shutdown is called, update the manifest completed ticks, elapsed time, status `COMPLETED`/`FAILED` (depending on exception status), and complete final telemetry flushes.

---

## 3. RNG and Determinism Footprint

Since the `RunArtifactRepository` operates purely on disk and metadata files *outside* of the `AuthoritativeState` loop, it introduces **zero RNG calls or side-effects**, matching our strict Phase 2 parity invariants perfectly!
- Verified that all repository folder creations and metadata checks occur before/after simulation ticks, avoiding any loop pollution.
- No changes to canonical state hash calculations.
