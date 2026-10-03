---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
artifact_type: investigation
tags: [world, simulation-quality, corpus]
---

# Investigation — TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD

## 1. IDENTITY bucket reachability — CONFIRMED hard engine-level ceiling

Traced the full producer/consumer chain for `entity.identity.role` and `entity.identity.faction`:

- **Consumer (apply path) exists and works correctly**: `IdentityUpdate.role_set`/`faction_set`
  (`src/core/updates.py:222`) are real fields, correctly applied by
  `src/engine/patches.py:192` (`if u_id.role_set is not None: rl = u_id.role_set`, and the
  equivalent for `faction_set`).
- **No producer exists anywhere in real `src/`**: `grep -rn "role_set=\|faction_set=" src/
  --include=*.py` (excluding the field declaration itself and the apply-path consumer) returns
  **zero** matches. No system, service, or pipeline phase in this codebase ever constructs an
  `IdentityUpdate` with `role_set` or `faction_set` populated.
- **The nearest real candidate — party defection — does NOT touch identity fields either.**
  `PartyLifecycleService.check_defection()` (`src/systems/social_systems/party_lifecycle.py:143`)
  is the only real "an entity's allegiance changes" mechanic in the codebase (grievance-threshold
  desertion → `BetrayalDesertionEvent`). Read its full body: it returns `(updated_group, event,
  entity_update)` where `entity_update` applies `notoriety_delta=2.0` via `SocialUpdate` only — it
  removes the entity from `group.member_ids` (party/group membership), but never touches
  `entity.identity.faction` or `entity.identity.role`. Docstring explicitly confirms: "Does NOT
  mutate group or entity" (returns new copies) and the mutation it *does* propose is
  notoriety-only.

**Conclusion**: `entity_role_changed`/`entity_faction_changed` (the `IDENTITY` bucket's only 2
trigger events per `entity_lifecycle_weights.yaml`) cannot be produced by *any* amount of authored
world content — this is a structural mechanism gap, not a content gap. No world in this corpus, no
matter how rich, can reach the `IDENTITY` bucket today. This world's own realistic `phase_coverage`
ceiling is **9/10**, not 10/10 — reported honestly below, not silently assumed away.

Per this ticket's own Out of Scope: filing the fix as a separate follow-up rather than
implementing it here (a new "promotion"/"role change" mechanic is a real design decision, not a
small fix — e.g. should HERO entities promote by level threshold? should defection actually flip
faction? — needs its own scoping, not folded into a world-authoring ticket).

## 2. NARRATIVE_QUEST reachability — RE-VERIFIED, materially better than the ticket's own premise

The ticket's own premise (written before this session's backlog-commit work landed) assumed
`quest_completed` is "confirmed dormant corpus-wide." That premise is **now stale** — the sibling
probe's 3 real defects it found (`TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`) were all fixed
by tickets that were already substantively complete but sat uncommitted until this session's own
backlog-commit reconciliation (same session, same day, just discovered/committed later):

- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`: `GuildAction.visit()` is now reachable via a real
  AI goal (`GoalKind.GUILD` → `GuildNeedScorer`, `src/ai/goals/scorers.py:229`), gated behind
  **`ENABLE_GUILD_QUEST_GENERATION`** (default OFF — confirmed via direct read, not assumed).
  Targets the `town_hall` building via `SpatialQueryService.nearest_building()`.
- `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`: `quest_event`'s mislabeling is fixed.
- `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP` /
  `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`: real completion evaluators now exist for 2 of 5
  `QuestKind`s. Confirmed via direct read of `src/engine/quests.py`
  (`QuestResolutionSystem`): only `evaluate_explore` and `evaluate_combat_victory` exist —
  GATHER/BOUNTY/LIBERATE genuinely still have **no evaluator** (disclosed, unchanged). Real
  completable templates in `QuestGenerator.TEMPLATES` (`src/quests/generator.py`):
  - `q_wood_survey` (EXPLORE) — completable, needs a real deterministic target position (any
    world works, no special content needed beyond `ENABLE_GUILD_QUEST_GENERATION`).
  - `q_wolf_hunt` (HUNT, `target_kind="wolf"`) — completable, needs a real "wolf"-race archetype
    population (`hungry_wolf`/`alpha_wolf`, present in `wolf_den_near_forest`).
  - `q_slime_cull` (HUNT, no target_kind — no "slime" content exists anywhere in the real corpus)
    — genuinely uncompletable, not this ticket's gap to fix.
  - `q_herb_gather`/`q_bandit_bounty`/`q_camp_liberate` (GATHER/BOUNTY/LIBERATE) — genuinely
    uncompletable (no evaluator), not this ticket's gap to fix.

**Conclusion**: `quest_started`/`quest_completed` are both real, reachable events for a world that
(a) enables `ENABLE_GUILD_QUEST_GENERATION`, (b) has a `town_hall` building, (c) has HERO entities
with spare project capacity, and (d) has real "wolf"-race content nearby for the one guaranteed
HUNT completion path. `quest_failed` reachability was not separately traced (lower priority — not
required for bucket coverage, `quest_started`+`quest_completed` alone satisfy `NARRATIVE_QUEST`).

## 3. Corpus precedent survey (avoid redundant authoring)

Reused, not re-invented, per `corpus_tier_taxonomy.md`'s own discipline:

| Precedent | What's reused |
|---|---|
| `hero_guild_routing` (Unit dual-role, 31 entities) | Its own proven-compatible 5-module base: `frontier_village_core` + `hero_adventurers` + `mountain_pass` + `ruins_mystery_quest` + `goblin_camp_conflict` — already compiles cleanly, real precedent for `ENABLE_ADVENTURE_ROUTING`. |
| `simq_scale_stress_seed42` (Stress, 68 entities) | Its own proven-compatible hostile-module additions: `wolf_den_near_forest`, `orc_clan_territory` (for extra COMBAT/FACTION diversity + real "wolf" content) and `river_crossing` (terrain variety). |
| `highland_traverse`/`frontier_living_world` | `ENABLE_SOCIAL_COOPERATION` + `ENABLE_BELIEF_ASSIMILATION` precedent (civilian/guard population from `frontier_village_core` satisfies `HelpNeedEvaluator`'s `current_objective_id` gate the same way `settled_quarter` does elsewhere — no need to also add `settled_quarter`, which would duplicate the settlement role `frontier_village_core` already fills and risks region/building ID collisions). |

**Region/faction ID collision check** (direct read of each candidate module's `regions`/
`factions` keys, not assumed clean): `hometown`, `mountain_pass_zone`, `haunted_battlefield`,
`goblin_camp`, `near_forest`/`wolf_den`, `orc_stronghold`, `river_ford` — 8 distinct region IDs,
no collisions. `town_council`/`merchant_league`, `hero_guild`, `undead_remnants`/`spirit_court`,
`goblin_warband`, `wild_beast_pack`, `orc_clan` — 8 distinct factions, no collisions. Real compile
(Implement phase) is the final confirming check, matching this session's own established
"verify via real execution, not static inspection alone" discipline.

## 4. Scale / performance

Real measured cost for the corpus's current largest worlds at 5000 ticks: ~250s (`frontier_
extended`/`frontier_marches`-class, ~56-62 entities, per `corpus_tier_taxonomy.md`'s own Long-run
observation section). The composition below (8 modules) is expected in the same 45-65 entity
range as `hero_guild_routing` (31) + the 3 added hostile modules' own entity counts — not
attempting to beat `simq_scale_stress_seed42`'s 68-entity raw-scale record (that's already a
separate, named gap this world is not trying to re-close). Real entity count and real 5000-tick
timing will be measured directly during Implement, not assumed.

## Docs Requiring Update
- `docs/simulation_quality/corpus_tier_taxonomy.md`: new Stress-tier world entry + a new named
  scale-diversity gap ("no world structurally reaches all 10 lifecycle-phase buckets, and IDENTITY
  is a hard ceiling regardless of content")
- `config/simulation_quality/corpus_registry.yaml`: regenerated (generated file, not hand-edited)
