---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-ORCHESTRATOR
artifact_type: investigation
tags: [lab, orchestrator]
---

# Investigation — Milestone 78 Orchestrator

## Current Mechanisms
- **World Specs**: Ingested and validated via `WorldValidator`. Compiled to `AuthoritativeState` via `WorldCompiler.compile(spec, seed)`.
- **Scenario Specs**: Ingested via `ScenarioSpec.load_scenario_spec_from_yaml(yaml_path)`. Validated via `ScenarioValidator`.
- **Experiment Specs**: Ingested via `ExperimentSpec.load_experiment_spec_from_yaml(yaml_path)`. Validated via `ExperimentValidator`.
- **LabRun Layouts**: Instantiated through `LabRunRepository.create_lab_run`.
- **Tick Loops**: Executed sequentially using a `Kernel` instance for each target seed.
- **Analysis**: Conducted via `AnalysisPipeline.run(run_id)`.
