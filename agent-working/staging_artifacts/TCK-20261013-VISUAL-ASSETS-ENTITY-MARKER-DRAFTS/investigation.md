---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS
artifact_type: investigation
tags: [architecture, testing, mcp]
---

# Investigation: entity role markers keyed on `kind`

## Precondition (recorded)
- Owner decision 2026-10-18 (relayed by lead-planner, GitHub #548): key on the presenter's role id `kind` (`src/api/presenters/state_presenter.py`, `present_entity`, field `kind`). No species/size markers.
- #523 is merged (the planner's base already carries main at `46d7c9da2`; `origin/main` has not moved past it today). D79 (#645) removed the level-up kind renames, so `kind` is stable. The exact #523 merge sha is not restated here: asset-planner recorded it in the ticket update `24c797b25`; the ticket's first acceptance criterion cites it from there.
- Branch base: `ab44d69b1` (planner's ticket update + merge of main). `git merge origin/main` was a no-op.

## Red set (re-derived on this base)
Command: `python -m tools.visual_assets_sample_map data --all` (reads the three compiled worlds, writes under the gitignored `reports/`). Counted from each `world_data.json` entity `kind`:

| kind | total | dungeon_crawl | frontier_living_world | highland_traverse |
|---|---|---|---|---|
| worker | 16 | 0 | 8 | 8 |
| scout | 14 | 6 | 8 | 0 |
| predator_hunter | 13 | 0 | 9 | 4 |
| sentinel | 12 | 6 | 6 | 0 |
| guard | 8 | 0 | 5 | 3 |
| merchant | 7 | 0 | 6 | 1 |
| wild_creature | 6 | 0 | 6 | 0 |
| raider | 4 | 0 | 4 | 0 |
| alpha | 2 | 0 | 1 | 1 |
| blacksmith | 2 | 0 | 1 | 1 |
| leader | 1 | 0 | 1 | 0 |

11 kinds, 85 entities. This equals asset-planner's re-derivation exactly and the ticket's list (the gap report's older "10 kinds, 79" plus `wild_creature` x6). No difference to record.

## What each kind is (`data/content/social/roles.yaml`)
worker = labor, humanoid tool user; guard = protector, humanoid; predator_hunter = ecological predator, carnivore; alpha = ecological leader, pack hunter; scout = recon, humanoid; raider = attacker, humanoid; leader = authority; merchant = trade; blacksmith = craft, craftsman; sentinel = guardian, **undead**; wild_creature = ecological forager, quadruped.

## Collision map the specs must beat (adopted art the markers sit beside)
- Class icons (24 px, shown elsewhere): warrior = shield with sword; ranger = longbow; mage = wizard hat; rogue = hooded cowl.
- Place glyphs (16 px): enemy camp = crossed swords, boss arena = skull, nest, resource grove = tree, ruins, shrine = obelisk, dungeon entrance = arch.
- Object nodes (16 px): grass tufts, herbs, berry bush, iron rock, crystals, wood logs, flowers, wisps, shards, resin tree.
- Building and item icons (24 px): anvil and hammer (blacksmith), coin purse (store), pickaxe (mine), tankard, banner, tower, crossed hammer and tongs (item.tool), sword (item.weapon).
So an entity marker must NOT be a shield, bow, wizard hat, cowl, crossed swords, a skull alone, a nest, a tree, an obelisk, a purse, an anvil or a pickaxe.

## Spec outline per kind (key family pending the owner's answer; specs are keyed by `kind` only)
Subject = one object or one small creature head upright and centred in the 16 px cell, 12x12 live area, theme D21 (medieval fantasy). Two candidates per kind go on the silhouette sheet; the owner picks.

| kind | candidate A (reads as) | candidate B | must not read as | distractors for the blind check |
|---|---|---|---|---|
| worker | a three-tine pitchfork, upright | a wooden spade | a trident, a pickaxe (mine icon), a fork | trident, rake, cutlery |
| guard | a spear with a pennant, planted upright (primary) | a kettle helm with a nose bar | a shield (warrior class), a flag, a javelin | flag, lance, sword |
| scout | a brass spyglass, diagonal | a hunting horn | a telescope on a stand, a rifle | rifle, trumpet, flashlight |
| raider | one bearded axe, head right (never crossed) | a torn red banner | crossed swords (enemy camp), a hatchet tool, the sword item | hammer, flag, pickaxe |
| sentinel (undead guardian) | an upright iron-bound coffin with a blue glow at the seam | a square stone idol face with two blue eye slits | any skull or bone (boss arena), the guard helm, a tombstone, a door | tombstone, door, violin case, robot head |
| merchant | a balance scale | a striped market awning on two poles | a coin purse (store), a pair of pans, a tent | purse, scales-of-justice emblem, tent |
| blacksmith | a horseshoe | an anvil | the blacksmith building icon (anvil with hammer, so B is the nearest collision), the crossed hammer and tongs tool | magnet, pliers, anvil-building |
| leader | a gold crown with three points | a signet seal | a tiara, a party crown | tiara, comb, flame |
| alpha | a wolf head, ears up, a notched ear | a standing wolf | a dog, a fox | dog, fox, cat |
| predator_hunter | three red claw slashes | a fanged snarling jaw | a scratch mark, a skull | scratch, rake, lightning |
| wild_creature | a grazing deer, side view | a hare | a horse, a goat, a nest | horse, goat, dog |

**Collision resolutions (asset-planner's review of ca3696cc0):** blacksmith dropped "tongs with ingot" (the crossed hammer and tongs tool, D21); merchant B dropped the laden pack (too close to the coin purse); sentinel has no skull, no bone and no helm (boss arena skull; guard's kettle helm), so it is a coffin or an idol face; raider is one weapon, never crossed (enemy camp).

Open design point (not decided here, an owner question at the silhouette gate): the treatment for the whole set. On a map cell a bare object can read as a dropped item or a resource node, not as a unit. The sheet shows, for worker, guard and sentinel, (a) a bare object emblem, (b) the emblem on a shared round unit token, (c) a figure silhouette; the other 8 kinds show A/B in treatment (b) as a preview. Every row is drawn on a 16 px cell beside the nearest existing glyph from the collision map, at 1:1 and x8.

## Not established
- Which candidate the owner prefers: the owner gate decides.
- The key family name: pending the owner's answer via lead (no key names are committed until it arrives).
