# Test Plan — TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS

## Coverage

| Test | Scenario |
|------|----------|
| magic-only target not perceived by humanoid | normal_humanoid_senses + target with only magic_signal → not in hostiles |
| arcane entity perceives magic target | arcane_senses + magic-only target → combat target selected |
| territorial entity selects target | territorial_predator drive → valid target selected |
| safety_pressure retreat trigger | cautious_commoner drive + hostile → SAFETY_PRESSURE_RETREAT |
| low safety no retreat | no profiles → no safety retreat |
| duty pressure target selection | disciplined_protector drive → target 2 selected |
| determinism | same state + profiles → identical update |

All 7 pass. Pre-existing test_stamina_drain failure unchanged (legality.py bug, unrelated).
