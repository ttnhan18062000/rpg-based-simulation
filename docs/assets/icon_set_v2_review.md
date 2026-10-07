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
| locations (5) | `icon.marker.resource_grove`, `ruins`, `dungeon_entrance`, `shrine`, `boss_arena` | 16x16, live area 12x12, 2 px margin, over the adopted plate | tree; ruined masonry (two broken column stubs of different heights with jagged tops, a fallen block between, on a ground slab); arched door; obelisk (slim straight shaft, pointed light-stone tip, gold marks, 2 px plinth); skull |
| buildings (5) | `icon.building.store`, `guild`, `inn`, `hero_house`, `class_hall` | 24x24 | coin purse with a coin; banner on a pole; mug; small house; open book |
| classes (3) | `icon.class.ranger`, `mage`, `rogue` | 24x24 | bow with an arrow; pointed hat; dagger |
| items (6) | `icon.item.weapon`, `armor`, `trinket`, `tool`, `consumable`, `material` | 24x24 | sword; chest plate; pendant on a chain; pick; potion flask; ore chunk |
| rarity (3) | `icon.rarity.common`, `uncommon`, `rare` | 8x8 | round bead (slate, one highlight pixel); kite gem (green); four-point sparkle gem (violet) |

Provenance: every drawing is our own pixels (`licence_state UNREVIEWED`, as for terrain); no outside art was copied or traced and no AI generator was used.
**How they were drawn, stated plainly:** through `visual_assets.drawing.api` called in-process from a script (`new_sprite`, `apply_ops`, then `handoff.build_handoff`), not by pasting each draw operation into the MCP tools. The MCP tools are thin wrappers
over the same functions (same Aseprite adapter, Lua pin, workspace, revisions and handoff packaging); the planner accepted the transport (2026-10-08). The handoff `limitations` text says this; no field claims an MCP call. The intakes were submitted with the
worktree CLI (`python -m visual_assets.store intake`), so there are no stray intakes in the main checkout's quarantine this time. The script and the prototype tooling are committed so the pixels are reproducible:
`agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET/drawing/` (`draw_all.py` draws all 22; `loc.py`, `pan.py`, `rar.py` hold the shapes, `canvas.py` the small pixel canvas with the same lint).

## The sheet rule on this set, as measured

`python -m tests.visual_assets.icon_v2_draft_set` (recorded in the v2 preview fixture as `icondraft_v2/rule_result.json`; draft set hash `sha256:07ded31ec3dbddba4cae5ba54eca5d80da9dc739bc544156af0fc97efc3d6d9c`). Groups and the shape-only rule are the owner's answers (I1 only for the five subject groups, I1 and I2 for rarity; 3 / 6 / 8 px at 8x8 / 16x16 / 24x24):

| Group | Pairs | Smallest silhouette difference | Needed | I2 (value) |
|---|---|---|---|---|
| rarity (3, 8x8) | 3 | 12 px | 3 | L* gap 9.2 (protan), 9.8 (normal), 10.4 (deutan), 10.6 (tritan), needed 6 |
| badges (rarity and tiers, 11, 8x8) | 55 | 4 px (a pair of adopted tiers, as before) | 3 | not checked (shape only) |
| locations (6, 16x16) | 15 | 17 px | 6 | not checked |
| buildings (6, 24x24) | 15 | 65 px | 8 | not checked |
| classes (4, 24x24) | 6 | 132 px | 8 | not checked |
| items (6, 24x24) | 15 | 71 px | 8 | not checked |
| rarity badge vs the nearest tier badge | | 8 px (common), 16 px (uncommon), 8 px (rare) | 3 (planner's floor) | |
| Result | | | | **PASS** (I1 true, I2 true, I3 true) |

Also measured, not ruled: no pixel outside the palette; `lint_sprite` has no warning on any of the 22 (info notes only); colour counts within budget (8 at 16 px or less, 12 at 24 px); the five location glyphs sit inside the 12x12 live area (the shrine
is narrower: margins 4, 2, 4, 2); every 24x24 icon sits inside the 20x20 live area.

**How this was reached (stated plainly).** The rule was fixed first (the 24x24 threshold and the group definitions are committed, child 3). All 22 were prototyped on a local pixel canvas with the same lint and the same rule, rendered and looked at, **before** drawing.
Changes made from looking at previews, not from the rule (design-loop changes): the first uncommon badge, a "kite" with a short 2x2 tail, read as an up-arrow and would be confused with the buff chevron, so it became a proper kite gem; the first common bead looked like a
dark tier octagon, so it got a highlight pixel; the broken column and the obelisk were both grey verticals, so the planner asked for different silhouettes (first redraw, before drawing; 39 px apart); several `value_separation` lint warnings on colour pairs of near-equal brightness (guild banner shade, inn foam, house roof, hall spine, trinket chain, tool handle, potion liquid and cork) were fixed by changing the shade
colours. After drawing nothing was tuned, and no threshold moved. No rule FAILED, so there was nothing to report before a redraw.

## Redraw of the shrine and the ruins, before the owner gate (planner request, 2026-10-08)

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

## Things the owner should judge with their own eyes (honest findings)

1. **Rarity next to tier at 8x8.** Rarity and the tier ladder are both small abstract gems. They differ in silhouette (bead, kite, sparkle against octagons and diamonds) and in size, but the common bead and the dark tier badges E and D are both round and dark-ish at 1x on a dark panel. The rule passes (8 px apart); whether a player tells them apart quickly is an eye judgement. The name stays as text beside each.
2. **The location glyphs are small.** At 16x16 on the plate the shrine is the narrowest glyph (4 px margins left and right). The closest pair of locations by silhouette is now boss arena vs dungeon entrance (17 px, both rounded domes of similar size, unchanged by the redraw below); worth a look at 1x.
3. **Stand-ins for real objects.** The coin purse reads as a bag of gold (store); the banner as a guild flag; the open book for the class hall is the most abstract building. The mug is for the inn. If any reads wrongly, the glyph table in `icon_style_guide.md` is where to change it.
4. **Items are six families, not categories.** A weapon is always the sword, whatever the weapon. The rarity badge sits beside the family icon (the client composites them; nothing is wired).
5. **Blade overlap across families (flag only, no change).** The rogue dagger (class) and the weapon sword (item) are both a diagonal blade with a gold guard and a brown grip, and the warrior (shield and sword, adopted) and the enemy camp (crossed swords, adopted) also use swords. The families never share a panel and the owner approved "dagger", so this is for the owner's judgement.
6. **Fallbacks.** Every key shows today's fallback beside it on the page (copied from each key's registry description, with its colour); the class hall has none today (the building name as text).

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
  --licence-evidence "<your own evidence reference>" --review-evidence "preview page rehearsal-icons.html of icons-v2, draft set hash sha256:07ded31ec3dbddba4cae5ba54eca5d80da9dc739bc544156af0fc97efc3d6d9c"
```

Run it from `/home/vboxuser/Work/rpg-aseprite-mcp` (the worktree that holds the drafts). If the set is not adopted, the batch stops after child 4 (child 5 records an adoption and is skipped).

## Where the intakes are

All 22 were submitted once with the worktree CLI (draft ids in `visual_assets/drafts/icons-v2/draft_set.json`); the handoff directories are in the Aseprite workspace's `handoffs/` (gitignored, 30-day local retention applies).
