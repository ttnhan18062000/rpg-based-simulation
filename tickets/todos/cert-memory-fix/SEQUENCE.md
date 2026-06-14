# Implementation Sequence: cert-memory-fix

Tickets in this batch have load-bearing dependencies. Implement in this order:

## Phase 1 (required first)
- **TCK-20260614-CERT-SAFE-SERIAL** — Adds `to_artifact_dict()` and fixes `to_json()`.  
  All other tickets consume this method.

## Phase 2 (depends on Phase 1)
- **TCK-20260614-CERT-RECORDER-REFACTOR** — Refactors recorder to use `to_artifact_dict()` and per-run files.  
  Requires `to_artifact_dict()` to exist on `CertificationResult`.

## Phase 3 (depends on Phase 1 and Phase 2)
- **TCK-20260614-CERT-EVIDENCE-LEVELS** — Adds `EvidenceLevel` enum and optional full canonical state export.  
  Requires both `to_artifact_dict(evidence_level=...)` signature and refactored recorder.

## Phase 3 (parallel with CERT-EVIDENCE-LEVELS)
- **TCK-20260614-CERT-MANIFEST-SNAPSHOT** — Writes `manifest_snapshot.json` to the proof output directory.  
  Depends on Phase 2 (recorder establishes the output dir path); can run in parallel with CERT-EVIDENCE-LEVELS.

## Independent (any time)
- **TCK-20260614-CERT-MEMRAY-BUDGET** — Makefile/script for Memray profiling runs.  
  No code dependency; can be implemented at any point.

## Rationale
`to_artifact_dict()` is the central serialization contract. Recorder and EvidenceLevel both extend it.  
Implementing recorder before the serialization boundary is fixed would perpetuate the memory issue  
and make test assertions meaningless.
