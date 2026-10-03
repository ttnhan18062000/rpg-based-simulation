---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION

## Scoped suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py tests/mechanic_scenarios/ -q
```

## Regressions fixed (real substance, not gate edits)

- Atlas prose (`entity-cognition#3` emotion, `entity-profile#7` genetics_aptitude,
  `faction-layer#5` cross_episode_social_consequences): badge cls + badge text + description
  hand-corrected, not just cls-regenerated — the prose itself asserted the now-wrong state.
- Capabilities tier regenerated (`mind#4` emotion: built → live).
- Wiring map `EMO` node: `:::bug` removed, label corrected, added to the `live` classDef list.
- `test_mechanism_registry_completeness_check.py`'s pinned counts: bound 20→23 (3 new
  domains/systems targets: `domains/emotion`, `systems/lifecycle_systems/genetics`,
  `systems/social_systems/consequence_events`); unbound 41→38.
- `test_mechanism_state_caller_check.py`'s pinned findings: now asserts exactly one remaining
  finding (`genetics_aptitude`, `gated_without_flag_context`), a known, understood low-confidence
  false positive (the flag check is several call-frames removed from the direct class reference).

## Result

181 tests passing, both with `graphify-out/` present and with it genuinely moved aside and
restored.
