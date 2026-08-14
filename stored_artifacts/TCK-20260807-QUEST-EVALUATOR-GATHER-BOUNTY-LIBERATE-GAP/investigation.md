---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP
artifact_type: investigation
tags: [simulation-quality, progression]
---

# Investigation: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP

## Revised premise (see ticket body's "UPDATE 2026-08-07" section)

The ticket's original premise ("HUNT/EXPLORE already work, GATHER/BOUNTY/LIBERATE are the only
gap") was wrong. `QuestGenerator.generate()` (`src/quests/generator.py`) never set
`QuestState.metadata` at all prior to this ticket's fix — it always defaulted to `{}`. Both
existing evaluators, `QuestResolutionSystem.evaluate_explore()` and
`.evaluate_combat_victory()` (`src/engine/quests.py`), read their match signal exclusively from
`project.metadata`. With `metadata` always empty, **neither evaluator could ever match a real
generated quest** — the completion gap was universal across all 5 `QuestKind` values, not scoped
to the 3 kinds lacking an `evaluate_*` method.

Per the user's explicit scope decision ("Fix HUNT + EXPLORE now; defer GATHER/BOUNTY/LIBERATE"),
this ticket's implementation targets exactly those two kinds — GATHER/BOUNTY/LIBERATE's own
`evaluate_*` methods remain out of scope, unchanged from the original ticket's own "Out of Scope"
section (their absence is now moot regardless, since even if they existed, no metadata would
reach them).

## EXPLORE — fixed

`evaluate_explore()` (`src/engine/quests.py:18-48`) reads `project.metadata.get("target_pos")` and
completes the quest when `entity.navigation.position` is within Manhattan distance 2.0 of it.
Fix: `QuestGenerator.generate()` now accepts an `origin_pos: Optional[tuple[float, float]]`
parameter; when the drawn template is `QuestKind.EXPLORE` and `origin_pos` is given, it computes a
deterministic target position (`DeterministicRNG.get_float(Domain.QUEST, tick, level, sub_id=1/2)`
for angle/distance, offset `[15.0, 40.0]` tiles from `origin_pos`) and sets
`metadata={"target_pos": (x, y)}`. `QuestGenerator.generate_quests()` and
`GuildAction.visit()` (`src/town/guild.py`) thread `entity.navigation.position` through as
`origin_pos` — the only real caller of the generator today
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s `GuildVisitPhase` → `GuildAction.visit()`).

Verified: `QuestGenerator.generate()` with `origin_pos` given produces a `target_pos` within
`[15.0, 40.0]` tiles of `origin_pos`, deterministically reproducible for the same
`(seed, level, tick, origin_pos)`. `evaluate_explore()` completes the quest once
`entity.navigation.position` is set to that `target_pos` (unit tests in
`tests/unit/quest/test_quest_generation.py`).

## HUNT — investigated, found not safely fixable in this pass, scope narrowed to EXPLORE only

`evaluate_combat_victory()` (`src/engine/quests.py:50-152`) has 4 independent match paths, in
priority order:

1. `target_archetype_id` (clean identity) vs `EntityIdentityResolver.resolve(victim).archetype_id`
2. `target_faction_id` (clean identity) vs `.faction_id`
3. `target_projected_label` vs `RelationProjectionService.project_relation(...).label`
4. `target_kind` (legacy) vs the raw `victim_kind` string passed by the caller

All 4 require `QuestGenerator.generate()` to populate the corresponding `metadata` key for a HUNT
template. `QuestTemplate` (the real, live dataclass in `src/quests/generator.py` — **not**
`src/quests/templates.py`'s dead `QuestTemplate`/`QUEST_TEMPLATES`, confirmed zero importers via
grep) has no field carrying any subject/target-kind information at all: `id`, `name`, `kind`,
`min_level`, `max_level`, `base_goal`, `base_xp`, `base_gold`, `items`. There is nothing in the
template to derive `target_archetype_id`/`target_faction_id`/`target_kind` from — unlike EXPLORE,
where `origin_pos` alone is sufficient to compute a valid target, HUNT needs the generator to know
*which entity kind/archetype/faction* the quest is about, and today's `QuestTemplate` carries no
such information (a real content-model gap, not a wiring gap).

Checked whether a real, ambient entity-identity signal could stand in for an explicit template
field — sampled `EntityIdentityResolver.resolve()` output across 4 real worlds
(`sandbox_world`, `dungeon_crawl`, `hero_guild_routing`, `urban_political`) for every non-hero/
non-town-service entity kind present (`scout`, `raider`, `leader`, `sentinel`,
`predator_hunter`, `alpha`, `merchant`, `blacksmith`):

- `role_id` resolves to `"citizen"` for **all** of them — no distinction between clearly
  monster-like kinds (`predator_hunter`, `alpha`) and clearly non-hostile kinds (`merchant`,
  `blacksmith`).
- `faction_id` resolves to `"neutral"` for **all** of them — same problem.
- `legacy_role`/`legacy_faction` mirror the above.
- The raw `.kind` string itself (e.g. `"predator_hunter"`) is the only signal that varies
  meaningfully by monster-ness, but `target_kind` matching (`evaluate_combat_victory()` Path 4)
  requires the generator to emit that exact string per template, and `QuestTemplate` has no field
  to hold it — the generator would need a hardcoded `{"q_slime_cull": "slime", "q_wolf_hunt":
  "wolf"}`-style mapping invented from scratch, matched against content that doesn't obviously use
  those exact `.kind` strings in every world (not verified against the full corpus of possible
  monster `.kind` values — this is exactly the kind of content/catalog-level assumption CLAUDE.md's
  Hard Rules prohibit guessing at: "Do not guess when uncertainty affects behavior or
  architecture").

**Conclusion:** fixing HUNT safely requires either (a) adding a real subject/kind field to
`QuestTemplate` and deciding, at the content-catalog level, what monster-kind vocabulary quest
templates should target — a game-design decision, not a code wiring fix — or (b) a broader
entity-identity model change (giving monster-like entities a real non-"citizen" role/faction
distinction) that is far outside this ticket's blast radius and would need its own investigation
and sign-off. Neither is safely doable as an extension of the EXPLORE fix in this pass. Per
CLAUDE.md's "Do not guess when uncertainty affects behavior or architecture" and the project's own
established pattern in this session (narrow scope, disclose honestly, file a follow-up rather than
force an unsafe fix), **this ticket's implementation is scoped to EXPLORE only.** A follow-up
ticket (`TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`) is filed to `tickets/todos/tech-debt/` for
HUNT specifically, since it is a real, disclosed, un-fixed gap distinct from GATHER/BOUNTY/
LIBERATE (which were already out of scope by the user's own original decision).

## GATHER / BOUNTY / LIBERATE — unchanged, deferred per user's original decision

No new investigation performed — these remain out of scope per the ticket's own "Out of Scope"
section and the user's explicit "defer GATHER/BOUNTY/LIBERATE" instruction. Not newly worse off:
they had no evaluator before this ticket and still have none; the metadata-population bug fixed
here doesn't affect them since GATHER/BOUNTY/LIBERATE quest kinds have no evaluator to feed
regardless of what metadata they'd carry.
