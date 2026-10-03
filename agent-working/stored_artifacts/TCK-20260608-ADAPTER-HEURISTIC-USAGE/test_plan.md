---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260608-ADAPTER-HEURISTIC-USAGE
artifact_type: test_plan
tags: [adapter, heuristic, usage]
---

# Test Plan — TCK-20260608-ADAPTER-HEURISTIC-USAGE

## Regression Surface
- tests/unit/core/test_registry_bridge.py (4 currently failing; must all pass after fix)
- tests/unit/content/test_runtime_content_mode.py (currently passing; must remain passing)

## New Tests Required
tests/unit/content/test_adapter_heuristic_reporting.py:
- Item adapter: use_kind heuristic emitted when use_kind missing
- Item adapter: class_fit heuristic emitted when class_fit missing
- Service adapter: affordances heuristic emitted when affordances missing
- Resource adapter: required_tool heuristic emitted in CATALOG_WITH_COMPATIBILITY
- Resource adapter: base_difficulty heuristic emitted in CATALOG_WITH_COMPATIBILITY
- heuristic_usages is empty in CATALOG_STRICT (STRICT raises AdapterError before appending)
- CATALOG_WITH_COMPATIBILITY mode returns populated heuristic_usages in AdapterProjectionResult
- heuristic_count property returns len(heuristic_usages)

## Scoped Pytest Commands
pytest tests/unit/core/test_registry_bridge.py tests/unit/content/test_adapter_heuristic_reporting.py tests/unit/content/test_runtime_content_mode.py -q
