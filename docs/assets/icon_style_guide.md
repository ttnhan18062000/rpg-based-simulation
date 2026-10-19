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

## Theme (D21, decided by the owner 2026-10-08)

**Medieval fantasy plus magic.** Every icon depicts an object a medieval craftsman, traveller, soldier or mage would own, a creature or place of that world, or an abstract UI glyph that names no object (tier badges, rarity gems, status frames, the plate). Magic items are allowed. **Nothing modern.**

| Allowed | Forbidden (modern lookalikes to avoid) |
|---|---|
| anvil, smith's hammer and tongs, sword, shield, bow, dagger, hooded cloak, wizard hat, tankard or horn, leather purse, banner, timber-framed cottage with a thatched or tiled roof, potion in a corked flask, ore, tome, amulet | suitcase, briefcase, toolbox with a plastic look, wrench or spanner, zips, plastic, screw-cap glass bottles, road-sign symbols (a red warning triangle), printed pages, light bulbs, electric or mechanical devices, suburban houses with large glass windows |

Each icon's spec (`visual_assets/icons/icon_specs.yaml`) records `theme` (what setting it belongs to) and `modern_lookalikes_to_avoid`; the loader refuses a spec without both. The blind recognition check asks an **era question** (third pass) and an answer naming a modern or futuristic setting flags the icon. The process rule checks theme fit at the spec step and at the check step. The theme constrains what is drawn, not how: style, palette and the sheet rule are unchanged.

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
- **Colours:** only palette colours; at most 8 at 16 px and ideally 6 or fewer (`craft §1`, Slynyrd; `craft §2`). The palette is data: `visual_assets/palettes/icons-v1.json` (and `terrain-v1.json`) with `.gpl` exports Aseprite can load; `lint_sprite` with `palette_id: "icons-v1"` reports off-palette pixels as advice (never a ruling, `docs/assets/icon_criteria.md`).
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
entries describe the adopted art as it is (nothing adopted changes). The source is `visual_assets/icons/icon_specs.yaml`; the table below is generated from it (`python -m visual_assets.review.icon_specs --table`) and `tests/visual_assets/test_icon_specs.py` fails if the two differ.

<!-- icon-specs-table:begin (generated by python -m visual_assets.review.icon_specs --table; do not edit by hand) -->

| Key | Size | Status | Subject | Theme | Modern lookalikes to avoid | Orientation | Proportions (px) | Parts | Reads as | Must not read as |
|---|---|---|---|---|---|---|---|---|---|---|
| `icon.building.blacksmith` | 24 | adopted | an anvil with a raised hammer | medieval: a blacksmith's anvil with a raised hammer | a modern workshop machine; a bird; a toaster | upright; anvil at the bottom, hammer raised above | anvil about 16 px wide and 8 px tall with a horn on the left and a flat top, a hammer raised above, orange sparks | anvil, hammer, sparks | a blacksmith's anvil | a bird, a hammer alone, a tooth |
| `icon.building.class_hall` | 24 | v2 | an open book | medieval: a hand-written tome or spellbook | a printed paperback; a tablet or e-reader; a notebook | upright, symmetric about the spine | two pages 9 px wide each and 10 px tall, a spine 2 px wide, text lines 1 px tall, a cover band 18 px wide and 3 px tall below; a gold bookmark | left page, right page, spine, text lines, cover, bookmark | an open book | a letter, a map, a notebook seen from the side |
| `icon.building.guild` | 24 | v2 | a banner on a pole | medieval: a heraldic banner on a pole | a modern office flag or pennant; a signpost; a bookmark | upright; pole on the left edge, cloth to the right | pole 2 px wide and 18 px tall with a gold finial; cloth 13 px wide and 10 px tall with a swallow-tail or notched bottom edge; a gold emblem about 4x5 px | pole, finial, cloth, notched edge, emblem | a guild banner or flag | a signpost, a bookmark, a tent |
| `icon.building.healer_hut` | 24 | v2 | a mortar and pestle with a herb sprig | medieval: a stone mortar and pestle of an herbalist, with a green herb sprig | a modern pill bottle or medicine cross; a coffee cup; a first-aid kit | upright, centred, the pestle leaning out to the upper right | a bowl 14 px wide and 9 px tall (flat-topped rim, rounded base on a 2 px foot) in stone grey; a pestle 3 px wide leaning out 9 px tall to the upper right; a green sprig of 2 leaf pairs rising from the bowl, at least 12 px of green; fits the 20x20 live area | stone bowl, rim, pestle, herb sprig, foot | an herbalist's mortar and pestle | a cup, a cauldron, a pot of soup |
| `icon.building.hero_house` | 24 | revision | a timber-framed cottage | medieval: a timber-framed cottage with a thatched or tiled roof and small windows | a modern suburban house with white walls and large blue glass windows; a cabin with a satellite dish; an apartment block | upright, symmetric, a steep roof over low walls | 20 px wide and 20 px tall including the outline; a steep thatched roof (golden thatch with a darker shaded half and specks) with deep eaves, at least 80 px of thatch; cream plaster walls in a dark timber frame (posts, beams and braces, at least 40 px of timber brown); two small windows 2x2 px with dark leaded panes and green shutters; an arched wooden door with planks and a latch; a stone chimney; NO blue glass, no white walls | thatched roof, timber frame, plaster walls, shuttered windows, arched door, stone chimney | a medieval cottage | a suburban house, a barn, a tent, a birdhouse |
| `icon.building.inn` | 24 | revision | a tankard with wooden staves and iron hoops | medieval: a tavern tankard (wood, horn or pewter) of ale, with staves and iron hoops | a modern glass beer mug or pint glass; a coffee mug; a paper cup | upright; handle on the right (the adopted silhouette, unchanged) | the adopted tankard's outline exactly (no outline pixel changes); the body gains two vertical stave seams (dark brown, at least 7 px tall each) and two iron hoops (steel grey bands, at least 9 px wide) near the top and the bottom; the foam cap and the ring handle are unchanged | wooden body, stave seams, iron hoops, foam, ring handle | a wooden tankard of ale | a glass beer mug, a coffee mug, a bucket, a barrel |
| `icon.building.mine_entrance` | 24 | v2 | a pickaxe | medieval: an iron-headed miner's pickaxe on a wooden haft | a modern jackhammer; a garden fork; a hockey stick | upright on a diagonal, head at the upper left, haft to the lower right | a haft 3 px wide and 17 px long on a diagonal; a curved double-pointed iron head 16 px across with two pointed tips curving down (steel grey with a light top edge); nothing else; fits the 20x20 live area | wooden haft, iron head, pointed tips, binding | a miner's pickaxe | a hammer, an axe, an anchor |
| `icon.building.store` | 24 | v2 | a coin purse | medieval: a leather purse of coins at a market stall | a modern wallet or credit card; a shopping bag; a cash register | upright, centred | bag body 16 px wide and 12 px tall, round-bottomed; a gathered neck 8 px wide tied with a brown cord; a coin about 7 px across on the front; two small gathered tips on top | bag body, tied neck, cord, coin, gathered top | a bag of money | a sack of flour, a pumpkin, a sock |
| `icon.building.town_hall` | 24 | v2 | a rolled charter scroll with a wax seal | medieval: a town charter, a parchment scroll tied with a ribbon and a red wax seal | a modern rolled poster tube; a diploma in a frame; a paper towel roll | upright, centred, the scroll slightly slanted | a parchment scroll 16 px wide and 12 px tall with both ends curled into 3 px rolls; a red wax seal 4 px across on a hanging ribbon at the lower right; two ink lines of text as 1 px dark dashes; fits the 20x20 live area | parchment, curled rolls, ink lines, wax seal, ribbon | a rolled parchment charter with a seal | an open book, a letter, a bandage |
| `icon.building.watchtower` | 24 | v2 | a crenellated stone tower with a pennant | medieval: a stone watchtower with a crenellated top, an arrow slit and a pennant | a modern lighthouse; a chimney; a rocket | upright, symmetric, centred, taller than wide | a tower 10 px wide and 17 px tall; four crenellations on top (2 px wide, 2 px gap); a 1x3 px arrow slit; a stone block pattern of lighter and darker greys; a 4 px pennant on a 3 px pole above the top; fits the 20x20 live area | stone shaft, crenellations, arrow slit, pennant, base | a medieval watchtower | a lighthouse, a chimney, a chess piece |
| `icon.class.mage` | 24 | v2 | a pointed wizard hat | medieval fantasy: a pointed wizard hat | a party hat; a graduation cap; a traffic cone | upright, symmetric | cone 12 px wide at the base and 13 px tall, a brim 18 px wide and 3 px tall, a gold band 8 px wide, a star or sparkle on the cone | cone, brim, gold band, sparkles | a wizard hat | a party hat, a traffic cone, a witch hat with no brim |
| `icon.class.ranger` | 24 | v2 | a longbow with a nocked arrow | medieval: a hunter's longbow and arrow | a compound bow with sights; a rifle or a crosshair; a crossbow | vertical bow with its belly bulging to the right (towards the target), string on the left pulled back to a V, arrow pointing right | bow at least 18 px tall; limbs curved so the belly stands at least 4 px (measured 7) from the line between the tips; a visible string (15 px); an arrow shaft 16 px long (1 px) nocked at the string and crossing the bow, a broad head and green fletching; NO stock and no horizontal bar thicker than 1 row | bow limbs, string, arrow shaft, arrowhead, fletching | a bow and arrow | a crossbow, a harp, a fishing rod |
| `icon.class.rogue` | 24 | revision | a hooded cowl | medieval fantasy: a hooded cowl of a thief or assassin | a modern hooded sweatshirt; a ski mask or balaclava; a gas mask | upright, symmetric | 18 px wide at the shoulders and 18 px tall; a peaked hood narrowing to a point at the top, a deep dark face opening about 8 px wide and 9 px tall with two gold eye glints, shoulders flaring below the hood to the full width, a hem band; dark cloak colours (never the mage hat's cone-and-brim) | peaked hood, face opening, eye glints, shoulders, hem band | a hooded cloak, a rogue | a wizard hat, a tent, a ghost, a bell |
| `icon.class.warrior` | 24 | adopted | a shield with a sword emblem | medieval: a heater shield with a sword emblem | a police badge; a riot shield; a modern coat of arms plaque | upright, symmetric | a heater shield about 16 px wide and 20 px tall, a sword emblem down its centre | shield, rim, sword emblem | a shield | a coat of arms with no sword, a keyhole |
| `icon.entity.alpha` | 16 | v2 | a standing wolf | medieval fantasy: a wild grey wolf standing in side view, head up, tail down | a dog; a fox; a cat | side view facing right, standing | a body 7 px long and 4 px tall, four legs 3 px tall, a head with a long snout and two pointed ears at the front, a thick tail down at the back; grey with a pale chest | body, legs, pointed ears, snout, tail | a standing wolf | a dog, a fox, a horse, the hooded rogue cowl |
| `icon.entity.blacksmith` | 16 | v2 | a horseshoe | medieval: an iron horseshoe, open end up, with nail holes | a magnet; a modern U-shaped clip; a letter U | open end up, centred | a thick U 10 px wide and 11 px tall with a 2 px band, six 1 px nail holes (three each side), flat ends; dark iron with a highlight on the left | arch, ends, nail holes | a horseshoe | a magnet, the anvil in the blacksmith building icon, the crossed hammer and tongs item |
| `icon.entity.guard` | 16 | v2 | a large iron gate key | medieval: a heavy iron key of a castle gate warden, round bow and two blocky teeth | a modern house key; a padlock; a wrench | upright, bow on top, teeth to the lower right | a round open bow 6 px across with a 2 px hole, a shaft 2 px wide and 6 px long, two square teeth 2 px wide on the right of the lower shaft; 8 px wide and 12 px tall; iron grey with a dark outline | bow, shaft, teeth | a large key | a padlock, a keyhole, a wrench, a door-key trinket item, a shield (the warrior class icon) |
| `icon.entity.leader` | 16 | v2 | a gold crown | medieval: a gold king's crown with three points and a band | a modern tiara; a party crown; a comb | front view, level, centred | a band 10 px wide and 3 px tall with three triangular points 3 px tall, a small round gem on the middle point; gold with a darker lower edge | band, three points, gem | a crown | a tiara, a flame, a comb, the guild banner |
| `icon.entity.merchant` | 16 | v2 | a balance scale | medieval: a market trader's brass balance with two hanging pans | modern kitchen scales; the scales of justice emblem; a coin purse | upright, symmetric, centred | a post 2 px wide and 9 px tall on a 6 px base, a beam 12 px wide across the top, two pans 4 px wide hanging on 1 px strings at each end; brass and dark outline | post, beam, strings, pans | a balance scale | a coin purse (the store icon), a tree, an anvil, a pair of bowls |
| `icon.entity.predator_hunter` | 16 | v2 | three claw slashes | medieval fantasy: three parallel red claw marks of a wild beast, tapering at the ends | a modern scratch icon; lightning; a rake | three near-vertical strokes leaning right | three strokes 2 px wide at the middle, tapering to 1 px points at both ends, 10 px tall, 3 px apart, red with a dark outline; no hand, no animal | three claw strokes | three claw slashes | a skull (the boss arena), a rake, lightning, a fence, steam |
| `icon.entity.raider` | 16 | v2 | a torn red banner | medieval: a tattered war banner on a pole, red cloth with a ragged lower edge | a modern flag; a pennant; a sail | upright pole at the left, cloth hanging to the right | a pole 1 px wide and 12 px tall at the left, red cloth 8 px wide and 6 px tall hanging from near the top with a torn zig-zag lower edge and two notches; the cloth is never a clean rectangle | pole, torn cloth, notches | a torn banner | a clean flag, the guild banner item, crossed swords (the enemy camp), a castle |
| `icon.entity.scout` | 16 | v2 | an open eye | abstract ui glyph: a watching eye, the almond outline with a round iris (an interface-style glyph, not a person) | a modern camera lens; a power button; an eyeball with veins | front view, level, centred | an almond outline 12 px wide and 7 px tall with a 4 px round iris and a 2 px pupil, a 1 px lid line above; no lashes, no blood vessels | almond outline, iris, pupil | an open eye | a camera lens, a power button, a fish, an eyeball for sale (a dropped item) |
| `icon.entity.sentinel` | 16 | v2 | a stone idol face | medieval fantasy: a square carved stone head of an undead guardian, two blue-lit eye slits | a modern robot head; a skull; a tombstone | front view, level, centred | a square block 10 px wide and 10 px tall with two 2 x 1 px blue eye slits, a 1 px nose groove and a flat chin; grey stone, no bone, no teeth, no helm | block head, eye slits, nose groove | a stone idol face | a skull or bone (the boss arena), the guard's gate key, a helm, a tombstone, a door |
| `icon.entity.wild_creature` | 16 | v2 | a grazing deer | medieval fantasy: a wild brown deer with branching antlers, head lowered to graze | a modern cartoon deer; a horse; a goat | side view facing left, head down | a body 7 px long and 4 px tall, four thin legs 3 px tall, a neck and head lowered to the left, branching antlers 3 px tall on the head, a short tail; brown with a pale belly | body, legs, lowered head, antlers, tail | a grazing deer | a horse, a goat, a dog, a nest, a tree |
| `icon.entity.worker` | 16 | v2 | a three-tine pitchfork | medieval: a farmer's iron pitchfork on a wooden shaft | a trident (a sea god's weapon); a modern garden fork; cutlery | upright, tines up, shaft down | three iron tines 6 to 7 px long joined by a 1 px crossbar, a wooden shaft 2 px wide and 4 to 5 px long below; about 9 px wide and 12 px tall; the tines are straight, the shaft is long, never a trident's barbs | tines, crossbar, wooden shaft | a pitchfork | a trident, a pickaxe (the mine icon), a rake, the crossed hammer and tongs item |
| `icon.item.armor` | 24 | v2 | a breastplate | medieval: a plate breastplate with pauldrons | a bulletproof vest; a t-shirt or vest; a kevlar jacket | upright, symmetric | 18 px wide at the shoulders and 18 px tall; two round pauldrons, a neck notch 4 px wide, a torso tapering to 8 px at the waist, a vertical centre ridge and a gold clasp | pauldrons, neck notch, torso plate, centre ridge, clasp | plate armour for the torso | a shirt, a vest, a tank top |
| `icon.item.consumable` | 24 | v2 | a potion flask | medieval fantasy: a corked alchemical potion flask | a screw-cap glass bottle; a light bulb; a syringe or pill bottle; a perfume bottle | upright, symmetric | round body 14 px wide and 12 px tall, a neck 6 px wide and 4 px tall, a tan cork 6x3 px, red liquid filling the lower two thirds, a highlight at the top left | round body, neck, cork, liquid, highlight | a healing potion | a lightbulb, a jar, a perfume bottle |
| `icon.item.material` | 24 | v2 | an ore chunk | medieval: a chunk of raw ore with gold flecks | a cut modern gemstone; a bag of coal; a pillow | upright, irregular | an irregular faceted chunk about 18 px wide and 17 px tall with 3 light and dark facets and 4-6 gold flecks | faceted body, light facet, dark facet, gold flecks | ore or a rock | a gem, a pillow, a cabbage |
| `icon.item.tool` | 24 | revision | a smith's hammer crossed with tongs | medieval: a smith's hammer crossed with tongs | a wrench or spanner; a toolbox or suitcase; pliers or power tools; a hammer in a weapon pose | two tools crossed in an X, centred and not a weapon pose: the hammer's handle from the bottom left to its flat-faced head at the top right, the tongs from their handles at the bottom right to closed jaws at the top left | 19 px wide and 19 px tall including the outline, inside the 20x20 live area (margins of at least 2 px); two long diagonal strokes crossing at a gold rivet near the centre; the hammer: a wooden handle 2 px wide and a short heavy steel head about 7 px across, at least 20 steel pixels in the top right (no spike, not a war hammer); the tongs: two steel arms meeting at the rivet, spreading apart at the handle end and closing to flat jaws at the other end | wooden handle, steel hammer head, tong arms, flat jaws, rivet | a blacksmith's hammer and tongs | a weapon, crossed swords, a wrench, a toolbox, an axe |
| `icon.item.trinket` | 24 | v2 | a pendant on a chain | medieval fantasy: an amulet on a chain | a modern necklace or locket; a sports medal on a ribbon; a watch | upright, symmetric | a thin 1 px chain loop 12 px wide that rises to a point, closed by a small bail ring (4 px or less) at the apex; a round gold pendant 10 px wide and 8 px tall hanging at the loop's foot with a blue gem at least 5x4 px; never two ribbons, never a neck and a body | bail ring, chain loop, gold setting, gem, highlight | an amulet or necklace | a medal, a potion flask, a ring, a compass, a clock |
| `icon.item.weapon` | 24 | v2 | a sword | medieval: an arming sword | a modern knife or machete; a letter opener; a key | upright, point up, centred on the vertical axis | total 20 px tall; blade 12 px (60 percent) long and 4 px wide with a 1 px light centre line and a 2 px tip; a gold crossguard 12 px wide and 2 px thick, perpendicular; a grip 2 px wide and 2 px long (never wider than the guard or the blade), brown; a gold pommel 4x2 px | blade, centre line, crossguard, grip, pommel | a longsword | a cleaver, a knife, a dagger, a key |
| `icon.marker.boss_arena` | 16 | v2 | a skull | medieval fantasy: a skull marking a deadly place | a poison or hazard label (skull and crossbones sign); a modern horror-mask emoji | upright, centred | cranium 10-12 px wide and about 8 px tall, two dark 2x2 eye sockets, a 1-px nose, a jaw 6-8 px wide with 3 tooth gaps | cranium, eye sockets, nose, jaw with teeth, shade on the right | a human skull | a ghost, a cloud, a mask |
| `icon.marker.dungeon_entrance` | 16 | v2 | an arched doorway | medieval dungeon: a stone archway into a keep or cave | a modern tunnel or subway entrance; a garage door; a window | upright, centred | arch frame 12 px wide and 12 px tall with a round top, a dark opening about 6 px wide and 7 px tall inside it, a 1-2 px stone frame | stone frame, arched dark opening, base step | a doorway into a dungeon or cave | a window, a tombstone, a mailbox, a tunnel seen from the side |
| `icon.marker.enemy_camp` | 16 | adopted | crossed swords | medieval fantasy: crossed swords marking a hostile camp | firearms or rifles crossed; a modern video-game battle pictogram; scissors | two diagonals crossing at the centre | two blades crossing in an X about 12 px across, gold guards, brown grips | two blades, two guards, two grips | crossed swords, battle | a pair of scissors, an X mark |
| `icon.marker.nest` | 16 | v2 | a bird's nest with three eggs | medieval fantasy: a woven twig nest of a wild beast with speckled eggs | a modern bowl of eggs; a straw hat; a basket | upright, centred, the nest low and wide | a nest 12 px wide and 6 px tall of interlaced twig lines (brown, two shades) with a ragged top rim; three pale speckled eggs 3x4 px resting in it, visible above the rim; fits the 12x12 live area | twig bowl, rim twigs, three eggs, shadow | a nest with eggs | a bowl of food, a hat, a basket |
| `icon.marker.resource_grove` | 16 | v2 | a tree | medieval fantasy: a wild broadleaf tree of the countryside | a modern park or street tree; broccoli; a cloud | upright, centred | crown 10-12 px wide and about 8 px tall; trunk 2 px wide and 3-4 px tall, centred under the crown; the crown is wider than tall | crown, shaded right side, trunk | a broadleaf tree | a bush, a speech bubble, a cloud, a lollipop |
| `icon.marker.ruins` | 16 | v2 | a ruined brick wall | medieval ruin: a broken masonry wall of a fort or castle | a modern brick building; concrete or a construction site; a staircase | upright, wider than tall, the broken top edge shaped like a U (never a one-way slope: that read as a boot, and a slab under it as a sole) | wall 10 px wide and about 9 px tall; 4 courses of bricks, two rows each, alternating light and dark with staggered mortar joints; a broken top edge with two towers of different heights (4 and 3 px from the top) either side of a low jagged gap; at least one fallen brick (a loose group of 2 or more px) lying in the gap; no ground slab and no matched pair of bricks under the wall (they read as wheels and a cart) | brick courses, mortar joints, two towers, low jagged gap, fallen brick | a broken brick wall | mountain peaks, a wagon, a boot, a chess piece, a stair, a tooth, a crown |
| `icon.marker.shrine` | 16 | v2 | an obelisk | ancient or medieval: a standing stone, obelisk or waymarker | a modern headstone or monument sign; a rocket; a bell | upright, centred, taller than wide | 8 px wide, 11 px tall; shaft 4 px wide with straight sides; pointed pyramid tip (1 px, then 2 px); plinth 6 px wide and 2 px tall; no rounded top, no flare | pyramid tip, shaft with a light left edge, gold marks, plinth | a standing stone, obelisk or monument | a bell, a bottle, a tombstone, a candle |
| `icon.node.berry_thicket` | 16 | v2 | a round bush with red berries | medieval fantasy: a wild berry bush with leaves and red berries | a modern holly wreath; a cherry emoji; a tomato plant | upright, round, wider than tall | a bush 12 px wide and 10 px tall, dark and light green clumps, five red berries 2 px across with a 1 px highlight, a 2 px trunk stub; fits the 12x12 live area | leaf clumps, red berries, trunk stub | a bush with red berries | a round tree crown, a cherry, a holly wreath |
| `icon.node.cover_patch_high` | 16 | v2 | a tall grass clump | medieval fantasy: tall wild grass hiding a person, reeds and long blades to head height | a modern lawn; a paintbrush; a broom | upright, blades fanning slightly | eleven blades in two greens, the tallest 11 px and the shortest 8 px, tips leaning outward by 1 px, a 2 px dark base; the tallest of the three cover patches; fits the 12x12 live area | tall blades, tips, base | tall grass | a feather, a flame, a broom |
| `icon.node.cover_patch_low` | 16 | v2 | a short grass tuft | medieval fantasy: ankle-high wild grass, a few short blades | a modern lawn; a paintbrush; a broom | upright, blades short and close | five blades in two greens, the tallest 4 px, a 2 px dark base; the shortest of the three patches; fits the 12x12 live area | short blades, base | a short grass tuft | a sprout, a bush, a wave |
| `icon.node.cover_patch_medium` | 16 | v2 | a medium grass tuft | medieval fantasy: waist-high wild grass, a tuft of blades | a modern lawn; a paintbrush; a broom | upright, blades fanning slightly | eight blades in two greens, the tallest 7 px and the shortest 5 px, a 2 px dark base; half the height of the high patch; fits the 12x12 live area | blades, tips, base | a tuft of grass | a bush, a flame, a feather |
| `icon.node.crystal_outcrop` | 16 | v2 | a cluster of pointed crystals on rock | medieval fantasy: three tall pointed blue crystals growing from a grey rock base | a modern glass shard; a diamond emoji; a candle flame | upright, three crystals of different heights on a low rock base | a rock base 11 px wide and 3 px tall; three hexagonal-pointed crystals 9 px, 7 px and 5 px tall in light blue with a white highlight edge; fits the 12x12 live area | rock base, three crystals, highlight edges | blue crystals | an icicle, a candle flame, a tooth |
| `icon.node.frost_shard_cluster` | 16 | v2 | a spray of ice shards | medieval fantasy: pale cyan ice shards bursting outward from one point, with a frost sparkle | a modern ice cube; a snowflake logo; a broken windshield | upright, shards radiating outward from the bottom centre | five thin angular shards radiating from a 2 px base, 5 to 9 px long, pale cyan with white edges; NO rock base; one white sparkle pixel above; fits the 12x12 live area | radiating shards, white edges, sparkle | shards of ice | a crystal outcrop on rock, a star, a claw |
| `icon.node.healing_flower_patch` | 16 | v2 | a single white and gold flower | medieval fantasy: a wild healing flower with five white petals and a gold centre on a leafy stem | a modern daisy emoji; a sunflower; a cotton swab | upright, one flower on a stem with two leaves | a stem 8 px tall; five white petals around a 3 px gold centre (a flower head 7 px across); two green leaves 3 px long; fits the 12x12 live area | petals, gold centre, stem, leaves | a single white flower | a sun, a star, a mushroom |
| `icon.node.herb_patch` | 16 | v2 | three leafy herb sprigs | medieval fantasy: wild medicinal herbs, three green sprigs with paired leaves and no blossoms | a modern potted plant; a salad; a clover icon | upright, three sprigs fanning from one base | three stems 9 px, 7 px and 8 px tall with 3 to 4 pairs of 2 px leaves, two greens, no flowers, a 1-px soil line; fits the 12x12 live area | stems, paired leaves, soil line | a few green herb sprigs | a cluster of cover grass, a flower, a seaweed frond |
| `icon.node.iron_vein` | 16 | v2 | a grey boulder with rust-brown ore seams | medieval: a rough rock with veins of iron ore in angular rust-brown chunks | a modern brick; a coal lump; a meteor | upright, a rough angular boulder, wider than tall | a boulder 12 px wide and 9 px tall in two cool greys with an angular silhouette; two rust-brown angular ore chunks 3 x 2 px set into it; no sparkle; fits the 12x12 live area | rock, angular ore chunks, shadow | a rock with iron ore | a brick, a lump of coal, an egg |
| `icon.node.moon_resin_tree` | 16 | v2 | a slim pale tree with an amber resin drop | medieval fantasy: a slender silver-barked tree with a glowing amber resin drop on its trunk | a modern street tree; a lollipop; a palm tree | upright, centred, a round crown on a slender trunk | a crown 9 px wide and 6 px tall in blue-green; a slender pale silver trunk 2 px wide and 5 px tall; one amber resin drop 2 x 3 px with a highlight on the trunk; fits the 12x12 live area | crown, pale trunk, amber drop | a tree with an amber resin drop | a lollipop, a mushroom, a plain green tree |
| `icon.node.silver_vein` | 16 | v2 | a rounded boulder with a bright silver seam | medieval: a smooth rock cut by a bright silver seam with a sparkle | a modern coin; a snowball; a pearl | upright, a rounded boulder, wider than tall | a boulder 12 px wide and 9 px tall in two warm greys with a ROUNDED silhouette; one diagonal pale silver seam 8 px long and 2 px wide; two white sparkle pixels beside it; fits the 12x12 live area | rounded rock, silver seam, sparkle | a rock with a silver seam | a pearl, an egg, a snowball |
| `icon.node.spirit_wisp` | 16 | v2 | a floating wisp flame with a curved tail | medieval fantasy: a pale blue-white will-o'-the-wisp, a teardrop flame with a curled tail floating above the ground | a modern light bulb; a candle; a ghost emoji | upright, the flame body above a curling tail, tilted slightly | a teardrop body 6 px wide and 7 px tall in pale blue with a white core; a curled tail 5 px long to one side; no base and no ground; two 1 px dark eye dots; fits the 12x12 live area | body, white core, curled tail, eye dots | a floating wisp of spirit flame | a candle flame, a water drop, a leaf |
| `icon.node.wood_node` | 16 | v2 | a stack of three logs | medieval: cut logs of timber stacked with their ends showing, ringed and bark-brown | a modern lumber plank; a stack of pipes; a barrel | upright, a 2-over-1 pyramid of logs | three round log ends 5 px across (two below, one above) with 2 px light ring marks and bark-brown rims; fits the 12x12 live area | log ends, growth rings, bark, shadow | a stack of logs | a barrel, a stack of pipes, a bunch of coins |
| `icon.plate.location` | 16 | adopted | a location plate | abstract UI glyph: a plaque the glyph sits on, no setting | a phone screen; a button with a label; a picture frame | square | 16x16, 1 px rim #9ea4b6, slate fill, a light top-left edge, a shadow bottom-right, cut corners | rim, fill, light edge, shadow edge | a plaque or button the glyph sits on | a window, a button with a label |
| `icon.rarity.common` | 8 | revision | a silver bead | abstract UI glyph: a plain bead, no setting | a button; a coin; a modern verified badge | centred | 7x7 px, round (fills at most 80 percent of its bounding box), a light silver fill (#c8d8e8) with a bright highlight (#eafeff) at the top left and a shaded lower right (#91a2ab), dark outline; never the tier's 8 px, and lighter than the dark tier badges E and D so it cannot be mistaken for them by value | round body, highlight, shade | a silver bead or pearl | a square, a tier badge, a coin |
| `icon.rarity.rare` | 8 | v2 | a four-point sparkle gem | abstract UI glyph: a sparkle gem, no setting | a plus sign or medical cross; a compass; a snowflake icon | centred | 8x8 px, four points of equal length on both axes, a 4x4 body, violet fill | four points, body | a sparkle or glint | a plus sign, a compass, a cross |
| `icon.rarity.uncommon` | 8 | v2 | a kite-shaped gem | abstract UI glyph: a cut gem, no setting | an arrow; a leaf; a modern location pin | point up, centred | 6 px wide at the widest and 6-7 px tall, a wide top and a pointed bottom, green fill | gem body, point | a cut gem | an up arrow, a shield, a leaf |
| `icon.status.frame_buff` | 16 | revision | a round frame with a solid up arrow | abstract UI glyph: an up arrow in a round frame, no setting | a modern upload or volume-up icon; a gem; a shield | upright, symmetric | the adopted round green frame unchanged (16x16, green rim, dark green interior); inside it a SOLID bone-coloured up arrow: a head 2, 4 then 6 px wide and a shaft 2 px wide and 5 px tall, centred, the mirror of the debuff's down arrow; no chevron outline | round frame, green rim, solid arrow head, solid arrow shaft | an increase, a buff | a gem, a shield, a cross, a sword |
| `icon.status.frame_debuff` | 16 | revision | a spiked ball frame with a down arrow | abstract UI glyph: a spiked-ball frame with a down arrow, no setting (a morning star's head) | a red road warning sign; a hazard label; a funnel; a gear or saw blade | upright, symmetric (eight spikes at the compass points) | 16x16, filling its canvas like the buff frame; a dark disc with a red rim ring and eight sharp triangular red spikes round it (the registry's 'spiked frame'); inside, a SOLID bone down arrow: a shaft 2 px wide and 4 px tall, then a head 6, 4 and 2 px wide (20 px in one piece); the silhouette is not a triangle and must differ from the round buff frame by at least 6 px (I1) | dark disc, red rim, eight spikes, solid down arrow | a harmful effect, a debuff | a warning sign, a gear, a sun, an up arrow |
| `icon.tier.a` | 8 | adopted | an octagon badge with a frame cut out | abstract UI glyph: a rank badge in a seal-like octagon, no setting | a stop sign; a modern button | centred | 8x8 octagon with a 2x1 cut-out | octagon, frame | a rank badge | a stop sign |
| `icon.tier.b` | 8 | adopted | an octagon badge with two pips cut out | abstract UI glyph: a rank badge in a seal-like octagon, no setting | a stop sign; a modern button | centred | 8x8 octagon with two 1x1 cut-outs | octagon, two pips | a rank badge | a stop sign |
| `icon.tier.c` | 8 | adopted | an octagon badge with one pip cut out | abstract UI glyph: a rank badge in a seal-like octagon, no setting | a stop sign; a modern button | centred | 8x8 octagon with one 1x1 cut-out | octagon, one pip | a rank badge | a stop sign |
| `icon.tier.d` | 8 | adopted | a plain octagon badge | abstract UI glyph: a rank badge in a seal-like octagon, no setting | a stop sign; a modern button | centred | 8x8 octagon, slightly lighter fill than E | octagon | a rank badge | a stop sign |
| `icon.tier.e` | 8 | adopted | a dark green plain octagon badge | abstract UI glyph: a rank badge in a seal-like octagon, no setting | a stop sign; a modern button | centred | 8x8 octagon, dark fill, outline | octagon | a rank badge | a stop sign |
| `icon.tier.s` | 8 | adopted | a silver diamond badge | abstract UI glyph: a rank gem (diamond), no setting | a playing-card suit; a diamond road sign | centred | 8x8 diamond, silver fill | diamond | a rank badge | a playing card suit |
| `icon.tier.ss` | 8 | adopted | a gold diamond badge with one pip | abstract UI glyph: a rank gem (diamond), no setting | a playing-card suit; a diamond road sign | centred | 8x8 diamond, gold fill, one cut-out | diamond, one pip | a rank badge | a playing card suit |
| `icon.tier.sss` | 8 | adopted | a platinum diamond badge with two pips | abstract UI glyph: a rank gem (diamond), no setting | a playing-card suit; a diamond road sign | centred | 8x8 diamond, platinum fill, two cut-outs | diamond, two pips | a rank badge | a playing card suit |

<!-- icon-specs-table:end -->

The entity markers (`icon.entity.<kind>`, 11 role kinds, 16x16 bare objects, owner decision 2026-10-19) are adopted as set `entity-markers-v1` and NOT built: no release candidate carries them yet. The owner accepted that 7 of the 11 read as an item or a resource on a map crop (blind check, two agents); the table is in `TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`.


**Reference study (D20: reference only, nothing traced or copied).** Looked at on 2026-10-08, to fix conventions before the redraw:

| Source | Author | Licence | What was observed (one line per object) |
|---|---|---|---|
| Kenney Tiny Dungeon preview, https://kenney.nl/assets/tiny-dungeon (16x16) | Kenney | CC0 | swords are upright and point up, the blade is about two thirds of the height and 2 to 3 px wide with a light edge, the crossguard is 1 px wider than the blade on each side, the grip is short and never wider than the guard; the dagger is the same shape but shorter and narrower; axe and hammer are upright with the head at the top; potions are a round flask with a short neck and a tan cork, liquid colour fills the lower body |
| Kenney 1-Bit Pack preview, https://kenney.nl/assets/1-bit-pack (16x16) | Kenney | CC0 | swords are drawn diagonally bottom-left to top-right with a long blade (about three quarters of the diagonal), a perpendicular crossguard, a short grip and a pommel; daggers are short with a wide guard; bows are an arc with a straight string; axes have the head at the top-right end |

Both were looked at as preview images only (no download of the packs, nothing committed, no pixel reused). game-icons.net and Shikashi's pack (the other two named in `research_packs_palettes.md`) were not examined in this pass: their SVG and 32x32 art did not add a convention the two packs above lack for these glyphs.

**Process rule for every future icon batch** (a step may not be skipped; a failure of a step is reported, never tuned away):

1. **Spec** per icon in `icon_specs.yaml` (orientation, pixel proportions, parts, reads as, must not read as, synonyms, distractors, **theme and modern lookalikes to avoid**), with the family conventions. **Theme fit (D21) is checked here first:** an object a medieval craftsman, traveller, soldier or mage would own, or an abstract UI glyph.
2. **Reference study**: 2 or 3 existing icons of the object at 16 to 32 px, recorded (title, author, source, licence, one line of conventions); nothing copied.
3. **One-colour silhouette sheet**: render every new icon's silhouette in one colour, side by side with the existing set, and have the owner approve the shapes before any colour is drawn. (The review folder's `06_silhouettes.png` is this sheet; the owner gets the folder path for this step too.)
4. **Draw** to the spec.
4b. **Numbers guessed before the silhouette are re-agreed, never restated after drawing.** A spec number written before the owner's silhouette question (a pixel count, a share, a minimum) is put to the owner at that question, next to the silhouette, and agreed there. If drawing shows it was wrong, the drawing or the number goes back to the owner as a new question; the implementer never restates it alone after the fact. (Origin: the theme-fit batch restated three numbers after drawing; the owner accepted them on 2026-10-08.)
5. **Spec compliance table** for every new or redrawn icon (`visual_assets/review/icon_compliance.py`): each proportion the spec states (blade length as a share of the height, blade width, guard width against grip width, pommel present, courses of bricks, bow curvature, roundness ...) **measured from the pixels** next to the spec value. A row that fails is reported, never tuned away.
6. **Checks** (theme fit included: the era question): the sheet rule (I1 to I3 and lint), the **blind recognition check** (`visual_assets/review/icon_recognition.py`: a fresh agent with no project context names every unlabelled icon, free text first, then a candidate list with distractors; answers stored as evidence) and the **whole-sheet look-alike report** (`visual_assets/review/icon_lookalikes.py`, report only).
7. **Owner gate**: the owner reviews the **review folder** and runs `adopt-set` (for revisions of adopted icons keep each draft with `draft keep --revises rNNNN` and one `adopt-set` adopts new icons and revisions together, ADR D22; the older per-slot `review` and `adopt --parent` still work) in their own terminal. **Every owner gate, the silhouette step 3 included, ships the folder path**: `python -m visual_assets.review review-sheets --set <draft_set_id>` writes `~/Work/asset-review/<set>/` (outside every repository) with six large labelled PNG canvases at whole-number zoom (`01_overview`, `02_before_after`, `03_groups`, `04_colour_vision`, `05_map_markers`, `06_silhouettes`) and a `README.txt` holding what each image shows, the recorded results, the findings and the exact owner commands. The live preview page stays for detail, but it is not the review surface (the owner found it slow: start Vite, scroll a long page).

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

