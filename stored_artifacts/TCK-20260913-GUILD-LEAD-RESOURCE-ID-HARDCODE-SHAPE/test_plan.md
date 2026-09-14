# Test Plan — TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE

## New tests (`tests/unit/world/test_guild_pipeline.py`)

- `test_guild_lead_resource_kind_exists_in_the_real_content_catalog` — the required fail-loud
  check: asserts `GUILD_LEAD_RESOURCE_KIND` is a real key in `ResourceRegistry` (bootstrapped from
  the real content catalog). Verified this actually detects a violation (not just passes on a
  clean repo) by checking `ResourceRegistry.contains()` against both a real id (`"iron_vein"`,
  True) and a fabricated one (False) directly, before trusting the test's own green result.
- `test_guild_lead_subject_derives_from_the_catalog_not_a_second_hardcode` — proves the second
  hardcode (`subject="iron_ore"`) is now derived from `ResourceRegistry.get(...).yield_item`, by
  asserting the lead's subject matches the registry lookup directly rather than a literal copied
  into the test.

## Regression

Ran under `.venv313` (CI parity), `-m "not slow and not extra_slow"`:
- `tests/unit/world/test_guild_pipeline.py`: 6 passed (4 pre-existing + 2 new).
- Broader guild/resource/information sweep (`tests/unit/world/test_guild_pipeline.py
  tests/unit/world/providers/test_resource_opportunity_provider.py
  tests/unit/strategic/test_belief_integration.py tests/unit/strategic/test_opportunities.py
  tests/unit/engine/test_kernel_feature_flags_propagation.py
  tests/integration/content/test_resource_region_coverage_corpus.py
  tests/architecture/test_guild_action_dormancy.py
  tests/integration/scenarios/test_phase5_information_belief_scenarios.py`): **51 passed**.
