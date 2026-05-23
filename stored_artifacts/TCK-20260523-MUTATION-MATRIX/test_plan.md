# Test Plan - Variant Matrix Builder

We will implement a unit test suite in `tests/unit/lab/test_variant_matrix_builder.py` covering:

## Tests
- `one_at_a_time` produces one variant per mutation + the base variant.
- `combined` produces one merged variant + the base variant.
- `factorial_limited` generates combined size-ordered mutation subsets and respects `max_variants` limit perfectly.
- Unbounded full-factorial sweep raises exceptions or clamps to default maximum safety guards.
- Base variant is correctly present in all matrix generations.
- Generated Variant IDs are stable, deterministic, and free from collision.
- The `VariantManifest` is populated with correct fields and represents validation success/failure statuses.
