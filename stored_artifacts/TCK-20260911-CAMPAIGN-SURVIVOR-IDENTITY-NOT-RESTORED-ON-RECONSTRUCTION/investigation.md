# Investigation — TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION

## Step 1: full field-level audit (per this ticket's own Scope requirement)

Compared exactly what a real spawn (`ArchetypeEntityFactory.build_entity()`,
`src/entities/archetype_factory.py:40-130`) sets on `EntityState`/`IdentityComponent` against what
`_build_initial_state()`'s survivor-reconstruction branch (`orchestrator.py`) sets. A real spawn
sets, beyond `kind`/`faction`:

- `identity.role` (from `contract.legacy_role`) — reconstruction never touches it, stays at
  `IdentityComponent`'s own default (`role: int = 0` = `EntityRole.HERO`).
- `identity.traits` (from `contract.traits`) — stays at the default empty set.
- `identity.properties` (`archetype_id`/`species_id`/`faction_id`/`role_id`/etc.) — stays at the
  default empty dict. **This matters beyond symmetry**: `get_faction_id_str()`
  (`src/content_semantics/faction.py:42-59`) checks `identity.properties["faction_id"]` *first*,
  falling back to `identity.faction` only if that's absent — so `properties` is arguably the more
  direct root of the faction bug, not just the bare int.
- `identity.personality` (via `build_personality_for_entity()`) — stays at
  `PersonalityComponent()`'s own all-zero default.

Fields that stay at their bare default for a *real spawn too* (not part of this divergence, not a
gap to fix here): `class_id`, `life_stage`, `learned_skills`, `known_recipes`,
`veterancy_points`/`veterancy_rank`, `unspent_ap`, `territory_maturity`, `active_breakthroughs`,
`cooldowns`, `group_id`, `latest_intent_results`. `combat.hp`/`.max_hp`/`.atk`/`.def_stat` are also
not carried, but not clearly a bug either — plausibly recomputed from carried `level`/`class_id`
by some effective-stats mechanism; not verified either way, not claimed as a finding.

## Step 2: real-consumer check, not assumed impact

`identity.role` has real, load-bearing consumers found by direct grep, not inferred:
`regional_sovereignty.py` (HERO-only region-ownership checks), `camp.py`/`spawn.py`/
`creature_territory.py` (MONSTER-role gating), `domains/adventure/scoring.py` (HERO/GUARD/
SHOPKEEPER route-scoring branches), `domains/cooperation/providers.py` (role-1/Hireling special
case). Since every reconstructed survivor defaults to `role=0` (=HERO), any surviving non-HERO
entity (e.g. a `goblin`-kind monster, if monsters ever carry forward in a given campaign) would
misreport as HERO post-reconstruction — the same shape of bug as the confirmed faction gap, just
on a different field.

`identity.personality` staying zeroed matches an **exact, already-fixed precedent**:
`TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY` fixed this same "every entity at
`PersonalityComponent()`'s own all-zero default" bug once already, for the episode-0 catalog-spawn
path. The survivor-reconstruction branch has the identical bug class, unfixed.

## Reported to peer before implementing, and the resulting scope decision

Per peer review's explicit instruction ("kind and faction are the confirmed gap... bring it to me
rather than quietly widening"), these findings (role, properties, traits, personality) were
reported before any implementation began. Peer review's decision: take all six fields, and reframe
the ticket around the governing invariant — a reconstructed survivor must be identity-equivalent to
a spawned entity — rather than an enumerated field list. `traits` (no confirmed load-bearing
consumer found) is carried anyway under that invariant, not dropped for lack of a found consumer.
`properties` was flagged as partially correcting the original ticket's own scope, since
`get_faction_id_str()` checks it before the bare `identity.faction` int.

The related `combat.hp`/`.atk`/`.def_stat` recompute question (also found during this audit) was
resolved as a real, separate divergence (confirmed: the stats-dirty recompute path never fires for
a freshly-reconstructed entity, only for a level increase relative to the entity's own current tick
state) and filed separately per peer review's own explicit routing decision —
`TCK-20260911-CAMPAIGN-SURVIVOR-COMBAT-STATS-NOT-RECOMPUTED-ON-RECONSTRUCTION`, not folded in here.

The ticket file itself was renamed to
`TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION` to reflect the reframed
scope, with all cross-references (in the position-collision predecessor and the new combat-stats
ticket) updated to match.
