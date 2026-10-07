---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# The Craft of Small Pixel-Art Icons: Research Report

Prepared 2026-10-06 for the RPG simulation's icon set (16x16 terrain map, React web UI, drawn in Aseprite through the pixel-art MCP tools).

Notes on evidence: every factual claim below carries a source URL. Where a statement is my own design inference rather than something a source says, it is marked **(inference)**. Claims I could not verify are marked **UNVERIFIED**. The Pixel Logic book and Brandon James Greer's material are video- or book-only. I could confirm their topic coverage, but I could not quote them directly.

---

## 1. Choosing an icon size and scaling it in a web UI

**Match the world grid.** Slynyrd's item lesson says: "If your environment is made out of 16x16px tiles, then 16x16px should be the perfect relative size of the items." The same lesson keeps "every item [at] about 6 colors or less." ([Slynyrd Pixelblog 24 - Items](https://raymond-schlitter.squarespace.com/blog/2019/12/21/pixelblog-24-items))

**Trade-offs by size** (inference, except where a source is cited):
- **8 px.** Only glyph-like marks fit: pips, arrows, letters. Use it for corner badges on top of a larger icon, not for a standalone pictogram.
- **12 px.** Fits small inline HUD or status marks. Mapbox's map symbol set Maki was designed to read at 11 px and 15 px. Its guidance says icons must be "legible at sizes as small as 11px", built from "straight, obvious vertical and horizontal lines according to the pixel grid", and "fill-based rather than stroke based" ([Maki / Mapbox cartography guide](https://amyleew.gitbooks.io/cartography-guide/content/iconography.html); [Maki on npm](https://www.npmjs.com/package/@mapbox/maki)).
- **16 px.** This matches the tile grid and the lint budget of 8 colours. A small-sprite guide recommends "around 4 to 8 colors" at 16 px, which is a lower-authority source ([sprite-ai 16x16 guide](https://www.sprite-ai.art/guides/how-to-create-16x16-pixel-art)).
- **24 / 32 px.** Room for a frame plus a pictogram, which suits loot cards, class portraits and tab icons that carry a frame.
- **Draw each size separately.** Maki ships two hand-drawn sizes because an icon "drawn once and then scaled" "will appear blurry and indistinct" ([Maki](https://www.npmjs.com/package/@mapbox/maki)).

**Integer scaling only.** Saint11 says pixel art can only be scaled "in 100% increments", and "every time someone mixes pixel art resolutions, an angel dies." His advice is to keep different resolutions on separate layers (UI vs. gameplay), to use only integer multiples ("100% and 200%, never 150%"), and to mix at most two resolutions ([Saint11 - Scaling](https://saint11.art/blog/scaling/)).

**CSS mechanics:**
- `image-rendering: pixelated` scales "to the nearest integer multiple of the original image size, then uses smooth interpolation to bring the image to the final desired size". At non-integer sizes it is therefore intentionally a little soft. `crisp-edges` does pure nearest-neighbour with "no blurring" ([MDN image-rendering](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/image-rendering)).
- When `devicePixelRatio` is fractional (for example browser zoom at 110% or a 1.25x OS scale), "certain pixels may be drawn larger than others", and "it is impossible to fill device pixels precisely" ([MDN - Crisp pixel art look](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)). At DPR 1.5, art pixels alternate between 1 and 2 device pixels ([voidmarch issue #20](https://github.com/starquake/voidmarch/issues/20)).
- On a canvas, draw at integer multiples of canvas pixels ([MDN](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)). Pick the integer zoom in *device* pixels (`Math.floor(scale * devicePixelRatio)`) ([voidmarch #20](https://github.com/starquake/voidmarch/issues/20)).
- **Recommendation (inference).** Render icons through a small `<PixelIcon>` component that sets the CSS size to `n * 16 / devicePixelRatio` for an integer `n`. Snap the position to whole device pixels as well, and listen for DPR changes with `matchMedia('(resolution: …)')`.

**Pixel icons next to vector text.** Saint11's "world consistency" principle says mixing styles is acceptable "if each area of your game is kept separated and internally consistent" ([Saint11 - Consistency](https://saint11.art/blog/consistency/)). In practice (inference): keep pixel icons at integer scale inside their own box, set the vector text beside them rather than over them, and never rotate or fractionally scale an icon to fit a text line height. Choose the line height to suit the icon instead.

---

## 2. Silhouette first, recognisability, metaphors and consistency

**Silhouette first.** Block the shape out in one colour before adding any detail: "If the silhouette isn't readable, no amount of shading will fix it" ([sprite-ai 16x16 guide](https://www.sprite-ai.art/guides/how-to-create-16x16-pixel-art)). Pixel Logic gives a whole chapter to readability, including "Recognisable features" and "Easy to read symbols" ([Pixel Logic contents via Goodreads/Scribd sample](https://www.scribd.com/document/1067222467/Pixel-Logic-Sample)). The chapter text itself is UNVERIFIED (I did not read it). Saint11 enlarges important features at low resolution beyond their true proportion ("the eyes, they are now bigger and regular") ([Saint11 - Basic Shading](https://saint11.art/pixel_art_articles/article4/)).

**Recognisability tests:**
- **Squint test.** Blurring the image leaves only "fundamental contrasts of light and dark, large and small" ([Squint Test, Medium](https://medium.com/@sifatrabbani_UX/the-squint-test-0677a08de848)).
- **Recognition test.** NN/G tests icons "in isolation, in the absence of a text label" and asks users to guess what each means. Its findability test measures time-to-locate among other icons. Its information-scent test checks that users grasp the *function*, which matters more than the depicted object ([NN/G - Icon testing](https://www.nngroup.com/articles/icon-testing/)).
- **Grid-off 1x preview.** Turn the grid off often and look at the sprite at actual size ([sprite-ai](https://www.sprite-ai.art/guides/how-to-create-16x16-pixel-art)).

**Metaphors for abstract concepts.** NN/G found that "a text label must be present alongside an icon to clarify its meaning", because most icons are ambiguous. Only a few (home, print, magnifier) enjoy near-universal recognition ([NN/G - Icon Usability](https://www.nngroup.com/articles/icon-usability/)). XAG 103 likewise recommends pairing symbols with text labels ([XAG 103](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103)). Applied to our tabs (inference): choose a concrete *object* metaphor that suits the fantasy setting and always ship a label or tooltip with it:
- **AI:** an eye or a gear-brain.
- **Narrative:** an open book or a scroll.
- **Quest:** a "!" or a sealed scroll. The "!" as the alert signifier is cited by XAG 103.
- **Events:** a bell or a clock.
- **Effects:** a swirl or a sparkle.

**Rules that keep a set consistent:**
- **Shared grid and keylines.** Material Design keeps a 24 dp icon to a 20 dp live area with 2 dp of padding, and uses keyline shapes (circle, square, rectangle) to equalise visual mass ([Material system icons](https://m2.material.io/design/iconography/system-icons.html)). Translated to pixels (inference): a 16 px icon gets a 14x14 live area with a 1 px margin. That margin also keeps the outline off the edge, which is what the `touches_edge` check enforces.
- **One light direction.** Saint11 warns against "shading an object with no clear light source" ([Saint11 - Basic Shading](https://saint11.art/pixel_art_articles/article4/)). Choose top-left and never vary it.
- **One outline policy.** A full dark outline guarantees separation from any background. Selective outlining ("selout") lightens the outline on the lit side ([Lospec selout tutorials](https://lospec.com/pixel-art-tutorials/tags/selectiveoutlining); [pixnote outlines guide](https://pixnote.net/en/learn/outlines/)). Lospec's rule is that "an outline should always be darker than both the object AND the background behind it". Where backgrounds vary, "favor darker shades or default to black for reliability" ([Lospec - Outlines Part 2](https://lospec.com/articles/pixel-art-outlines-part-2-using-color/)).
- **One perspective per family.** Slynyrd lists a "consistent visual language" of colour, shape, size and positioning as a core UI goal ([Slynyrd Pixelblog 26 - UX/UI](https://raymond-schlitter.squarespace.com/blog/2020/2/23/pixelblog-26-uxui-design-basics)). Recommendation (inference): buildings and markers in 3/4 front view, items in a 3/4 diagonal "inventory" pose, tab glyphs flat and front-on.
- **Colour count.** Saint11 calls "sticking to a low color count" the most common way to stay consistent, and warns against introducing new colours without reusing them ([Saint11 - Consistency](https://saint11.art/blog/consistency/)).

---

## 3. Map markers

- **Separation from busy terrain.** Map-UI guidance says to "add outlines or shadows to make markers pop against any background" and to test against the darkest and brightest backgrounds the marker will sit on ([Eleken - Map UI design](https://www.eleken.co/blog-posts/map-ui-design)). Lospec's outline rule (darker than both the object and the background) applies directly ([Lospec](https://lospec.com/articles/pixel-art-outlines-part-2-using-color/)). Map icons need "good contrast against the background" ([Mapbox map design guide](https://www.mapbox.com/insights/map-design-process)).
- **Backplates and pins.** The conventional pin is the "upside-down, teardrop-shaped marker indicating an exact location" ([Map UI Patterns - Marker](https://mapuipatterns.com/marker/)). Recommendation (inference): give every marker a shared plate or pin shape (for example a 1 px dark-outlined disc or shield with a one-colour drop shadow at bottom-right). The plate's *shape* then encodes the marker category, and the glyph inside encodes the specific site. Contrast is measurable: one itch.io quest-marker test found a teal accent at 1.9:1 against charcoal "barely visible", while ivory reached 16:1 ([itch.io quest-marker feedback](https://itch.io/t/7022926/map-ui-creators-can-you-read-these-three-64px-quest-markers)).
- **Zoom behaviour.** I found no authoritative pixel-art source. Recommendation (inference): keep markers at a fixed *screen* integer scale while the map zooms (counter-scaling), rather than letting them scale with the tiles. When zoomed far out, collapse them into a simpler 8 px pip of the same plate shape. Map clustering is a common pattern, but its use with pixel markers is UNVERIFIED.
- **State variants** (discovered, cleared, hostile). XAG 103 says greying alone must not signal state. Sea of Thieves greys out locked items *and* adds a lock symbol, and Forza adds a "Not available" label ([XAG 103](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103)). Recommendation (inference):
  - **Undiscovered:** a "?" plate.
  - **Discovered:** the full icon.
  - **Cleared:** the icon with a check or flag badge plus desaturation.
  - **Hostile:** a spiked or red-outlined plate plus a crossed-swords badge.

  Each state therefore changes shape, not only colour.

---

## 4. Rarity and grade tiers without relying on hue

**History.** Colour-coded loot was popularised by Diablo (1996) and Diablo II, whose designer took the idea from Angband. WoW standardised grey, white, green, blue, purple, orange ([Wikipedia - Loot](https://en.wikipedia.org/wiki/Loot_(video_games)); [TV Tropes](https://tvtropes.org/pmwiki/pmwiki.php/Main/ColorCodedItemTiers)). Hades uses outline colour for boon rarity (Common white, Rare blue, Epic purple, Heroic red, Legendary orange) ([Hades Wiki - Boons](https://hades.fandom.com/wiki/Boons)). These systems are hue-first. WoW only added player-customisable quality colours in Patch 11.1.5 to help colour-blind players ([GameRant](https://gamerant.com/world-of-warcraft-patch-11-1-5-colorblind-accessibility-option-item-rarity/)). That is the fallback XAG 103 prescribes when colour is primary: "If color is the primary method of communication… (like if rare items have a blue highlight and legendary items have an orange highlight), the player should be able to configure those colors" ([XAG 103](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103)).

**Non-hue channels used in shipped games:**
- **Shape and minimap symbol.** Diablo III legendaries show a star on the minimap and set items an asterisk. Each also gets a light beam and a distinct sound ([Diablo Wiki - Legendary](https://www.diablowiki.net/Legendary); [Fandom - Legendary Items](https://diablo.fandom.com/wiki/Legendary_Items)). Path of Exile filters let players attach minimap icon *shapes* (Circle, Diamond, Hexagon, Square, Star, Triangle, Cross, Moon, Raindrop, Kite, Pentagon, UpsideDownHouse) and three sizes, independently of colour ([PoE item filter docs](https://www.pathofexile.com/item-filter/about)).
- **Escalating pictogram.** Slay the Spire's attack intent changes weapon *shape* with damage tier, "scaling from dagger to scythe" across damage bands of 0-4, 5-9 and so on up to 30+ ([Slay the Spire Wiki - Intent](https://slaythespire.wiki.gg/wiki/Intent)).
- **Animation and sparkle.** Slynyrd: "The more important or beneficial the item, the more special the feedback can be", using shine and sparkle idle animations kept "simple and non-distracting" ([Slynyrd Pixelblog 24](https://raymond-schlitter.squarespace.com/blog/2019/12/21/pixelblog-24-items)).

**Proposed tier ladder** (inference), with several redundant channels per step:
- **Frame complexity:** none, then a 1 px plain frame, a 1 px frame with corners, a double frame, a notched or ornate frame.
- **Corner pip count:** 0 to 4.
- **Brightness of the frame:** increasing up the ladder, which survives greyscale.
- **Highest tiers:** an idle sparkle animation.

Grades E..SSS already *are* glyphs, so draw the letters as the primary signal. Add a frame-shape ladder (E/D plain square, C/B bevelled, A shield, S/SS/SSS star-plate with 1, 2 or 3 stars), and treat colour as reinforcement only.

---

## 5. Status-effect conventions

- **Buff vs. debuff framing.** Darkest Dungeon marks buffs with "a double upward blue arrow" and debuffs with "a double downward orange arrow". The direction of the arrows carries the meaning without colour ([DD Wiki - Buff](https://darkestdungeon.wiki.gg/wiki/Buff_(Darkest_Dungeon)); [DD Wiki - Debuff](https://darkestdungeon.wiki.gg/wiki/Debuff_(Darkest_Dungeon))). Darkest Dungeon II moved to small "tokens" displayed next to heroes ([gamepressure DD2 icons](https://www.gamepressure.com/darkest-dungeon-ii/icons-tokens-abbreviations/zcf03c)).
- **Type coding.** WoW (since Patch 1.11) colours debuff borders by dispel type: Curse purple, Disease brown/yellow, Magic blue, Poison green ([Wowpedia - Debuff](https://wowpedia.fandom.com/wiki/Debuff)). This is a hue-only scheme, so avoid copying it without a shape channel.
- **Numbers and stacks.** Slay the Spire puts numbers on its intents (damage × hits). In StS2, multiple intents sit side by side rather than being merged into one icon ([StS2 Intent wiki](https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Intent)).
- **Recommendation** (inference):
  - **Frame shape:** buffs in a rounded or circular frame with an up-chevron badge, debuffs in a spiked or inverted-triangle frame with a down-chevron badge.
  - **Stacks:** the stack count is a 3x5 pixel-font digit in the bottom-right corner on a dark backplate.
  - **Duration:** a radial or vertical "drain" overlay darkening the icon from the top, or a remaining-turns digit at top-left.
  - **Glyph space:** keep the central 10x10 area for the effect glyph.

---

## 6. Colour blindness and accessibility

- **Game Accessibility Guidelines (Basic):** "Ensure no essential information is conveyed by a fixed colour alone" and "Provide high contrast between text/UI and background" ([GAG - Basic](https://gameaccessibilityguidelines.com/basic/)). Colour should be backup reinforcement for symbols, patterns or shapes. The guideline cites colour blindness affecting about 8-10% of males and lists Puzzle Retreat's "integrated symbols with colour" as a good example ([GAG - colour alone](http://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-colour-alone)).
- **Xbox XAG 103:** "Color alone should never be used to represent information." Colour-expressed critical content "needs to be expressed by using at least one additional signifier such as shape, pattern, iconography, or text labels." Greying must be accompanied by another method. Simulators are fine during development but are not a substitute for testing with colour-blind players. It recommends Color Oracle and the Colour Contrast Analyser ([XAG 103](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103)). XAG 102 covers contrast ([XAG 102](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/102)).
- **Ubisoft practice.** A study of Xbox accessibility across the Far Cry series exists ([Springer UAIS](https://link.springer.com/article/10.1007/s10209-025-01208-4)), but I did not read its icon-specific findings, so they are UNVERIFIED.
- **Relation to our lint** (inference). The `value_separation` check (adjacent luma diff < 12/255) is a per-sprite internal contrast check. It is not the same as a *between-icon* greyscale test. Also run a set-level test: convert the whole sheet to greyscale and to a deuteranopia/protanopia/tritanopia simulation, then confirm every tier, state and buff/debuff pair still differs by shape or glyph.

---

## 7. Production workflow for an icon set

1. **Style guide or style tile first.** It sets the grid and live area, light direction, outline policy (full vs. selout), perspective per family, palette and ramps, and the frame/plate system. Industry advice: "establish a visual identity… and create a style guide for icon design", and use an icon grid that matches the UI grid ([Number Analytics - Icon design essentials](https://www.numberanalytics.com/blog/icon-design-essentials-game-developers)). This is a lower-authority source.
2. **Key icons first.** Draw 3-5 icons that stress different things, for example one marker on a plate, one building, one class, one framed loot item and one status icon. Lock the look, then produce the rest "against that style card", laying them out in a grid to check framing and size consistency ([Morphic - game icons for inventory UI](https://morphic.com/resources/how-to/make-game-icons-for-inventory-ui)). This is a lower-authority, AI-tool vendor source; the practice itself is common studio lore and its formal provenance is UNVERIFIED.
3. **Lock the palette.** Build ramps (`make_ramp`), keep a master palette and remap everything to it (`remap_palette`). Saint11 warns that inconsistency creeps in when new colours aren't reused ([Saint11 - Consistency](https://saint11.art/blog/consistency/)).
4. **Generate variants by layering, not redrawing** (inference). Separate the frame or plate, the glyph, and the badge (state, stack, tier pip) so the tier × item and state × marker matrices come from composition.
5. **Review on a contact sheet** (inference, supported by NN/G's findability/recognition testing, [NN/G](https://www.nngroup.com/articles/icon-testing/)). Show all icons at 1x and 2x on light, dark and real terrain backgrounds, and in greyscale.

---

## Checklist: per icon and per set

**Per icon**
- [ ] Drawn natively at its target size (16 px, or 8/24/32 for designated families). No scaled-down art.
- [ ] Content sits inside the live area (1 px margin at 16 px). `touches_edge` is clean, except for intentional plates or frames.
- [ ] A single-colour silhouette is recognisable at 1x with the grid off. It passes the squint/blur test.
- [ ] Colour count is within budget (8 at 16 px, ideally 6 or fewer per Slynyrd). Only master-palette colours are used.
- [ ] The light source is top-left and shading follows it. No "pillow" shading around the outline.
- [ ] The outline follows the set policy and is darker than both the object and the expected background.
- [ ] `value_separation` is clean (adjacent luma diff ≥ 12/255) where separation matters.
- [ ] The icon reads on light UI, dark UI and the busiest terrain tile.
- [ ] Shipped with a text label or tooltip (abstract tab icons always).

**Per family and set**
- [ ] Every distinction (tier, grade, rarity, buff/debuff, marker state, hostile/friendly) survives greyscale and a CVD simulation through shape, glyph, pip count, frame or brightness. Hue is never the only channel.
- [ ] Perspective is consistent within each family (markers/buildings, items, tabs).
- [ ] Rarity/grade ladder: frame complexity, pip count and brightness all increase monotonically. Animation is reserved for the top tiers and stays subtle.
- [ ] Buff and debuff frames differ in shape and carry an up or down chevron. Stack digits and duration overlays use the same pixel font and position everywhere.
- [ ] Marker plates share one shape vocabulary. The states discovered, cleared and hostile each add a badge or shape change, not only a tint.
- [ ] A contact sheet at 1x and 2x on mixed backgrounds has been reviewed. A recognition test (unlabelled guess) has been run on the abstract icons.
- [ ] Web rendering: integer CSS scale relative to `devicePixelRatio`, `image-rendering: pixelated`, whole-device-pixel positioning, and the pixel layer kept separate from the vector text layer.
- [ ] The key icons (3-5) were approved before the rest of the set was produced, and the style guide is updated with any rule they changed.
