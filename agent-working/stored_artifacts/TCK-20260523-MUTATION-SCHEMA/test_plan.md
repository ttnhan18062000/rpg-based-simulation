---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-SCHEMA
artifact_type: test_plan
tags: [mutation, schema]
---

# Test Plan - MutationSpec Schema & Validator

This document establishes the testing strategy, scenarios, and assertions to verify the correctness of the MutationSpec implementation.

---

## 1. Schema Unit Tests (`tests/unit/lab/test_mutationspec_schema.py`)

This test file verifies structural parsing, polymorphic operation types, safe loading, and custom error formats.

### Scenarios & Assertions:
1. **`test_valid_mutationspec_loads`**:
   * Given a valid complex YAML containing all mutation operations (`set`, `add`, `multiply`, `toggle`, `remove`, `duplicate`), `load_mutation_spec_from_yaml` successfully loads it into a Pydantic `MutationSpec` object.
   * Asserts Pydantic attributes match input values.
2. **`test_missing_required_fields`**:
   * Given YAML files missing `mutation_id`, `schema_version`, or `base_world_id`.
   * Asserts `InvalidMutationSpecError` is raised with a descriptive error message.
3. **`test_invalid_operation_rejected`**:
   * Given a YAML file with a mutation having an invalid operation literal (e.g. `operation: "divide"`).
   * Asserts `InvalidMutationSpecError` is raised.
4. **`test_invalid_numeric_operands`**:
   * Given a YAML file where `multiply` or `add` value is a string or list.
   * Asserts `InvalidMutationSpecError` is raised.
5. **`test_matrix_modes_validation`**:
   * Given a YAML file with an invalid matrix sweep mode name.
   * Asserts `InvalidMutationSpecError` is raised.
6. **`test_extra_fields_preserved`**:
   * Given a YAML containing future metadata/arbitrary fields.
   * Asserts these fields are parsed and preserved in `model_extra`.

---

## 2. Validator Unit Tests (`tests/unit/lab/test_mutationspec_validator.py`)

This test file verifies the semantic validation rules and strict/non-strict error elevation policies.

### Scenarios & Assertions:
1. **`test_validator_base_references`**:
   * Given mock repositories for worlds and scenarios.
   * Verify that a spec referencing a non-existent `base_world_id` or `base_scenario_id` raises `InvalidMutationSpecError` indicating missing resources.
2. **`test_validator_metamorphic_variant_existence`**:
   * Given metamorphic relationship rules referencing undefined variant IDs (e.g., `baseline_variant: "nonexistent"`).
   * Verify that `InvalidMutationSpecError` is raised.
3. **`test_validator_unrecognized_metric_warning`**:
   * Given metamorphic rules monitoring unrecognized metrics.
   * Verify that a warning issue is generated, but non-strict validation does *not* raise an exception.
4. **`test_validator_strict_mode`**:
   * Given a warning issue (e.g., unrecognized metric).
   * Verify that calling `validate(spec, strict=True)` elevates the warning into a raised `InvalidMutationSpecError`.
