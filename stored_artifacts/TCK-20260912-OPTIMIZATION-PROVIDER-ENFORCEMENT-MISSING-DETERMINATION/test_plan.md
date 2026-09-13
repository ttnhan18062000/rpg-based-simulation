# Test Plan — TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION

Covered by the shared regression sweep run for all three tickets:
`pytest tests/unit/domains/optimization/ tests/unit/perf/ tests/perf/ tests/unit/core/
tests/unit/observability/ tests/unit/world/providers/ tests/integration/perf/
tests/api/test_admission_control.py -q -m "not slow and not extra_slow"`: 1528 passed, 1 skipped.
`tests/unit/world/providers/test_resource_opportunity_provider.py` (the real, live provider's own
test) confirmed to still pass, unaffected. Post-deletion grep confirms zero remaining references to
`ProviderBudgetEnforcement`/`provider_enforcement.py` anywhere.
