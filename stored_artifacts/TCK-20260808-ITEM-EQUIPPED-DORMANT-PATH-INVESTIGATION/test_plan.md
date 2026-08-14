---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION
artifact_type: test_plan
tags: [progression, simulation-quality]
---

# Test Plan — TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION

No code change lands — verification means confirming both real claims directly, not from memory.

## Normal flow
- `grep -rln "ENABLE_PROGRESSION_EVOLUTION" config/simulation_quality/profiles/` returns zero
  matches — re-run as the literal verification step.
- `grep -rln "EquipmentService\." src/ --include=*.py` (excluding `core/equipment.py` itself)
  returns zero matches — re-run as the literal verification step.

## Edge cases
- Confirm `ENABLE_PROGRESSION_EVOLUTION`'s real default (`FeatureMode.OFF`) directly in
  `src/domains/optimization/feature_flags.py`, not assumed from the profile-scan alone (a flag
  could theoretically default ON with all profiles silent).

## Failure modes
- N/A — no code changed.

## Regression-prone paths
- N/A — no code changed; existing tests for `EquipmentService`/`ConversionIntentResolver`
  unaffected.

## Scoped test commands
- `pytest tests/unit/resource/test_equipment_chests_storage.py -q` (confirm untouched, still
  green)
- `pytest tests/unit/ -k "progression and resolver" -q` (if any exist for
  `ConversionIntentResolver`, confirm untouched)
