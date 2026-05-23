# Plan - Variant Matrix Builder

We will implement the `VariantMatrixBuilder` and schema additions to support generating experiment variants safely:

## Steps
1. **Schema Definitions**:
   - Define `WorldVariant` and `ScenarioVariant` helper structures.
   - Define Pydantic schema model `VariantManifest` containing metadata fields specified in the requirements.
   - Define `VariantMatrix` holding the sweep index.
2. **Matrix Combinatorial Generation**:
   - Implement `VariantMatrixBuilder` that consumes base `WorldSpec`, base `ScenarioSpec`, and `MutationSpec`.
   - Implement mode logic:
     - `one_at_a_time`: Generates individual mutation variants (1 mutation per variant).
     - `combined`: Generates a single variant combining all mutations in sequence.
     - `factorial_limited`: Generates subsets of mutations incrementally by cardinality size (size 2, size 3, ...), capping generation strictly at `max_variants` limit.
   - Validate each generated variant using `MutationEngine`.
   - Save validated variant specifications to target workspace files, logging validation outcomes.
3. **Robust Test Suite**:
   - Implement unit tests covering each mode, base inclusion, ID stability, and combinatorial explosion guards.
