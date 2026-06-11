---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260405-CONVERGENCE
artifact_type: test_plan
tags: [convergence]
---

# AOA Convergence Test Plan (TCK-20260405-CONVERGENCE)

## What to Test
- All unit, integration, and E2E tests in the 1,227-test suite.
- Specifically verify that legacy attribute access (`e.stats`) has been replaced with AOA aspect paths in the affected tests.
- Performance: Ensure that simulation TPS remains > 0.5 for 500 entities.

## Test Cases
| Category | Test File | Case | Expected Result |
| :--- | :--- | :--- | :--- |
| Quest | `tests/test_quests.py` | `TestQuestTracking` | ALL PASS (AOA path aligned) |
| AI | `tests/unit/ai/test_attention.py` | `test_attention_pool_spiking` | ALL PASS (MindAspect modularized) |
| World | `tests/integration/world/test_regions.py` | `test_region_lookup` | ALL PASS (Model attribute access restored) |
| Performance | `tests/benchmarks/test_scaling_bench.py` | `test_scaling_500_entities` | PASS (TPS > 0.5) |

## Regression Surface
- **Mind/Emotion**: Spiking and appraisal triggers.
- **Progression**: Gold, XP, and state-transitions.
- **Spatial**: Entity difficulty scaling and vision ranges.

## Automated Verification Command
```bash
DISABLE_KAFKA=1 pytest -v --disable-pytest-warnings -p no:typeguard
```
