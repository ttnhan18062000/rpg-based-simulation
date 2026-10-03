---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-MOVEMENT-OA-TEST-FACTION-FIXTURE
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-MOVEMENT-OA-TEST-FACTION-FIXTURE

## Title
Fix `test_normal_move_triggers_oa`'s stale `faction=2` fixture — uses a non-hostile faction for the
"monster" entity

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Part of a batch of 7 tickets fixing genuinely pre-existing CI failures. This one:
`tests/unit/movement/test_movement_spatial_regression.py::test_normal_move_triggers_oa` fails with
`assert 0 > 0` (the real assertion is `updates[1].combat.damage_taken > 0`, which evaluates to
`0 > 0`).

Root cause (confirmed via investigation, including an experimental fix verification): the test's
"monster" entity uses `faction=2` (`Faction.TOWN_COUNCIL`), which is not hostile toward the hero's
default `Faction.HERO_GUILD`. This was harmless when the test was authored
(`56211688`, "Resource V2 Implementation", 2026-05-18 — faction was raw shorthand for "some other
faction"), but `ff0235a7` ("Implement world restructure, generation engine, documentation pages
#11", 2026-06-12) introduced content-driven faction semantics
(`src/content_semantics/faction.py::FactionSemanticsService.is_hostile_compat`) that real attack
legality now depends on — `LegalityServiceV2.verify_attack_legality` correctly rejects the attack
as `FRIENDLY_FIRE_ILLEGAL` since `town_council` isn't hostile toward `hero_guild` in the real
content data. `CombatResolutionSystem.resolve_multi_attack` then has zero legal attackers, producing
`damage_taken=0` — exactly matching the observed failure. This matches the documented Friendly-Fire
Law (`docs/mechanics/02_combat_laws.md:112-113`). Production code is correct and consistent with the
Mechanics Bible; only the test's fixture literal is stale. Experimentally confirmed: substituting
`faction=Faction.MONSTER_HORDE` produces `damage_taken=4`, `outcome_kind='SURVIVE'`,
`is_opportunity_attack=True` — the test's original intent.

## Scope
- Change `monster = create_mock_entity(2, (2.0, 1.0), faction=2)` to use
  `faction=Faction.MONSTER_HORDE` (matching this file's own existing convention of using the named
  enum elsewhere, e.g. line 119) at `tests/unit/movement/test_movement_spatial_regression.py:166`.

## Out of Scope
- Any other of the 7 CI failures in this batch (each has its own ticket).
- Any change to `LegalityServiceV2`, `FactionSemanticsService`, or combat resolution logic — all
  confirmed correct and matching the documented Friendly-Fire Law.

## Acceptance Criteria
- [ ] `test_normal_move_triggers_oa` uses a genuinely hostile faction for the "monster" entity.
- [ ] `test_normal_move_triggers_oa` passes.
- [ ] No other test in the same file regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
- `docs/mechanics/02_combat_laws.md` (Friendly-Fire Law, §ref line 112-113 — confirms current
  production behavior is correct and documented; no doc change needed)

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/unit/movement/test_movement_spatial_regression.py`

## Implementation Notes
Changed `faction=2` to `faction=Faction.MONSTER_HORDE`, matching the named-enum convention already
used elsewhere in the same file (e.g. line 119). `Faction` was already imported.

## Test Summary
- `pytest tests/unit/movement/test_movement_spatial_regression.py -v`: 5 passed (all tests in the
  file, no regressions).

## Files Changed
- `tests/unit/movement/test_movement_spatial_regression.py` — line 166, `faction=2` →
  `faction=Faction.MONSTER_HORDE`.

## Completion Summary
Fixed the stale test fixture: the "monster" entity now uses a genuinely hostile faction, matching
the test's own original intent (an opportunity attack should trigger). Production combat-legality
code was confirmed correct throughout — it correctly rejects attacks against non-hostile factions
per the documented Friendly-Fire Law (`docs/mechanics/02_combat_laws.md`); only the test's fixture
was stale, dating to before content-driven faction semantics were introduced.
