---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-MUTATION-ORCHESTRATION
artifact_type: test_plan
tags: [mutation, orchestration]
---

# Test Plan: Mutation Lab Orchestration

We will verify all components of the Mutation Lab Orchestration, CLI, and Safety gates using unit and integration tests.

## Test Areas

1. **Mutation Repository Tests**:
   - Save, load, list, and index rebuild of MutationSpecs.
   - Enforce path traversal protection.

2. **Mutation Lab Orchestration Loop Integration**:
   - Standard run with base + one variant.
   - Folder isolation verification: check that variants are isolated under `variants/base` and `variants/{variant_id}`.
   - Telemetry mapping validation: check that metrics are aggregated from child reports accurately.
   - Central manifest and report verification.

3. **Safety and Anti-Misdirection Integration**:
   - Exclude failed/invalid variants from comparison card.
   - Weak evidence flag check (1 seed matrix sweep triggers weak evidence).
   - Unrelated scenario validation: block comparison of variants from different scenarios.
   - Failed sweep: if all variants fail, overall manifest is FAILED.
   - Pre-flight budget guardrail checks: oversized sweeps should be blocked.

4. **Lab CLI Subcommand Tests**:
   - Validate subcommand outputs.
   - Preview subcommand outputs.
   - Run subcommand end-to-end execution.

## Automated Verification Command
- Scoped execution: `pytest tests/integration/lab/ -k "mutation"`
