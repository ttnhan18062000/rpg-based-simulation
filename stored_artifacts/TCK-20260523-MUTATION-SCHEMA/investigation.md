# Investigation Report - MutationSpec Schema & Validator

This report documents the repository architecture analysis, integration points, and baseline health state before implementing Milestone 84.

---

## 1. Integration Analysis

### A. Location for Specification Schemas
* **File:** `src/lab/schema.py`
* **Status:** This file currently implements `ScenarioSpec`, `ExperimentSpec`, and `LabRunManifest` using Pydantic V2 and custom YAML parsers (like `load_scenario_spec_from_yaml`).
* **Recommendation:** Integrating the new `MutationSpec` Pydantic schemas, exception models, and `load_mutation_spec_from_yaml` directly into `src/lab/schema.py` ensures all schema definition boundaries remain centered in the same target module.

### B. Location for Validator Rules
* **File:** `src/lab/validator.py`
* **Status:** This file houses pluggable validation rule classes (e.g. `ScenarioValidationRule`, `ExperimentValidationRule`) and their respective validators (`ScenarioValidator`, `ExperimentValidator`), utilizing the common `ValidationIssue` from `src/worldbuilding/validator.py`.
* **Recommendation:** Defining `MutationValidationRule`, its concrete rule subclasses, and `MutationValidator` inside `src/lab/validator.py` ensures all lab-specific semantic validations are consolidated, following the DRY principle and established boundaries.

### C. Reference Sets (Telemetry & Observability)
* **Status:** In `src/lab/validator.py`, a global constant `STANDARD_METRICS` defines recognized engine metrics (`hard_law_violations`, `resource_production_rate`, `stuck_entity_ratio`, etc.).
* **Recommendation:** Leverage this `STANDARD_METRICS` set in our `MetamorphicRelationshipRule` to raise warning issues for unrecognized metrics.

---

## 2. Baseline Verification

* Scoped unit tests run:
  ```bash
  python3 -m pytest tests/unit/lab/ -v --tb=short
  ```
* Output: **57 passed** in 1.55 seconds.
* Verification: The Scenario Lab codebase is stable and healthy. There are no preexisting compiler or unit test failures in the lab module.
