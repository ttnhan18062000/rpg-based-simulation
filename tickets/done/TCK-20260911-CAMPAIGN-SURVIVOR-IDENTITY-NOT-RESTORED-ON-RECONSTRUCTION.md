---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION
phase: done
date: 2026-09-11
tags: [world, architecture, simulation-quality]
---

# TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION

## Title
Survivor reconstruction did not restore spawn-time identity — fixed via full
kind/role/faction/properties/traits/personality carry-forward; a real 3-episode campaign now
completes at full length (episode 2: tick 150, was 52), meeting the campaign-completion
acceptance bar transferred from `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while verifying `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own
real 3-episode acceptance run. That ticket's position fix is confirmed correct with direct
evidence — episode 1's 13 survivors and episode 2's 9 survivors both reconstruct on fully distinct,
legal tiles, zero `LAW-SPAWN-OCCUPANCY` violations either time. But episode 2 still stalled at
tick 52 (`STALL_THRESHOLD=50` consecutive zero-event ticks) despite the position fix — a different
failure, not a recurrence.

Dumping episode 2's reconstructed entities found the real, confirmed root: every one of episode 2's
9 entities had `kind="entity"` (the literal hardcoded string
`EntityState(id=eid, kind="entity")` — never the real archetype, `"human"`/`"goblin"`/etc.) and
`identity.faction=0` (the bare `IdentityComponent` default) uniformly.

**A direct field-level audit — comparing exactly what `ArchetypeEntityFactory.build_entity()` (the
real spawn path) sets against what `_build_initial_state()`'s survivor-reconstruction branch sets —
found this is not a two-field gap.** A real spawn sets `kind`, `identity.role`, `identity.faction`,
`identity.properties`, `identity.traits`, and `identity.personality`, all from the same single block
of spawn-time construction code. The survivor-reconstruction branch sets **none** of them —
`EntityCarryForward` never captured any, and reconstruction builds every entity from
`EntityState`'s own bare dataclass defaults for all six.

**The governing invariant, and the reason this ticket is scoped by that invariant rather than by an
enumerated field list**: *a reconstructed survivor must be identity-equivalent to a spawned entity*
— indistinguishable in `kind`/`role`/`faction`/`properties`/`traits`/`personality`, not merely
"restore whichever fields someone found a consumer for." The second framing ages badly: the next
field added to `build_entity()` silently becomes a new, undiscovered divergence, and whoever finds
it has to re-run this same audit to rediscover the same boundary. Fields verified to be genuinely
unset even by a *real spawn* (`class_id`, `life_stage`, `learned_skills`, `known_recipes`,
`veterancy_points`/`.veterancy_rank`, `unspent_ap`, `territory_maturity`, `active_breakthroughs`,
`cooldowns`, `group_id`, `latest_intent_results`) are correctly out of scope — the invariant is
"match what a spawn actually does," not "carry everything."

**Per-field evidence, not assumed impact:**
- `identity.role` (defaults to `0` = `EntityRole.HERO`): real, load-bearing consumers confirmed by
  direct grep — `regional_sovereignty.py` (HERO-only region-ownership checks),
  `camp.py`/`spawn.py`/`creature_territory.py` (MONSTER-role gating),
  `domains/adventure/scoring.py` (HERO/GUARD/SHOPKEEPER route-scoring branches),
  `domains/cooperation/providers.py`. Any surviving non-HERO entity (e.g. a `goblin`) would
  misreport as HERO after reconstruction — arguably the strongest single candidate for the actual
  stall cause of the set, given how pervasively role gates behavior.
- `identity.properties` — **this finding partially corrects the original, narrower version of this
  ticket.** `get_faction_id_str()` (`src/content_semantics/faction.py:42-59`) checks
  `identity.properties["faction_id"]` *first*, only falling back to the bare `identity.faction` int
  if that key is absent. Fixing `identity.faction` alone — the original scope — would have set a
  value the resolver only consults *second*, while the first lookup (`properties`) stayed empty.
  That fix would have looked complete and may not have actually worked.
- `identity.traits` — no clearly load-bearing consumer found during this audit. Carried anyway,
  per the governing invariant above: "no consumer found" is a reason to ask whether `traits` itself
  is unused elsewhere (a separate, possible dead-code question, not explored here), not a reason to
  leave reconstruction diverging from spawn.
- `identity.personality` (defaults to `PersonalityComponent()`'s own all-zero values): matches an
  **exact, already-fixed precedent** — `TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY` fixed
  this identical "every entity at all-zero personality" bug once already, for the episode-0
  catalog-spawn path. The survivor-reconstruction branch carries the identical, unfixed instance of
  the same bug class.

**A related, separate divergence was found and deliberately NOT folded in here**: reconstructed
survivors' `combat.hp`/`.max_hp`/`.atk`/`.def_stat` are also not recomputed from their carried
`evolution_level` at reconstruction time (the real stats-recompute path only fires on a level
*increase relative to the entity's own current tick state*, which never applies to a freshly-built
initial entity). Different fix shape (recompute, not carry) and different blast radius — filed
separately: `TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION`.

**What this is NOT (yet) confirmed to be**: the cause of episode 2's tick-52 stall specifically.
Episode 1's survivors were reconstructed by the exact same branch, with the exact same identity
defects, and episode 1 completed its full 150-tick length without stalling. "Broken identity →
degenerate behavior → stall" therefore cannot be the whole mechanism on its own, or episode 1
should have stalled too — unless cast size, cumulative effect across two reconstructions, or some
other factor is also part of the real explanation. This remains the ticket's own open question, not
a foregone conclusion the fix is built around.

## Scope
- Fix the confirmed divergence: thread `kind`, `identity.role`, `identity.faction`,
  `identity.properties`, `identity.traits`, and `identity.personality` through
  `EntityCarryForward`, extraction (`_extract_entity_carry_forwards()`), and reconstruction
  (`_build_initial_state()`'s survivor branch), the same locations `last_position` was added by
  this ticket's predecessor.
- If, during implementation, `_build_initial_state()`'s survivor branch starts accumulating enough
  special-case field-by-field logic to become hard to follow inline, extract it into its own
  module the way `src/domains/campaigns/survivor_placement.py` already did for position — say so
  rather than silently letting the branch become a pile of cases. Not pre-decided; a real call to
  make once the actual diff shape is visible.
- **Open question, must be investigated with real evidence before or alongside the fix, not
  assumed**: what actually causes episode 2's stall? Real instrumentation (an event-stream
  listener, matching `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`'s own
  `_CollectingRecorder` pattern), not guessing from static entity dumps. Three outcomes are all
  acceptable and must be recorded as what they are, not overclaimed: (1) identity fixed, episode 2
  completes — *consistent with* the identity gap being the cause, not proof unless instrumented;
  (2) identity fixed, episode 2 still stalls — a third layer exists, file it, the acceptance bar
  moves again; (3) identity fixed, the stall changes shape (different tick, different signature) —
  the most informative outcome, chase it.
- **The acceptance bar this ticket owns, transferred explicitly from
  `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`**: a real 3-episode
  `campaign_life_arc`-shaped run (`frontier_living_world`) completes all three episodes at their
  configured tick length, no early stall. If it doesn't — if a third defect is waiting behind this
  one — that defect gets found with the same discipline and the bar moves again to whichever
  ticket owns it. It must not quietly disappear into a pile of individually-true, individually-
  closed tickets that never add up to a working campaign.

## Out of Scope
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own position-resolution
  fix — confirmed correct and closed on its own narrower claim; not reopened here.
- `TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION` — filed
  separately, different fix shape, not folded in here.
- `class_id`, `life_stage`, `learned_skills`, `known_recipes`, `veterancy_points`/`.veterancy_rank`,
  `unspent_ap`, `territory_maturity`, `active_breakthroughs`, `cooldowns`, `group_id`,
  `latest_intent_results` — confirmed, by direct audit, to be unset even by a real spawn; not part
  of this divergence, not widened into scope.
- `AttributeComponent` (STR/INT/etc.) carry-forward — not part of the confirmed identity divergence
  audited here; if the combat-stats ticket's own Investigate finds it's needed for a meaningful
  recompute, that's that ticket's own scope question, not this one's.

## Acceptance Criteria
- [x] `kind`, `identity.role`, `identity.faction`, `identity.properties`, `identity.traits`, and
      `identity.personality` are threaded through `EntityCarryForward`, extraction, and
      reconstruction, matching exactly what a real spawn sets for each.
- [x] A real test confirms a reconstructed survivor and a freshly-spawned entity are identity-
      equivalent for all six fields (not spot-checked on one or two).
      `test_reconstructed_survivors_are_identity_equivalent_to_the_real_extracted_snapshot`
      (`tests/integration/campaigns/test_survivor_identity_reconstruction.py`) runs the real
      pipeline end to end (real episode-0 spawn → real `run_episode()` completion → real
      `_extract_entity_carry_forwards()` → real `_build_initial_state()` reconstruction) and
      compares all six fields for every alive survivor, not a mocked field-by-field check.
- [x] Real evidence (not inference) for what actually caused episode 2's stall — recorded as what
      it actually is, not overclaimed: a real, controlled before/after comparison (same manifest,
      same seeds, only the identity fields changed) shows episode 2 completing at tick 150
      (full configured length) after this fix, versus the confirmed prior stall at tick 52. This
      is **outcome 1 of the three predicted in Scope — "identity fixed, episode 2 completes" —
      which is *consistent with* the identity gap being the cause, not independently proven via
      granular event-type instrumentation** (an event-stream listener comparing which specific
      event types changed was not additionally run, given the coarser but still real,
      controlled tick-completion comparison already demonstrates the fix works end to end; not
      claimed as a fully dissected causal mechanism). Episode 1's own prior completion (despite
      the identical defects) is accounted for, not ignored: it remains real, unexplained evidence
      that "broken identity" alone wasn't sufficient to guarantee a stall — consistent with,
      not proof against, "broken identity was necessary for episode 2's specific stall."
- [x] A real 3-episode `campaign_life_arc`-shaped run (`frontier_living_world`) completes all
      three episodes at their configured tick length, with zero `LAW-SPAWN-OCCUPANCY` violations
      throughout. **Confirmed, with real evidence — this outcome is the one that occurred.**
      `test_real_three_episode_campaign_completion_after_identity_fix` — episode 0: tick 150/150;
      episode 1: tick 150/150, zero occupancy violations; episode 2: **tick 150/150** (was 52
      before this fix), zero occupancy violations. The campaign-completion acceptance bar
      transferred from the predecessor ticket is met; it does not need to move again.
- [x] No regression in `tests/unit/domains/campaigns/` (170 passed), `tests/integration/campaigns/`
      (19 passed, plus the 3 new real acceptance tests across both this ticket and its
      predecessor, all passing).

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (done — origin of this
  finding; the campaign-completion acceptance bar is transferred here explicitly from that ticket)
- `TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION` (filed from this
  ticket's own investigation — a related, separate divergence in the same reconstruction branch,
  deliberately not folded in here)
- `TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY` (done — the exact same "all-zero personality"
  bug class, already fixed once on the episode-0 path)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — the sibling episode-0 catalog-spawn path,
  where all six identity fields ARE set correctly, the real reference for "correct"
- `TCK-20260911-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION`-adjacent work — anything depending on real
  multi-episode faction/role/hostility behavior is also blocked by this gap

## Related Docs
None yet.

## Related Stored Artifacts
- `staging_artifacts/TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION/
  investigation.md` — the field-level audit this ticket's own findings are drawn from

## Related Code Areas
- `src/domains/campaigns/state.py` (`EntityCarryForward` — needs all six identity fields)
- `src/domains/campaigns/orchestrator.py` (`_extract_entity_carry_forwards()`,
  `_build_initial_state()`'s survivor-reconstruction branch — same locations `last_position` was
  added; `kind="entity"` hardcoded literal at the `EntityState(...)` construction call)
- `src/content_semantics/faction.py` (`get_faction_id_str()` — confirmed the real downstream
  consumer affected by the `properties`/`faction` gap specifically)
- `src/entities/archetype_factory.py` (`ArchetypeEntityFactory.build_entity()`, lines 40-130 — the
  episode-0 path's own correct identity assignment; the reference this ticket's fix must match)
- `src/content_semantics/personality.py` (`build_personality_for_entity()` — the real personality-
  seeding function; confirm whether reconstruction should call this fresh or carry the survivor's
  own prior-episode personality verbatim, a real design question, not assumed)
- `src/world/regional_sovereignty.py`, `src/world/camp.py`, `src/world/spawn.py`,
  `src/world/creature_territory.py`, `src/domains/adventure/scoring.py`,
  `src/domains/cooperation/providers.py` — confirmed real `identity.role` consumers

## Assumptions / Open Questions
- ~~Personality: carry forward verbatim, or re-derive fresh?~~ **Resolved**: carry forward
  verbatim, matching level/xp's own treatment. `PersonalityComponent`'s own docstring states
  "Persistent psychological traits" — the dataclass's own stated intent is accumulated,
  persistent per-entity state, not a fresh per-episode roll. Re-deriving fresh via
  `build_personality_for_entity()` at reconstruction would silently give every survivor a *new*
  personality each episode, contradicting "persistent." No consumer of mid-episode personality
  mutation was found during this ticket's own investigation, supporting the "carry" reading.
- ~~The central open question, deliberately not pre-answered: does fixing identity alone make
  episode 2 complete at full length?~~ **Resolved, with real evidence, not inference**: yes — see
  Acceptance Criteria for the full before/after comparison. Recorded honestly as "consistent with
  the identity gap being the cause," not as an independently-proven causal mechanism (granular
  event-type instrumentation was not additionally run — the real, controlled tick-completion
  comparison already demonstrates the fix works end to end). Episode 1's own prior completion
  despite the identical defects remains real, accounted-for evidence that the relationship between
  "broken identity" and "stalls" isn't a simple, unconditional rule — consistent with the fix
  being necessary for episode 2's specific case, not proof that it's sufficient in general.

## Implementation Notes
Built exactly to the reframed scope locked in with peer review before implementation started: all
six identity fields (`kind`, `role`, `faction`, `properties`, `traits`, `personality`), matching
the governing invariant that a reconstructed survivor must be identity-equivalent to a spawned
entity, not a field-by-field enumeration.

- `EntityCarryForward` (`src/domains/campaigns/state.py`): added `kind: str = ""`,
  `role: int = 0`, `faction: int = 0`, `properties: dict`, `traits: Tuple[str, ...] = ()`,
  `personality: dict`. Defaults chosen to round-trip cleanly for pre-existing records serialized
  before these fields existed, and `traits` is serialized as a sorted list (`to_dict()`) for
  determinism, reconstructed as a sorted tuple.
- `_extract_entity_carry_forwards()`: captures all six unconditionally (same reasoning as
  `last_position` from the predecessor ticket — these aren't opt-in carry-forward preferences,
  they're the entity's own identity).
- `_build_initial_state()`'s survivor branch: `kind`/`role`/`faction`/`evolution_level`/
  `evolution_points`/`properties`/`traits`/`personality` are all built via
  `V2EntityBuilder(eid).kind(...).identity(...)` — **not** a raw `dataclasses.replace()` on the
  identity component directly. See the CI-failure note below for why.
- Personality carried verbatim rather than re-derived — see resolved Assumptions/Open Questions
  above for the reasoning.

Confirmed `TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION`'s own
premise with a direct code read before filing it (not assumed): the `stats_dirty` recompute path
in `src/engine/apply.py` only fires on a level increase *relative to the entity's own current tick
state*, which never applies to a freshly-reconstructed initial entity — a real, separate
divergence, correctly not folded into this ticket.

**Real CI failure, found and fixed post-merge-approval, before landing (2026-09-12):** the first
implementation built `role`/`faction` via a direct
`dataclasses.replace(identity_component, role=cf.role, faction=cf.faction, ...)` call. Two
architecture guard tests (`tests/architecture/test_role_set_identity_patch_only_guard.py`,
`tests/architecture/test_faction_mutation_write_paths.py`) correctly caught this as a real
violation: those two fields may only be mutated through the authoritative `IdentityPatch`'s own
apply step (live tick-time mutation) or `V2EntityBuilder`'s own initial-construction seeding
(pre-tick, not a live mutation) — the same allowlisted exemption `ArchetypeEntityFactory.
build_entity()` already relies on for a real spawn. Reconstruction IS initial-episode
construction, so the fix was to route through `V2EntityBuilder.identity()` (the sanctioned path)
instead of the raw dataclass replacement, matching the real spawn path's own construction style
exactly rather than inventing a second, competing way to set these two fields. Re-verified
against the full `tests/architecture`/`tests/docs`/`tests/integrity`/`tests/static`/
`tests/refactor` suite (246 passed) and the full campaigns suite (170 unit + 19 integration + 3
real acceptance tests, all producing identical results to before the fix) before re-pushing.

This routing turned out to be more than a check-satisfying fix, per peer review: it makes the
ticket's own governing invariant ("a reconstructed survivor is identity-equivalent to a spawned
entity") **structural** rather than something maintained by hand across a field list — spawn and
reconstruction now both build identity through the same `V2EntityBuilder`, so the next field added
to `ArchetypeEntityFactory.build_entity()` is far harder to silently miss on the reconstruction
side.

**Noted, not filed**: the architecture guards that caught this (`test_role_set_identity_patch_
only_guard.py`, `test_faction_mutation_write_paths.py`) scan file text, not the AST — an
explanatory code comment that happened to quote the banned `replace(...role=...faction=...)`
pattern literally tripped the same regex as real code would. Rephrasing the comment was the
correct response, not weakening the guard. A text-scanning guard will occasionally false-trip on
comments this way; one occurrence with a trivial fix isn't worth its own ticket, but a second
occurrence would establish a pattern worth handing to whoever owns the line-keyed-pinning-
brittleness class of finding.

## Test Summary
- `pytest tests/unit/domains/campaigns/ -q` — 170 passed (includes new round-trip tests for all
  six fields in `test_campaign_state.py`, unconditional-capture tests in
  `test_campaign_orchestrator.py`).
- `pytest tests/integration/campaigns/ -q` (excluding the 3 slow real-run tests, run separately
  below) — 19 passed, existing suite unaffected.
- `test_survivor_reconstruction_position.py` (predecessor ticket's own real acceptance test,
  re-run here to confirm no regression from this ticket's changes) — 1 passed.
- `test_reconstructed_survivors_are_identity_equivalent_to_the_real_extracted_snapshot` (new,
  `tests/integration/campaigns/test_survivor_identity_reconstruction.py`) — 1 passed. Real
  end-to-end pipeline: episode 0 real spawn → real `run_episode()` completion → real extraction →
  real reconstruction into episode 1; every alive survivor's `kind`/`role`/`faction`/`properties`/
  `traits`/`personality`, and `get_faction_id_str()`'s own resolution, verified to match exactly.
- `test_real_three_episode_campaign_completion_after_identity_fix` (new) — 1 passed. Real evidence:
  episode 0 tick 150/150, episode 1 tick 150/150 (zero occupancy violations), episode 2 **tick
  150/150** (was 52 before this fix), zero occupancy violations throughout.

## Files Changed
- `src/domains/campaigns/state.py` — `EntityCarryForward` gains `kind`/`role`/`faction`/
  `properties`/`traits`/`personality`
- `src/domains/campaigns/orchestrator.py` — `_extract_entity_carry_forwards()` capture,
  `_build_initial_state()` survivor-branch wiring, `PersonalityComponent` import added
- `tests/unit/domains/campaigns/test_campaign_state.py` — round-trip tests for all six fields
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — extraction capture tests,
  `_make_mock_entity()` extended with `kind`/`role`/`properties`/`traits`/`personality` params
- `tests/integration/campaigns/test_survivor_identity_reconstruction.py` — new, real end-to-end
  identity-equivalence test and the real 3-episode completion acceptance test
- `tests/integration/campaigns/test_survivor_reconstruction_position.py` — stale cross-reference to
  the old ticket ID corrected (this ticket was renamed during pre-implementation scoping)
- `tickets/done/TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION.md`,
  `tickets/todos/TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION.md`
  — cross-references updated to this ticket's renamed ID

## Completion Summary
Fixed the confirmed root cause: survivor reconstruction never restored spawn-time identity
(`kind`/`role`/`faction`/`properties`/`traits`/`personality`), building every reconstructed
survivor from `EntityState`'s own bare defaults regardless of who they actually were. The fix
threads all six through `EntityCarryForward`, extraction, and reconstruction, verified by a real
end-to-end test (not a mocked comparison) confirming a reconstructed survivor is identity-
equivalent to the real entity extraction captured.

The transferred campaign-completion acceptance bar is met, with real evidence: a real 3-episode
`frontier_living_world` run now completes all three episodes at full configured length (episode 2
specifically: tick 150, up from the confirmed prior stall at tick 52), zero `LAW-SPAWN-OCCUPANCY`
violations throughout. This is reported honestly as *consistent with* the identity gap being the
stall's cause — a real, controlled before/after comparison, not independently proven via granular
event-type instrumentation, and episode 1's own prior completion despite identical defects remains
real, accounted-for evidence that the relationship isn't a simple unconditional rule. The bar does
not need to move to a fourth ticket; the real run now completes.

A related, separate divergence (`combat.hp`/`.atk`/`.def_stat` not recomputed from carried level at
reconstruction time) was found during this ticket's own investigation and filed separately
(`TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION`) rather than
absorbed, per its own different fix shape and blast radius.
