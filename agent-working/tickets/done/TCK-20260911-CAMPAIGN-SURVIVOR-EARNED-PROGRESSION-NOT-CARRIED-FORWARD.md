---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD
phase: done
date: 2026-09-11
tags: [world, architecture]
---

# TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD

## Title
Reconstructed survivors lose earned attributes, skills, class tier, breakthroughs, unspent AP, veterancy, and known recipes — combat stats regress to bare defaults regardless of carried level

**Retitled and re-tiered 2026-09-12** (was "...combat stats not recomputed... hotfix"). Investigation
found the missing mechanism is carry-forward, not recompute: combat stats are a function of
`AttributeComponent` + equipment + skills, not of `evolution_level` directly — no amount of
recomputing fixes a survivor whose attributes came back at defaults. `EntityCarryForward` already
carries `level`, but `level` has no mechanical effect on its own; its value lives entirely in the
attributes it granted along the way. Re-tiered from hotfix to standard: this is the same class and
scale of fix as `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION`'s own
widening from 2 fields to 6, for the same reason — the field list was arbitrary, the invariant
("a survivor retains what it earned") is the real boundary.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION`'s own
investigation, while determining whether it was safe to leave `combat.hp`/`.atk`/`.def_stat`
uncarried on the assumption they're recomputed from carried `level`. They are not, for a
reconstructed survivor specifically — and, as this ticket's own investigation found, they cannot be,
from `level` alone, under any recompute.

`src/engine/apply.py`'s `stats_dirty` recompute path (`SkillScalingService.get_effective_stats()`,
called around line 573) only fires when comparing an incoming `EntityUpdate` against the entity's
own current tick state within an already-running episode. A freshly-reconstructed survivor has no
prior-tick state to compare against, so `stats_dirty` never fires and `combat` sits at
`EntityState`'s own bare defaults (100 HP / 10 ATK / 5 DEF) regardless of carried level.

**But calling the recompute function at reconstruction time would not fix this either, because
combat stats are not a function of `evolution_level` at all.** Traced `get_effective_stats()` →
`LevelingService.recalculate_combat_stats()` (`src/progression/leveling.py:76-`) in full:
`max_hp = base_hp + (attributes.vitality * 2) + (attributes.endurance * 0.5) + gear_hp`,
`atk = base_atk + (attributes.strength * 0.5) + gear_atk`, `def_stat = base_def + (attributes.
vitality * 0.3) + gear_def` — no `level` parameter anywhere in the chain. Level only enters
indirectly: leveling up grants `unspent_ap_delta` (5 AP/level via `LevelingService.
_execute_level_up()`) that gets spent on specific attributes via a separate, path-dependent
mechanism. `EntityCarryForward` does not carry `AttributeComponent`. So a reconstructed survivor's
attributes are always level-1 defaults, and calling the recompute function against them would
produce stats close to the bare default regardless of the survivor's real carried level — the
recompute function has nothing real to recompute from.

**Full earned-progression audit, per peer review's explicit request (the same kind of audit that
scoped the identity ticket) — every field confirmed via its real mid-episode mutation path, not
guessed from its name:**

| Field | Component | Confirmed via | Direct `get_effective_stats()` input? |
|---|---|---|---|
| `strength`/`agility`/`vitality`/`endurance`/`intelligence`/`spirit`/`wisdom`/`perception`/`charisma` | `AttributeComponent` (all 9) | The dominant driver of `max_hp`/`atk`/`def_stat`/`evasion` (see formula above) | Yes — the primary `attributes` arg |
| `unspent_ap` | `IdentityComponent` | Granted `+5`/level via `LevelingService._execute_level_up()`; banked, not auto-spent | No (but real earned progression lost if not carried) |
| `learned_skills` | `IdentityComponent` | Mutated live via `IdentityUpdate.learned_skills`, not a static archetype default | Yes — passive skill bonuses |
| `active_breakthroughs` | `IdentityComponent` | Mutated live via `patches.py`; consumed by `BreakthroughService.apply_bonuses()` | Yes |
| `class_id` | `IdentityComponent` | Mutated live via `class_id_set`; defaults to `"NOVICE"` otherwise (a real class-tier reset if not carried); consumed by `ClassTierService.apply_bonuses()` | Yes |
| `veterancy_points`/`veterancy_rank` | `IdentityComponent` | Accumulated via `VeterancyService.process_points()`, wired live through `patches.py`/`apply.py` | No — see note below |
| `known_recipes` | `IdentityComponent` | Real, player-earned progression by the same test ("what does a survivor accumulate that should persist") | No (crafting-relevant, not combat) |

**Note on veterancy**: `VeterancyService.get_stat_multiplier(rank)` — the function that would apply
rank as a real +5%/rank combat bonus — has zero real callers anywhere in `src/`. Veterancy
accumulates correctly but never affects combat stats today, a separate, pre-existing gap (filed as
`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`, not this ticket's to fix). Carrying
`veterancy_points`/`veterancy_rank` forward is still correct — preserving real earned state is right
even while its downstream application is separately incomplete.

**Checked and explicitly excluded, not silently omitted** (per peer review: an implicit decision a
later reader can't distinguish from an oversight is the same failure this whole batch keeps finding
from the other direction):
- `craft_target` — transient in-progress intent, not accumulated progression. Belongs with
  `cooldowns` (both reset).
- `territory_maturity` — confirmed via `src/world/creature_territory.py` to be a creature/NPC
  territorial mechanic, not survivor/hero-relevant.
- `wounds`/`scars` (`CombatComponent`) — **a deliberate divergence, not an oversight.** Under the
  "a survivor retains what it earned" invariant this ticket establishes, scars are arguably earned
  too — but reconstruction already resets them to fresh via `V2EntityBuilder().build()`'s own
  defaults (existing, already-shipped behavior), and that is being kept: survivors are narratively
  recovered/healed between episodes. Recorded explicitly here so a future reader sees a documented
  choice, not a gap to "fix" by accident.
- `cooldowns` — tick-scoped transient state, meaningless across an episode boundary.

## Scope
- Add `AttributeComponent` (all 9 fields) and the 6 `IdentityComponent` fields above
  (`unspent_ap`, `learned_skills`, `active_breakthroughs`, `class_id`, `veterancy_points`,
  `veterancy_rank`, `known_recipes` — 7 total) to `EntityCarryForward`, following the same pattern
  `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION` already established for
  its own 6 identity fields.
- Wire these carried values into `_build_initial_state()`'s survivor-reconstruction branch — the
  `V2EntityBuilder(eid)....identity(...)` call already sets `evolution_level`/`evolution_points`;
  extend it (or the builder itself) to also set the 7 new `IdentityComponent` fields and a real
  `AttributeComponent`.
- Call `SkillScalingService.get_effective_stats()` once at reconstruction time, using the survivor's
  now-real carried attributes, equipment (already carried), learned_skills, traits (already
  carried), class_id, and active_breakthroughs — so `combat.max_hp`/`.atk`/`.def_stat`/`.evasion`
  reflect their real accumulated power, the same way an in-episode level-up would set it.
- Real test proving the fix with a survivor who has **both** carried equipment and carried
  attributes — assert the resulting stats differ from bare defaults in a way attributable to each
  (an equipment-only fixture would pass on a half-fix, which this ticket explicitly does not accept
  — see Assumptions).

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION`'s own identity fields
  (`kind`/`role`/`faction`/`properties`/`traits`/`personality`) — already fixed there, not
  reopened here.
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` — the separate, pre-existing gap that
  `VeterancyService.get_stat_multiplier()` is never called anywhere; filed as its own ticket.
- `craft_target`, `territory_maturity`, `wounds`/`scars`, `cooldowns` — checked and explicitly
  excluded, see the audit table above.
- Any change to `get_effective_stats()`/`recalculate_combat_stats()`'s own formula, or to the
  tick-time `stats_dirty` recompute path in `apply.py` — this ticket only adds a reconstruction-time
  call using the same, unmodified function.

## Acceptance Criteria
- [x] Direct confirmation (not just code-read reasoning) that reconstructed survivors currently
      return with default combat stats regardless of carried level. Done via a real
      counterfactual — saved the implementation diff, reverted to HEAD, ran the exact scenario
      (confirmed `max_hp=100/atk=10/def_stat=5`), restored the implementation.
- [x] All 7 `IdentityComponent` fields plus the full `AttributeComponent` are added to
      `EntityCarryForward` and correctly threaded through reconstruction. Done.
- [x] Real fix: survivor combat stats recomputed at reconstruction time from carried attributes,
      equipment, skills, class, and breakthroughs — verified by a real test using a survivor with
      **both** carried equipment and carried (non-default) attributes, asserting exact expected
      values (`max_hp=210`, `atk=45`, `def_stat=35`), not merely "differs from default" — only
      possible if both contributions landed and summed correctly.
- [x] `wounds`/`scars` non-carry is recorded as an explicit, deliberate divergence in this
      ticket's own Completion Summary, not left implicit. Done, both in this ticket's text and
      via a dedicated test.
- [x] `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` filed as its own P2 ticket. Done.
- [x] No regression in `tests/unit/domains/campaigns/`, `tests/integration/campaigns/`. 174 + 13
      passed.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION` (origin of this finding;
  the precedent for widening a narrow field list to the real invariant boundary)
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (the first ticket in this same
  reconstruction-branch arc)
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (new, filed from this ticket's own
  veterancy check — dead-code finding, not this ticket's to fix)

## Related Docs
None yet.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

## Related Code Areas
- `src/domains/campaigns/orchestrator.py` (`_extract_entity_carry_forwards()`,
  `_build_initial_state()`'s survivor-reconstruction branch)
- `src/domains/campaigns/state.py` or wherever `EntityCarryForward` is defined (the dataclass to
  extend)
- `src/core/builder.py` (`V2EntityBuilder`, its `.identity()`/`.combat()`/`.attributes()` methods)
- `src/engine/rpg_depth.py` (`SkillScalingService.get_effective_stats()`)
- `src/progression/leveling.py` (`LevelingService.recalculate_combat_stats()`, for reference only —
  not modified)

## Assumptions / Open Questions
- ~~Whether `AttributeComponent` also needs carrying for the recompute to be meaningful is the real
  open question here~~ Resolved: yes, confirmed the dominant driver; full field audit done, see the
  table above.
- Acceptance bar, explicit per peer review: a fix proven only against a survivor with carried
  equipment (and default attributes) would pass while still failing an unequipped high-level
  survivor — rejected as shipping something that doesn't satisfy its own AC. The real test must use
  a survivor with both.

## Implementation Notes
Traced `get_effective_stats()` → `LevelingService.recalculate_combat_stats()` in full before
implementing anything — confirmed combat stats are a function of `AttributeComponent` + equipment
+ skills, not `evolution_level` directly. Reported this finding to peer review before proceeding
(it invalidated the ticket's own original "narrow, hotfix" framing); peer review re-tiered to
standard and asked for a full earned-progression audit, the same style as the identity ticket's
own field-list widening, rather than trimming the fix to fit the original hotfix tier.

Audited every `IdentityComponent` field against its real mid-episode mutation path (`patches.py`,
the leveling/veterancy/breakthrough services) rather than guessing from field names — surfaced 7
real fields to add (1 component + 6 scalars/sets), one genuine dead-multiplier finding
(`VeterancyService.get_stat_multiplier()`, zero real callers — filed separately, not fixed here),
and 4 explicit exclusions with recorded reasoning (`craft_target`, `territory_maturity`,
`wounds`/`scars`, `cooldowns`).

Captured the pre-fix bug via a real counterfactual rather than trusting code-read reasoning alone,
per this ticket's own AC: saved the implementation diff (`git diff` of the two changed files),
reverted both to `origin/main`'s HEAD, ran the exact repro scenario (confirmed
`max_hp=100/atk=10/def_stat=5` — `EntityState`'s bare defaults, unaffected by the survivor's real
level=20), restored the implementation via `git apply` on the saved diff, and re-verified the fix
produces the correct, different values.

Extended `EntityCarryForward` with the 8 new fields (unconditional, not gated by
`carry_forward_rules`, matching the identity ticket's own precedent), threaded them through
`_extract_entity_carry_forwards()` and the survivor-reconstruction `V2EntityBuilder` call, and
added a real `SkillScalingService.get_effective_stats()` call at reconstruction time — the same,
unmodified function the live tick-time `stats_dirty` path in `apply.py` uses — using the
survivor's real carried attributes/equipment/skills/class/breakthroughs. `hp` set to the newly
derived `max_hp` (full health), consistent with the wounds/scars-reset framing.

Proved the fix per peer review's explicit acceptance note: a test with a survivor carrying BOTH
real equipment (`iron_sword`/`iron_plate`) and real attributes (`strength=50`/`vitality=50`/
`endurance=20`), asserting exact expected values computed independently from the documented
formula (`max_hp=210`, `atk=45`, `def_stat=35`) — only possible if both contributions landed and
summed correctly, not just "differs from bare default," which an equipment-only or
attributes-only fixture would also satisfy on a half-fix.

Filed `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` for the dead-multiplier finding, per
peer review's explicit instruction — a genuine "earned progression with no mechanical effect"
shape, the same class as the knowledge-layer and behavior-analytics-pipeline findings from the
prior batch.

`wounds`/`scars` recorded explicitly as a deliberate divergence, not silently excluded: under the
"a survivor retains what it earned" invariant this ticket establishes, scars are arguably earned
too, but reconstruction intentionally keeps them reset to fresh — survivors are narratively
recovered between episodes. Both the ticket text and a dedicated test
(`test_reconstructed_survivor_wounds_and_scars_are_deliberately_reset_not_carried`) make this
explicit, so a future reader sees a documented choice rather than a gap to "fix" by accident.

## Test Summary
4 new tests in `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (default-attribute
recompute proof, both-contributions exact-value proof, identity-field carry-forward, deliberate
wounds/scars exclusion) plus 3 new tests in `tests/unit/domains/campaigns/test_campaign_state.py`
(serialization default/round-trip/missing-key contract for the 8 new fields, matching the identity
ticket's own precedent test shape). Full regression: `tests/unit/domains/campaigns/` — 174 passed;
`tests/integration/campaigns/` — 13 passed, 9 deselected (slow); broader `rpg_depth`/`leveling`/
`builder`-keyword sweep — 122 passed. No regressions.

## Files Changed
- `src/domains/campaigns/state.py` — `EntityCarryForward` extended with `attributes`,
  `unspent_ap`, `learned_skills`, `active_breakthroughs`, `class_id`, `veterancy_points`,
  `veterancy_rank`, `known_recipes`; `to_dict()`/`from_dict()` updated symmetrically.
- `src/domains/campaigns/orchestrator.py` — `_extract_entity_carry_forwards()` populates the new
  fields; survivor-reconstruction branch threads them through `V2EntityBuilder` and calls
  `SkillScalingService.get_effective_stats()` to derive real combat stats.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — 4 new tests.
- `tests/unit/domains/campaigns/test_campaign_state.py` — 3 new tests.
- `tickets/todos/TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED.md` — new.
- `stored_artifacts/TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD/{investigation.md,plan.md,test_plan.md}`
  — full evidence trail.
- `tickets/done/TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD.md` — this
  file, closed (renamed from its original filename to match the retitled root cause).

## Completion Summary
Retitled and re-tiered from a hotfix "call the recompute function" fix to a standard "carry the
earned state the recompute function actually needs" fix, after tracing `get_effective_stats()`'s
real formula and confirming level has no mechanical effect on combat stats on its own — the
missing mechanism was carry-forward, not recompute. A peer-requested full earned-progression audit
(the same style as the identity ticket's own field-list widening) surfaced 7 real fields to carry
(1 component + 6 scalars/sets), one separate dead-multiplier finding filed as its own ticket, and
4 explicit, recorded exclusions.

Confirmed the pre-fix bug via a real counterfactual (revert/test/restore), not code-read reasoning
alone. Implemented the carry-forward and reconstruction-time recompute using the same, unmodified
stat-derivation function the live tick-time path uses. Proved the fix with a survivor carrying
both real equipment and real attributes, asserting exact expected values — the acceptance bar peer
review explicitly required to rule out shipping a half-fix that passes on equipment alone.

**`wounds`/`scars` are intentionally not carried forward — survivors are narratively recovered
between episodes.** This is a deliberate divergence from the "retains what it earned" invariant
this ticket otherwise establishes, recorded explicitly here (and via a dedicated test) so it is
never mistaken for an oversight by a future reader.
