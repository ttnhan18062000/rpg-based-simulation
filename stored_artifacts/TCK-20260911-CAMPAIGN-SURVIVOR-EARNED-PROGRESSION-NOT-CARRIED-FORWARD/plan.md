# Plan — TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD

## Disposition
Retitled and re-tiered from hotfix to standard: the missing mechanism is carry-forward, not
recompute — combat stats are a function of attributes/equipment/skills, not evolution_level. Full
earned-progression field audit done per peer review's explicit request (the same audit style as
the identity ticket): 1 full component (`AttributeComponent`) + 7 `IdentityComponent` fields
(`unspent_ap`, `learned_skills`, `active_breakthroughs`, `class_id`, `veterancy_points`,
`veterancy_rank`, `known_recipes`) added to `EntityCarryForward`.

## Steps
1. Extend `EntityCarryForward` (`src/domains/campaigns/state.py`) with the 8 new fields
   (1 dict + 7 scalar/set), symmetric `to_dict()`/`from_dict()`.
2. Extend `_extract_entity_carry_forwards()` to populate them, unconditional (not gated by
   `carry_forward_rules`), matching the identity ticket's own precedent.
3. Extend the survivor-reconstruction `V2EntityBuilder` call in `_build_initial_state()` with the
   7 identity fields and a new `.attributes(...)` call.
4. After equipment resolution, call `SkillScalingService.get_effective_stats()` (the same,
   unmodified function the live tick-time path uses) and apply the result to `combat`, including
   setting `hp = max_hp` (full health — consistent with wounds/scars-reset framing).
5. Real counterfactual confirmation of the pre-fix bug (git-diff-save, revert, test, restore,
   re-test) before finalizing test coverage — captured in investigation.md.
6. Real test proving the fix with a survivor who has both carried equipment and carried
   attributes, asserting exact expected values.
7. Real tests for the 7 identity-field carry-forwards, the deliberate wounds/scars exclusion, and
   `EntityCarryForward`'s own serialization round-trip for the new fields.
8. File `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` for the veterancy dead-multiplier
   finding — not this ticket's to fix.
9. Close this ticket, with the wounds/scars exclusion recorded explicitly in the Completion
   Summary, not left implicit.

## Guardrails
- Do not modify `get_effective_stats()`/`recalculate_combat_stats()`'s own formula — reuse
  unmodified, same as the live tick-time path.
- Do not carry `wounds`/`scars` — deliberate divergence, recorded explicitly.
- Do not wire `VeterancyService.get_stat_multiplier()` in as part of this ticket — separate,
  filed ticket, real design decision not resolved here.
