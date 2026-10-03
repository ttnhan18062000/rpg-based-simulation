---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP
phase: done
date: 2026-08-07
tags: [simulation-quality, progression]
---

# TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP

## Title
HUNT quests can never complete — `QuestTemplate` has no subject/target-kind field, and no real
entity-identity signal in any sampled world distinguishes hostile monsters from other neutral NPCs

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`'s own investigation, after
that ticket's scope was narrowed from "fix HUNT + EXPLORE" to "fix EXPLORE only" once this gap
turned out not to be safely fixable as a mechanical extension of the EXPLORE fix.

`QuestResolutionSystem.evaluate_combat_victory()` (`src/engine/quests.py:50-152`) advances HUNT
quests via 4 match paths against `project.metadata`: `target_archetype_id`, `target_faction_id`,
`target_projected_label`, and a legacy `target_kind` fallback. `QuestGenerator.generate()`
(`src/quests/generator.py`) never populates any of these for HUNT-kind quests — `QuestTemplate`
(the real, live dataclass) has fields `id`, `name`, `kind`, `min_level`, `max_level`, `base_goal`,
`base_xp`, `base_gold`, `items` and nothing carrying subject/target-kind information at all. As a
result every generated HUNT quest (e.g. `q_slime_cull`, `q_wolf_hunt`) is permanently stuck at
`ACTIVE` regardless of real combat activity — confirmed via a real 3000-tick `sandbox_world_seed42`
run with live combat and multiple HUNT quests generated, none of which ever progressed
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own real-kernel verification).

Checked whether an ambient entity-identity signal (not requiring a new template field) could
substitute: sampled `EntityIdentityResolver.resolve()` output across 4 real worlds
(`sandbox_world`, `dungeon_crawl`, `hero_guild_routing`, `urban_political`) for every non-hero/
non-town-service entity kind present (`scout`, `raider`, `leader`, `sentinel`, `predator_hunter`,
`alpha`, `merchant`, `blacksmith`). Every one of them resolves to `role_id="citizen"`,
`faction_id="neutral"` — no distinction anywhere between clearly monster-like kinds and clearly
non-hostile ones. The raw `.kind` string is the only signal that varies by monster-ness, but using
it (`target_kind` matching) requires the generator to emit an exact string per template, and there
is no existing field to hold it, nor a confirmed, corpus-wide vocabulary of monster `.kind` values
to hardcode against.

## Scope
1. **Investigate** (mandatory before Plan): decide, at the content-catalog level, what
   subject/target-kind vocabulary HUNT quest templates should target. This is a real game-design
   decision, not a code wiring fix — do not invent it unilaterally; surface the open question to
   the user during Investigate if multiple reasonable designs exist (e.g. add a `target_kind:
   str` field to `QuestTemplate` and hardcode per-template values like `q_wolf_hunt` → `"wolf"`,
   vs. giving monster-like entities a real non-`"citizen"` role/faction in the identity model —
   these have very different blast radii and the second one is likely out of scope for this
   ticket alone).
2. **Plan**: design the chosen approach's exact field/data changes and `evaluate_combat_victory()`
   wiring (if it needs to change beyond what already exists).
3. **Implement**: populate HUNT quest metadata at generation time; confirm `evaluate_combat_victory()`
   matches correctly against real content.
4. Recalibrate `grade_anchors.json` for any scenario whose PROGRESSION grade shifts once HUNT
   quests can actually complete.

## Out of Scope
- GATHER/BOUNTY/LIBERATE — still have no `evaluate_*` method at all; unrelated to this ticket
  (tracked, if ever picked up, as a separate continuation of
  `TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`'s original, still-deferred scope).
- Any broader entity-identity/role/faction model redesign beyond what's strictly needed to make
  HUNT quest matching work — if Investigate finds that's the only safe path, split it into its own
  ticket rather than absorbing a large identity-model change here.

## Acceptance Criteria
(Revised: the original wording assumed a single uniform HUNT fix; investigation found only
`q_wolf_hunt` is safely fixable — `q_slime_cull` has zero real content backing. See
investigation.md for the full corpus trace.)
- [x] `investigation.md` documents the chosen subject/target-kind vocabulary approach and why
      (`target_kind` field, `"wolf"` for `q_wolf_hunt`, deliberately none for `q_slime_cull`)
- [x] HUNT-kind quests generated via `QuestGenerator.generate()` carry metadata that
      `evaluate_combat_victory()` can match against real killed entities in live gameplay — true
      for `q_wolf_hunt`; `q_slime_cull` remains a disclosed, unfixed content gap (no target_kind
      fabricated)
- [x] Unit test: a hand-constructed HUNT `QuestState` with real generator-produced metadata
      completes when the matching entity kind is defeated, and does not complete for an unrelated
      kill
- [x] Real-kernel(-adjacent) verification: the full real `generate()` →
      `evaluate_combat_victory()` → `QuestService.add_progress()` lifecycle, driven by 9 real
      simulated "wolf" kills, reaches `QuestStatus.COMPLETED` — codified as a permanent test
- [x] `docs/parity_ledger/progression.yaml` updated (new `PROG-120`; `PROG-119` got an
      `update_2026_08_07` note pointing to it); `grade_anchors.json` not recalibrated — HUNT
      quests were never completable in any scored scenario before this fix
- [x] Scoped pytest run passes (30/30 quest tests; 106/106 wider sweep)

## Related Tickets
- TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP (source of this finding; fixed EXPLORE
  only, DONE)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (the real-kernel run that first surfaced HUNT quests
  never completing, DONE)

## Related Docs
- `docs/simulation/quest_contract.md` (Quest Generation Contract — metadata population section)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP/investigation.md`
  (full corpus-sampling trace for the identity-signal dead end)

## Related Code Areas
- `src/quests/generator.py` (`QuestGenerator`, `QuestTemplate`)
- `src/engine/quests.py` (`QuestResolutionSystem.evaluate_combat_victory()`)
- `src/entities/identity_resolver.py` (`EntityIdentityResolver`) — only if the chosen approach
  touches identity resolution rather than just the quest template

## Assumptions / Open Questions
- Whether the right fix is a new `QuestTemplate` field (narrow, quest-system-local) or a broader
  entity-identity change (wide, affects other identity-consuming systems) is genuinely open —
  Investigate must surface this to the user before Plan, not assume.

## Implementation Notes
Traced `entity.kind`'s real runtime value: it comes from `src/entities/contract_builder.py:41`'s
`kind=arch.race_id` — the archetype's `race` catalog field, a materially different, more reliable
signal than the `role_id`/`faction_id` dead end the sibling ticket
(`TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`) already found unusable. Both
`hungry_wolf` and `alpha_wolf` archetypes declare `race: "wolf"`, giving `q_wolf_hunt` a real,
grounded target. Grepped every `race:` value in `entity_archetypes.yaml` and confirmed no
`"slime"` exists anywhere — `q_slime_cull` targets a monster type with zero real content, a
genuine content-authoring gap left honestly disclosed (no `target_kind` fabricated for it) rather
than silently worked around.

Added `QuestTemplate.target_kind: Optional[str] = None`, set to `"wolf"` on `q_wolf_hunt`'s
`TEMPLATES` entry. `generate()` now sets `metadata={"target_kind": template.target_kind}` for
HUNT templates that declare one. Verified the full real lifecycle end-to-end: `generate()` →
`evaluate_combat_victory()` → `QuestService.add_progress()`, driven by 9 simulated real "wolf"
kills, reaches `QuestStatus.COMPLETED` — not just a single evaluator call.

## Test Summary
New tests: `tests/unit/quest/test_quest_generation.py`
(`test_wolf_hunt_quest_gets_real_target_kind`, `test_slime_cull_quest_has_no_target_kind`,
`test_evaluate_combat_victory_completes_wolf_hunt_quest_on_matching_kill`,
`test_evaluate_combat_victory_does_not_progress_wolf_hunt_quest_on_unrelated_kill`,
`test_wolf_hunt_quest_reaches_completed_status_through_real_kill_loop`). All 30/30 tests in the
file pass. Wider regression sweep (guild pipeline/intel/scorer/phase/architecture-guard + entity
identity resolver): 106/106 pass.

## Files Changed
- `src/quests/generator.py` — `QuestTemplate.target_kind` field; `q_wolf_hunt`'s
  `target_kind="wolf"`; `generate()`'s HUNT metadata population
- `tests/unit/quest/test_quest_generation.py` — 5 new tests
- `docs/simulation/quest_contract.md` — Metadata population section extended
- `docs/parity_ledger/progression.yaml` — new `PROG-120` entry; `update_2026_08_07` note on
  `PROG-119`

## Completion Summary
Fixed HUNT quest completion for `q_wolf_hunt` — the one HUNT template with real content backing —
by tracing `entity.kind` to its real source (`race_id`, not the identity-resolver fields the
sibling ticket already ruled out) and adding a narrow, corpus-grounded `target_kind` field, per
the user's explicit design decision. `q_slime_cull`'s own deeper content gap (no "slime" content
exists anywhere) was found and honestly disclosed rather than worked around with a fabricated
value — this is the last of the originally-approved 6 tech-debt tickets plus its own 3 follow-ups;
`q_slime_cull`'s content gap was not filed as a new ticket, since fixing it requires authoring new
game content (a design decision), not a code or metadata change this repo's ticket pipeline is
positioned to resolve unilaterally.
