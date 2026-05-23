# TCK-20260523-MUTATION-MATRIX

## Title

Milestone 86 — Variant Matrix Builder

## Status

DONE

## Request Summary

Implement the `VariantMatrixBuilder` to generate experiment variant configurations from base `WorldSpec` and `ScenarioSpec` templates using one of three modes: `one_at_a_time`, `combined`, and `factorial_limited` (avoiding unbounded full-factorial sweeps). Generate `VariantManifest` indexes detailing variant metadata, mutation histories, and validation barriers.

## Scope

- Implement `WorldVariant` and `ScenarioVariant` structures/models.
- Implement `VariantManifest` Pydantic schema in `src/lab/schema.py` or `src/lab/mutation.py`.
- Implement `VariantMatrixBuilder` class, supporting `one_at_a_time`, `combined`, and `factorial_limited` modes.
- Enforce the `max_variants` safety ceiling to prevent exponential combinatorial explosion in `factorial_limited` mode.
- Establish robust generation tests in `tests/unit/lab/test_variant_matrix_builder.py`.

## Out of Scope

- Metamorphic assertions checking pipeline (Milestone 87).
- Comparison Engine orchestrations (Milestone 88).

## Acceptance Criteria

- `one_at_a_time` creates one variant per mutation plus base variant.
- `combined` creates all mutations combined in sequence plus base variant.
- `factorial_limited` generates size-ordered combinations of mutations up to the `max_variants` limit.
- Builder refuses unbounded full factorial by default if too many mutations exist without constraint, or honors `max_variants` ceiling strictly.
- Base variant is always included first with no mutations.
- Variant IDs are stable and deterministic (e.g. `var_base`, `var_set_width`, `var_comb_all`, `var_combo_1`).
- All validation states are compiled correctly into `VariantManifest`.

## Related Tickets

- TCK-20260523-MUTATION-ENGINE (Done)

## Related Docs

- `lab_phase13.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/mutation.py`
- `src/lab/schema.py`
- `tests/unit/lab/test_variant_matrix_builder.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented standard combination algorithms via `itertools.combinations`.
- Handled size-ordered incremental combination compilation in `factorial_limited` mode, enforcing safety limits cleanly.

## Test Summary

- 6 unit tests added to `tests/unit/lab/test_variant_matrix_builder.py` covering all modes, limits, stable IDs, and failed validation scenarios.
- All 88 lab unit tests passed successfully in 2.0s.

## Files Changed

- `src/lab/schema.py`
- `src/lab/mutation.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_variant_matrix_builder.py`

## Completion Summary

- Designed `VariantManifest` and fully implemented `VariantMatrixBuilder`. Exceeded core validation requirements by preserving error details in failed variant manifests to maximize debugging visibility. Cleaned workspace and updated AST knowledge graph.
