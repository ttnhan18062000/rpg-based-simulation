---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, testing, hud]
---

# Icon palette and sheet rule (`I1`-`I3`)

Written and committed by `TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE` **before any icon art exists**, so no threshold can be tuned to a drawing. The decision is ADR D20
(`docs/architecture/visual_asset_foundation_adr.md`): palette = `terrain-v1` colours + 3-4 step ramps + a small accent set, checked sheet-wide. `lint_sprite`'s `value_separation` only compares
neighbouring pixels inside one sprite; nothing else checks that two tiers, or a buff and a debuff frame, differ by more than hue. This page fixes the rule that does. It is the icon analogue of
`AM5-S` (`docs/assets/pilot_terrain_m5_criteria.md`) and reuses its Machado simulation, Lab and CIE76 code (`tests/visual_assets/pilot_colour_vision.py`).

Code: `tests/visual_assets/icon_sheet_rule.py` (the rule), `icon_palette.py` (the palette's derivation), `icon_sheet_synthetic.py` (mock-ups and the baseline measurement),
`test_icon_sheet_rule.py` (tests on planted input). Palette file: `visual_assets/palettes/icons-v1.json`. None of this decides a verdict on art; the verdict on `icons-key-v1` is recorded by
the draft-set ticket when the art exists.

## The user's answers (2026-10-06, one blocking question, neutral options in ascending order, after the baselines below)

| Question | Answer |
|---|---|
| I1: minimum silhouette difference (8x8 badge / 16x16 frame) | `3 / 6` |
| I1 for the 8 tier badges | "E and D may share a silhouette" (I1 covers the other 26 pairs; only I2 separates E from D) |
| I2: minimum L* difference | `T = 6` |
| I3: minimum L* difference, plate rim against terrain tile | `T = 12` |

## The rule

A **must-differ group** is a named list of icon names split into *classes*; icons of one class may share a silhouette on purpose. The groups of `icons-key-v1` are the 8 tiers
(classes `[E, D] [C] [B] [A] [S] [SS] [SSS]`), the buff and debuff status frames (two classes), and the plates against the terrain tiles (I3).

- **I1 shape.** Every pair from different classes of a group differs in its 1-bit alpha silhouette (alpha >= 128) by **at least 3 pixels at 8x8 and 6 pixels at 16x16**. A recolour has 0 differing pixels
  and fails. No threshold existed for 24x24 when this was written (no group had panel icons); one was added on 2026-10-07 (see "Icon set v2" below: 8 px), and a size without a threshold still raises an error instead of passing.
- **I2 value.** Every pair of a group (same class or not) has **interior mean colours** (the sRGB mean of the opaque pixels that are not on the silhouette's outer boundary) whose **L\* differ by at least 6**
  under normal vision (this is the greyscale reading), protanopia, deuteranopia and tritanopia. The interior is measured because an 8x8 badge is more than half outline.
- **I3 plate contrast.** Every distinct colour on a plate's outer rim differs in **L\* from the mean colour of every `terrain-v1` tile by at least 12** under all four visions (23 tiles: 22 drafts plus the adopted forest tile).
- **Verdict:** `PASS` iff I1, I2 and I3 all hold. Reported, never ruled: pixels outside the palette, and each tile's darkest and lightest pixel L*.

Vision simulation: Machado, Oliveira and Fernandes 2009, severity 1.0, in linear RGB; L* is CIE L*a*b* (D65). No assistive-technology or colour-blind-reviewer claim: this is arithmetic on colours.

## Measured baselines (synthetic mock-ups and the real tiles; `agent-working/stored_artifacts/TCK-20261006-VISUAL-ASSETS-ICON-PALETTE-AND-SHEET-RULE/baseline_measurements.txt`)

| Measure | Result |
|---|---|
| I1: a 1-pixel change / a recolour only / one 2x2 pip / the mock buff vs debuff frame | 1 px / 0 px / 4 px / 80 px |
| I1: the mock tier ladder (E-D plain, C-B 1-2 pips, A frame, S/SS/SSS a diamond with 0-2 pips), pairs across classes | smallest 4 px (C vs E, S vs SS); E vs D = 0 px by design |
| I2: today's grade chips (`GRADE_COLORS`), smallest L* gap over 28 pairs | 0.26 / 0.25 / 1.28 / 1.60 (normal / protan / deutan / tritan); 6 / 4 / 7 / 7 pairs are under 8 |
| I2: the best 8-step value ladder the palette allows (every pair, all four visions) | smallest gap 8.74 (a heuristic lower bound) |
| I2: mock buff vs debuff frames | L* gap 18.2 / 28.5 / 12.2 / 17.9 |
| I3: `terrain-v1` tile mean L* | 10.9 (floor) to 85.6 (snow); all but snow are under 49 |
| I3: a near-black outline `#0e1018` as the rim | 6.0 (floor, the closest) |
| I3: the proposed rim `#9ea4b6` | 18.0 (deutan) to 18.5 (protan); the closest tile is snow, then farmland |
| I3: the largest gap any single rim colour can have | about 18.6 (tile means span 11 to 86 and one colour must stay clear of both ends) |

What the user's thresholds accept and reject: 3/6 rejects 1-2 px changes at 8x8 and recolours, accepts one pip; `T = 6` rejects today's colour-only grade chips and accepts the best palette ladder with 2.7 L\*
to spare; `T = 12` accepts the proposed rim with 6 L\* to spare and rejects every dark outline against the floor tile.

## Consequence for the style guide: the plate rim is not a dark outline

`docs/assets/icon_style_guide.md` asks for one dark outline "darker than both the object and the expected background". The terrain is dark (22 of 23 tile means are under L\* 49), so a dark plate
rim cannot clear a dark tile: `#0e1018` reaches only 6.0 against the floor tile and fails I3 at any answer. A plate's rim is therefore the mid-light palette colour `plate_rim` (`#9ea4b6`, L\* about 67)
and the dark outline belongs to the glyph and the badges drawn on the plate. The guide's outline row is amended accordingly in the same commit.

## The palette `icons-v1`

`visual_assets/palettes/icons-v1.json` is exactly the output of `tests/visual_assets/icon_palette.py::build_palette` (a test asserts it), 52 colours, a list of `#rrggbb` that `remap_palette` takes directly,
with an `entries` list recording where each colour comes from:

1. **Terrain base, 23 colours:** the Live Map fill of each `terrain-v1` key. Each is checked against its adopted tile: the 256-pixel mean is within 2.5 units per channel of the fill. The 22 re-tinted drafts are within 1.0;
   `terrain.forest` is the pilot tile adopted before the re-tint and is 2.42 off, which is why the tolerance is not 1.0.
2. **Ramps, 21 further colours:** seven terrain fills (wall, farmland, shallow water, lava, dungeon entrance, road, snow) each turned into a 4-step ramp by the drawing tool's own `make_ramp`
   (`base_index=1`: one shadow step, the seed, two lighter steps). The seed is exactly the terrain fill.
3. **Accents, 8 colours:** the outline `#0e1018`, the plate rim `#9ea4b6` and six signal colours (gold, ember, leaf, sky, violet, bone). They are the only colours not traced to a terrain fill. The set is a proposal
   for the owner's review of the key set's art, not a decided set; a colour added later changes the file and its test.

Lint budget per sprite is unchanged (8 colours up to 16 px, 12 up to 32 px): the palette is the pool, each icon takes at most its budget from it.

## Icon set v2 (2026-10-07)

Written and committed by `TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS` **before any v2 art exists**. The key-set answers above are unchanged (I1 3 px at 8x8 and 6 px at 16x16, I2 L\* 6, I3 L\* 12). Two things are new.

**The user's answers (2026-10-07, one blocking question, neutral options in ascending order, after the baselines below):**

| Question | Answer |
|---|---|
| I1 at 24x24 (buildings, classes, item families): minimum silhouette difference | `N = 8` |
| I2 for the groups of different subjects (locations, buildings, classes, item families) | "I1 only" |

So **24x24 now has an I1 threshold of 8 px** (a size with no threshold still raises an error instead of passing: the code has `shape_min = {8: 3, 16: 6, 24: 8}`), and the four subject groups are checked by I1 alone.

**The v2 must-differ groups** (`tests/visual_assets/icon_v2_groups.py`; a group is a list of classes, every pair from different classes must differ):

| Group | Members | Size | Rules |
|---|---|---|---|
| `rarity` | the 3 rarity badges | 8x8 | I1 and I2 (L\* 6; three badges can differ by up to 35) |
| `badges` | every rarity badge against every tier badge (E and D still share a class): 11 badges | 8x8 | **I1 only** (two ladders, each next to its own text; the best 11-step palette ladder is only 4.5 L\* apart, so brightness cannot separate eleven) |
| `locations` | enemy camp + the 5 v2 glyphs: 6 | 16x16 | I1 only |
| `buildings` | blacksmith + the 5 v2 buildings: 6 | 24x24 | I1 only |
| `classes` | warrior + ranger, mage, rogue: 4 | 24x24 | I1 only |
| `items` | the 6 item families | 24x24 | I1 only |

`evaluate_sheet(..., shape_only=...)` names the groups checked by I1 alone and reports `value_checked: false` for them.

**Measured baselines** (synthetic sprites and the icons already drawn; `agent-working/stored_artifacts/TCK-20261007-VISUAL-ASSETS-ICON-V2-SHEET-RULE-GROUPS/baseline_measurements.txt`):

| Measure | Result |
|---|---|
| 24x24 disc, 1 edge pixel removed / 3 edge pixels / one 2x2 pip / one 4x4 hole / the whole disc shifted 1 px | 1 / 3 / 4 / 16 / 36 px |
| 24x24: the most similar pair of simple distinct silhouettes (diamond vs cross) | 64 px |
| the real drawn blacksmith vs warrior (24x24) | 135 px |
| I2 on the real blacksmith vs warrior | 5.2 L\* in every vision (under 6: two ordinary drawings of different subjects can miss it by accident, which is why the subject groups are I1 only) |
| proposed rarity shapes (round bead, kite gem, sparkle gem) as 8x8 mock-ups against the tier silhouettes | smallest difference 8 px (bead or sparkle vs the S diamond), kite 16; rarity against rarity 12 to 16 |
| best N-step value ladder the palette supports (smallest L\* gap) | N = 3: 35.4, 4: 22.2, 6: 12.3, 8: 8.7, 10: 5.0, 11: 4.5 |

What the threshold accepts and rejects: 8 px accepts a 3x3 notch or two 2x2 pips (about 1.4% of the canvas) and rejects 1 to 7 px changes and recolours.
