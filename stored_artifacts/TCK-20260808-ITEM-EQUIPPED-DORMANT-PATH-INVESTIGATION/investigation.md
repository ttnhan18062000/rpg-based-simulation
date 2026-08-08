---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION
artifact_type: investigation
tags: [progression, simulation-quality]
---

# Investigation — TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION

## Both real, independent producers traced to confirmed, distinct root causes

### 1. `ConversionIntentResolver`'s `EQUIP_ITEM` path — gated behind an always-off feature flag

`src/domains/progression/resolver.py:37-44`'s `EQUIP_ITEM` branch is real, wired code, called from
`ProgressionConversionPhase.execute()` (`src/domains/progression/phase.py:73`), which is itself a
real, registered pipeline phase (`src/engine/pipeline.py:326`):

```python
update = run_phase("progression_conversion", update,
    lambda u: ProgressionConversionPhase.execute(state, u), "ENABLE_PROGRESSION_EVOLUTION")
```

**Confirmed via direct read**: `ENABLE_PROGRESSION_EVOLUTION` defaults to `FeatureMode.OFF`
(`src/domains/optimization/feature_flags.py:20`), and `grep -rln "ENABLE_PROGRESSION_EVOLUTION"
config/simulation_quality/profiles/` returns **zero matches** — no real corpus world profile ever
turns this flag on. This entire phase, and everything downstream of it (`EQUIP_ITEM`,
`REPAIR_GEAR`, `CRAFT_ITEM` conversion kinds — a real, separate "subjective progression decision"
subsystem distinct from `EvolutionSystem`'s own level-up-driven AP spending), is simply never
exercised anywhere in the current corpus. A clean, simple, confirmed "flag never turned on"
finding — **not** the same root cause as the sibling
`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD` ticket's own `EvolutionSystem` finding
(that one is gated by real gameplay pacing; this one is gated by a flag nobody has flipped).

Worth noting for whoever scopes a future fix: `ConversionIntentResolver.resolve()`'s own
`EQUIP_ITEM` branch hardcodes `slot_updates={EquipSlot.MAIN_HAND: "iron_sword"}` regardless of
`selected`'s own real item choice (comment: "We assume iron_sword stack exists in inventory to
equip") — even if the flag were flipped on, this looks like placeholder/incomplete logic, not a
fully general equip-any-item mechanism. Flagged, not fixed here (out of this investigation
ticket's own scope).

### 2. `EquipmentService.auto_equip()` — complete, tested, but has zero real callers

`src/core/equipment.py:201-233`'s `auto_equip()` is a real, well-formed, self-documenting function
("Scan inventory for better equipment and return an EntityUpdate if any slot should be changed" —
explicitly designed as a pure proposal function, doesn't mutate state itself) with real unit test
coverage (`tests/unit/resource/test_equipment_chests_storage.py`). **`grep -rln
"EquipmentService\." src/ --include=*.py` (excluding its own module) returns zero matches** — no
pipeline phase, AI goal scorer, or action system anywhere in `src/` ever calls it. This is
genuinely dead-but-correct code: a complete equip-upgrade mechanism that nothing in the real
engine ever invokes.

## Real conclusion: 2 confirmed, distinct, non-forced findings — no fix implemented

Both causes are real and fixable in principle, but **neither is a narrow, obviously-safe fix**:

- Flipping `ENABLE_PROGRESSION_EVOLUTION` on corpus-wide is exactly the kind of flag change this
  session's own `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING` investigation showed
  can carry real, non-obvious regressions (that ticket found a genuine pipeline bug only by
  actually testing the flip, not by reasoning about it statically). Flipping this flag needs the
  same real, controlled before/after verification, which is a fix-ticket's own job, not this
  investigation's.
- Wiring `auto_equip()` into the real pipeline requires a real design decision this investigation
  ticket has no mandate to make: which phase should call it, how often (every tick? on inventory
  change only?), and for which entities (all, or role-gated?) — none of that is specified anywhere
  in the current code or docs.

Per this ticket's own Scope ("this may not be a 'fix' ticket at all... report that honestly"), no
code change lands here. Both findings are documented in
`docs/audits/D21_entity_lifecycle_foundation_layers.md` as real, confirmed, actionable leads for
a future fix ticket, not forced into an unscoped implementation now.

## Docs Requiring Update
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`: record both confirmed findings.
