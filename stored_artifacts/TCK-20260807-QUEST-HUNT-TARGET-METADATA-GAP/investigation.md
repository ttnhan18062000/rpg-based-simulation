---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP
artifact_type: investigation
tags: [simulation-quality, progression]
---

# Investigation: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP

## Chosen approach (per user decision)

The user chose: add a `target_kind: str` field to `QuestTemplate`, hardcoded per-template,
matched against the victim entity's raw `.kind` string — narrow, quest-system-local, mirroring
`evaluate_combat_victory()`'s own pre-existing legacy `target_kind` fallback path (Path 4). This
was chosen over investigating a broader entity-identity-model change (giving monster-like
entities a real non-`"citizen"` role/faction distinction), which would have had a much wider
blast radius for what is, in the real corpus, only a 2-template gap.

## Tracing `entity.kind`'s real value

`evaluate_combat_victory(attacker, victim_kind, victim_entity)`'s `victim_kind` parameter is
`target.kind` (`EntityState.kind`, the raw runtime field) — confirmed by reading both call sites
(`src/engine/domain/combat_actions.py:72`, `src/engine/domain/aoe_actions.py:91`). Traced how
`EntityState.kind` gets populated at spawn time: `src/entities/contract_builder.py:41` sets
`kind=arch.race_id` — the archetype's `race` catalog field, NOT the archetype's own `id` or
`role`. Confirmed via `data/content/entities/entity_archetypes.yaml`: `hungry_wolf` and
`alpha_wolf` (different `role`s — `predator_hunter` and `alpha` — but the SAME `race: "wolf"`)
both resolve to `EntityState.kind == "wolf"` at runtime.

**This is a materially different, more reliable signal than the `role_id`/`faction_id` dead end
the sibling ticket (`TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP`) found** — that
investigation checked `EntityIdentityResolver`'s `role_id`/`faction_id` fields (which resolve to
`"citizen"`/`"neutral"` for everything non-hero/non-town-service) and correctly found no usable
signal there. `entity.kind`/`race_id` is a completely separate field, populated at a different
layer (spawn-time contract building, not the identity resolver), and — for monster archetypes
specifically — carries real, distinguishing content (`"wolf"`, `"goblin"`, `"orc"`, `"undead"`,
`"spider"`, `"troll"`, `"lizardfolk"`, `"dragonkin"`, all present in the real catalog).

## Per-template disposition

| Template | Real `race`/kind content? | Disposition |
|---|---|---|
| `q_wolf_hunt` ("Wolf Cull") | **yes** — `race: "wolf"` on both `hungry_wolf`/`alpha_wolf` archetypes | `target_kind="wolf"` |
| `q_slime_cull` ("Clear the Slimes") | **no** — grepped every `race:` value in `entity_archetypes.yaml` (`wolf`, `goblin`, `human`, `elf`, `spider`, `orc`, `undead`, `spirit`, `dragonkin`, `lizardfolk`, `troll`, `dwarf`) — no `"slime"` anywhere | left `target_kind=None` (deliberately, not guessed) |

`q_slime_cull` targeting a monster type with zero real content backing is a genuine
content-authoring gap — the template was presumably authored aspirationally or against
now-removed/never-added content. Per CLAUDE.md's "Do not guess when uncertainty affects behavior
or architecture," no `target_kind` was invented for it. This quest remains honestly
uncompletable, same as before this fix, rather than silently matching against a fabricated kind
string that would never occur in real gameplay (which would be a worse outcome than staying
disclosed-broken — it would look fixed while still never completing).

## Real-kernel-adjacent verification

Drove the full real production lifecycle: `QuestGenerator.generate()` (real draw, level 8, HUNT
tier) → `QuestResolutionSystem.evaluate_combat_victory()` (real evaluator, called once per
simulated real "wolf" kill) → `QuestService.add_progress()` (real progress accumulation). After 9
real wolf kills (`goal_value=8.8` at level 8), the quest reached `QuestStatus.COMPLETED` — not
just a single evaluator call returning a truthy update, the full lifecycle end to end. Also
confirmed the negative case: a "goblin" kill against the same quest produces zero `QuestUpdate`s
(no false-positive matching).

## Acceptance criteria disposition

The original ticket's AC list assumed a single, uniform fix ("HUNT quests generated via
`QuestGenerator.generate()` carry metadata that `evaluate_combat_victory()` can match against
real killed entities in live gameplay"). Delivered for `q_wolf_hunt` specifically; `q_slime_cull`
remains a disclosed, out-of-reach content gap — fixing it would require authoring real slime
content (a design/catalog decision, not a metadata-wiring fix), which is out of this ticket's own
scope per its own "Investigate must resolve, not invent, unilaterally" framing.
