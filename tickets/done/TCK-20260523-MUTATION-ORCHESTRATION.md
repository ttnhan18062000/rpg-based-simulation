# TCK-20260523-MUTATION-ORCHESTRATION

## Title

Milestones 89, 90, 91 — Mutation Lab Orchestrator, CLI, and Safety Compliance

## Status

DONE

## Request Summary

Implement the `MutationLabOrchestrator` to run end-to-end variant mutation sweeps, integrate sweep controls into the RPG Lab CLI, and enforce strict anti-misdirection safety guards to prevent misleading balance claims.

## Scope

- **Mutation Lab Orchestrator (`src/lab/mutation_orchestrator.py`)**:
  - Load and validate base world, scenario, and mutation specifications.
  - Generate the variant matrix directory layout under `data/mutation_labs/{mutation_lab_id}/`.
  - Isolate each variant's simulation execution inside its own sub-repository and child lab run directory.
  - Gracefully log and report failed variants without corrupting the baseline variant run or blocking the overall sweep execution.
  - Gather and average metrics across child run reports.
  - Run metamorphic validation and overall balance comparisons dynamically.
  - Output centralized manifest summaries, metamorphic analysis, and scorecards.
- **Pluggable Repositories (`src/lab/repository.py`)**:
  - Add `MutationRepository` supporting safe YAML loading/saving and index manifest builds.
- **Lab CLI Commands (`src/lab/cli.py`)**:
  - `rpg-lab mutation validate <mutation_id>`
  - `rpg-lab mutation preview <mutation_id>`
  - `rpg-lab mutation run <mutation_id> --experiment <experiment_id>`
  - `rpg-lab mutation report <mutation_lab_id>`
- **Safety and Anti-Misdirection Rules**:
  - Exclude invalid/failed variants from the overall balance comparisons.
  - Block oversized sweeps via budget guardrails.
  - Track and expose execution cost profiles (runtime, artifact sizes, event volume, analysis time).
  - Enforce one-seed sweep `WEAK_EVIDENCE` indicators.
- **Verification Tests**:
  - Add integration tests covering standard runs, safety exceptions, budget blocks, and CLI execution.

## Out of Scope

- Standard non-mutation scenario lab sweeps (already completed).

## Acceptance Criteria

- Mutation sweep runs base + generated variants successfully, isolating each in separate folders.
- Failed variant configurations are reported as `FAILED` or `INVALID_VARIANT` without halting other variants or base results.
- Unrelated scenario IDs are blocked from being compared.
- Sweeps with all failed variants do not mark success.
- Oversized mutation sweeps are preemptively blocked by budgets.
- Executive markdown reports accurately summarize costs, results, and recommendations.

## Related Tickets

- TCK-20260523-BALANCE-COMPARISON (Done)

## Related Docs

- `lab_phase13.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/repository.py`
- `src/lab/mutation_orchestrator.py`
- `src/lab/cli.py`
- `tests/integration/lab/test_mutation_lab_orchestrator.py`

## Assumptions / Open Questions

- We assume default configurations are loaded from default profile loaders.

## Implementation Notes

- **Dynamic Variant ID Resolution**: Dynamic resolution maps user-specified mutation IDs in the metamorphic rule's `compared_variant` field to the actual generated variant ID (e.g., `var_one_wood_low`) using each `VariantManifest`'s list of `applied_mutations`.
- **Int Coercion Guard**: Implemented math-rounding (`int(round(x))`) when mutating `int` type baseline values to keep them as valid integers in generated World and Scenario spec configurations, avoiding validation crashes against strict schemas.
- **Base Variant folder alignment**: Save baseline specs directly under `base` variant directory instead of `var_base` for pristine naming parity with the baseline manifest ID.

## Test Summary

- `tests/integration/lab/test_mutation_lab_orchestrator.py` (3/3 tests passed):
  - `test_mutation_lab_orchestrator_end_to_end`
  - `test_mutation_lab_budget_blocked`
  - `test_mutation_lab_invalid_spec_blocked`
- 107/107 unit tests passed (`pytest tests/unit/lab/`)
- 8/8 integration tests passed (`pytest tests/integration/lab/`)

## Files Changed

- `src/lab/mutation.py`
- `src/lab/mutation_orchestrator.py`
- `tests/integration/lab/test_mutation_lab_orchestrator.py`

## Completion Summary

- Implemented dynamic metamorphic resolution, budget blocks, schema integer validation guards, and base variant naming parity in the Mutation Lab Orchestrator. Verified and certified all 115 tests successfully.

