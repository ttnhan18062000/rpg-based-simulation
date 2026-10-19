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

## Blind naming check of the 22 silhouette emblems (after the redraw of cdd08be93's review)
Two fresh subagents, free text, no list, 22 shuffled unlabelled emblems on the token at x8 and 1:1. PASS = both named the intended object. 11 pass, 11 flagged; flagged shapes still go to the owner, marked as flagged.

| kind | cand. | intended | answers (agent 1 / agent 2) | result |
|---|---|---|---|---|
| worker | A | three-tine pitchfork | trident or pitchfork / same | PASS (trident risk) |
| worker | B | wooden spade | swan or duck / swan or snake | FLAG |
| guard | A | spear with a pennant | signpost or flag on a pole / same | FLAG |
| guard | B | nasal helm | helmet or archway / archway or doorway | FLAG |
| scout | A | brass spyglass | horn or megaphone / same | FLAG |
| scout | B | hunting horn | bowl or horned helmet / bird or bat, or a helmet | FLAG |
| raider | A | one bearded axe | flag on a pole / same | FLAG |
| raider | B | torn banner | banner or pennant / same | PASS |
| sentinel | A | iron-bound coffin | keyhole or lightbulb or map pin / key or lightbulb | FLAG |
| sentinel | B | stone idol face | face or mask / blank stone face | PASS |
| merchant | A | balance scale | scales of justice or a tree / same | PASS |
| merchant | B | striped market awning | crowned chest or fortress / treasure chest or fortress | FLAG |
| blacksmith | A | horseshoe | horseshoe or magnet / same | PASS (magnet risk) |
| blacksmith | B | anvil | anvil or hourglass / same | PASS (hourglass risk) |
| leader | A | gold crown | crown / crown | PASS |
| leader | B | signet seal | figure with a halo / figure with round head | FLAG |
| alpha | A | wolf head | bird head or fox/boar head / boar or bear head or a fish | FLAG |
| alpha | B | standing wolf | dog or wolf / same | PASS (dog risk) |
| predator_hunter | A | three claw slashes | claw marks / claw marks or bars | PASS |
| predator_hunter | B | fanged jaw | castle wall or gate / castle wall or jaws | FLAG |
| wild_creature | A | grazing deer | deer or stag / deer or horse | PASS |
| wild_creature | B | hare | rabbit or hare / same | PASS |


Finding: `icon_lookalikes.all_icon_sprites()` (key-set + v2 drafts) holds r0001 art; the seven owner-fix revisions (r0002: item.tool hammer and tongs, class.rogue, ...) are only in `icon_owner_fixes_draft_set.proposed_sprites()`. The entity sheet overlays them; other consumers of `all_icon_sprites()` still see the old wrench.

## Round 2 (guard and scout, new objects C and D), blind check with 4 passing distractors
Guard C lantern: FLAG (padlock x2). Guard D large gate key: PASS (key x2). Scout C open eye: PASS (eye x2). Scout D boot: PASS (boot x2). Distractors: crown PASS, hare PASS, horseshoe PASS (magnet risk), predator_hunter A claws read as steam or heat waves by both (it passed in round 1: borderline). Every kind now has a passing candidate (11 of 11); flagged shapes remain on the sheet, marked flagged. Guard A (spear) stays the treatment-comparison object on `01_treatments.png`.

## Consumers of `icon_lookalikes.all_icon_sprites()` (r0001 art for the 7 owner-fix keys), for the backlog ticket
Without the owner-fix overlay: `visual_assets/review/review_sheets.py:509` (adopted pictures on every review folder), `visual_assets/review/icon_silhouette_sheet.py:49`, `visual_assets/review/icon_recognition.py:211`, `visual_assets/review/icon_owner_fixes_draft_set.py:51` (its own base, then overlaid), tests `tests/visual_assets/test_icon_lookalikes.py:55`, `test_icon_recognition.py:13`, `test_icon_silhouette_sheet.py:27,39`, `test_icon_compliance.py:62,85,98` and `test_icon_owner_fixes_draft_set.py:59,73`. Some of those tests read r0001 deliberately (`test_icon_compliance.py:155,186-192` compare old against new). This batch's `tools/visual_assets_entity_marker_sheet.py:41` overlays `proposed_sprites()` itself.

## Colour drafts: compliance and final blind check (2026-10-19, set entity-markers-v1, draft set hash sha256:2f734b3feb9abff7285d321a5d3f1b04e441230f8e49e02912a3756433e88135)
Compliance (measured from the pixels of the kept drafts; 11 sprites, icons-v1 palette only, margin >= 2 px):

| kind | intake | bbox (w x h) | margin to edge (px) | colours / budget 8 | off-palette | fill mean L* (grass L* 38) | fill px weak against grass (contrast < 1.5) | weakest fill colour vs outline (contrast) | opaque px | fits live area (margin >= 2) |
|---|---|---|---|---|---|---|---|---|---|---|
| `icon.entity.alpha` | in-c18162e3a80693aa | 12 x 11 | 2 | 4 / 8 | none | 54 | 2 % | 2.8 | 102 | yes |
| `icon.entity.blacksmith` | in-c4c6e7646b850a3c | 12 x 11 | 2 | 4 / 8 | none | 52 | 15 % | 2.8 | 114 | yes |
| `icon.entity.guard` | in-bf7c72dbb48338ac | 8 x 12 | 2 | 3 / 8 | none | 59 | 0 % | 4.6 | 78 | yes |
| `icon.entity.leader` | in-f8b0e2e22f511692 | 12 x 8 | 2 | 5 / 8 | none | 72 | 2 % | 4.0 | 84 | yes |
| `icon.entity.merchant` | in-011ccc4be2bb89e5 | 12 x 12 | 2 | 4 / 8 | none | 72 | 0 % | 4.6 | 90 | yes |
| `icon.entity.predator_hunter` | in-338661ff2c6e9e12 | 12 x 11 | 2 | 3 / 8 | none | 46 | 100 % | 1.9 | 87 | yes |
| `icon.entity.raider` | in-f2a13d7d0371f7f0 | 11 x 12 | 2 | 4 / 8 | none | 48 | 76 % | 1.9 | 84 | yes |
| `icon.entity.scout` | in-d537975588e4c29f | 12 x 8 | 2 | 4 / 8 | none | 76 | 25 % | 2.2 | 80 | yes |
| `icon.entity.sentinel` | in-afe0e401c69c498e | 12 x 12 | 2 | 5 / 8 | none | 61 | 21 % | 2.7 | 136 | yes |
| `icon.entity.wild_creature` | in-dcc955af54c9ec2f | 12 x 12 | 2 | 5 / 8 | none | 42 | 88 % | 2.8 | 99 | yes |
| `icon.entity.worker` | in-73b77edca6e2faf8 | 11 x 12 | 2 | 5 / 8 | none | 72 | 0 % | 1.6 | 74 | yes |

Map-crop blind check (two fresh agents, 19 markers on a real map crop: the 11 entity markers, 4 resource nodes and 4 item icons as controls; question: what it depicts, and UNIT / ITEM / RESOURCE). Controls: 8 of 8 right in both. Entity markers: PASS (read as UNIT by both): alpha, scout, sentinel, wild_creature. FLAG (read as ITEM by both): blacksmith (horseshoe or magnet), guard (key), leader (crown), merchant (balance scale), raider (banner), worker (pitchfork or trident). FLAG (read as RESOURCE by both): predator_hunter (claw marks or red sticks). 4 of 11 read as a unit. Object naming right for 10 of 11 (predator_hunter split). The full per-agent table is at the top of the review folder's README.txt (~/Work/asset-review/entity-markers-v1/). Worker was redrawn once for contrast (lighter tines) before this check.
