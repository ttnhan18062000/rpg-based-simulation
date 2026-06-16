---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260614-WORLDDAT-NEWMODS
artifact_type: test_plan
tags: [worldmodules, data, content, new-modules]
---

# Test Plan — TCK-20260614-WORLDDAT-NEWMODS

## Integration Tests (existing file extended)
tests/integration/worldassembly/test_real_content_world_modules.py

Extend MODULE_MATRIX to include all 4 new modules:
- forest_deep_ecology
- ruins_mystery_quest
- trading_company_hub
- scalable_bandit_camp

Existing test functions cover: load, normalize, resolve contributions, reference graph edges.
No new test functions needed — all 4 modules are covered by existing parametric matrix.

## Unit Tests (parameter evaluator)
tests/unit/worldmodules/test_parameter_evaluator.py

New Group G — scalable_bandit_camp AC scenarios:
1. `danger_scale=4` → population count expression `"{danger_scale} * 3"` evaluates to 12
2. `danger_scale=6` → exceeds max_value=5 → raises AssemblyParameterError

## AC Coverage
- AC1: All 4 modules load via WorldModuleRepository ✓ (integration matrix)
- AC2: scalable_bandit_camp with danger_scale=4 → count=12 ✓ (unit test G1)
- AC3: scalable_bandit_camp with danger_scale=6 → AssemblyParameterError ✓ (unit test G2)
- AC4: ruins_mystery_quest produces 2 QuestDefinition entries ✓ (integration resolve)
- AC5: trading_company_hub relationship refs resolve ✓ (integration reference graph)
- AC6: forest_deep_ecology assembles without recipe fields ✓ (integration normalize)
- AC7: All 4 selectable by ModuleScorer ✓ (module_type + observability_tags confirmed valid)
