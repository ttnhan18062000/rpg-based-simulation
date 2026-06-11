---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260429-E3-MISSING-LOGIC
artifact_type: test_plan
tags: [e3, missing, logic]
---

# Test Plan: E3 Missing Logic

## Test File
`tests/rpg/test_rpg_depth.py` — 54 tests

## Test Coverage

### Stamina (12 tests)
- TestStaminaDrainOnAttack: attack/move/harvest/skill drain, insufficient stamina gate
- TestStaminaRegen: resting/active rates, capped at max, zero at max
- TestExhaustion: penalty application, no penalty above threshold, max derivation

### Wounds/Scars (7 tests)
- TestWoundInfliction: massive hit threshold (40%), stat impact, cumulative, healed ignored
- TestScarPermanence: heal→scar transition, lesser penalty (30%), cumulative

### Mob Leash (8 tests)
- TestMobLeash: within/beyond radius, no leash at 0, chase give-up (distance/timeout), continues within limits, return target, is_at_home

### Terrain Cost (5 tests)
- TestTerrainCost: road cheap, swamp expensive, plain default, full table, path cost sum

### Target Stickiness (6 tests)
- TestTargetStickiness: no target→switch, same→no switch, marginal→no switch, large→switch, loyalty factor, dead target→switch

### Skill Scaling (4 tests)
- TestSkillScaling: physical/magical/elemental formulas, minimum damage floor

### Attribute Caps (2 tests)
- TestAttributeCaps: cap enforcement, no-op within range

### Effective Stats (3 tests)
- TestEffectiveStats: wound penalties, scar vs wound vs clean comparison, evasion cap

### Apply Integration (7 tests)
- TestStaminaApplyIntegration: drain, clamp to zero, set override
- TestWoundApplyIntegration: wound add, scar add, wound heal
- TestPassiveStaminaRegen: apply_generation passive regen

## Execution
```bash
python3 -m pytest tests/rpg/test_rpg_depth.py -v
```

## Full Suite Regression
```bash
python3 -m pytest tests/ -v --tb=short
# Result: 669 passed, 2 skipped, 0 failed
```
