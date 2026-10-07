---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation, hud]
---

# Icon set v2 `icons-v2`: what was drawn, how it measures, how to review it

Written by `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`. The set is a **draft**: nothing is adopted, released or read by the game, and the adopted key set `icons-key-v1` is unchanged (no pixel of it was touched).
Style: `docs/assets/icon_style_guide.md` (D20 and the v2 decisions: six item families, three rarity badges, the glyph table). Palette and sheet rule: `docs/assets/icon_criteria.md` (the owner's thresholds, 2026-10-06 and 2026-10-07).

## What is in the set (22 keys, own pixels, palette `icons-v1` only)

| Family | Keys | Size | Drawing |
|---|---|---|---|
| locations (5) | `icon.marker.resource_grove`, `ruins`, `dungeon_entrance`, `shrine`, `boss_arena` | 16x16, live area 12x12, 2 px margin, over the adopted plate | tree; a ruined brick wall (4 courses of alternating light and dark bricks, a U-shaped broken top edge, a fallen brick in the gap; redrawn in 4c); arched door; obelisk (slim straight shaft, pointed light-stone tip, gold marks, 2 px plinth); skull |
| buildings (5) | `icon.building.store`, `guild`, `inn`, `hero_house`, `class_hall` | 24x24 | coin purse with a coin; banner on a pole; mug; small house; open book |
| classes (3) | `icon.class.ranger`, `mage`, `rogue` | 24x24 | longbow with a nocked arrow (vertical, curved limbs, pulled string, no stock; redrawn in 4c); pointed hat; dagger |
| items (6) | `icon.item.weapon`, `armor`, `trinket`, `tool`, `consumable`, `material` | 24x24 | upright sword (20 px, 12 px blade, 12 px guard, pommel; redrawn in 4c); chest plate; pendant on a thin chain loop (redrawn in 4c); wrench (redrawn in 4c); potion flask; ore chunk |
| rarity (3) | `icon.rarity.common`, `uncommon`, `rare` | 8x8 | round 7x7 bead (slate, one highlight pixel; redrawn in 4c); kite gem (green); four-point sparkle gem (violet) |

Provenance: every drawing is our own pixels (`licence_state UNREVIEWED`, as for terrain); no outside art was copied or traced and no AI generator was used.
**How they were drawn, stated plainly:** through `visual_assets.drawing.api` called in-process from a script (`new_sprite`, `apply_ops`, then `handoff.build_handoff`), not by pasting each draw operation into the MCP tools. The MCP tools are thin wrappers
over the same functions (same Aseprite adapter, Lua pin, workspace, revisions and handoff packaging); the planner accepted the transport (2026-10-08). The handoff `limitations` text says this; no field claims an MCP call. The intakes were submitted with the
worktree CLI (`python -m visual_assets.store intake`), so there are no stray intakes in the main checkout's quarantine this time. The script and the prototype tooling are committed so the pixels are reproducible:
`agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET/drawing/` (`draw_all.py` draws all 22; `loc.py`, `pan.py`, `rar.py` hold the shapes, `canvas.py` the small pixel canvas with the same lint).

## The sheet rule on this set, as measured

`python -m tests.visual_assets.icon_v2_draft_set` (recorded in the v2 preview fixture as `icondraft_v2/rule_result.json`; draft set hash `sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4`). Groups and the shape-only rule are the owner's answers (I1 only for the five subject groups, I1 and I2 for rarity; 3 / 6 / 8 px at 8x8 / 16x16 / 24x24):

| Group | Pairs | Smallest silhouette difference | Needed | I2 (value) |
|---|---|---|---|---|
| rarity (3, 8x8) | 3 | 13 px | 3 | L* gap 9.6 (protan), 10.2 (normal), 10.8 (deutan), 11.0 (tritan), needed 6 |
| badges (rarity and tiers, 11, 8x8) | 55 | 4 px (a pair of adopted tiers, as before) | 3 | not checked (shape only) |
| locations (6, 16x16) | 15 | 17 px | 6 | not checked |
| buildings (6, 24x24) | 15 | 65 px | 8 | not checked |
| classes (4, 24x24) | 6 | 132 px | 8 | not checked |
| items (6, 24x24) | 15 | 71 px | 8 | not checked |
| rarity badge vs the nearest tier badge | | 9 px (common), 16 px (uncommon), 8 px (rare) | 3 (planner's floor) | |
| Result | | | | **PASS** (I1 true, I2 true, I3 true) |

Also measured, not ruled: no pixel outside the palette; `lint_sprite` has no warning on any of the 22 (info notes only); colour counts within budget (8 at 16 px or less, 12 at 24 px); the five location glyphs sit inside the 12x12 live area (the shrine
is narrower: margins 4, 2, 4, 2; the ruins wall: 2, 2, 2, 3); every 24x24 icon sits inside the 20x20 live area.

**How this was reached (stated plainly).** The rule was fixed first (the 24x24 threshold and the group definitions are committed, child 3). All 22 were prototyped on a local pixel canvas with the same lint and the same rule, rendered and looked at, **before** drawing.
Changes made from looking at previews, not from the rule (design-loop changes): the first uncommon badge, a "kite" with a short 2x2 tail, read as an up-arrow and would be confused with the buff chevron, so it became a proper kite gem; the first common bead looked like a
dark tier octagon, so it got a highlight pixel; the broken column and the obelisk were both grey verticals, so the planner asked for different silhouettes (first redraw, before drawing; 39 px apart); several `value_separation` lint warnings on colour pairs of near-equal brightness (guild banner shade, inn foam, house roof, hall spine, trinket chain, tool handle, potion liquid and cork) were fixed by changing the shade
colours. After drawing nothing was tuned, and no threshold moved. No rule FAILED, so there was nothing to report before a redraw.

## Redraw of the shrine and the ruins, before the owner gate (planner request, 2026-10-08; the ruins were redrawn again in 4c, below)

The first drawings did not read at 1x: the shrine (a tapered shaft with a wide gold cap and a flared base) read as a bell or bottle, and the ruins (one wide column on a slab with a fallen chip) as a boot or chess piece. Only those two slots were redrawn
(intakes `in-480096d34ae89c62` ruins and `in-25999d7f6179c6af` shrine, `draft keep --replace`; the other 20 are untouched):

- **shrine:** a slim straight shaft with straight sides, a pointed pyramid tip in light stone (no cap, no flare), two gold marks, a 2 px plinth. Bounding box 4, 2, 11, 13 (live area respected).
- **ruins:** two broken column stubs of different heights with jagged, notched tops and a fallen block between them, on one ground slab, so it cannot read as a single object. Bounding box 2, 2, 13, 13.

| Rule, locations (floor 6 px) | Before the redraw | After the redraw |
|---|---|---|
| result | PASS | PASS |
| smallest silhouette difference in the group | 17 px (boss arena vs dungeon entrance) | 17 px (same pair, untouched) |
| ruins vs the other five | not recorded per pair | 27 px (dungeon entrance), 40 (boss arena), 49 (shrine), 54 (grove), 61 (enemy camp) |
| shrine vs the other five | not recorded per pair | 45 px (grove, boss arena), 49 (ruins), 52 (camp), 62 (dungeon entrance) |
| ruins vs shrine (the old column vs obelisk pair) | 39 px | 49 px |
| draft set hash | `sha256:e51c69dd07ecf63c8ac80ca125600b6b3bd67f0bffe795e3588fb9d2dd9c7399` | `sha256:07ded31ec3dbddba4cae5ba54eca5d80da9dc739bc544156af0fc97efc3d6d9c` |

Everything else in the rule result is unchanged (I1 group minimums, rarity I2, lint with no warnings, no off-palette pixel). The two redraws were prototyped on the local canvas first and the drafts equal the prototypes pixel for pixel. The redraw sprites are named `icon_marker_ruins_r2` and
`icon_marker_shrine_r2` in the Aseprite workspace (the first drawings remain there as revisions of the original names); `draw_all.py` in the stored artifact reproduces the final set from scratch with the final shapes.

## Recognisability redraw (child 4c, 2026-10-08)

**Why.** At the owner gate the weapon sword looked wrong; the root cause was that every gate measures that icons can be told apart and none measures that an icon reads as its object, or that it was drawn to its own proportions (child 4b built the specs, the blind recognition check and the look-alike report; the style guide's process rule now has a **spec compliance table** step).
Six icons were redrawn to their specs (the planner's ruling): the sword, the ruins, the trinket, the tool, the ranger and the common bead. The dagger was kept (see below); the adopted buff and debuff frames and tier badges B, D and E are report-only (their pixels are the owner's adoption).
Intakes `in-67d30565242ae4b2` (sword), `in-fa44bc9593c67d1a` (ruins, second redraw; the first, `in-dd060effff6114b2`, was replaced), `in-cea39b417969f237` (trinket), `in-f3317753fdded43f` (tool), `in-bdc7f9c4c8598f7e` (ranger), `in-685f6313c25ff506` (common bead), each `draft keep --replace` on its own slot; the other 16 v2 icons are untouched.

| Icon | Before (blind free text, 4b) | Why it misread / was wrong | After (blind free text, final round) | Choice pass after |
|---|---|---|---|---|
| `icon.item.weapon` | "steel sword" (looked wrong to the owner) | blade 4 px long, grip wider than the guard, no pommel; a near twin of the dagger (55 XOR px) | "short sword" | a sword |
| `icon.marker.ruins` | "grey mountain peaks" (earlier: a boot) | one-way stepped silhouette | "grey building blocks" (**still flagged**; round A, with a slab and two bricks under the wall, was "grey wagon cart") | a ruined brick wall |
| `icon.item.trinket` | "gold medal" | the chain read as two ribbons | "blue gem amulet" | a pendant on a chain |
| `icon.item.tool` | "war hammer" | a hammer reads as a weapon | "steel wrench" | **none of these** (round A picked a wrench) |
| `icon.class.ranger` | "crossbow" | a thick arrow bar read as a stock | "bow and arrow" | a longbow with a nocked arrow |
| `icon.rarity.common` | "dark grey square" | 6x6 bead with cut corners | "grey-blue circle" | a round bead |

**Decisions recorded in the specs (`icon_specs.yaml`):**
- The **tool** family icon is a **wrench**, diagonal. The catalog's `tool` category holds two items, a repair kit and a spirit lantern; neither is a mining tool, and a hammer or pick reads as a weapon. A wrench is the one tool glyph that fits the repair kit and reads as a tool; the lantern has no match (flag for the owner: a lantern item would show a wrench).
- The **sword** is upright (Tiny Dungeon's convention) and the **dagger stays diagonal**, so they never share a pose. The dagger was kept: after the redraw its nearest neighbour is the wrench at 160 XOR px and the sword's is the shrine at 101 (the planner's bar was about 100 px between the dagger and the new sword).
- The **ruins** went through four ideas: broken column (a boot), two stubs (mountain peaks), a stepped wall with a slab and two bricks (a wagon cart: the slab read as a cart bed and the bricks as wheels), and finally a wall with a **U-shaped broken top** and the fallen brick lying in the gap, no slab. The last reads as a brick wall in the choice pass; free text still says "building blocks" (see the flags).

### Spec compliance table (each proportion MEASURED from the pixels; the full tables are in `docs/assets/` stored artifact `compliance_after.md`)

**`icon.item.weapon`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | upright, point up, centred on the vertical axis | height 20 px, width 14 px, tip row 2 px wide, content centre x 11.5 of canvas centre 11.5 | ok |
| total height | 20 px | 20 px | ok |
| blade length | >= 60 % of the total height | 12 px = 60 % | ok |
| blade width | 3 to 4 px | 4 px | ok |
| crossguard width | 9 to 12 px | 12 px | ok |
| crossguard thickness | 2 px | 2 px | ok |
| grip width | never wider than the guard or the blade | 2 px (guard 12, blade 4) | ok |
| grip length | 2 to 3 px | 2 px | ok |
| pommel | present, wider than the grip | 2 row(s), 4 px wide | ok |

**`icon.marker.ruins`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| brick courses | >= 4 alternating light and dark rows (read down the tallest column) | 4 colour bands | ok |
| broken top edge: distinct heights | >= 3 column heights | 6 ([3, 4, 7, 8, 9, 10]) | ok |
| broken top edge: U-shaped, not a slope | heights go up and down (not monotone) and the middle is lower than both ends | heights left to right [4, 4, 4, 8, 9, 7, 10, 3, 3, 3] | ok |
| fallen brick | >= 1 loose group of 2 px or more, not part of the wall | 1 ([2] px) | ok |
| nothing under the wall | no ground slab or matched pair of bricks below the wall's bottom course | 0 row(s) below the wall's bottom row | ok |
| wall width | about 10 px | 10 px | ok |

**`icon.item.trinket`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| bail ring at the apex | a ring of 4 px or less at the top row | top row 2 px wide | ok |
| chain thickness | 1 px strands (never a ribbon) | longest horizontal run in the chain rows 1 px | ok |
| chain loop | two separate strands from the apex down to the pendant | 4 of 4 chain rows have 2 strands | ok |
| chain loop width | wider than the pendant's neck so it rises to a point: >= 12 px | 12 px | ok |
| pendant width | >= 9 px | 10 px | ok |
| pendant height | >= 8 px | 8 px | ok |
| gem | >= 5 px wide and >= 4 px tall | 6 x 5 px | ok |

**`icon.item.tool`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | diagonal: long axis rises to the right at 35 to 55 degrees | 45 degrees | ok |
| elongation | long axis at least 2 times the short axis | 2.5 | ok |
| open jaw | a notch in the head: solidity (pixels over convex hull) at most 0.90 | 0.63 | ok |
| hole in the handle end | >= 1 enclosed hole (outline-coloured, no transparent neighbour) | 1 ([3] px) | ok |

**`icon.class.ranger`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| orientation | vertical bow, at least 18 px tall | 18 px tall (whole icon 20) | ok |
| curved limbs | the belly stands at least 4 px away from the line between the tips | 7 px | ok |
| string | >= 14 visible string pixels | 15 px | ok |
| arrow nocked | a horizontal shaft of at least 12 px that crosses the bow | longest run 16 px | ok |
| no stock or bar | no horizontal bar thicker than 2 rows | 1 row(s) with a run of 8 px or more | ok |

**`icon.rarity.common`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| round, not square | silhouette fills at most 80 % of its bounding box (a circle is 79 %, a square 100 %, an octagon about 88 %) | 76 % | ok |
| size | 7 px across (never the tier's 8) | 7 x 7 px | ok |
| highlight | one lighter pixel inside | 1 lighter pixel(s) among 2 fills | ok |
| distance from the tier badges | >= 3 px (I1 floor) from every tier silhouette | 9 px | ok |

Before the redraw the same measurements failed: the old sword could not even be measured (no crossguard to find), the old ruins had 3 colour bands and no fallen brick, the old tool was not elongated and had no hole, the old bow's belly stood 0 px from its tips, the old bead filled 89 % of its box at 6 px, and the old pendant's loop was 9 px wide (`compliance_before.md`). Two of my measurement definitions were corrected after I looked at their numbers on the new drawings (the pendant's narrow top rows were counted as chain, and the wrench's hole is drawn in the outline colour, not transparent); thresholds were not changed.

### Blind recognition check, run again on all 36 (two fresh agents per round, sonnet, same neutral setup as 4b)

- **Round A** (ruins still the wall with a slab): flagged in free text: ruins ("grey wagon cart"), common bead ("grey round disc", which names a round object but none of the spec's synonyms), buff and debuff frames, tier D and E; choice pass missed nothing. Under the same spec the sword, trinket, tool and ranger all named correctly.
- **Round B** (final art): flagged in free text: ruins ("grey building blocks"), `icon.class.rogue` ("curved sword hilt"), `icon.rarity.uncommon` ("green dot"), buff, debuff, tier B, D and E; choice pass missed the tool ("none of these", although round A picked "a wrench") and the buff frame. The sword, trinket, tool (in free text), ranger and common bead named correctly in free text.
- **It is noisy.** The unchanged dagger was "curved dagger", "dagger in sheath" and "curved sword hilt" in three rounds, the unchanged uncommon gem "green gem" and "green dot", the tier badges B, D, E flip between rounds: one model, one sample per round. Read a flag as a hint to look, not a verdict. Answers, prompts and hashes: `blind_check/` in the stored artifact. The same caveat as 4b applies about "no project context".
- **One synonym was added after seeing an answer:** "archway" for the dungeon entrance (a correct reading, "stone archway", counted as a miss because the spec only listed "arch"). It is recorded here and in the spec's history; no other synonym was added after a result, and "round" was removed from the bead's list before scoring because it is too lax.

### Look-alike report after the redraw

`lookalike_after.json`: 15 pairs at or under 60 XOR px (it was 16); the sword and the dagger are no longer each other's nearest neighbour. **New close pair, worth a look: the common bead and the dark tier badges D and E at 25 XOR px** (a round 7 px bead against octagon badges once both are fitted to the same canvas; at their own sizes they differ by 9 px and the rule passes). The rarity badge sits beside the tier badge in the UI, so this is the pair to judge at 1x. Other close pairs are boxy badges and tiles, the method's known limit.

## Things the owner should judge with their own eyes (honest findings)

1. **Rarity next to tier at 8x8.** Rarity and the tier ladder are both small abstract badges. They differ in silhouette (round bead, kite, sparkle against octagons and diamonds) and in size, and the rule passes (the bead is 9 px from the nearest tier silhouette). The look-alike report puts the **common bead and the dark tier badges D and E at 25 XOR px** once fitted to one canvas, and the blind check read the bead as "dark grey square" before the redraw and as a circle after; whether a player tells the bead from a dark tier badge at 1x is an eye judgement. The name stays as text beside each.
2. **The location glyphs are small, and the ruins are the hardest glyph in the set.** At 16x16 on the plate the shrine is the narrowest glyph (4 px margins left and right). The closest pair of locations by silhouette is boss arena vs dungeon entrance (17 px, both rounded domes of similar size, never touched by a redraw). The ruins have now been redrawn four times (a boot, mountain peaks, a wagon cart, now a brick wall): the choice pass names the wall correctly every time, but free text still says "building blocks", so a reader without a label may not say "ruins" (the name stays as text).
3. **Stand-ins for real objects.** The coin purse reads as a bag of gold (store); the banner as a guild flag; the open book for the class hall is the most abstract building. The mug is for the inn. If any reads wrongly, the glyph table in `icon_style_guide.md` is where to change it.
4. **Items are six families, not categories.** A weapon is always the sword, whatever the weapon. The rarity badge sits beside the family icon (the client composites them; nothing is wired).
5. **Blade overlap across families (flag only, no change).** The rogue dagger (class) and the weapon sword (item) are both blades with a gold guard and a brown grip, and the warrior (shield and sword, adopted) and the enemy camp (crossed swords, adopted) also use swords. After the 4c redraw the sword is upright and the dagger diagonal, so they no longer look alike (the sword's nearest neighbour is the shrine, the dagger's the wrench), but they still share parts. The families never share a panel and the owner approved "dagger"; for the owner's judgement.
6. **Fallbacks.** Every key shows today's fallback beside it on the page (copied from each key's registry description, with its colour); the class hall has none today (the building name as text).
7. **The tool is a wrench (4c).** The catalog's two tool items are a repair kit and a spirit lantern; a wrench fits the first and not the second, and an item that reads as a weapon (a hammer, a pick) was wrong for the family. Adopt the wrench or ask for a different tool glyph.
8. **Adopted icons that the blind check could not read (report only, nothing changed).** The buff frame ("green round gem", "green round shield") and the debuff frame ("red warning triangle") are not read as arrows at a glance, and tier badges B, D and E are read as circles; their pixels are the owner's adoption from `icons-key-v1`, so they are reported, not changed.

## Review it

The preview page shows the adopted key set as before and, below it: the v2 contact sheet by family at 1x and 2x on a dark and a light panel beside the fallbacks; the six location glyphs (the adopted enemy camp and the five new) on the plate over the darkest (floor) and brightest (snow) terrain-v1
tile; the rarity badges next to the eight tier badges in colour, greyscale and three simulated visions (a visual approximation only: the verdict is the recorded result above); and the recorded v2 rule result.

```
cd /home/vboxuser/Work/rpg-aseprite-mcp/frontend && npx vite
# open http://[::1]:5173/rehearsal-icons.html  (the port Vite prints; dev only, never in the production build)
```

`adopt-set` is human-only and **needs your own terminal** (it refuses without a TTY; an agent session cannot run it). If you adopt the set, you give your own name, role, licence decision and evidence (nothing is pre-answered here; `adopt-set --help` says only `CLEARED` is adoptable):

```
/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python -m visual_assets.store adopt-set icons-v2 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" \
  --licence-evidence "<your own evidence reference>" --review-evidence "preview page rehearsal-icons.html of icons-v2, draft set hash sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4"
```

Run it from `/home/vboxuser/Work/rpg-aseprite-mcp` (the worktree that holds the drafts). If the set is not adopted, the batch stops after child 4 (child 5 records an adoption and is skipped).

## Where the intakes are

All 22 were submitted once with the worktree CLI (draft ids in `visual_assets/drafts/icons-v2/draft_set.json`); the handoff directories are in the Aseprite workspace's `handoffs/` (gitignored, 30-day local retention applies).
