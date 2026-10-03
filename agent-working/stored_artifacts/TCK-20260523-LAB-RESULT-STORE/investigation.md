---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-RESULT-STORE
artifact_type: investigation
tags: [lab, result, store]
---

# Investigation - Lab Result Store (Milestone 80)

We analyzed the existing `LabRunRepository` implementation in `src/lab/repository.py` and the orchestrator's directory outputs.

## Findings
* **Lab Run Layout**:
  - Root: contains `lab_run_manifest.json`, `lab_summary.json`, `lab_summary.md` (which are written by the orchestrator at `run_dir` root, wait, let's verify if `lab_summary.json` is at the root or under `analysis/`. Our orchestrator writes:
    - JSON: `run_dir / "lab_summary.json"`
    - MD: `run_dir / "lab_summary.md"`
  - `world/` directory: contains `world.yaml` and `world_compile_report.json`. Wait, does `world_compile_report.json` exist? Yes, it's compiled during the compilation phase. Let's check `ScenarioLabOrchestrator.run_lab` logic:
    ```python
    initial_state, compile_report = WorldCompiler.compile(world_spec, seed)
    ...
    # Compiles and saves compile report
    ```
  - `runs/` directory: contains subfolders `run_{lab_run_id}_seed_{seed}/` or similar, each containing `run_report.json`.
* **Path Traversal Rules**:
  - We must use absolute path comparison using `.resolve()` and `.is_relative_to(base)` or try-except blocks to catch traversals reliably on all operating systems (including Linux/Windows).
