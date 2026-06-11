---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260530-PHASE11-ASSEMBLY-HARDENING
artifact_type: test_plan
tags: [phase11, assembly, hardening]
---

# Test Plan - Phase 11 Assembly Hardening

## Automated Verification Steps
1. Run pytest to check existing tests:
   `pytest tests/unit/worldassembly/`
2. Add new tests to `tests/unit/worldassembly/test_assembly.py`:
   - Test explicit profile overrides vs role defaults.
   - Test that compile_context is correctly populated.
   - Test clean separation of stages.
3. Add new tests to `tests/unit/worldassembly/test_provenance.py` checking determinism without operational timestamp comparison.
