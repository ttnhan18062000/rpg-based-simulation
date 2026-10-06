# Fantasy pixel-art icon packs, palettes, and licensing: research notes

Date: 2026-10-06. Web research only; nothing was downloaded. Each claim cites the page it came from. **UNVERIFIED** marks anything I could not confirm on a primary page. This is not legal advice.

Project context: 16x16 top-down terrain, hand-drawn in Aseprite, provenance-tracked asset store. We mostly use third-party art as reference. We reuse it directly only when its licence is compatible and can be recorded.

---

## 1. Icon and tile packs

### 1.1 Summary table

| Pack | Size | Palette / outline | Licence (exact) | Attribution | Reuse / redistribution | URL |
|---|---|---|---|---|---|---|
| Kenney 1-Bit Pack | 16x16, 1,078 tiles | 1-bit look. Colour count not stated on the page (UNVERIFIED). | CC0 | Not required. Optional credit is "Kenney". Kenney's logo is reserved. | Unrestricted | https://kenney.nl/assets/1-bit-pack, https://kenney.nl/support |
| Kenney Tiny Dungeon | 16x16, 130 files | Minimalist "Tiny" series | CC0 | Not required | Unrestricted | https://kenney.nl/assets/tiny-dungeon |
| Kenney Tiny Town | 16x16, 130 files | Minimalist "Tiny" series, tagged RPG/overworld | CC0 | Not required | Unrestricted | https://kenney.nl/assets/tiny-town |
| Kenney Game Icons | 105 icons. Size not stated. | Interface/gamepad prompts, not fantasy content | CC0 | Not required | Unrestricted | https://kenney.nl/assets/game-icons |
| game-icons.net | Vector SVG, about 4,000+ icons from 40+ authors | Single-colour silhouettes, recolourable in their "Studio" | CC BY 3.0 | **Required.** Suggested form: "Icons made by {author}. Available on https://game-icons.net" | Allowed with attribution | https://game-icons.net/about.html |
| Shikashi's Fantasy Icons Pack | 32x32, 284 icons (229 unique + 55 recolours) | "Bright and colourful palette", with background variants | CC BY 4.0 | **Required:** "Matt Firth (shikashipx)" **and game-icons.net**, because many icons derive from game-icons | Commercial use and editing allowed | https://shikashipx.itch.io/shikashis-fantasy-icons-pack |
| Shikashi's 600+ Icon Pack (paid successor, £2+) | 16x16 and 32x32, 607 icons | "Bright and warm 32 colour palette". Marked "No generative AI was used". | The page states the terms in prose (commercial use and editing allowed, credit required). It does not name a CC licence (UNVERIFIED). | Required | Commercial use allowed | https://shikashipx.itch.io/shikashis-600-icon-pack |
| 0x72 DungeonTileset II | 16x16 | Recoloured with GrafxKid's Linear Color Palette. "No generative AI was used". | CC0 ("use this tileset for whatever you like (CC-0)") | Not required | Unrestricted | https://0x72.itch.io/dungeontileset-ii |
| Dungeon Crawl Stone Soup tiles | 32x32, 3,000+ tiles plus a 3,000+ supplement. Three-quarter overhead view. | Painterly 32px style | CC0 | Not required. The page asks for a courtesy link. | **Caveat:** the upstream repo keeps a list of tiles with unclear licences, which are excluded | https://opengameart.org/content/dungeon-crawl-32x32-tiles, https://github.com/crawl/tiles |
| Battle for Wesnoth art | Hex-based, not a 16px grid | Painterly | GPL v2 or later (older art). Contributions since 2017-07-30 default to CC BY-SA 4.0. | Required | **Share-alike / copyleft** (see section 3) | https://wiki.wesnoth.org/Wesnoth:Copyrights |
| Oryx Design Lab (e.g. 16-Bit Fantasy, 24x24) | 24x24 | Commercial pixel art | Proprietary commercial licence | **Required:** "must credit www.oryxdesignlab.com" | Commercial use allowed. **Redistribution forbidden.** Cannot be used to make new artwork for sale or distribution. | https://www.oryxdesignlab.com/license, https://www.oryxdesignlab.com/products/p/16-bit-fantasy-tileset |
| Raven Fantasy Icons (Clockwork Raven) | 16x16, 32x32 and 64x64. 8,000+ icons. | "Classic pixel art with dark outlines". "No generative AI was used". | Proprietary. The free tier covers personal or free projects only. The premium tier ($35) allows commercial use. | "Not necessary but welcome" | Cannot be redistributed or sold as a separate product | https://clockworkraven.itch.io/raven-fantasy-icons |
| 496 pixel art icons for medieval/fantasy RPG (Henrique Lazarini / 7Soul1) | 34x34 | Classic RPG item/skill icons | CC0. The author moved from CC BY 3.0 to public domain, and icons derived from copyrighted games were removed. | Not required | Unrestricted | https://opengameart.org/content/496-pixel-art-icons-for-medievalfantasy-rpg |
| 7Soul's RPG Graphics: Icons (current paid pack, $15+) | 16x16, 1,700+ icons (equipment, skills, food, **status effects**) | Two variants: one for dark backgrounds, one outlined for light backgrounds | **CC BY-ND 4.0** | Required | **No derivatives.** The author said in comments that recolours are acceptable. | https://7soul.itch.io/7souls-rpg-graphics-pack-1-icons |
| Kyrise's Free 16x16 RPG Icon Pack | 16, 32 and 48 px. 300+ sprites from 48+ designs. | Black outlines, styled after classic 16-bit RPGs | CC BY 4.0 | **Required:** "Kyrise's Free 16x16 RPG Icon Pack \| Graphics made by Kyrise: https://kyrise.itch.io/" | Allowed with attribution | https://opengameart.org/content/kyrises-free-16x16-rpg-icon-pack |
| OGA "RPG status icons 16x16 and 8x8" | 16x16 and 8x8 (poison, bleed, burning, buffs, etc.) | n/a | CC BY 3.0 and GPL 3.0 (per the search snippet; UNVERIFIED on the page) | Required | n/a | https://lpc.opengameart.org/content/rpg-status-icons-16x16-and-8x8 |
| OGA "RPG UI Icons" | 16x16 and 32x32 (status, elements, items) | n/a | CC0 (per the search snippet; UNVERIFIED on the page) | n/a | n/a | https://opengameart.org/content/rpg-ui-icons |
| PixelLab (AI generator) | Generates pixel art | n/a | Its terms say "You retain ownership of any content you create" and allow use "for any purpose". The service is "as is", with no warranty of non-infringement. The user carries the legal responsibility. Training models on its outputs needs written permission. | n/a | See the provenance risks in section 3.4 | https://www.pixellab.ai/termsofservice |

### 1.2 Observations for our use

- **Same 16x16 grid as ours:** Kenney 1-Bit, Tiny Dungeon and Tiny Town, 0x72, Kyrise, 7Soul (paid) and Shikashi 600+ all have 16px variants. Raven also has a 16px version. The others are 24 to 34 px (Oryx, 496-pack, Shikashi original, DCSS), so they can serve as layout and silhouette references, not drop-in assets.
- **Safe to reuse directly and easy to record:** the CC0 packs (Kenney, 0x72, the DCSS tiles minus the excluded list, the 496-pack). Attribution is not required, but recording the origin in our store is still good provenance practice.
- **Reusable with obligations:** CC BY (game-icons.net, Kyrise, Shikashi). Shikashi carries a **chained attribution** to game-icons.net, which our provenance record would have to capture as well.
- **Avoid for direct reuse:**
  - 7Soul paid (ND: no derivatives, which clashes with redrawing to our palette).
  - Wesnoth (GPL / BY-SA share-alike).
  - Oryx and Raven (redistribution forbidden; an open-source repo would count as redistribution).
  - The free tier of Raven (non-commercial only).

---

## 2. Palettes (Lospec)

| Palette | Colours | Character (from Lospec descriptions) | Creator / known use | URL |
|---|---|---|---|---|
| Endesga 32 | 32 | Balanced warm earth tones, vibrant accents, cool blues. 205k+ downloads. | ENDESGA. Originally made for NYKRA. A Sprite Pencil preset. | https://lospec.com/palette-list/endesga-32 |
| Endesga 64 | 64 | "High contrast, high saturation", "refined for materialistic pixelart" | ENDESGA. 101k downloads. | https://lospec.com/palette-list/endesga-64 |
| Resurrect 64 | 64 | Organised ramps across warm, cool and neutral tones. 361k downloads. | Kerrie Lake | https://lospec.com/palette-list/resurrect-64 |
| DawnBringer 16 | 16 | Dark #140c1c up to #deeed6. Warm browns, cool blues, greens and reds. Fairly muted. | DawnBringer | https://lospec.com/palette-list/dawnbringer-16 |
| DawnBringer 32 | 32 | Balanced warm and cool tones, from black to white | DawnBringer. **Ships as an Aseprite preset ("DB32")**. | https://lospec.com/palette-list/dawnbringer-32 |
| Sweetie 16 | 16 | Vibrant. Mainly 4 hue-shifted ramps. | GrafxKid. **TIC-80's default palette**. | https://lospec.com/palette-list/sweetie-16 |
| PICO-8 | 16 | Fixed, highly saturated set | Lexaloffle (the PICO-8 fantasy console) | https://lospec.com/palette-list/pico-8 |
| AAP-64 | 64 | Wide range: deep darks, vivid reds and oranges, cool blues, earth tones | Adigun A. Polack | https://lospec.com/palette-list/aap-64 |
| Apollo | 46 | "Perfectly balanced" smooth ramps, tagged 16bit/linear. 206k downloads. | AdamCYounis | https://lospec.com/palette-list/apollo |
| Fantasy 24 | 24 | Warm earth tones, forest greens, sunset oranges, muted teals. Explicitly fantasy/RPG oriented. | Gabriel C | https://lospec.com/palette-list/fantasy-24 |
| Journey | 64 | Lots of magentas, purples and warm oranges. Saturated and dramatic. | 57k downloads. Creator not confirmed (UNVERIFIED). Journey24 (24) and Journey 6 also exist. | https://lospec.com/palette-list/journey, https://lospec.com/palette-list/journey24 |

**Fit for us.** The best natural match for a muted fantasy overworld looks like Fantasy 24, DB16 or DB32, or Apollo. Endesga 64, PICO-8 and Journey are more saturated. This is a judgement from the Lospec descriptions, not a measurement.

### 2.1 Colour-blind suitability

- **No published colour-vision-deficiency (CVD) analysis of these specific palettes was found** (UNVERIFIED / no source). A search turned up general guidance only.
- Lospec does have palettes made for colour blindness, tagged "colorblind": https://lospec.com/palette-list/tag/colorblind. Examples:
  - Krzywinski Colorblind 16 (16 colours, for deuteranopia and protanopia)
  - IBM Color Blind Safe (7)
  - Human16 (16, made for iconography)
  - DeuteroSpill (9)
  - CVD3, CVD6 and CVD8
- Game Accessibility Guidelines: never convey essential information by colour alone. About 8–10% of males have trouble with red/green. Orange versus blue, plus a lightness difference, is a robust default pair. Simulator testing is recommended. Source: https://gameaccessibilityguidelines.com/ensure-no-essential-information-is-conveyed-by-a-fixed-colour-alone/
- Xbox Accessibility Guideline 103 makes the same point: https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/103
- **Implication for rarity and status icons:** pair each rarity colour with a non-colour cue (frame shape, pip count, border pattern). Run the chosen ramp through a CVD simulator, such as the one at https://davidmathlogic.com/colorblind/. Do not rely on any palette being "CVD-safe".

### 2.2 Derive our own palette vs adopt a public one

| | Derive from our 23 adopted terrain tiles | Adopt a public Lospec palette |
|---|---|---|
| Consistency with the live map | Exact. The colours already come from the map's flat fills. | Needs remapping of existing tiles, or a hybrid. |
| Provenance | Fully internal; nothing external to record | External origin to record. The legal risk is low: the US Copyright Office says "mere variations of coloring", including familiar sets of colours, are not copyrightable (Compendium 313.4(K), https://www.copyright.gov/comp3/chap300/ch300-copyrightable-authorship.pdf). Lospec does not state a formal licence per palette (UNVERIFIED). |
| Ramp quality (hue shifting, highlights, accents for loot/rarity) | Terrain fills are usually mid-tones. We would need to add ramps and saturated accents ourselves. | Ramps are already designed (e.g. Sweetie 16's hue-shifted ramps, Resurrect 64's organised ramps). |
| Tooling | Aseprite: "New Palette from Sprite" / "Create Palette from Current Sprite" (https://aseprite.org/docs/tutorial/color-bar-tutorial/). The community reports that Aseprite's extractor can drift from the exact RGB values, and Lua scripts exist to fix this (https://community.aseprite.org/t/new-script-for-perfect-palette-generation-from-rgb-sprite/9043). | Import a .gpl/.ase/.hex file from Lospec. DB32 is built into Aseprite. |

**Suggested hybrid** (my opinion, not sourced):
1. Extract the exact terrain palette as the base.
2. Extend each terrain hue into a 3–4 step ramp.
3. Add a small, CVD-checked accent set for rarity and status. Accents may be borrowed by value from a public palette, and that borrowing should be recorded as reference.

---

## 3. Licensing guidance

### 3.1 Style reference vs copying

- **Copyright protects expression, not ideas or style.** The US Copyright Office looked at protecting artistic style when AI imitates it, and recommended *not* extending protection to style at this time (Copyright and AI, Part 1, https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-1-Digital-Replicas-Report.pdf).
- So studying a pack's outline weight, palette size or shading is safe. Tracing or redrawing specific icons pixel by pixel is copying expression, and needs a licence.
  - This is a general principle; I did not find a specific case on pixel tracing (UNVERIFIED).
  - At 16x16 the gap between independent creation and a copy is narrow. Recording "reference only" sources in provenance helps show independent creation.
- Colour choices alone are not copyrightable (Compendium 313.4(K), link above).

### 3.2 Share-alike (CC BY-SA, GPL)

- **CC BY-SA 4.0 is one-way compatible with GPLv3**: BY-SA material can go into GPLv3, but not the other way (https://creativecommons.org/2015/10/08/cc-by-sa-4-0-now-one-way-compatible-with-gplv3/, https://wiki.creativecommons.org/wiki/ShareAlike_compatibility:_GPLv3).
- CC licences are suitable for "separate artistic elements such as game art", but are not recommended for code (same sources).
- **What gets bound:**
  - ShareAlike applies to **adaptations**. Merely collecting BY-SA work next to other material does not relicense that other material (CC FAQ, https://creativecommons.org/faq/).
  - In practice, a BY-SA icon that we *modify* (recolour or redraw from it) becomes an adaptation, and our derived icon must be BY-SA.
  - Under GPL, the art plus its "preferred form for modification" must be shared, as Wesnoth interprets it (https://wiki.wesnoth.org/Wesnoth:Copyrights).
- **Recommendation:** keep BY-SA and GPL art out of the adopted store unless we are willing to publish those derivatives under the same licence. Using them as reference only is fine.

### 3.3 Attribution recording

- CC's best practice is **TASL**: Title, Author, Source (URL), License (with a link). For adaptations, also:
  - state that the work is modified,
  - credit the adapter,
  - confirm that the licence allows adaptations (ND licences do not).

  Source: https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution
- **Suggested provenance fields per adopted asset:**
  - `origin_kind` (original / reference-only / derived / direct-reuse)
  - title, author, source URL, licence ID (SPDX, e.g. `CC0-1.0`, `CC-BY-4.0`)
  - licence URL
  - upstream attributions (for chains such as Shikashi → game-icons.net)
  - modification note
  - retrieval date
  - AI-used flag
- Even CC0 packs are worth recording, for traceability.

### 3.4 AI-generated art: provenance concerns

- **Copyrightability (US):**
  - Outputs are protected only where a human determined sufficient expressive elements, such as perceptible human input or creative arrangement or modification (US Copyright Office Part 2, 29 Jan 2025: https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf, https://www.copyright.gov/newsnet/2025/1060.html).
  - *Thaler v. Perlmutter* (D.C. Cir., 18 Mar 2025) held that the Copyright Act requires human authorship (https://law.justia.com/cases/federal/appellate-courts/cadc/23-5233/23-5233-2025-03-18.html).
  - Practical effect: raw AI output may be **unprotectable**, so we could not stop others from copying it.
- **Infringement risk:** generator terms, e.g. PixelLab's, disclaim warranties and put responsibility for third-party rights on the user (https://www.pixellab.ai/termsofservice).
- **Steam:**
  - Since January 2024, developers disclose "Pre-Generated" AI content (art and so on that ships with the game) and "Live-Generated" AI content (needs guardrails) in the Content Survey. Much of the disclosure appears on the store page (https://store.steampowered.com/news/group/4145017/view/3862463747997849618).
  - A January 2026 tweak clarified that the disclosure covers content consumed by players, not behind-the-scenes dev tools (https://store.steampowered.com/news/group/4218320/view/506225182828923398, a GamingOnLinux repost; https://www.techpowerup.com/345302/steam-ai-disclosure-gets-clarification-for-ai-in-dev-tools).
- **itch.io:**
  - Asset creators must disclose generative-AI use, and untagged AI assets are de-indexed. Assets that used AI at all, even if hand-edited, must be tagged (https://www.pcgamer.com/software/platforms/indie-distribution-platform-itch-io-now-requires-asset-creators-to-disclose-the-use-of-generative-ai-in-their-work/, https://itch.io/t/4309690/generative-ai-disclosure-tagging).
  - Several packs above (0x72, Raven, Shikashi 600+) advertise "No generative AI was used". That label is a useful provenance signal when picking references.
- **Recommendation:**
  - If AI tools are ever used, record it per asset (an `ai_used` flag plus the tool and its version) so that a Steam or itch disclosure can be produced from the store.
  - Treat AI output as at most a reference or draft that a human redraws in Aseprite.
  - Do not use AI output for reference packs whose own provenance is unknown.

---

## 4. Bottom line

1. For direct reuse at 16px, prefer the CC0 packs (Kenney 1-Bit, Tiny Town and Tiny Dungeon; 0x72; the 496-pack, which is 34px). They need no attribution and are easy to record.
2. game-icons.net (CC BY 3.0) is the richest source of fantasy symbols (classes, status effects, buildings) as silhouette references. If we redraw closely from it, attribution is owed.
3. Avoid reusing ND (7Soul paid), share-alike (Wesnoth) and no-redistribution (Oryx, Raven) packs in the store. They are fine as style reference.
4. Palette: extend our terrain-derived palette with ramps and a CVD-checked accent set, rather than switching wholesale. Fantasy 24, DB32 and Apollo are the closest public references.
5. Rarity and status must not be distinguished by colour alone.
