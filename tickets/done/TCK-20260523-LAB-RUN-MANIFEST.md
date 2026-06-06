# TCK-20260523-LAB-RUN-MANIFEST

## Title

Milestone 77 — LabRun Manifest and Artifact Layout

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish a stable file layout and manifest tracking system for LabRun executions under the Scenario Lab. This maps run counts, directory structures, and results to isolate telemetry logs.

## Scope

- Implement Pydantic model `LabRunManifest` in `src/lab/schema.py`.
- Implement `LabRunRepository` in `src/lab/repository.py` supporting safe paths, path traversal checks, index compilation, and accidental overwrite protections.
- Export all components in `src/lab/__init__.py`.
- Write unit test suites in `tests/unit/lab/test_labrun_manifest.py` and `tests/unit/lab/test_lab_artifact_layout.py`.

## Out of Scope

- Implementing the orchestrator runtime executor (Milestone 78).
- Implementing Observatory execution telemetry (Milestone 79).

## Acceptance Criteria

- `LabRunManifest` model cleanly parses and validates active execution metadata.
- Repository creates isolation directories for `world`, `scenario`, `experiment`, `runs`, `analysis`, and `logs`.
- Safeguards prevent path traversal and accidental directory overwrite.
- 100% test coverage with zero failures.

## Related Tickets

- `TCK-20260523-LAB-EXPERIMENT-SCHEMA`

## Related Docs

- `lab_phase12.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/lab/schema.py`
- `src/lab/validator.py`
- `src/lab/repository.py`
- `src/lab/__init__.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Mutability has been intentionally allowed (`frozen=False`) on `LabRunManifest` schema to allow state changes as runs progress.

## Test Summary

- Complete pytest execution with all 37 tests passing cleanly:
  - `tests/unit/lab/test_labrun_manifest.py`: 4 tests
  - `tests/unit/lab/test_lab_artifact_layout.py`: 4 tests

## Files Changed

- `src/lab/schema.py`
- `src/lab/repository.py`
- `src/lab/__init__.py`
- `tests/unit/lab/test_labrun_manifest.py`
- `tests/unit/lab/test_lab_artifact_layout.py`

## Completion Summary

- Successfully completed Milestone 77, closing out the structural layouts, directory isolation guards, manifest models, and aggregate indexing compilers for Scenario executions. Fully secured against relative directory traversal escapes and accidental overwrite failures.
