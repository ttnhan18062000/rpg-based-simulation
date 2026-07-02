---
ticket_id: TCK-20260619-E62D-PARITY-VERIFY
phase: test_plan
date: 2026-06-23
---

# Test Plan — TCK-20260619-E62D-PARITY-VERIFY

## Tests Created

`tests/integration/culture/test_culture_drift_acceptance.py` (2 tests):
- test_two_regions_diverge_after_5_episodes — WORLD-CULT-003 acceptance; verifies fatalism and hero_veneration axis divergence >0.3
- test_calamity_region_higher_caution_delta_than_hero_region — verifies behavioral delta divergence >0.1 on caution tag

Both marked @pytest.mark.integration.

## Full Regression

- tests/unit/culture/ — 31 pass
- tests/unit/campaigns/ — 90 pass
- tests/unit/motivation/ — 4 pass
- tests/integration/culture/ — 2 pass

## Result: 127 passed
