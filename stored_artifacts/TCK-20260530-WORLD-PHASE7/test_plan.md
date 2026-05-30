# Test Plan: Provenance Manifest and Report Integration (Phase 7)

## Coverage Scope

1. **Manifest Schema Compliance**:
   - Assert all 11 top-level manifest parameters exist (`manifest_id`, `world_id`, `catalog_fingerprint`, etc.).
   - Verify records hold regions, populations, resources, buildings, factions, and profiles mappings.

2. **Group/Range Mappings**:
   - Verify that range-based grouping or population references are structured elegantly.

3. **Determinism**:
   - Compile the same composition multiple times and assert byte-identical manifest output.

4. **Regressions**:
   - Verify that all compilation loops and existing world building test suites are unaffected.

## Commands to Run
```bash
.venv/bin/pytest tests/unit/worldassembly/test_provenance.py -v
.venv/bin/pytest tests/unit/worldassembly/ -x
```
