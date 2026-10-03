---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION

## Updated pinned tests (each with a full investigation comment)

- `test_mechanism_state_caller_check.py::test_real_registry_findings_pinned` — finding set expanded
  6→9: 3 new understood/false-positive checker limitations documented
  (`opportunity_rumor_seeds`/`campaigns`/`chronicle`), 1 real finding that changed the registry
  instead of the pin (`calamity_intensity`, reverted rather than pinned as a false positive).
- `test_mechanism_registry_completeness_check.py::test_real_registry_enumeration_and_binding_counts_pinned`
  — `bound` 29→33, `unbound` 32→28, with per-target attribution.

## Manual verification

- Every one of the 23 mechanisms' proposed bindings independently checked for a real, non-test
  caller via direct grep before being written to the registry.
- `calamity_intensity`: the checker's own flag was independently re-verified (not trusted blindly
  either direction) before reverting the binding.
- `registry.py::validate()` re-run after every substantive edit.
- All 5 blocking mechanism-registry checks re-run clean after the full batch.

## Results

`tests/unit/tools/` full suite: 260 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5
blocking checks: clean.
