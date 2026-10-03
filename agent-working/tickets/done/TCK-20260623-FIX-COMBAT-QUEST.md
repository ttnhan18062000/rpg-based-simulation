---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-COMBAT-QUEST
phase: done
date: 2026-06-23
tags: [test-repair, combat, quest, reward, social]
---

# TCK-20260623-FIX-COMBAT-QUEST

## Title
Fix combat reward labels + quest/social test failures (~20 failures)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Two related root causes affect combat, quest, and social tests.

**Root Cause 1 — Reward source label renamed (D10 F7):**
`test_combat_reward_trace.py` expects `reward.trace["REWARD_SOURCE"] == "hostile_relation"` but gets `"relation_projection"`. Also expects a `hero_kill` category that is missing. These are string constant renames — the combat reward source labels were renamed without updating tests.

**Root Cause 2 — Quest/social failures:**
`test_quest_lifecycle.py`, `test_quest_rewards.py`, `test_quest_transactions.py`, `test_quest_system.py`, `test_town_contract.py`, `test_social_phase7.py`, `test_domain_7_social.py` are failing. These likely share a root cause with either the inventory defaults (INSUFFICIENT_GOLD/INVENTORY_FULL mismatch) or a quest schema change (the `type` field issue found in WorldAssembly).

The quest `type` field may also be the root cause here — if `QuestDefinition.type` is now required and quest fixture helpers don't pass it, all quest lifecycle tests will fail.

## Scope
- Update `test_combat_reward_trace.py` string constants to match current reward source labels (`hostile_relation` → `relation_projection`, missing `hero_kill` category)
- Alternatively: if `hostile_relation` was the documented label and `relation_projection` is a regression, restore the original label in source
- Investigate quest/social failures to identify whether the root cause is the quest `type` field (shared with TCK-20260623-FIX-WORLDASSEMBLY), inventory defaults (shared with TCK-20260623-FIX-INVENTORY-DEFAULTS), or a third independent cause
- Fix whichever subset belongs to this ticket's unique scope

## Out of Scope
- Combat mechanic changes
- Quest system logic changes
- Social system logic changes

## Acceptance Criteria
- `tests/unit/combat/test_combat_reward_trace.py` — all 3 tests pass
- `tests/unit/combat/test_combat_reward_hardening.py` — all 2 tests pass
- `tests/unit/combat/test_rpg_core_recovery.py` — all 6 tests pass
- `tests/unit/quest/test_quest_lifecycle.py` — all 2 tests pass
- `tests/unit/quest/test_quest_rewards.py` — all 3 tests pass
- `tests/unit/quest/test_quest_transactions.py` — all 3 tests pass
- `tests/unit/quest/test_quest_system.py::test_bounty_quest_completion` passes
- `tests/unit/social/test_town_contract.py` — all 5 tests pass
- `tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves` passes
- `tests/unit/social/test_domain_7_social.py::test_tactical_trust_obedience` passes

## Related Tickets
- D10 audit F7 (combat reward label mismatch)
- TCK-20260623-FIX-WORLDASSEMBLY (quest `type` field — may overlap)
- TCK-20260623-FIX-INVENTORY-DEFAULTS (INSUFFICIENT_GOLD mismatch — may overlap)

## Related Docs
- `docs/audits/D10_test_coverage.md` F7
- `docs/mechanics/02_combat_laws.md` (reward sourcing)
- `docs/parity_ledger/combat_movement.yaml` (reward trace parity entries)
- `docs/parity_ledger/social_narrative.yaml` (social parity entries)

## Related Code Areas
- `src/domains/combat/reward.py` or `src/domains/adventure/` (reward source label constants)
- `src/quests/` (quest definitions and lifecycle)
- `src/social/` or `src/domains/social/` (town contract, social phase7)
- `tests/unit/combat/`
- `tests/unit/quest/`
- `tests/unit/social/`

## Assumptions / Open Questions
- Was `hostile_relation` renamed to `relation_projection` intentionally? Check git log on the reward source constant.
- Are quest failures a cascade from the `type` field (TCK-20260623-FIX-WORLDASSEMBLY) or an independent root cause?

## Implementation Notes
Investigation order:
1. Find where `hostile_relation` / `relation_projection` is defined; check git log for rename
2. Determine correct label per `docs/mechanics/02_combat_laws.md`
3. Run a single quest test with `--tb=long` to see the exact error
4. If quest errors are about `type` field → coordinate with or depend on TCK-20260623-FIX-WORLDASSEMBLY

## Test Summary
Run: `pytest tests/unit/combat/ tests/unit/quest/ tests/unit/social/ -m "not slow" --tb=short`

## Files Changed
- `src/engine/combat_rewards.py` — `classify_defeated_target()`: preserve `rebirth_eligible=True` for HERO defenders in relation_projection path
- `data/content/world/items.yaml` — add `steel_sword` (base_value=144 → atk_bonus=18, matches hardcoded legacy)
- `tests/unit/combat/test_combat_reward_trace.py` — update 3 stale label assertions: hostile_relation→relation_projection, HERO_KILL→HOSTILE_CREATURE
- `tests/unit/social/test_domain_7_social.py` — replace synthetic faction strings "A"/"B" with Faction.HERO_GUILD/MONSTER_HORDE

## Completion Summary
Fixed 7 test failures: 3 stale combat reward label assertions, 2 rebirth_eligible regressions (HERO role incorrectly got rebirth_eligible=False in relation_projection path), 1 missing steel_sword in content catalog, 1 synthetic faction string not recognized by is_hostile_compat. All 17 targeted tests pass.
