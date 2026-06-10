# Test Plan — TCK-20260610-SWAMP-BORDER-PACK

11 tests in tests/integration/content/test_swamp_border_pack.py:
- manifest validates against schema
- manifest has sample_compositions and sample_scenarios
- strict_validation_result == "PASS"
- archetypes resolve in catalog
- populations resolve in catalog
- world module files exist
- sample composition file exists
- dependencies resolve
- no unknown dependencies
- swamp pack strict matrix passes (no blocking errors)
- base world unaffected

All 11 pass.
