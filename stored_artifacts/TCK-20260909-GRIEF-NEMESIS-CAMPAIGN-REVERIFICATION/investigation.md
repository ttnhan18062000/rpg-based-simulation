# Investigation — TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION

## Both real trigger paths traced before running anything, per peer review's exercisability warning

- **`grief_urgency_triggered`** has genuinely both paths named in the origin ticket:
  - Mid-episode: `Kernel._phase_observability()` → `EventExtractor.detect_grief_triggers()`
    (`event_extractor.py:1717+`), called every tick. Fires when a currently-alive entity's
    `entity.social.trust_history` toward a *newly-dead* entity (a real `lifecycle.active`
    True→False transition, detected directly on state, not gated on any specific "kill" event
    type) meets `ALLY_TRUST_THRESHOLD` (`src/core/social_constants.py:17` = `0.30`). Emits a real
    `GriefUrgencyTriggeredEvent` SimulationEvent and queues the trigger for a later tick's
    `_phase_resolution` (or episode teardown) to actually apply the `StrategicUpdate`.
  - Episode-boundary: `CampaignOrchestrator._advance_grief_urgencies()`
    (`orchestrator.py:344-367`), reading `NarrativeLedger` entries with `event_type ==
    "entity_death"`, checking `social_memories[eid].relationship_scores.get(dead_id, 0.0) >=
    ALLY_TRUST_THRESHOLD` — a *different* field (`social_memories`/`relationship_scores`, not the
    live `entity.social.trust_history` the mid-episode path reads) but the same threshold.
- **`nemesis_relation_formed` has NO mid-episode path at all** — confirmed by an exhaustive grep
  of `kernel.py`/`event_extractor.py` for any nemesis-related trigger; none exists.
  `CampaignOrchestrator._advance_nemesis_relations()` (`orchestrator.py:393-455`) is the only
  emission site, and it requires `NEMESIS_EPISODE_COUNT = 2`
  (`src/domains/campaigns/grief_urgency.py:28`) distinct *episodes* of `"betrayed"`/`"conflict"`
  interaction against the same other entity — structurally impossible to test within one episode.
  A real multi-episode campaign is required to even attempt this, not a design gap.

## Real death event-type naming, corrected mid-investigation

My own first probe filtered raw `simulation_events.jsonl` for `event_type == "entity_death"`,
assuming that was the literal SimulationEvent name — wrong, and caught before it produced a false
negative. The real per-tick "this specific entity was killed" event is `"entity_killed"`
(`src/observability/event_shapers.py:304-311`, the live "push cutover" shaper path,
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`), gated specifically on
`combat_upd.outcome_kind == "KILL"` — a narrower classifier than the raw `lifecycle.active`
transition `EventExtractor.detect_grief_triggers()` itself watches. An older `CombatKillEvent`
class (`event_type = "combat_kill"`) also exists in `event_extractor.py` but is superseded by the
shaper path per that file's own documented gaps (old-age deaths and some hazard-caused deaths
never carry a `combat_upd` at all, so neither `"entity_killed"` nor `"combat_kill"` fires for
them — only the raw `lifecycle.active` transition is universal, which is exactly what
`detect_grief_triggers()` correctly watches instead of either named event).

## Real multi-episode run — nemesis and grief's episode-boundary path: BLOCKED, not negative

Ran a real 3-episode campaign (150 ticks/episode, `frontier_living_world`, seed 42). Episode 0
completed cleanly (150 ticks, 765 real events, no crash). Episodes 1 and 2 both stalled almost
immediately (~tick 52) with a real `LAW-SPAWN-OCCUPANCY` hard-law violation — confirmed at scale:
13 of 16 episode-0 survivors all reconstruct at the identical `(0.0, 0.0)` position in episode 1's
initial state (`CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction branch
never touches `WorldEntitySpawner` at all — filed as
`TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`). This is a real, previously
unexercisable bug (Campaign mode had zero entities, so zero survivors, until this same follow-up
batch's own earlier work), not a workaround-able test artifact — per peer review, explicitly did
NOT hand-construct carry-forwards with distinct positions to route around it, since that would
reproduce the exact "verified synthetically instead of through a real run" flaw this
reverification ticket exists to correct.

**Result: `nemesis_relation_formed` and grief's episode-boundary path are BLOCKED, not
negative.** A real multi-episode run cannot currently progress far enough into episode 1+ to give
either mechanism a genuine chance to fire. No conclusion about their correctness can honestly be
drawn until `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` lands.

## Real single-episode run — grief's mid-episode path: INCONCLUSIVE, not negative

Episode 0 doesn't depend on the survivor-reconstruction bug (it's the catalog-spawn path, already
fixed by `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`), so this leg is testable now.
Ran a real single 500-tick episode (`frontier_living_world`, seed 7, hooking `Kernel
._event_listeners` directly for ground-truth per-tick observation, not just the post-hoc JSONL).

- **Real deaths did occur**: 4 real `lifecycle.active` True→False transitions observed directly
  (entities at ticks including 179, 182, 215, and one earlier). Zero `entity_killed`/`combat_kill`
  events accompanied any of them (581 `combat_resolved` events occurred, all non-`KILL` outcomes;
  2470 `cooperation_event`s; no `entity_killed` at all) — consistent with the disclosed hazard/
  old-age gap in `event_shapers.py`'s own comments, not a sign these lifecycle transitions were
  fake or unrelated to real gameplay.
- **`grief_urgency_triggered` fired zero times.**
- **Root-caused the zero, not just observed it**: for every one of the 4 real deaths, checked
  every other alive entity's `entity.social.trust_history` toward the dead entity directly — every
  single lookup was empty (`{}`, no key for the dead entity at all) for every entity, for the
  entire 500-tick run, despite 2470 real `cooperation_event`s occurring. The `ALLY_TRUST_THRESHOLD
  = 0.30` precondition was never met for any of the 4 real deaths — not because the grief-trigger
  detection code is broken, but because no entity in this run ever accumulated any real trust
  value in `entity.social.trust_history` toward anyone at all.

**Result: INCONCLUSIVE, not negative.** The grief-trigger detection mechanism itself was never
given a genuine chance in this run — its own precondition (a real ally-trust relationship) was
never satisfied. Whether `trust_history` populating from `cooperation_event`/other real
interactions is itself working correctly, too slow to matter within one episode, or gated on some
other precondition not met by this seed/composition is a **separate, unconfirmed question** — not
investigated further here (thin evidence, not a confirmed defect; not filed as its own ticket per
this batch's own established discipline against filing unfalsifiable observations). Recorded here
as the evidence trail for whoever investigates next, rather than a fresh trace being needed.
