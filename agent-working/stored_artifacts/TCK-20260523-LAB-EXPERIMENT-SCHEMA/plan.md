---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-LAB-EXPERIMENT-SCHEMA
artifact_type: plan
tags: [lab, experiment, schema]
---

# Milestone 76 Implementation Plan

Provide a robust file-based ExperimentSpec schema, pluggable rules validator, and traversal-safe repository under the `src/lab/` domain package.

## Components Map

- `src/lab/schema.py`:
  - `ExperimentRunSpec`
  - `ExperimentObservabilitySpec`
  - `ExperimentAnalysisSpec`
  - `ExperimentRetentionSpec`
  - `ExperimentBudgetsSpec`
  - `ExperimentSpec` (frozen Pydantic model with `experiment_type`)
  - `InvalidExperimentSpecError` exception and YAML loader helper
- `src/lab/validator.py`:
  - `ScenarioExistenceRule` checking scenario existence using injected repository (Option A)
  - `ExperimentParameterRule` enforcing bounds (ticks, seeds, repeats, baseline comparison bounds)
  - `ExperimentObservabilityRule` checking validity of the observability modes
  - `ExperimentValidator` orchestrator
- `src/lab/repository.py`:
  - `ExperimentRepository` managing stored experiments under `data/experiments/`
  - Path traversal checks
  - Manifest compiler rebuilding `experiment_index.json`
- `src/lab/__init__.py`: Export new classes.

## Verification Plan

### Automated Tests
- `tests/unit/lab/test_experimentspec_schema.py`
- `tests/unit/lab/test_experimentspec_validator.py`
