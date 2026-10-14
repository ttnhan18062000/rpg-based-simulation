---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Blind recognition check and look-alike report: run record and results

Run on 2026-10-08 for `TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`. Evidence, not a CI gate.

## How the check was run

- Tool: `python -m tests.visual_assets.icon_recognition build|evaluate` (`tests/visual_assets/icon_recognition.py`). 36 icons (the 14 adopted and the 22 v2 drafts as they stood at `2d5742368`), each rendered unlabelled on one strip (native size and 4x, dark and light panel; a location glyph on the plate over the darkest and the brightest terrain fill), shuffled with seed 20261008 into neutral file names `icon-01.png` to `icon-36.png`. The answer key and the image hashes are in `blind_check/answer_key_and_image_hashes.json`; rebuilding with the same seed gave identical hashes.
- Two independent fresh agents (so the free-text pass was never primed by the candidate list): `general-purpose` subagents, model `sonnet`, each given a one-line prompt that only said to read a task file in a neutral directory (`/tmp/claude-1000/sheets/`, whose path does not mention the project) and follow it. The task files are stored in `blind_check/`. Pass 1: name each object in free text. Pass 2: pick the one candidate (the intended name once, the spec's distractors, `none of these`).
- **Context they had, stated plainly:** no project context was passed. The harness may still attach this repository's instructions to a subagent; I cannot see that, so "no project context" is the intent and not a verified fact. They were told to read nothing but the task file and the images, and each made 38 tool calls (the task file, 36 images and one more). They saw file names only (`icon-NN`), never a key, family or subject.
- Scoring: an icon is **flagged** when its free-text answer contains none of its spec's synonyms as a whole word (`icon_specs.yaml`). A first scoring counted "crossbow" as the synonym "bow" (substring); the tool was changed to whole-word matching and re-scored before this record (a test pins it); the answers were not touched.
- One run, one model, one pass each: the answers are not deterministic and the numbers are a single sample.

## Results (all 36)

| Icon | Status | Free-text answer | Free-text score | Choice pass |
|---|---|---|---|---|
| `icon.building.blacksmith` | adopted | anvil with hammer | named | correct |
| `icon.building.class_hall` | v2 | open spellbook | named | correct |
| `icon.building.guild` | v2 | red flag | named | correct |
| `icon.building.hero_house` | v2 | red-roofed house | named | correct |
| `icon.building.inn` | v2 | beer mug | named | correct |
| `icon.building.store` | v2 | gold coin pouch | named | correct |
| `icon.class.mage` | v2 | purple wizard hat | named | correct |
| `icon.class.ranger` | v2 | crossbow | **FLAG** (confused with: crossbow) | correct |
| `icon.class.rogue` | v2 | curved dagger | named | correct |
| `icon.class.warrior` | adopted | sword shield | named | correct |
| `icon.item.armor` | v2 | steel breastplate armor | named | correct |
| `icon.item.consumable` | v2 | red potion flask | named | correct |
| `icon.item.material` | v2 | gold ore rock | named | correct |
| `icon.item.tool` | v2 | war hammer | **FLAG** (confused with: hammer) | correct |
| `icon.item.trinket` | v2 | gold medal | **FLAG** (confused with: medal) | **missed**: a medal |
| `icon.item.weapon` | v2 | steel sword | named | correct |
| `icon.marker.boss_arena` | v2 | white skull | named | correct |
| `icon.marker.dungeon_entrance` | v2 | stone archway door | named | correct |
| `icon.marker.enemy_camp` | adopted | crossed swords | named | correct |
| `icon.marker.resource_grove` | v2 | green tree | named | correct |
| `icon.marker.ruins` | v2 | grey mountain peaks | **FLAG** | correct |
| `icon.marker.shrine` | v2 | stone obelisk marker | named | correct |
| `icon.plate.location` | adopted | grey square tile | named | correct |
| `icon.rarity.common` | v2 | dark grey square | **FLAG** | **missed**: a octagon |
| `icon.rarity.rare` | v2 | purple gem | named | correct |
| `icon.rarity.uncommon` | v2 | green gem | named | correct |
| `icon.status.frame_buff` | adopted | green round gem | **FLAG** | correct |
| `icon.status.frame_debuff` | adopted | red warning triangle | **FLAG** | correct |
| `icon.tier.a` | adopted | grey ring | named | correct |
| `icon.tier.b` | adopted | green round shield | **FLAG** | correct |
| `icon.tier.c` | adopted | dark ring on grey | named | correct |
| `icon.tier.d` | adopted | dark green circle | **FLAG** | correct |
| `icon.tier.e` | adopted | dark green circle | **FLAG** | correct |
| `icon.tier.s` | adopted | grey diamond | named | correct |
| `icon.tier.ss` | adopted | gold ring diamond | named | correct |
| `icon.tier.sss` | adopted | white diamond shape | named | correct |

**Flagged in free text (10):** `icon.class.ranger`, `icon.item.tool`, `icon.item.trinket`, `icon.marker.ruins`, `icon.rarity.common`, `icon.status.frame_buff`, `icon.status.frame_debuff`, `icon.tier.b`, `icon.tier.d`, `icon.tier.e`. **Missed in the choice pass (2):** `icon.item.trinket`, `icon.rarity.common`.

### What the flags mean (candid reading, for the planner to judge)

- **Real v2 misreads found:** `icon.marker.ruins` read as "grey mountain peaks" (the redraw's two stubs read as peaks); `icon.item.trinket` as "gold medal" (the pendant's chain is too short or thin to read as a necklace; the choice pass missed it too); `icon.item.tool` as "war hammer" (the pickaxe head reads as a hammer; the choice list rescued it); `icon.class.ranger` as "crossbow" (the bow and arrow read as a crossbow); `icon.rarity.common` as "dark grey square" (and missed in the choice pass, which picked "octagon": the bead's outline is squarish at 6x6).
- **Not caught: the sword.** `icon.item.weapon` was named "steel sword" in free text and picked correctly, and `icon.class.rogue` as "curved dagger". The owner's complaint about the sword (a short blade, a lumpy grip, a cleaver look, a near twin of the dagger) is a **quality and cross-family similarity** problem, not a naming problem: the check measures category recognition and cannot see "looks wrong". The look-alike report below does see the twin.
- **Calibration on the 14 adopted icons (report only, nothing changed):** flagged: `icon.status.frame_buff` ("green round gem": the up arrow is not read at a glance), `icon.status.frame_debuff` ("red warning triangle": the arrow is not read), `icon.tier.b`, `icon.tier.d`, `icon.tier.e` (abstract octagons named "green round shield" or "dark green circle"). Tier badges are abstract by design (the letter beside them carries the rank), so a free-text miss on them is expected; the buff and debuff frames are the notable ones. The other nine adopted icons named correctly.
- The choice pass is easier than free text (the answer is on the list): it missed only 2 of 36, so free text is the stricter reading.

## Whole-sheet look-alike report

`python -m tests.visual_assets.icon_lookalikes` (stored: `lookalike_report.json`): 36 icons, method: bounding box fitted to 24x24 by nearest neighbour, XOR pixels out of 576; report only. 16 pairs are at or under 60 XOR pixels (11 across families). The closest cross-family pairs, nearest first:

| Pair | XOR px |
|---|---|
| `icon.item.material` and `icon.status.frame_buff` | 41 |
| `icon.marker.boss_arena` and `icon.tier.d` | 48 |
| `icon.marker.boss_arena` and `icon.tier.e` | 48 |
| `icon.marker.dungeon_entrance` and `icon.rarity.common` | 48 |
| `icon.rarity.common` and `icon.tier.d` | 52 |
| `icon.rarity.common` and `icon.tier.e` | 52 |
| `icon.class.rogue` and `icon.item.weapon` | 55 |
| `icon.marker.dungeon_entrance` and `icon.plate.location` | 55 |
| `icon.plate.location` and `icon.rarity.common` | 55 |
| `icon.rarity.uncommon` and `icon.tier.s` | 56 |

The weapon sword and the rogue dagger are each other's nearest neighbour at 55 XOR px, while the nearest other neighbour of either is 152 px away: an isolated twin, which is the signal. Most other close pairs are boxy badges and tiles (the bounding box is fitted to the canvas, so rounded squares and octagons come out close); that is a limit of the method and is why the report is read by a person and decides nothing.
