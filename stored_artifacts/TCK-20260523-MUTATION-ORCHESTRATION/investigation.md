---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ORCHESTRATION
artifact_type: investigation
tags: [mutation, orchestration]
---

# Investigation: Mutation Lab Orchestration

## Current Codebase Architecture

1. **Specs and Schema (`src/lab/schema.py`)**:
   - Contains definitions for `MutationSpec`, `MutationBudgetsSpec`, `ExpectedRelationshipSpec`, and `VariantManifest`.
   - `VariantMatrixBuilder` in `src/lab/mutation.py` maps base Specs + MutationSpec to mutated specs on disk and outputs `VariantManifest` list.

2. **Validation Engine (`src/lab/validator.py`)**:
   - `MutationValidator` validates base references and metamorphic relationship rule syntax.
   - Raises `InvalidMutationSpecError` on non-conforming configurations.

3. **Metamorphic Rule Engine (`src/lab/metamorphic.py`)**:
   - Evaluates `ExpectedRelationshipSpec` records against computed `variant_metrics`.
   - Flags missing metrics with `INSUFFICIENT_DATA` and small seed sweeps with `weak_evidence`.

4. **Balance Comparison Engine (`src/lab/comparison.py`)**:
   - Per-metric differential analysis against baseline.
   - Summarizes overall sweeps with dynamic scorecards.

## Mapping telemetries to metrics
To feed metamorphic and balance engines, the orchestrator needs to map aggregated child simulation run outputs to a uniform `variant_metrics` map:
```json
{
  "health_score": 92.5,
  "hard_law_violations": 0.0,
  "critical_anomalies": 1.2,
  "stuck_ratio": 0.05,
  "resource_production": 412.5,
  "run_count": 5
}
```

We will build a high-fidelity mapper that scans each variant's lab run folder, reads all successful `run_report.json` seed documents, and computes their averages or totals as required.

## Directory Isolation Design
To achieve clean isolation:
```text
data/mutation_labs/
  mutation_lab_{mutation_id}/
    mutation_lab_manifest.json
    mutation.yaml
    variants/
      base/
        world.yaml
        scenario.yaml
        lab_run/
          lab_run_manifest.json
          runs/
            run_base_seed_42/
              run_report.json
      wood_low/
        world.yaml
        scenario.yaml
        lab_run/
          lab_run_manifest.json
    analysis/
      metamorphic_results.json
      balance_comparison.json
      mutation_lab_report.md
```

We will mock small, virtual `WorldRepository` and `ScenarioRepository` structures in temporary directories for each variant before feeding them to the standard `ScenarioLabOrchestrator`. This ensures the exact codebase behavior remains 100% stable while running variant matrix simulations.
