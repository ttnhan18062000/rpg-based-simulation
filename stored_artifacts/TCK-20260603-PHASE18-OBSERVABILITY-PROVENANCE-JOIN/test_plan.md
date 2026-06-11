---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE18-OBSERVABILITY-PROVENANCE-JOIN
artifact_type: test_plan
tags: [phase18, observability, provenance, join]
---

# Test Plan: Phase 18 Observability Provenance Join

This document outlines the testing strategy for verifying Phase 18 implementation.

## Automated Tests

### 1. Model Schema Tests
- Verify that `RunManifest` and `RunRecord` accept and serialize/deserialize `compile_context_path` and `runtime_content_source` fields.
- Verify warehouse adapters parse and ingest these new fields correctly.

### 2. Mapped Provenance Lookups
- Add new test cases to `tests/unit/observability/test_provenance_lookup.py` to verify mapping of:
  - Numeric `entity_id` -> its population ID -> source module/profile.
  - Resource ID (10000+) -> resource spec ID -> source module/resource type.
  - Building ID (20000+) -> building spec ID -> source module/building type.
- Assert correct handling of invalid or unknown IDs (return None or default gracefully).

### 3. Integration Smoke Tests
- Run `pytest` on existing world assembly, compiler, and generator test suites to ensure zero regressions in simulation startup, compilation, and execution.
