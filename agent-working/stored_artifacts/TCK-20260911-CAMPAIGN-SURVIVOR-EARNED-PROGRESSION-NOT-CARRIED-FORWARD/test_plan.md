# Test Plan — TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD

## Real evidence
- Real counterfactual (revert/re-test/restore, not code-read reasoning) confirming the pre-fix
  bug: a level=20 survivor with no carried attributes/equipment got `max_hp=100/atk=10/def_stat=5`
  (`EntityState`'s bare defaults) — identical to what a level-1 entity would get.
- `test_reconstructed_survivor_with_no_carried_progression_gets_default_attribute_stats_not_bare_combat_defaults`
  — post-fix, the same scenario now produces `max_hp=112/atk=12/def_stat=6` (the correct
  `get_effective_stats()` output for default attributes), proving the recompute call genuinely
  executes.
- `test_reconstructed_survivor_combat_stats_reflect_both_earned_attributes_and_carried_equipment`
  — a survivor with both carried equipment (`iron_sword`/`iron_plate`) and carried attributes
  (`strength=50`/`vitality=50`/`endurance=20`), asserting exact expected values (`max_hp=210`,
  `atk=45`, `def_stat=35`) computed independently from the documented formula — only possible if
  both contributions are present and correctly summed. Per peer review's explicit acceptance
  note: an equipment-only or attributes-only test would pass on a half-fix.
- `test_reconstructed_survivor_earned_identity_progression_is_carried` — `unspent_ap`,
  `learned_skills`, `active_breakthroughs`, `class_id`, `veterancy_points`/`rank`, `known_recipes`
  all carried.
- `test_reconstructed_survivor_wounds_and_scars_are_deliberately_reset_not_carried` — the
  deliberate divergence, asserted explicitly rather than left implicit.
- `test_entity_carry_forward_earned_progression_fields_default`,
  `test_entity_carry_forward_earned_progression_fields_round_trip`,
  `test_entity_carry_forward_from_dict_missing_earned_progression_keys` — `EntityCarryForward`'s
  own serialization contract for the 8 new fields, including the pre-existing-record
  missing-key case, matching the identity ticket's own precedent test shape.

## Regression suites run
- `tests/unit/domains/campaigns/` — 174 passed (full suite, including all new tests).
- `tests/integration/campaigns/` — 13 passed, 9 deselected (slow).
- `tests/unit/domains/campaigns/test_campaign_state.py` — 28 passed (serialization contract).
- Broader sweep on `rpg_depth`/`leveling`/`builder` keyword-matched tests — 122 passed.

## Acceptance criteria mapping
- Direct confirmation (not code-read reasoning) that reconstructed survivors currently return
  with default combat stats → done, via the real counterfactual above.
- All 7 `IdentityComponent` fields plus the full `AttributeComponent` added to
  `EntityCarryForward` and correctly threaded → done.
- Real fix verified by a real test using a survivor with both carried equipment and carried
  (non-default) attributes → done, exact-value assertions.
- `wounds`/`scars` non-carry recorded as an explicit, deliberate divergence → done, both in the
  ticket text and via a dedicated test.
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` filed as its own P2 ticket → done.
- No regression in `tests/unit/domains/campaigns/`, `tests/integration/campaigns/` → confirmed.
