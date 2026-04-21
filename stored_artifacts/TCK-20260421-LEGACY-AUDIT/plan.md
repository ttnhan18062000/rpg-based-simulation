# Plan: Legacy Logic Audit

## Goal
Audit and mark the status of legacy requirements in `src_v2`.

## Approach
1.  **Research Subsystems**: Map `src_v2` modules to legacy `src` subsystems.
2.  **Verify Parity**: Check specific logic (Combat, Movement, Resources, Strategy) in `src_v2`.
3.  **Check System Compatibility**: Verify CLI, Logging, and Replay implementation.
4.  **Update Checklists**: Mark items with status and evidence links.

## Verification
-   Run `pytest tests_v2/integrity/`.
-   Run `pytest tests_v2/` to ensure full coverage.
-   Direct source inspection.
