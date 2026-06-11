---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE22-3-REPAIR
artifact_type: test_plan
tags: [phase22, repair]
---

# Staging Test Plan - TCK-20260606-PHASE22-3-REPAIR

## Unit Tests
Modify `tests/unit/worldmodules/test_modules.py` or add new tests to verify:
- `test_list_resources_normalize_to_count_one`
- `test_dict_resources_preserve_counts`
- `test_dict_buildings_preserve_counts`
- `test_dict_services_preserve_counts`
- `test_negative_count_fails`
- `test_zero_count_fails`
- `test_duplicate_list_refs_fail`

## Integration/Regression Tests
- Verify existing tests in `tests/unit/worldassembly/test_assembly.py` and `tests/unit/worldmodules/test_modules.py` still pass.
