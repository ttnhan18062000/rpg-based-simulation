---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [progression, simulation-quality]
---

# Test Plan — TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION

## New test — `tests/unit/movement/test_tactical_movement.py`

`test_opportunity_attack_lethal_hero_defender_triggers_rebirth` — real opportunity-attack scenario
(mirroring the existing `test_opportunity_attack_lethal_grants_resource_transfers_to_attacker`
fixture pattern) where the defeated defender is `EntityRole.HERO` with
`lifecycle.generation < 4`: asserts the full-pipeline result carries `generation_delta == 1` on
the victim's own lifecycle update (via `refined.entity_updates[victim_id].lifecycle`).

## Regression guard

`pytest tests/unit/movement/test_tactical_movement.py tests/unit/combat/ -q` — must still pass
unchanged for every non-HERO/non-rebirth scenario (confirms the port doesn't alter existing
monster-kill behavior).

## Real re-verification (not just unit test)

Re-run `make simq-long-run-lifecycle-observation` on `hero_guild_routing` post-fix — real,
disclosed as run-dependent (may not flip `life_arc_detector_reachable` within any single run given
how rare reaching 4+ real HERO deaths still is), but the unit test's own direct pipeline assertion
is the primary, deterministic proof of the fix.
