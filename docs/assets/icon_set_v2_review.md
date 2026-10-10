---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation, hud]
---

# Icon set v2 `icons-v2`: what was drawn, how it measures, how to review it

Written by `TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET` and extended by the recognisability tickets. **Adopted by the owner on 2026-10-08T00:40:15Z** (set adoption `sa-c9082d078b954f6b`, approver nhan, owner, 22 entries), after this review; recorded by `TCK-20261007-VISUAL-ASSETS-RECORD-ICON-V2-ADOPTION`. No release candidate covers the icon slots (rc-0007 has 34) and the game does not read them. Before the adoption the set was a draft; the text below describes the set as reviewed. The adopted key set `icons-key-v1` was never touched.
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

`python -m visual_assets.review evaluate --set icons-v2 --recorded` (recorded in the v2 preview fixture as `icondraft_v2/rule_result.json`; draft set hash `sha256:bb41c3eef245f6eab3488d5c7a940e574a463112a0bfba611b0c5cfd012737f4`). Groups and the shape-only rule are the owner's answers (I1 only for the five subject groups, I1 and I2 for rarity; 3 / 6 / 8 px at 8x8 / 16x16 / 24x24):

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

## Owner fixes before PR #418 merges (2026-10-08): seven revisions of adopted icons

**Why.** The owner held the merge and chose to fix every judgement item of the planner's readiness comment, then added theme fit (D21: medieval fantasy plus magic, nothing modern). All the slots are **adopted sources**, so each change is a **new revision `r0002` (parent `r0001`)** made by the store's own `adopt --parent`, never an edit of an adopted file. The drawings live in a new draft set `icons-owner-fixes-v1` (draft set hash `sha256:bab784060aedc76838ebc246a3534d88559c9493082b1e076a1bdedb8b8fc6e0`); `icons-v2` and `icons-key-v1` stay as history and their recorded hashes still hold.
**`adopt-set` cannot make revisions today** (it only creates new source assets): the owner runs one `review` and one `adopt` per slot, below (14 commands for seven slots). A store change to allow revisions in a set is out of scope here.

**Owner decisions, recorded verbatim (relayed through the planner's blocking questions, 2026-10-08).** After seeing the first six drafts: "Keep current versions" for the ruins arch and the spear-tent camp: **not revised, not proposed** (the adopted brick wall and crossed swords stay; both new drawings still misread in free text). Theme fit: theme = "Medieval fantasy + magic", tool = "Hammer and tongs" (the toolbox was rejected as a modern suitcase), hero house = "Redraw as cottage", debuff frame = "Reshape the frame", inn = "Add staves". The owner approved the hammer-and-tongs outline by my own blocking question ("Approve option A") and the cottage, spiked frame and tankard outlines by another ("Approve all three"). The two declined drafts stay in `icons-owner-fixes-v1` only because the store has no command to drop a draft slot (`draft` has `keep`, `export` and `verify`); they are marked "not proposed for adoption, owner decision" and are never candidates.

**Process followed (style guide, steps 1 to 6).** Specs first (`icon_specs.yaml`, status `revision`, now with `theme` and `modern_lookalikes_to_avoid`); a reference study (Kenney previews, CC0, recorded in the style guide); a one-colour silhouette sheet the owner approved before drawing; drawing; the compliance table; the sheet rule, the blind check (free text, choice list **and the new era question**) and the look-alike report.

| Slot | Before (blind answers on the adopted drawing) | Why it changed | After (round 5: free text / era answer) | Choice pass after |
|---|---|---|---|---|
| `icon.status.frame_buff` | green round gem / green round shield | the chevron frame read as a gem, not an up arrow | up arrow on green badge / cannot tell: upward arrow badge | a round frame with a solid up arrow |
| `icon.status.frame_debuff` | red warning triangle (era-flagged: a modern road sign) | an inverted red triangle reads as a modern road warning sign (theme fit D21) | red spiked gear target / cannot tell: red gear emblem (**free text flagged, era flagged**) | a spiked ball frame with a down arrow |
| `icon.class.rogue` | curved sword hilt (round 3), curved dagger / dagger in sheath (rounds 1, 2) | the dagger duplicated the sword's blade motif | hooded figure / medieval or fantasy: hooded cloaked figure | a hooded cowl |
| `icon.item.tool` | steel wrench (era-flagged: a modern mechanic's tool) | a wrench is a modern tool; the owner rejected the toolbox as a modern suitcase and chose hammer and tongs (D21) | crossed hammer and wrench / medieval or fantasy: hammer and wrench (**free text flagged, era flagged**) | a smith's hammer crossed with tongs |
| `icon.rarity.common` | grey round disc / grey-blue circle | it sat next to the dark tier badges E and D and looked like them | white orb / cannot tell: grey round orb | a silver bead |
| `icon.building.hero_house` | small red house (the era question could not say) | white walls and blue glass windows read as a modern suburban house (D21): "Redraw as cottage" | cottage house / medieval or fantasy: thatched cottage house | a timber-framed cottage |
| `icon.building.inn` | beer mug (era: medieval; borderline) | a glass-like mug; "Add staves": the same tankard with wooden staves and iron hoops (D21) | beer mug / medieval or fantasy: wooden beer tankard | a tankard with wooden staves and iron hoops |

**Sheet rule on the set as it would stand with these seven in place: PASS** (key-set groups PASS, v2 groups PASS; thresholds unchanged). Smallest silhouette difference by group: status 28 px, tiers 4 px, badges 4 px, buildings 69 px, classes 53 px, items 71 px, locations 17 px, rarity 13 px. Buff vs debuff (status): 28 px apart (needed 6) and I2 smallest L* gap normal 15.659, protan 20.247, deutan 12.815, tritan 15.52 (needed 6); rarity I2 smallest L* gap normal 14.444, protan 13.012, deutan 14.482, tritan 14.822. Rarity vs the tier badges: common 9 px. Lint: no warnings; no pixel outside the palette.

### Spec compliance table (each proportion MEASURED from the pixels)

**`icon.status.frame_buff`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| frame unchanged | no pixel outside the central 8 x 9 box differs from the adopted frame | 0 pixels differ outside the box (16 in all) | ok |
| solid head | head rows 2, 4 then 6 px wide | first rows [2, 4, 6] | ok |
| shaft | 2 px wide and 5 px tall below the head | rows [2, 2, 2, 2, 2] | ok |
| solid, not an outline | 22 bone pixels in all, one filled shape | 22 px in 1 piece(s) | ok |
| centred | the arrow's columns centre on the canvas axis | columns 5 to 10 of 16 | ok |

**`icon.status.frame_debuff`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| size | 16 x 16 px, filling its canvas like the buff frame | 16 x 16 px | ok |
| eight spikes | a red spike beyond the ring in each of the eight compass directions | spikes in 8 of 8 directions | ok |
| red rim | >= 40 red pixels | 52 px | ok |
| solid down arrow | 20 bone pixels in one piece: a shaft 2 wide and 4 tall, then a head 6, 4 and 2 wide | 20 px, row widths [2, 2, 2, 2, 6, 4, 2] | ok |
| not a triangle (not a road sign) | the silhouette fills at least 60 % of its bounding box (a triangle fills 50 %) | 69 % | ok |
| symmetric | the silhouette is mirror-symmetric left to right | 0 differing px | ok |
| differs from the round buff frame | >= 6 px (I1 at 16x16) | 28 px | ok |

**`icon.class.rogue`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| peaked hood | the top row is 2 px wide or less and rows widen steadily to the shoulders | top row 2 px; widest 18 px; steady widening over the first 12 rows: True | ok |
| shoulders | widest row 18 px | 18 px | ok |
| face opening | >= 8 px wide and >= 8 px tall, dark | 8 x 9 px, 56 px | ok |
| eye glints | two separate gold marks of 2 px | 4 px in 2 marks | ok |
| no brim | the hood is never wider than the shoulders at its top half (a hat has a brim): the first 10 rows are at most 14 px wide | widest of the first 10 rows 12 px | ok |
| live area | margins of at least 2 px left, top and right on the 24x24 canvas | 2, 2, 2 px | ok |

**`icon.item.tool`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| size | 19 px wide and 19 px tall, outline included (an X, not a long weapon) | 19 x 19 px | ok |
| live area | margins of at least 2 px on all four sides of the 24x24 canvas | 3, 2, 2, 3 px | ok |
| wooden handle | >= 14 px of wood colour (the hammer's handle) | 21 px | ok |
| steel hammer head | >= 20 steel pixels in the top right (a short heavy head; the outline the owner approved gives 22) | 22 px | ok |
| tong jaws | >= 8 steel pixels in the top left (the closed jaws) | 16 px | ok |
| rivet at the crossing | a gold rivet of at least 8 px | 8 px | ok |
| crossed, one piece | the two tools touch: all content is one connected piece | 1 piece(s) | ok |

**`icon.rarity.common`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| round, not square | silhouette fills at most 80 % of its bounding box | 76 % | ok |
| size | 7 x 7 px | 7 x 7 px | ok |
| silver fill | >= 12 px of silver (#c8d8e8) | 13 px | ok |
| highlight | 2 px of bright highlight (#eafeff) | 2 px | ok |
| shade | >= 4 px of shade (#91a2ab) on the lower right | 6 px | ok |
| lighter than the dark tier badges | mean L* at least 20 above tier D and tier E | 52.3 L* above the nearer one | ok |
| distance from the tier badges | >= 3 px (I1 floor) from every tier silhouette | 9 px | ok |

**`icon.building.hero_house`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| size | 20 px wide and 20 px tall, outline included | 20 x 20 px | ok |
| thatched roof | >= 80 px of thatch (two golds; the approved outline gives 84) | 84 px | ok |
| timber frame | >= 40 px of timber brown | 52 px | ok |
| plaster walls | >= 30 px of cream plaster (the approved outline gives 36) | 36 px | ok |
| small windows with dark panes | two separate dark panes of 4 px | 2 panes [4, 4] | ok |
| shutters | four separate green shutter strips | 4 strips | ok |
| arched wooden door | >= 20 px of door wood | 23 px | ok |
| no modern blue glass | no pixel of the old window blue (#50a8e0) | 0 px | ok |
| palette | within the 24x24 budget of 12 colours (outline included) | 11 | ok |

**`icon.building.inn`**: all measurements within the spec

| Measurement | Spec | Measured from the pixels | |
|---|---|---|---|
| same outline | the silhouette is exactly the adopted tankard's | 0 differing px | ok |
| stave seams | >= 2 vertical dark brown seams of at least 7 px | columns [8, 11, 13] | ok |
| iron hoops | two steel-grey rows of at least 9 px | rows [11, 17] | ok |
| foam and handle untouched | no pixel outside the body box differs from the adopted drawing | 0 px differ outside the body | ok |

### Blind check, round 5 (three fresh agents, sonnet, neutral setup; all 36 icons with the seven in place)

- **Named correctly in free text, in the choice list and in the era question:** the cottage ("cottage house"; era: "thatched cottage house"), the tankard ("beer mug"; era: "wooden beer tankard"), the buff frame, the rogue ("hooded figure") and the silver bead ("white orb").
- **Two new drawings still misread at a glance (the choice pass names both):** the tool's tongs read as a **wrench** ("crossed hammer and wrench", era: "hammer and wrench", flagged by the named modern object) and the spiked-ball debuff frame as a **gear** ("red spiked gear target", era: "red gear emblem", flagged). **Owner decision (planner's blocking question, 2026-10-08), verbatim: tool "Accept as drawn"; debuff spiked ring "Accept as drawn".** Nothing was tuned.
- Still flagged in free text as before: the adopted ruins wall (kept by the owner), tier badges A, D and E (abstract, expected). The era question is weak on its own (most answers are "cannot tell"); it only flags when the object named is modern, which is why free-text scoring also checks the named object now.
- One model, one sample per round, noisy; the "no project context" caveat applies.

### Look-alike report with the seven in place

14 pairs at or under 60 XOR px. The closest cross-family pair is still the common bead and tier D and E at 25 px (a shape twin, an owner finding). The new icons' nearest neighbours: cottage class.rogue 96, tankard building.store 83, hammer and tongs marker.enemy_camp 134, spiked frame status.frame_buff 63.

### Theme audit of all 36 icons (D21)

`agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-THEME-FIT/audit_36_icons.md`: three offenders found (the wrench, the hero house, the debuff frame), the planner's glass-mug first pass overturned (an opaque tankard; "Add staves" is a light improvement), and the ranger's registry fallback `Lucide Crosshair` noted as today's UI chrome and left as is.

### Disclosures

- **Defects and refinements found after drawing:** the first tent broke the 16x16 live area (a draft then not proposed); the first spiked-ball debuff frame was lopsided by 30 mirror pixels, so it was symmetrised at the source after drawing began (the outline the owner approved was the lopsided one; the sheet now shows the symmetric one); the tool's rivet colour was changed to clear a lint warning.
- **Thresholds written before drawing and restated after measuring, disclosed:** the hammer head (at least 20 steel pixels, was 25), the thatch (at least 80, was 90) and the plaster (at least 30, was 50), each measured on the outline the owner approved; two measurements had bugs (the ruins stub, the spike count: a diagonal spike is two loose pixels) and were fixed with tests. Sheet-rule thresholds are untouched. **Owner decision (2026-10-08), verbatim: "Accept the changes".** The style guide now has a process rule (step 4b): spec numbers guessed before the silhouette are re-agreed at the owner's silhouette question, never restated after drawing.
- The tool covers the repair kit; **the spirit lantern, the family's other item, cannot also be drawn** (one family icon).
- Drawing went through `visual_assets.drawing.api` in-process, as before.

### Adopted by the owner (2026-10-08T14:23:46Z to 14:24:07Z)

The owner ran all 14 commands in their own terminal: **seven new adoptions, each `r0002` with parent `r0001`**, approver nhan/owner, for `icon.building.hero_house`, `icon.building.inn`, `icon.class.rogue`, `icon.item.tool`, `icon.rarity.common`, `icon.status.frame_buff` and `icon.status.frame_debuff`; `store verify` ok. The two declined drafts (ruins, enemy camp) are not adopted. The 77 adoption records and 154 intake files are committed byte for byte (`TCK-20261008-VISUAL-ASSETS-RECORD-ICON-OWNER-FIXES-ADOPTION`); the catalog still holds 70 sources, now 77 revisions. The recorded decisions and the findings printed in the review folder README come from one file, `visual_assets/icons/owner_fixes_decisions.yaml`.

### Review it, and the owner's commands

**The review folder (the primary review surface):** `python -m visual_assets.review review-sheets --set icons-owner-fixes-v1` writes `~/Work/asset-review/icons-owner-fixes-v1/` with six large labelled PNG canvases and a `README.txt` that repeats the commands below. The live preview page stays for detail, with each draft beside its adopted drawing (the arch and the tent marked not proposed), the recorded result and the compliance tables:

```
# the Vite dev server serves the worktree (http://[::1]:5173/rehearsal-icons.html)
cd /home/vboxuser/Work/rpg-aseprite-mcp/frontend && npx vite
```

`adopt` is **human-only and needs your own terminal** (it refuses without a TTY and asks you to type the id). Run these commands in order from `/home/vboxuser/Work/rpg-aseprite-mcp`, which holds the intakes: a `review` and an `adopt` per slot (14 commands). Each slot needs `review` first (it renders the source with Aseprite and writes the review image `adopt` checks). Fill the four placeholders yourself (the licence decision must be `CLEARED`; nothing is pre-answered here). The source asset id is the EXISTING one and `--parent r0001` is the latest unrevoked revision, so the store records `r0002`:

```
cd /home/vboxuser/Work/rpg-aseprite-mcp
PY=/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python

# icon.status.frame_buff
$PY -m visual_assets.store review in-a927d82fcd493c0a
$PY -m visual_assets.store adopt in-a927d82fcd493c0a --visual-key icon.status.frame_buff --source-asset-id icon_status_frame_buff --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.status.frame_debuff
$PY -m visual_assets.store review in-6ee2b5282280c703
$PY -m visual_assets.store adopt in-6ee2b5282280c703 --visual-key icon.status.frame_debuff --source-asset-id icon_status_frame_debuff --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.class.rogue
$PY -m visual_assets.store review in-f332aa813db19054
$PY -m visual_assets.store adopt in-f332aa813db19054 --visual-key icon.class.rogue --source-asset-id icon_class_rogue --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.item.tool
$PY -m visual_assets.store review in-7d3825eda1fdb00e
$PY -m visual_assets.store adopt in-7d3825eda1fdb00e --visual-key icon.item.tool --source-asset-id icon_item_tool --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.rarity.common
$PY -m visual_assets.store review in-db5985f18b3164cf
$PY -m visual_assets.store adopt in-db5985f18b3164cf --visual-key icon.rarity.common --source-asset-id icon_rarity_common --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.building.hero_house
$PY -m visual_assets.store review in-cce3e6b4fb609dc5
$PY -m visual_assets.store adopt in-cce3e6b4fb609dc5 --visual-key icon.building.hero_house --source-asset-id icon_building_hero_house --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"

# icon.building.inn
$PY -m visual_assets.store review in-ca88fbc521414581
$PY -m visual_assets.store adopt in-ca88fbc521414581 --visual-key icon.building.inn --source-asset-id icon_building_inn --parent r0001 \
  --approver "<your name>" --approver-role "<your role>" --licence "<your licence decision>" --licence-evidence "<your own evidence reference>"
```

You can adopt some slots and leave others at `r0001`; each is its own decision. If you adopt none, nothing changes.

## Things the owner should judge with their own eyes (honest findings)

1. **Rarity next to tier at 8x8.** Rarity and the tier ladder are both small abstract badges. They differ in silhouette (round bead, kite, sparkle against octagons and diamonds) and in size, and the rule passes (the bead is 9 px from the nearest tier silhouette). The look-alike report puts the **common bead and the dark tier badges D and E at 25 XOR px** once fitted to one canvas, and the blind check read the bead as "dark grey square" before the redraw and as a circle after; whether a player tells the bead from a dark tier badge at 1x is an eye judgement. The name stays as text beside each.
2. **The location glyphs are small, and the ruins are the hardest glyph in the set.** At 16x16 on the plate the shrine is the narrowest glyph (4 px margins left and right). The closest pair of locations by silhouette is boss arena vs dungeon entrance (17 px, both rounded domes of similar size, never touched by a redraw). The ruins have now been redrawn four times (a boot, mountain peaks, a wagon cart, now a brick wall): the choice pass names the wall correctly every time, but free text still says "building blocks", so a reader without a label may not say "ruins" (the name stays as text). The owner looked at a broken-arch redraw and kept the adopted brick wall ("Keep current versions", 2026-10-08).
3. **Stand-ins for real objects.** The coin purse reads as a bag of gold (store); the banner as a guild flag; the open book for the class hall is the most abstract building. The mug is for the inn. If any reads wrongly, the glyph table in `icon_style_guide.md` is where to change it.
4. **Items are six families, not categories.** A weapon is always the sword, whatever the weapon. The rarity badge sits beside the family icon (the client composites them; nothing is wired).
5. **Blade overlap across families: resolved.** The rogue (hooded cowl, if the owner adopts it) no longer carries a blade, so the sword is the only new blade; the warrior's shield-and-sword emblem and the enemy camp's crossed swords are adopted and stay (the owner kept the crossed swords: "Keep current versions", 2026-10-08).
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
