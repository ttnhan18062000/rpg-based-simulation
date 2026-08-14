---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY
artifact_type: investigation
tags: [combat, observability, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY

## Context search (mandatory step)
`search_docs`/`graphify query` (this session's own prior turns) already surfaced the real,
relevant docs: `docs/engine/contracts/combat_contract.md` §4 (Opportunity Attacks),
`docs/simulation_quality/event_type_coverage.md` (the real event-registration contract),
`docs/mechanics/02_combat_laws.md` (confirmed to not claim any evasion/miss mechanic, consistent
with the sibling investigation).

## Real event architecture, re-confirmed (not assumed)
`src/observability/event_shapers.py`'s `CombatShaper` (`SHAPER_REGISTRY["combat"]`) is the real,
**live** producer of `combat_damage`/`combat_initiated`/`near_death_survival`/`entity_killed`
today — confirmed via `event_extractor.py`'s own comments: `ENABLE_PUSH_EVENT_SHAPERS` defaults
"ON", and `event_extractor.py`'s own legacy branches are the rollback path, not the live one.
`CombatShaper.shape(prior_state, update, tick, mode)` is invoked once per tick from
`run_shadow_shapers()` with the **full** `prior_state: AuthoritativeState` and `update:
StateUpdate` — meaning both the defender (`prior_state.entities[eid]`, the entity being iterated)
and the attacker (`prior_state.entities[real_combat.attacker_id]`) are real, directly available,
pre-mutation `EntityState` objects inside the shaper. This is the correct, established extension
point for the new events — no new shaper class needed, extend `CombatShaper` directly.

## Real signals already available for each new event (source-verified)

**`combat_engagement_started`** — reuses the exact same real gate `combat_initiated` already uses
(`hp_delta < 0 and real_combat is not None and prior_hp == prior_max_hp and new_hp < prior_max_hp`)
— fires alongside it, not replacing it. `trigger_reason` is directly derivable from
`CombatUpdate.is_opportunity_attack` (already a real field, set at the real source in both
`resolve_attack()`'s own callers): `OPPORTUNITY_ATTACK` if true, else `GOAL_ENGAGE` (a legal
attack that isn't an OA can only originate from `tactical.py`'s own deliberate `ATTACK`/`SKILL`
emission branch — confirmed structurally distinct from every retreat/reposition/hold branch in
that function by construction, this session's own prior investigation).

**`combat_engagement_ended`** — 4 real, distinct trigger conditions, all confirmed source-side:
1. **KILL**: reuses the exact same real gate `entity_killed` already uses
   (`outcome_kind == "KILL"`).
2. **CAUGHT_FLEEING**: `real_combat.is_opportunity_attack is True` and NOT also a kill this tick —
   a real opportunity attack, by construction, only ever fires on a hostile's own disengagement
   movement (`movement.py`'s own `engaged_hostiles and not skip_oa` gate) — this **is** "caught
   while fleeing," no new instrumentation needed.
3. **PURSUIT_ABANDONED**: `update.entity_updates[eid].task.payload_set.get("reason")` in
   `("LEASH_RETURN", "STALEMATE_BREAK")` — both real, already-emitted reason strings from
   `tactical.py` (confirmed lines: `LeashService`-driven leash-return, `stale_ticks > 10`
   anti-stalemate break). Neither branch currently sets a `target_id` in its own `payload_set` —
   the real prior pursuit target must be read from `prior_ent.task.payload.get("target_id")`
   instead (the target the entity was chasing *before* giving up this tick), which is real and
   available via `prior_state`.
4. **ESCAPED**: confirmed via direct read of `movement.py:184-186` that a successful,
   opportunity-attack-free disengagement (`MovementMode.RETREAT` + `ActionStyle.EVASIVE` →
   `skip_oa=True`, with `engaged_hostiles` genuinely non-empty — i.e. a real hostile that *would*
   have attacked, but didn't) currently leaves **zero trace** on the returned `EntityUpdate` — no
   existing field distinguishes this from an ordinary move with nothing nearby. **Real, minimal,
   additive instrumentation required** at the source: tag
   `property_updates["combat_escape"] = "EVASIVE_SUCCESS"` (plus the real, already-computed
   `engaged_hostiles` id list, for "escaped from whom") only in the genuine `engaged_hostiles and
   skip_oa` case. This is the one place this ticket touches `movement.py` itself — a single,
   additive dict entry using the file's own already-established `property_updates` pattern
   (`"movement_resolution": "POSITION_SWAP"` is the existing precedent for exactly this shape of
   tag), not a change to any real combat/movement resolution logic.

## Real entity-snapshot fields, confirmed available on live `EntityState`
`identity.evolution_level` (level), `combat.hp`/`combat.max_hp`, `combat.atk`/`combat.def_stat`,
`identity.role` (a real `EntityRole` `IntEnum`, serialized as `.name` via
`EntityRole(role).name` with a defensive fallback for any unmapped legacy int),
`identity.properties.get("faction_id")`/`.get("race_id")`, `identity.personality.bravery`,
`combat.action_style` (this session's own new real signals). All confirmed real, populated fields
on `EntityState` — no new state needed, a pure read-and-serialize helper.

## Real registration requirement
`docs/simulation_quality/event_type_coverage.md` §5 "Unscored Intentional" is the real,
established, authoritative home for new event types not yet integrated into SimQ pillar scoring
— confirmed via its own real table format and precedent entries (e.g. `item_equipped`,
`recipe_learned`, all landed the same way by this session's own sibling entity-observability
tickets). Both new events land there, not §1 Scored Events — deferring the real pillar-scoring
integration decision to a later ticket (matching this repo's own established precedent), not
pre-decided here.

## Docs Requiring Update
- `docs/simulation_quality/event_type_coverage.md` §5: register both new event types.

## Real corpus re-verification (Test phase, post-implementation)

Ran a real, live `Kernel.tick_once()` loop for 2000 ticks against both `dungeon_crawl` (seed 42,
32 entities) and `urban_political` (seed 42, 30 entities), reading `kernel._event_recorder`'s real
recorded events directly (no synthetic/mocked state).

**Corpus default config** (`ENABLE_COMBAT_ENGAGEMENT` left at its real repo default, `OFF` —
confirmed via `src/domains/optimization/feature_flags.py:17`): `combat_engagement_ended` fired at
real, non-zero, honest volume:
- `dungeon_crawl`: `PURSUIT_ABANDONED` × 10
- `urban_political`: `PURSUIT_ABANDONED` × 10, `ESCAPED` × 5

Both read real `TaskUpdate.payload_set`/`property_updates` data with no attack-resolution
dependency, confirming §5's PURSUIT_ABANDONED/ESCAPED trigger conditions fire naturally in this
corpus without needing the combat-engagement phase active at all — a genuine, disclosed finding.

**`ENABLE_COMBAT_ENGAGEMENT=ON` (forced via env, matching this repo's own documented override
pattern)**: `combat_engagement_started`, `combat_engagement_ended(KILL)`, and
`combat_engagement_ended(CAUGHT_FLEEING)` did **not** fire in either 2000-tick run. This is **not**
a gap introduced by this ticket: verified directly that the pre-existing sibling events they ride
alongside (`combat_initiated`, `combat_damage`, `entity_killed` — all present in this repo before
this ticket) also recorded **zero** occurrences in the same runs, both through the live push-shaper
path and through `event_extractor.py`'s own legacy combat branch. The individual-attack
`CombatUpdate`/`EntityUpdate.combat` path this shaper reads is corpus-wide inactive at this scale
under this seed — a pre-existing condition of `dungeon_crawl`/`urban_political`, not something this
ticket's code broke or was expected to force. (The `combat_kill` events that did appear at
`ENABLE_COMBAT_ENGAGEMENT=ON`, 30 occurrences, are a separate, unrelated producer —
`CombatKillEvent` from a faction-vs-faction `military_conflict` pipeline phase, which never
populates `EntityUpdate.combat` and is out of this shaper's scope by design.)

These 3 conditions are instead verified via real hand-constructed `EntityState`/`CombatUpdate`
objects in the unit-test suite (`tests/unit/observability/test_event_shapers.py`, 12 new tests
covering all 6 real trigger conditions plus the snapshot helper) — the same precedent this
session's own sibling tickets established for corpus-unreachable-at-scale events (see
`item_equipped`, `wound_sustained`, `skill_cooldown_started` in `event_type_coverage.md` §5).

**Unrelated, pre-existing finding, not caused by this ticket:** confirmed via `git stash` that
`tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run
[urban_political_seed42_2000t]` (SOCIAL pillar score drift) fails identically on the clean
pre-ticket tree — out of scope for this ticket, not fixed or touched here.
