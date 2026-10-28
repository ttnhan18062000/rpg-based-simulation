---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261027-LEGACY-RECIPE-REGISTRY-AND-BLACKSMITH-ACTION-UNREACHED
artifact_type: test_plan
tags: [economy]
---

# Test plan

- tests/unit/world/test_economy_contract.py (shop test stays), tests/unit/core/test_same_name_class_guard.py (legacy row removed; a stale row would fail), tests/integration/economy/test_crafting_live_path.py (+1 moved test).
- tests/unit/tools/test_mechanism_registry_completeness_check.py and the check script: no pin may move (stop and ask if one does).
- Gates: make code-health, make lint-imports, scoped tests, tests/tools/test_agent_working_paths_guard*.py, mechanism_registry_changed_code_check advisory.
