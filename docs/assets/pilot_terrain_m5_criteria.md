---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [mcp, live-map, testing]
---

# Pilot terrain role: predeclared `AM-M5` criteria

Written and committed by `TCK-20261004-VISUAL-ASSETS-M5-GAP-CLOSURE` **before** the pilot scene exists, is captured, is simulated or is reviewed, so that no
criterion can be fitted to a result. Results are recorded elsewhere (`docs/assets/surface_rehearsal_result.md`, ticket 5 rewrites it). This page covers the
role `terrain.forest` only (`docs/assets/pilot_terrain_key.md`); nothing here activates anything.

## AM-U21: the preserved-information contract for the terrain role

| Item | Contract |
|---|---|
| Role | Live Map terrain cell, tile code 6 (Forest), one 16-pixel cell at scale x1 |
| Preserved fact | the **terrain type**: `TILE_NAMES[code]`, here "Forest" |
| Carried by | the flat fill `TILE_COLORS[code]` (`#1b3a1b`) and the hover text `TILE_NAMES[code]`; the image is decoration on top, never the only carrier |
| Fallback | exactly the flat fill, plus the same hover text. No glyph, no letter, no other colour |
| Failure cases that must show the fill | the key is not in the manifest; the image is missing from the build; the image is corrupt or the wrong size; the image is still loading or arrives late for a superseded release; the manifest is invalid |
| Not allowed | the image changing hover text, the fill colour of any other cell, or anything gameplay-relevant; an image drawn for a cell whose terrain code is not 6 |

## AM5-W03: reviewer criteria for the crowded scene

The reviewer is the user (owner). The reviewer looks at native-scale captures (device pixel ratio 1, then 2) of two canvases drawn from the same layout: the **image**
scene (forest cells use the tile) and the **flat** control (forest cells use the fill). Each criterion is answered `yes`, `no` or `unsure`, with a note.

| Id | Criterion |
|---|---|
| C1 identifiable | The forest cells read as forest or woodland at 1:1, not as noise, a glitch or an unfinished tile |
| C2 distinct | Forest is told apart at a glance from its neighbours in the same scene: Swamp, Mountain, Desert, Jungle and Grassland |
| C3 seamless | No visible seam, grid or repeat line where forest cells touch each other (a repeat of at least 3 x 3 cells exists in the scene) |
| C4 markers | The entity and building markers drawn on forest cells are as readable as the same markers on the flat control's forest cells |
| C5 quiet | No forest cell draws the eye ahead of its neighbours or of the markers on it |

Rule: `W03` is `PASS` only if all five are `yes`; any `no` makes it `FAIL` with that criterion named; any `unsure` with no `no` leaves it `INCONCLUSIVE`.
Review is by one person, so a pass means "the owner accepts it for this role", not a usability study.

## AM5-W05: the colour-vision check and its pass rule

Method (automated, deterministic, no assistive-technology claim): simulate protanopia, deuteranopia and tritanopia (Machado, Oliveira and Fernandes 2009, severity
1.0, applied in linear RGB) on the colours involved, convert to CIE L\*a\*b\* (D65) and measure CIE76 colour difference `dE`. "Normal" is the identity.

- `neighbours`: the mean colour of the fills of Swamp, Mountain, Desert, Jungle and Grassland, as `TILE_COLORS` gives them.
- `dmin_tile(v)`: for each vision `v` (normal, protan, deutan, tritan), the smallest `dE` between the mean colour of the tile's 256 pixels and any `neighbours` entry.
- `dmin_fill(v)`: the same with the flat fill `#1b3a1b` in place of the tile's mean.
- `texture(v)`: the standard deviation of L\* over the tile's 256 pixels.

Pass rule, fixed now:

- **P1 (no worse)**: for all four visions, `dmin_tile(v) >= dmin_fill(v) - 2.0`.
- **P2 (adds a non-hue cue)**: for all four visions, `texture(v) >= 2.0`.
- `W05` is `PASS` if P1 holds; `FAIL` if P1 fails for any vision. The report says "better" when P1 and P2 hold, "same" when P1 holds and P2 fails, "worse" when P1 fails.
- Context to state with the result: terrain on the normal map is already told apart by hue alone (flat fills), so the baseline is not a colour-vision-safe design; a pass here means the tile is not worse than it.

## The pilot crowded scene (predeclared layout)

12 x 8 cells, native 16-pixel cells, smoothing off. Terrain code of cell `(x, y)` is `[6, 6, 8, 9, 6, 7, 6, 17, 15, 6][(x + 3 * y) % 10]`
(Forest 6, Swamp 8, Mountain 9, Desert 7, Jungle 17, Grassland 15; half of the cells are Forest). The fill colours are a copy of `TILE_COLORS` asserted equal to it by a test.
Markers, drawn the way the Live Map draws them (copied constants, asserted equal by a test), identical in both canvases:

| Where | Marker |
|---|---|
| on forest cells | hero `(1,0)`, goblin `(4,0)`, wolf `(9,0)`, store building `(6,1)`, inn building `(0,2)`, goblin_warrior `(1,3)` |
| on other terrain (control) | goblin `(2,0)` on Swamp, hero `(7,2)` on Mountain |

## AM5-W07: the supported-client matrix

Proposed to the user in a blocking question **before** any run; the approved matrix and the answer, with date and wording, are recorded in the ticket and in the result record.
Each approved client is captured locally and its result recorded per client; a client that was not run is not claimed.
