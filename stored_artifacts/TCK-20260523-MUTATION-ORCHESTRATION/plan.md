---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ORCHESTRATION
artifact_type: plan
tags: [mutation, orchestration]
---

# Implementation Plan: Mutation Lab Orchestration

## Proposed Steps

1. **Implement `MutationRepository` (`src/lab/repository.py`)**:
   - Provide file-based CRUD & indexing for `MutationSpec` files.
   - Enforce path traversal guards.

2. **Implement `MutationLabOrchestrator` (`src/lab/mutation_orchestrator.py`)**:
   - Create a clean class coordinate loading and validating specs.
   - Run budget checks (guardrails) before any variant matrices are built.
   - Call `VariantMatrixBuilder` to build variant world/scenario combinations.
   - Execute variant runs sequentially by setting up virtual sub-repositories.
   - If a variant simulation fails, log it and keep variant status as FAILED without halting.
   - Compile aggregated results and average metrics.
   - Run metamorphic rule evaluation and scorecard generation.
   - Write Central Manifest, Metamorphic results, Balance scorecards, and a gorgeous MD report.

3. **Integrate CLI Sweep Commands (`src/lab/cli.py`)**:
   - Add subcommands under `rpg-lab mutation`:
     - `validate <mutation_id>`: Validates mutation syntax and metric mappings.
     - `preview <mutation_id>`: Compiles mutation layout and prints variant preview matrix.
     - `run <mutation_id> --experiment <experiment_id>`: Runs the full mutation lab orchestration.
     - `report <mutation_lab_id>`: Prints or regenerates a gorgeous markdown summary.

4. **Safety and Anti-Misdirection Rules**:
   - Exclude invalid/failed variants from the balance comparison.
   - Ensure small sweeps (low seed counts) are flagged with `WEAK_EVIDENCE`.
   - Prevent comparing differing scenarios.
   - Check variant limits and cumulative tick bounds via guardrails.

5. **Verify and Audit**:
   - Run integration test suites covering the orchestration loop, CLI, safety gates, and budget thresholds.
