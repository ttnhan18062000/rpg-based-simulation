---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-COMBAT-ACTIONSTYLE-WIRING

## Normal flow
- `test_get_action_style_for_bravery_thresholds`: exact boundary behavior (0.65 → AGGRESSIVE
  inclusive, 0.35 → EVASIVE inclusive, mid-range → BALANCED).
- `test_compiler_faction_bravery_bias_produces_real_action_style_skew`: a 30-entity
  `wild_beast_pack` synthetic-world compile asserts >50% AGGRESSIVE and confirms at least one
  non-default (non-BALANCED) value is real, not dormant.

## Data-driven loading (shared with the sibling ticket's own fix)
- `test_personality_bias_config_loads_from_real_data_file`: confirms the real
  `personality_bias.yaml` is read, not the in-code fallback.
- `test_personality_bias_config_falls_back_safely_on_bad_file`: confirms a missing/malformed file
  never crashes world compilation.

## Real corpus re-verification (not unit-test-only)
Live probe against `dungeon_crawl`/`urban_political` post-fix: `wild_beast_pack` (highest bravery
bias) → 5/5 real entities AGGRESSIVE; `merchant_league` (no bias) → real, roughly even 3/3/3
split across all 3 ActionStyle values.

## Failure modes / regression-prone paths
- Full `tests/unit/worldbuilding/test_world_compiler.py` suite (35 tests) re-run to confirm no
  regression to unrelated compiler behavior.
- `tests/unit/content/` (232 tests) re-run after registering the new data file in
  `NON_CATALOG_FILES`/the content usage matrix, to confirm the real strict-load validator and
  matrix-consistency tests both accept the new file's classification.

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ \
  tests/unit/combat/ tests/unit/strategic/ tests/unit/entities/ tests/unit/content/ \
  tests/unit/core/ tests/unit/tactical/ tests/unit/movement/ -q -m "not slow"
```
Result: 2 pre-existing failures (`test_module_family_anchored` — missing world data directory;
`test_normal_move_triggers_oa` — confirmed pre-existing back in
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`), both confirmed unrelated via
prior bisection this session. 1052 passed.
