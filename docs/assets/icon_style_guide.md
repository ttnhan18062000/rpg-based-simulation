---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# Icon style guide (`icons-key-v1` and the icons after it)

Written by `TCK-20261006-VISUAL-ASSETS-ICON-STYLE-DECISION` **before any icon art exists**. The style decisions are ADR D20
(`docs/architecture/visual_asset_foundation_adr.md`), taken by the user on 2026-10-06. Everything marked **(proposal)** is
the planner's reading of the research, which the user confirmed only as a direction: the key set's art (child 5) is
reviewed against it, and an art review may change a proposal, never a user decision. Research sections are cited as
`craft §n`, `games §n`, `packs §n`, `synthesis` for the files in `docs/assets/icon_research/`.

Not covered here: the palette and the sheet-wide colour-vision rule (child 3, thresholds are the user's), the key names
(child 2), the map zoom code (child 4).

## Decided (D20)

| Item | Decision |
|---|---|
| Style | B plus tier badges (`synthesis`, "Planner recommendation") |
| Map glyph | 16x16, on a shared plate per category |
| Panel icon | 24x24 |
| Tier badge | 8x8, shape escalates |
| Status frame | buff and debuff frames differ in **shape**, with up and down chevrons |
| Palette basis | `terrain-v1` colours, 3-4 step ramps, a small accent set, checked sheet-wide |
| Outside art | reference only, recorded as title, author, source and licence; no AI generators |
| Map zoom | whole-number scales only |
| Tier and marker state | separate keys, never variant axes (D17) |

## Sizes and live area

Every icon is drawn natively at its size; nothing is scaled down from a larger drawing (`craft §1`, Maki).

| Family | Canvas | Margin rule | Live area | Notes |
|---|---|---|---|---|
| Map glyph | 16x16 | 2 px | 12x12, centred | drawn over the plate; the 2 px margin keeps the plate's rim visible all round (planner ruling, 2026-10-06) |
| Category plate | 16x16 | none: the plate is the frame | 16x16 | `touches_edge` is allowed for a plate or frame only (planner ruling, 2026-10-06; `craft` checklist) |
| Panel icon | 24x24 | 2 px | 20x20 | the Material 24 dp / 20 dp live area, `craft §2` |
| Tier badge | 8x8 | 0 px, a mark not a pictogram | 8x8 | letters, pips, arrows and stars fit at 8 px (`craft §1`) **(proposal)** |
| Status frame | 16x16 | 1 px | 14x14, effect glyph in the central 10x10 | `craft §5` "glyph space" |

Plate and glyph are **separate keys**, both on 16x16 canvases, composited by the client: the plate first, the glyph over it
(planner ruling, 2026-10-06). The plate fills the full 16x16, so `touches_edge` is allowed for plates and frames only. The
key names are in `visual_assets/catalog/definitions/visual_keys.yaml` (`icon.plate.location`, `icon.marker.enemy_camp`, ...).

## One set of conventions

- **Light** comes from the top-left, always (`craft §2`, "one light direction").
- **Outline policy:** one full dark outline on glyphs and badges, darker than the object (`craft §2`, Lospec rule). Selective outlining is not used **(proposal)**.
  **Plates are the exception:** the terrain is dark (22 of 23 tile means under L* 49), so a plate's rim is the mid-light palette colour `plate_rim` and not a dark outline; `docs/assets/icon_criteria.md` (I3) measures why.
  The glyph's dark outline separates it from its plate.
- **View angle, one per family** (`craft §2`, inference): buildings and map markers in 3/4 front view, items in a 3/4
  diagonal inventory pose, tab and class glyphs flat and front-on **(proposal)**.
- **Colours:** only palette colours; at most 8 at 16 px and ideally 6 or fewer (`craft §1`, Slynyrd; `craft §2`).
  The `lint_sprite` colour budget is the authority.
- **Silhouette first:** block the shape in one colour and check it at 1x with the grid off before shading (`craft §2`).
- **Abstract concepts** (AI, narrative, quest, events, effects) use a concrete fantasy object and always ship a label or
  tooltip (`craft §2`, NN/G): AI an eye or gear-brain, narrative a book or scroll, quest an exclamation mark or sealed
  scroll, events a bell or clock, effects a swirl or sparkle. These are candidates, not decisions.
- **Meaning is never hue alone.** Tier, grade, rarity, buff or debuff, marker state and hostile or friendly each differ by
  shape, glyph, pip count, frame or brightness, with hue as reinforcement (`craft §4`, `§6`; Game Accessibility
  Guidelines and Xbox XAG 103).

## Tier badge ladder (proposal)

One 8x8 badge; the letter stays as text beside it (D20; `craft §4`: grades "already are glyphs", so the text is primary).

| Grade | Shape channel |
|---|---|
| E, D | plain badge, no pips |
| C, B | pips (C one, B two) |
| A | a frame around the badge |
| S, SS, SSS | star badge with one, two or three stars |

Frame complexity, pip count and brightness all increase monotonically up the ladder (`craft` checklist). Animation is
not used in the key set; if added later it is reserved for the top tiers and stays subtle (`craft §4`, Slynyrd).
The research's own proposal differed in detail (E and D a plain square, C and B bevelled, A a shield; `craft §4`); the
split above follows the ticket, and child 5's art is where it is judged.

## Status frames (proposal for the frame shapes)

- **Buff:** a rounded or circular frame with an up chevron. **Debuff:** a spiked or inverted-triangle frame with a down
  chevron (`craft §5`; Darkest Dungeon uses arrow direction without colour).
- Stack count: a 3x5 pixel-font digit, bottom-right, on a dark backplate. Duration: a drain overlay from the top or a
  turns digit at top-left. These two overlays are not drawn in the key set.
- Dispel-type colouring (hue only) is not copied (`craft §5`, WoW).

## Map markers

- The plate's **shape encodes the category** (location against building); the glyph encodes the specific site
  (`craft §3`, inference).
- Marker state (undiscovered, discovered, cleared, hostile) changes **shape or adds a badge**, never only a tint
  (`craft §3`; XAG 103: greying alone must not signal state). State and tier are separate keys.
- A marker must read against the darkest and brightest terrain it can sit on; contrast is measured, not judged by eye
  (`craft §3`).

## Per-icon checklist

From `craft`'s checklist, adjusted to the sizes above.

- [ ] Drawn natively at its family size, not scaled down.
- [ ] Content inside the live area (see the table); `touches_edge` clean except for a plate or frame.
- [ ] A one-colour silhouette is recognisable at 1x with the grid off and passes a squint test.
- [ ] Colour count within the lint budget; only palette colours.
- [ ] Light top-left; no pillow shading.
- [ ] Outline follows the set policy and is darker than the object and the expected background.
- [ ] `value_separation` clean where separation matters.
- [ ] Reads on the light panel, the dark panel and the busiest terrain tile.
- [ ] Ships with a label or tooltip (abstract tab icons always).

## Per-set checklist

- [ ] Every distinction survives greyscale and a colour-vision simulation through shape, glyph, pips, frame or
  brightness (the sheet rule of child 3 measures this; `craft §6`).
- [ ] One view angle per family.
- [ ] The tier ladder is monotonic in frame, pips and brightness.
- [ ] Buff and debuff frames differ in shape and carry a chevron; digits and overlays share one font and position.
- [ ] Plates share one shape vocabulary; each marker state adds a shape or badge.
- [ ] A contact sheet at 1x and 2x on light, dark and real terrain backgrounds, and in greyscale, was reviewed by the
  owner (`craft §7`, step 5).
- [ ] Web rendering at an integer scale relative to `devicePixelRatio`, `image-rendering: pixelated`, whole-device-pixel
  positions, pixel layer separate from vector text (`craft §1`; child 4).
- [ ] The key icons were approved before the rest of the set was drawn, and this guide records any rule they changed
  (`craft §7`, step 2).

## Outside references

Outside art is **reference only**: nothing is traced, copied, recoloured or imported, and **no AI image generator** is
used at any step (D20). Copyright protects expression, not style, and redrawing a specific icon is copying (`synthesis`,
"Agreed across all three reports", point 5). When an outside piece informed a drawing, record it with the drawing's
intake notes as four fields:

| Field | Example |
|---|---|
| Title | the icon pack or page name |
| Author | the named creator |
| Source | the URL |
| Licence | the licence as printed on the page, or `UNVERIFIED` |

A licence that could not be confirmed on a primary page is recorded `UNVERIFIED`, as in `packs §1`, and the piece stays reference only like every other.
