# TCK-20260424-PH12-M3-WORKFLOW-CUTOVER

## Title
Phase 12 Milestone 3: Workflow, CI, and Operational Artifact Cutover

## Status
DONE

## Request Summary
Transition internal workflows, CI validation paths, and operational artifact generation from the legacy `src` engine to the hardened `src_v2` engine.

## Scope
- [x] Task 1: Update `Makefile` to point `test` and `test-cov` targets to `tests_v2` and `src_v2`.
- [x] Task 2: Update CI validation jobs (if any) to use the new supported test paths.
- [x] Task 3: Migrate automated replay/report generation scripts to depend on `src_v2` by default.
- [x] Task 4: Ensure all operational proofs (release/certification) are sourced from the V2 truth.
- [x] Task 5: Document any legacy workflows that are retired or explicitly preserved for audit.

## Acceptance Criteria
- [x] `make test` runs `tests_v2`.
- [x] `make test-cov` generates coverage for `src_v2`.
- [x] Automated benchmarking and proof scripts (`run_benchmarks.py`, `refresh_proofs.py`) are confirmed as the primary operational paths.
- [x] No CI/CD or workflow path implicitly relies on legacy `src` without an explicit override.

## Completion Summary
Milestone 3 is complete. Internal workflows are now fully aligned with the V2 engine. `Makefile` targets have been modernized, operational proofs refreshed via `refresh_proofs.py`, and contributor documentation updated to enforce V2-first development.

## Implementation Notes
- Use `tests_v2` as the authoritative verification suite.
- Legacy `tests/` can be kept for backward compatibility but should not be part of the default `make test` path.
