---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-FRONTIER-EXTENDED-PACK
artifact_type: test_plan
tags: [frontier, extended, pack]
---

# Test Plan: TCK-20260609-FRONTIER-EXTENDED-PACK

## Tests to Run

```bash
pytest tests/integration/content/test_strict_world_matrix.py -v --tb=short
pytest tests/integration/content/test_expansion_gate.py -v --tb=short
```

## Expected Results

### Strict world matrix
- All pre-existing 7 rows: same as before (no regression)
- New row "orc_clan" (8th): PASS for pre-assembly tests; xfail for assembly tests (CAT-REL-099)
- New row "forest_warden" (9th): PASS for pre-assembly tests; xfail for assembly tests (CAT-REL-099)

### Expansion gate
- Gates 01-10: PASS (same as before + new modules load/normalize)
- Gate 11: XFAIL (unchanged, CAT-REL-099)
- Gate 12: PASS (unchanged)

## Coverage

| Concern | Test |
|---|---|
| New modules load from repository | test_each_module_loads_from_repository (parametrized) |
| New modules normalize | test_each_module_normalizes_without_error (parametrized) |
| New modules have fingerprints | test_each_module_has_deterministic_fingerprint (parametrized) |
| New composition parses | gate 08 |
| No new dead content | gate 04 (ADDITIONAL state exempt) |
