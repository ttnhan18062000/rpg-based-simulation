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
As built (`icons-key-v1`): S, SS and SSS are a diamond with 0, 1 and 2 pip cut-outs in silver, gold and platinum, not stars, because a true 1/2/3-star badge does not fit 8x8 under the dark outline (one outlined four-point sparkle is 5x5 and three need more than 8 px); see `docs/assets/icon_key_set_review.md`.
The research's own proposal differed in detail (E and D a plain square, C and B bevelled, A a shield; `craft §4`); the
split above follows the ticket, and child 5's art is where it is judged.

## Status frames (proposal for the frame shapes)

- **Buff:** a rounded or circular frame with an up chevron. **Debuff:** a spiked or inverted-triangle frame with a down
  chevron (`craft §5`; Darkest Dungeon uses arrow direction without colour).
- Stack count: a 3x5 pixel-font digit, bottom-right, on a dark backplate. Duration: a drain overlay from the top or a
  turns digit at top-left. These two overlays are not drawn in the key set.
- As built (`icons-key-v1`): the buff frame is a rounded frame with an up chevron; the debuff frame is the inverted triangle with a **solid down arrow** (2 px shaft). A first debuff drawing with a down chevron and two dots read as a smiling face and was redrawn before the owner gate (`docs/assets/icon_key_set_review.md`).
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
  positions, pixel layer separate from vector text (`craft §1`; child 4). Built: `frontend/src/lib/pixelScale.ts` (levels `n / devicePixelRatio`, `fitScale`, device-pixel snapping),
  the Live Map zoom (`GameCanvas.tsx`) and `frontend/src/components/PixelIcon.tsx`.
  The zoom has one **overview level** at the bottom (0.5x at DPR 1; none at DPR 2, where 0.5 is already an art level) where art pixels are not whole: the user decided (2026-10-06) that it
  draws plain terrain colours instead of pixel art. The art path of the wiring batch must check `isOverviewZoom(zoom, dpr)` and draw the flat fill there; the Live Map draws only fills today.
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

## Icon set v2 decisions (2026-10-07)

Decided by the user by blocking question on 2026-10-07 (after PR #388): the next icon batch is **draw only, no wiring**. Using adopted art in the live app is gated (AM-M6 is NO-GO until the owner signs its
charter, and AM-M6 covers one forest tile only; HUD icons are a broad rollout beyond it). Families: map locations (5), buildings and classes (8), rarity badges (3), item families.
Ticket `TCK-20261007-VISUAL-ASSETS-ICON-V2-FAMILY-DECISIONS`; the keys, the sheet-rule groups and the art are later children of the same epic.

**Item families: six, one per first category.** An item has no `item_type` field; the app derives it from the first `categories` tag (`src/api/presenters/metadata_presenter.py`). Measured from the loaded catalog on
2026-10-07 (37 items): material 19, weapon 10, trinket 2, armor 2, tool 2, consumable 2, so **six** distinct values. (The ticket first said about 15; that was a raw count over tags in every position, not
the presenter's first-tag derivation, and the planner corrected it on 2026-10-07. The user chose "about 8 families" from that count, was then shown the real six, and chose six one-to-one over an eight-family
split of `material` by a second tag.) The mapping is data, `visual_assets/icons/item_families.yaml`; `tests/visual_assets/test_icon_item_families.py` maps every item of the real catalog to exactly one family and
fails on a first category that is not listed, so a new category forces a decision and never falls through.

| Family | First category | Items |
|---|---|---|
| weapon | weapon | 10 |
| armor | armor | 2 |
| trinket | trinket | 2 |
| tool | tool | 2 |
| consumable | consumable | 2 |
| material | material | 19 |

**Rarity badges: three, not four.** The catalog has four rarity values (common 13, uncommon 12, rare 11, legendary 1: `ancient_core`); the app's `RARITY_COLORS` knows only common, uncommon and rare. The user chose
**three** badges: common, uncommon, rare. The single legendary item gets no badge in this batch (a legendary badge would also have no colour fallback in the UI). Each badge is 8x8, a different base shape from the
tier octagon and diamond so the two ladders are never confused, and the name stays as text: common = a round bead, uncommon = a kite-shaped gem, rare = a four-point sparkle gem.

**Glyphs (accepted as proposed):**

| Family | Key's subject | Glyph |
|---|---|---|
| map location | resource_grove | a tree |
| map location | ruins | a broken column |
| map location | dungeon_entrance | an arched door |
| map location | shrine | an obelisk |
| map location | boss_arena | a skull |
| building (24x24) | store | a coin purse |
| building | guild | a banner |
| building | inn | a mug |
| building | hero_house | a small house |
| building | class_hall | an open book |
| class (24x24) | ranger | a bow |
| class | mage | a pointed hat |
| class | rogue | a dagger |

The five buildings follow the UI's building types (store, blacksmith, guild, inn, hero_house, class_hall; blacksmith is already drawn). The catalog's own building definitions (blacksmith, healer_hut, inn, mage_tower,
mine_entrance, shop, shrine, town_hall, watchtower) are a different set and are not what the panels key on today. Not in this batch: UI tab, advanced-class, per-item and per-effect icons (an icon must beat text,
`docs/brainstorm/render-and-art/visual-system-planning.md` section 15).

## Recognisability: specs, reference study and the process rule (2026-10-08)

**Why this section exists.** At the owner gate of `icons-v2` the weapon sword looked wrong to the owner (a short 4 px blade, a lumpy grip wider than the guard, no pommel: it read as a cleaver and nearly duplicated the rogue dagger). Root cause (planner and implementer,
2026-10-08): every gate measures that icons can be told **apart** (I1 shape, I2 value, I3 contrast, lint); none measures that an icon **reads as its object**. Four icons of 36 passed every gate and still misread: the debuff frame (a smile), the shrine (a bell), the ruins (a boot) and the sword (a cleaver).
The causes were one-word glyph specs with no proportions, drawing from memory with no reference study, a design loop that optimised the rule's numbers, no comparison across families, and agent eyeballing of tiny pixel art, which both the implementer and the planner got wrong for the sword.
Ticket `TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS`; the user chose "Fix the process now" (blocking question, 2026-10-08).

**Family conventions** (the full text per family is in `visual_assets/icons/icon_specs.yaml`, `families`): location glyphs 16x16 inside a 12x12 live area, one object upright and centred, no scene; building, class and item icons 24x24 inside 20x20, one object centred; **weapons point up on the vertical axis**
(the item sword) while the **class dagger is diagonal** (45 degrees, point top right), so the two never share a pose; rarity badges 8x8 and never an octagon or a diamond (those are the tier ladder); status frames carry meaning by the arrow's direction, not by colour.

**Per-icon specs.** Every one of the 36 icons has a spec written **before** any drawing or redraw: orientation, proportions in pixels, parts, one line "reads as" and one line "must not read as", plus the synonyms the blind check counts and the distractors it offers. `status: v2` entries are targets the drawing must meet; `status: adopted`
entries describe the adopted art as it is (nothing adopted changes). The source is `visual_assets/icons/icon_specs.yaml`; the table below is generated from it (`python -m tests.visual_assets.icon_specs --table`) and `tests/visual_assets/test_icon_specs.py` fails if the two differ.

<!-- icon-specs-table:begin (generated by python -m tests.visual_assets.icon_specs --table; do not edit by hand) -->

| Key | Size | Status | Subject | Orientation | Proportions (px) | Parts | Reads as | Must not read as |
|---|---|---|---|---|---|---|---|---|
| `icon.building.blacksmith` | 24 | adopted | an anvil with a raised hammer | upright; anvil at the bottom, hammer raised above | anvil about 16 px wide and 8 px tall with a horn on the left and a flat top, a hammer raised above, orange sparks | anvil, hammer, sparks | a blacksmith's anvil | a bird, a hammer alone, a tooth |
| `icon.building.class_hall` | 24 | v2 | an open book | upright, symmetric about the spine | two pages 9 px wide each and 10 px tall, a spine 2 px wide, text lines 1 px tall, a cover band 18 px wide and 3 px tall below; a gold bookmark | left page, right page, spine, text lines, cover, bookmark | an open book | a letter, a map, a notebook seen from the side |
| `icon.building.guild` | 24 | v2 | a banner on a pole | upright; pole on the left edge, cloth to the right | pole 2 px wide and 18 px tall with a gold finial; cloth 13 px wide and 10 px tall with a swallow-tail or notched bottom edge; a gold emblem about 4x5 px | pole, finial, cloth, notched edge, emblem | a guild banner or flag | a signpost, a bookmark, a tent |
| `icon.building.hero_house` | 24 | v2 | a small house | upright, symmetric | roof triangle 18 px wide and 8 px tall, walls 14 px wide and 9 px tall, a door 4 px wide and 6 px tall, two 3x3 windows, a chimney on the right | roof, walls, door, two windows, chimney | a cottage | a barn, a tent, a birdhouse |
| `icon.building.inn` | 24 | v2 | a mug of beer | upright; handle on the right | body 11 px wide and 12 px tall; a ring handle 5 px wide on the right; a foam cap 11 px wide and 4 px tall that overflows the rim | mug body, foam, handle, base band | a beer mug | a cup of coffee, a bucket, a jar |
| `icon.building.store` | 24 | v2 | a coin purse | upright, centred | bag body 16 px wide and 12 px tall, round-bottomed; a gathered neck 8 px wide tied with a brown cord; a coin about 7 px across on the front; two small gathered tips on top | bag body, tied neck, cord, coin, gathered top | a bag of money | a sack of flour, a pumpkin, a sock |
| `icon.class.mage` | 24 | v2 | a pointed wizard hat | upright, symmetric | cone 12 px wide at the base and 13 px tall, a brim 18 px wide and 3 px tall, a gold band 8 px wide, a star or sparkle on the cone | cone, brim, gold band, sparkles | a wizard hat | a party hat, a traffic cone, a witch hat with no brim |
| `icon.class.ranger` | 24 | v2 | a longbow with a nocked arrow | vertical bow with its belly bulging to the right (towards the target), string on the left pulled back to a V, arrow pointing right | bow at least 18 px tall; limbs curved so the belly stands at least 4 px (measured 7) from the line between the tips; a visible string (15 px); an arrow shaft 16 px long (1 px) nocked at the string and crossing the bow, a broad head and green fletching; NO stock and no horizontal bar thicker than 1 row | bow limbs, string, arrow shaft, arrowhead, fletching | a bow and arrow | a crossbow, a harp, a fishing rod |
| `icon.class.rogue` | 24 | revision | a hooded cowl | upright, symmetric | 18 px wide at the shoulders and 18 px tall; a peaked hood narrowing to a point at the top, a deep dark face opening about 8 px wide and 9 px tall with two gold eye glints, shoulders flaring below the hood to the full width, a hem band; dark cloak colours (never the mage hat's cone-and-brim) | peaked hood, face opening, eye glints, shoulders, hem band | a hooded cloak, a rogue | a wizard hat, a tent, a ghost, a bell |
| `icon.class.warrior` | 24 | adopted | a shield with a sword emblem | upright, symmetric | a heater shield about 16 px wide and 20 px tall, a sword emblem down its centre | shield, rim, sword emblem | a shield | a coat of arms with no sword, a keyhole |
| `icon.item.armor` | 24 | v2 | a breastplate | upright, symmetric | 18 px wide at the shoulders and 18 px tall; two round pauldrons, a neck notch 4 px wide, a torso tapering to 8 px at the waist, a vertical centre ridge and a gold clasp | pauldrons, neck notch, torso plate, centre ridge, clasp | plate armour for the torso | a shirt, a vest, a tank top |
| `icon.item.consumable` | 24 | v2 | a potion flask | upright, symmetric | round body 14 px wide and 12 px tall, a neck 6 px wide and 4 px tall, a tan cork 6x3 px, red liquid filling the lower two thirds, a highlight at the top left | round body, neck, cork, liquid, highlight | a healing potion | a lightbulb, a jar, a perfume bottle |
| `icon.item.material` | 24 | v2 | an ore chunk | upright, irregular | an irregular faceted chunk about 18 px wide and 17 px tall with 3 light and dark facets and 4-6 gold flecks | faceted body, light facet, dark facet, gold flecks | ore or a rock | a gem, a pillow, a cabbage |
| `icon.item.tool` | 24 | revision | a toolbox | upright, symmetric, wider than tall | 18 px wide and 17 px tall; a red body with a lighter lid band, a flat arched carry handle 8 px wide on top, a gold latch about 4x4 px in the centre and four rivets; it depicts the catalog's repair kit (the spirit lantern, the family's other item, cannot also be drawn: one family icon, stated) | body, lid band, carry handle, latch, rivets | a toolbox, a repair kit | a treasure chest, a briefcase, a lunchbox, a first-aid kit |
| `icon.item.trinket` | 24 | v2 | a pendant on a chain | upright, symmetric | a thin 1 px chain loop 12 px wide that rises to a point, closed by a small bail ring (4 px or less) at the apex; a round gold pendant 10 px wide and 8 px tall hanging at the loop's foot with a blue gem at least 5x4 px; never two ribbons, never a neck and a body | bail ring, chain loop, gold setting, gem, highlight | an amulet or necklace | a medal, a potion flask, a ring, a compass, a clock |
| `icon.item.weapon` | 24 | v2 | a sword | upright, point up, centred on the vertical axis | total 20 px tall; blade 12 px (60 percent) long and 4 px wide with a 1 px light centre line and a 2 px tip; a gold crossguard 12 px wide and 2 px thick, perpendicular; a grip 2 px wide and 2 px long (never wider than the guard or the blade), brown; a gold pommel 4x2 px | blade, centre line, crossguard, grip, pommel | a longsword | a cleaver, a knife, a dagger, a key |
| `icon.marker.boss_arena` | 16 | v2 | a skull | upright, centred | cranium 10-12 px wide and about 8 px tall, two dark 2x2 eye sockets, a 1-px nose, a jaw 6-8 px wide with 3 tooth gaps | cranium, eye sockets, nose, jaw with teeth, shade on the right | a human skull | a ghost, a cloud, a mask |
| `icon.marker.dungeon_entrance` | 16 | v2 | an arched doorway | upright, centred | arch frame 12 px wide and 12 px tall with a round top, a dark opening about 6 px wide and 7 px tall inside it, a 1-2 px stone frame | stone frame, arched dark opening, base step | a doorway into a dungeon or cave | a window, a tombstone, a mailbox, a tunnel seen from the side |
| `icon.marker.enemy_camp` | 16 | adopted | crossed swords | two diagonals crossing at the centre | two blades crossing in an X about 12 px across, gold guards, brown grips | two blades, two guards, two grips | crossed swords, battle | a pair of scissors, an X mark |
| `icon.marker.resource_grove` | 16 | v2 | a tree | upright, centred | crown 10-12 px wide and about 8 px tall; trunk 2 px wide and 3-4 px tall, centred under the crown; the crown is wider than tall | crown, shaded right side, trunk | a broadleaf tree | a bush, a speech bubble, a cloud, a lollipop |
| `icon.marker.ruins` | 16 | v2 | a ruined brick wall | upright, wider than tall, the broken top edge shaped like a U (never a one-way slope: that read as a boot, and a slab under it as a sole) | wall 10 px wide and about 9 px tall; 4 courses of bricks, two rows each, alternating light and dark with staggered mortar joints; a broken top edge with two towers of different heights (4 and 3 px from the top) either side of a low jagged gap; at least one fallen brick (a loose group of 2 or more px) lying in the gap; no ground slab and no matched pair of bricks under the wall (they read as wheels and a cart) | brick courses, mortar joints, two towers, low jagged gap, fallen brick | a broken brick wall | mountain peaks, a wagon, a boot, a chess piece, a stair, a tooth, a crown |
| `icon.marker.shrine` | 16 | v2 | an obelisk | upright, centred, taller than wide | 8 px wide, 11 px tall; shaft 4 px wide with straight sides; pointed pyramid tip (1 px, then 2 px); plinth 6 px wide and 2 px tall; no rounded top, no flare | pyramid tip, shaft with a light left edge, gold marks, plinth | a standing stone, obelisk or monument | a bell, a bottle, a tombstone, a candle |
| `icon.plate.location` | 16 | adopted | a location plate | square | 16x16, 1 px rim #9ea4b6, slate fill, a light top-left edge, a shadow bottom-right, cut corners | rim, fill, light edge, shadow edge | a plaque or button the glyph sits on | a window, a button with a label |
| `icon.rarity.common` | 8 | revision | a silver bead | centred | 7x7 px, round (fills at most 80 percent of its bounding box), a light silver fill (#c8d8e8) with a bright highlight (#eafeff) at the top left and a shaded lower right (#91a2ab), dark outline; never the tier's 8 px, and lighter than the dark tier badges E and D so it cannot be mistaken for them by value | round body, highlight, shade | a silver bead or pearl | a square, a tier badge, a coin |
| `icon.rarity.rare` | 8 | v2 | a four-point sparkle gem | centred | 8x8 px, four points of equal length on both axes, a 4x4 body, violet fill | four points, body | a sparkle or glint | a plus sign, a compass, a cross |
| `icon.rarity.uncommon` | 8 | v2 | a kite-shaped gem | point up, centred | 6 px wide at the widest and 6-7 px tall, a wide top and a pointed bottom, green fill | gem body, point | a cut gem | an up arrow, a shield, a leaf |
| `icon.status.frame_buff` | 16 | revision | a round frame with a solid up arrow | upright, symmetric | the adopted round green frame unchanged (16x16, green rim, dark green interior); inside it a SOLID bone-coloured up arrow: a head 2, 4 then 6 px wide and a shaft 2 px wide and 5 px tall, centred, the mirror of the debuff's down arrow; no chevron outline | round frame, green rim, solid arrow head, solid arrow shaft | an increase, a buff | a gem, a shield, a cross, a sword |
| `icon.status.frame_debuff` | 16 | adopted | an inverted-triangle frame with a down arrow | upright, symmetric | an inverted triangle frame with an ember rim, a solid down arrow inside | triangle frame, ember rim, down arrow | a decrease, a debuff | a smile, a warning sign |
| `icon.tier.a` | 8 | adopted | an octagon badge with a frame cut out | centred | 8x8 octagon with a 2x1 cut-out | octagon, frame | a rank badge | a stop sign |
| `icon.tier.b` | 8 | adopted | an octagon badge with two pips cut out | centred | 8x8 octagon with two 1x1 cut-outs | octagon, two pips | a rank badge | a stop sign |
| `icon.tier.c` | 8 | adopted | an octagon badge with one pip cut out | centred | 8x8 octagon with one 1x1 cut-out | octagon, one pip | a rank badge | a stop sign |
| `icon.tier.d` | 8 | adopted | a plain octagon badge | centred | 8x8 octagon, slightly lighter fill than E | octagon | a rank badge | a stop sign |
| `icon.tier.e` | 8 | adopted | a dark green plain octagon badge | centred | 8x8 octagon, dark fill, outline | octagon | a rank badge | a stop sign |
| `icon.tier.s` | 8 | adopted | a silver diamond badge | centred | 8x8 diamond, silver fill | diamond | a rank badge | a playing card suit |
| `icon.tier.ss` | 8 | adopted | a gold diamond badge with one pip | centred | 8x8 diamond, gold fill, one cut-out | diamond, one pip | a rank badge | a playing card suit |
| `icon.tier.sss` | 8 | adopted | a platinum diamond badge with two pips | centred | 8x8 diamond, platinum fill, two cut-outs | diamond, two pips | a rank badge | a playing card suit |

<!-- icon-specs-table:end -->

**Reference study (D20: reference only, nothing traced or copied).** Looked at on 2026-10-08, to fix conventions before the redraw:

| Source | Author | Licence | What was observed (one line per object) |
|---|---|---|---|
| Kenney Tiny Dungeon preview, https://kenney.nl/assets/tiny-dungeon (16x16) | Kenney | CC0 | swords are upright and point up, the blade is about two thirds of the height and 2 to 3 px wide with a light edge, the crossguard is 1 px wider than the blade on each side, the grip is short and never wider than the guard; the dagger is the same shape but shorter and narrower; axe and hammer are upright with the head at the top; potions are a round flask with a short neck and a tan cork, liquid colour fills the lower body |
| Kenney 1-Bit Pack preview, https://kenney.nl/assets/1-bit-pack (16x16) | Kenney | CC0 | swords are drawn diagonally bottom-left to top-right with a long blade (about three quarters of the diagonal), a perpendicular crossguard, a short grip and a pommel; daggers are short with a wide guard; bows are an arc with a straight string; axes have the head at the top-right end |

Both were looked at as preview images only (no download of the packs, nothing committed, no pixel reused). game-icons.net and Shikashi's pack (the other two named in `research_packs_palettes.md`) were not examined in this pass: their SVG and 32x32 art did not add a convention the two packs above lack for these glyphs.

**Process rule for every future icon batch** (a step may not be skipped; a failure of a step is reported, never tuned away):

1. **Spec** per icon in `icon_specs.yaml` (orientation, pixel proportions, parts, reads as, must not read as, synonyms, distractors), with the family conventions.
2. **Reference study**: 2 or 3 existing icons of the object at 16 to 32 px, recorded (title, author, source, licence, one line of conventions); nothing copied.
3. **One-colour silhouette sheet**: render every new icon's silhouette in one colour, side by side with the existing set, and have the owner approve the shapes before any colour is drawn.
4. **Draw** to the spec.
5. **Spec compliance table** for every new or redrawn icon (`tests/visual_assets/icon_compliance.py`): each proportion the spec states (blade length as a share of the height, blade width, guard width against grip width, pommel present, courses of bricks, bow curvature, roundness ...) **measured from the pixels** next to the spec value. A row that fails is reported, never tuned away.
6. **Checks**: the sheet rule (I1 to I3 and lint), the **blind recognition check** (`tests/visual_assets/icon_recognition.py`: a fresh agent with no project context names every unlabelled icon, free text first, then a candidate list with distractors; answers stored as evidence) and the **whole-sheet look-alike report** (`tests/visual_assets/icon_lookalikes.py`, report only).
7. **Owner gate**: the owner reviews and runs `adopt-set` in their own terminal.

**Why step 5 exists (found on the first redraw, 2026-10-08).** The weapon sword was named "steel sword" by the blind check, in free text and from the list, and it still looked wrong to the owner: naming catches **misreads**, not **bad drawing**. A sword with a short 4 px blade, a grip wider than the guard and no pommel is
still a sword to a reader. Only measuring the drawing against its own spec catches that, which is why every proportion in a spec must be one a program can measure.

A flagged icon (free text names none of its synonyms) or a cross-family twin is reported; a person decides whether to redraw. The recognition check is evidence, not a CI gate, because a model's answer is not deterministic.

## Owner fixes before PR #418 merged: reference study and the changed specs (2026-10-08)

The owner held the merge and chose to fix every judgement item of the planner's readiness comment: the ruins, the common bead, the adopted buff frame, the blade motifs (the rogue dagger and the enemy camp's crossed swords) and the tool that could not depict the spirit lantern. All six slots are **adopted sources**
(the owner adopted `icons-v2` and, earlier, `icons-key-v1`), so each change is a new revision (`r0002`, parent `r0001`) made by the store's own `adopt --parent`, never an edit of an adopted file; the new drawings live in a new draft set `icons-owner-fixes-v1`. The process rule above applies unchanged (specs, reference study, one-colour silhouette sheet approved by the owner, drawing, compliance table, checks, owner gate).

**Reference study (D20: reference only, nothing traced or copied).** Looked at on 2026-10-08 as preview images only (the ruins arch and the enemy-camp tent were drawn but the owner kept the adopted versions, so those two rows are record only) (no pack downloaded, nothing committed, no pixel reused):

| Glyph | Source | Author | Licence | What was observed |
|---|---|---|---|---|
| broken arch (ruins) | Kenney Tiny Town preview, https://kenney.nl/assets/tiny-town (16x16) | Kenney | CC0 | stone arches are drawn as a thick dark-outlined stone ring (two pixels of stone, light faces on the inner edge) around a dark opening; pillars are straight 3 px columns with a light edge |
| silver bead | Kenney 1-Bit Pack preview, https://kenney.nl/assets/1-bit-pack | Kenney | CC0 | round objects (coins, orbs, shield bosses) are a filled disc with one bright highlight pixel at the top left and a darker lower-right rim; discs stay lighter than their dark outline |
| solid up arrow (buff) | Kenney 1-Bit Pack preview (arrow icons) | Kenney | CC0 | arrows are solid: a triangular head about twice as wide as the shaft on a thick shaft, no outline-only chevrons; green is used for up and increase |
| hood or mask (rogue) | Kenney 1-Bit Pack preview (helmet and head icons) | Kenney | CC0 | hoods and helmets are a dome narrowing upward with a dark face opening or eye slits; the opening is the strongest feature |
| tent with spears (enemy camp) | Kenney 1-Bit Pack preview (tents and campsite tiles) | Kenney | CC0 | tents are a triangle wider than tall with a dark doorway triangle at the base centre; poles and flags rise above the apex |
| toolbox (tool) | Kenney 1-Bit Pack preview (briefcase and box icons), Kenney Tiny Town preview (buckets and crates) | Kenney | CC0 | boxes are wider than tall with a flat lid line, a small arched handle on top and a clasp in the centre of the lid |

Only Kenney's previews were examined (game-icons.net and Shikashi were not), so the conventions come from one author's low-resolution style.

