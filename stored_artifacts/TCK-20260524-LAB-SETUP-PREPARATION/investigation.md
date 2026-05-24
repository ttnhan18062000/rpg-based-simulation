# Staging Investigation: TCK-20260524-LAB-SETUP-PREPARATION

## Investigation & Existing Patterns
- Checked `src/lab/validator.py`: Contains `ScenarioValidator` and `ExperimentValidator` which are fully implemented and can validate specs directly.
- Checked `src/lab/guardrails.py`: Contains `LabBudgetGuardrails` which can estimate budgets based on `WorldSpec` and `ExperimentSpec`.
- Checked `src/worldbuilding/schema.py`: Contains `load_world_spec_from_yaml` and `WorldSpec` schema.
- Duplication checks: Can read index files in `data/worlds/world_index.json`, `data/scenarios/scenario_index.json`, and `data/experiments/experiment_index.json`.
