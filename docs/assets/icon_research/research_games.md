---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# Visual language and icon systems in comparable games: research for a 16px observer-sim icon set

Research date: 2026-10-06. Every factual claim has a source URL. Anything I could not confirm from a source is marked **UNVERIFIED**. Pixel sizes for commercial games often come only from modding docs or fan wikis, so treat them as "authoring size" rather than "guaranteed on-screen size".

---

## 1. Per-game findings

### Battle for Wesnoth (hex, 72px, layered terrain: the model for our terrain fringes)
- **Sizes:** terrain tiles and unit sprites are both 72x72 px canvases ([Tiles Tutorial](https://wiki.wesnoth.org/Tiles_Tutorial), [Creating Unit Art](https://wiki.wesnoth.org/Creating_Unit_Art)).
- **Conventions:** light comes from the upper right, and units face lower right with their feet about 55 px from the top ([Creating Unit Art](https://wiki.wesnoth.org/Creating_Unit_Art)). The map has a base layer and an overlay layer (plants, buildings, villages) ([TerrainMacrosWML](https://wiki.wesnoth.org/TerrainMacrosWML)).
- **Ownership and markers:** a team-coloured ellipse sits under each unit ([SingleUnitWML](https://wiki.wesnoth.org/SingleUnitWML)). A captured village shows an animated team-coloured flag ([SideWML](https://wiki.wesnoth.org/SideWML), [GameConfigWML](https://wiki.wesnoth.org/GameConfigWML)). Unit sprites are drawn with a specific magenta "TC" palette that the engine recolours per team ([Team Color Shifting](https://wiki.wesnoth.org/Team_Color_Shifting)).
- **Status:** there are only four unit statuses (poisoned, slowed, petrified, invisible), each with a small icon image (`misc/poisoned.png` and so on). When a unit has more than one, the UI used to show only the first; it now adds an ellipsis and puts the rest in a tooltip ([issue #3197](https://github.com/wesnoth/wesnoth/issues/3197)). That is a real lesson in overflow handling.
- **Accessibility:** a recent GitHub issue asks not to use the mid/average team colour for UI elements ([issue #11526](https://github.com/wesnoth/wesnoth/issues/11526)), and team colours were revised in 1.19 ([PR #11492](https://github.com/wesnoth/wesnoth/pull/11492)). A dedicated colour-blind mode is **UNVERIFIED**.

### Dwarf Fortress (Steam premium)
- **Sizes:** sprites are 32x32. Large creatures spill into neighbouring tiles, and text is not the same size as the sprites ([Shacknews](https://www.shacknews.com/article/110491/dwarf-fortress-is-coming-to-steam-with-actual-graphics)). The tileset was made by Michał "Mayday" Madej and Patrick "Meph" Schroeder ([Variety](https://variety.com/2019/gaming/news/dwarf-fortress-steam-itchio-1203162351/)). Mayday's earlier community tileset was 16x16 ([DFFD](https://dffd.bay12games.com/file.php?id=7025)).
- **Reception:** opinion is mixed. Some Steam users call the graphics "REALLY bad" ([Steam discussion](https://steamcommunity.com/app/975370/discussions/0/3727323242810735222)). Community sprite tools check "palette, outline, proportions, stray pixels, readability" ([df-sprite-studio](https://github.com/Hearnoevil343/df-sprite-studio)).
- **Not confirmed:** how quality and rarity are signalled visually in the premium version, and whether it has a colour-blind mode. Both are **UNVERIFIED**.

### Caves of Qud (strictest palette discipline)
- **Grid and palette:** tiles are 16x24 px on an 80x25 grid. Each tile uses at most 3 of the game's **18 fixed colours** (primary, detail, background) ([Official wiki: Visual Style](https://wiki.cavesofqud.com/wiki/Visual_Style)). Modders describe the tiles as 2 colours plus transparency ([Custom Player Tiles](https://wiki.cavesofqud.com/wiki/Modding:Tutorial_-_Custom_Player_Tiles)).
- **Criticism:** the default view on Switch is described as "tinyyyy" ([Nintendo Life](https://www.nintendolife.com/reviews/switch-eshop/caves-of-qud)). Players ask for bigger tiles and more zoom levels ([Steam](https://steamcommunity.com/app/333640/discussions/2/541906348054033960/?l=english)). Busy terrain can hide enemies ([Steam](https://steamcommunity.com/app/333640/discussions/0/3570700856112361164/)).
- **Lesson:** a hard palette gives instant coherence, but with low-contrast terrain behind them, small icons get lost.

### RimWorld (the best-documented "icon, not illustration" philosophy)
- **Sizes:** vanilla art is 64 px per tile, and newer DLC uses 128 ([RimWorld wiki: Textures](https://rimworldwiki.com/wiki/Modding_Tutorials/Textures)).
- **Style rules** ([RWModdingResources artstyle.md](https://github.com/spdskatr/RWModdingResources/blob/master/artstyle.md)):
  - Items and buildings get a thick black outline, about 2 px per 64 px of tile.
  - Pawns get thicker outlines than items.
  - Plants get a dark-green outline or none, so they recede.
  - Use few or no black inlines.
  - Details under 3 px wide are wasted unless they have high contrast.
  - Story-relevant objects must stand out, and unimportant ones should recede.
- **Tynan's philosophy:** "RimWorld has graphics like a novel has a typeface" (same source). He also borrowed the Prison Architect style ([Ludeon forum](https://ludeon.com/forums/index.php?topic=2325.0)).
- **Quality tiers:** 7 tiers, Awful through Legendary ([wiki](https://rimworldwiki.com/wiki/Quality)), shown as text. Colour-coding comes from mods ([Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=2801204005)).
- **Colour blindness:** a mod adds support ([GitHub](https://github.com/Scurvyez/ColorBlindness)). Players report the game works fairly well without colour vision because it relies on text and icon shapes ([Steam](https://steamcommunity.com/app/294100/discussions/0/1735468061758912803/)).

### Songs of Syx (the counter-example for "too small")
- **Sizes:** each person gets roughly 10 px, built from 7 layered parts ([GamingOnLinux](https://www.gamingonlinux.com/2019/09/songs-of-syx-the-pixel-art-city-builder-with-an-epic-scale-now-has-a-steam-page-and-newer-demo/)).
- **Criticism:** players say things look blurred on high-resolution displays, doors are hard to tell apart, foliage needs a special map mode, and the game lacks medium zoom levels ([Steam](https://steamcommunity.com/app/1162750/discussions/0/3038230013016785254/), [Zoom Levels](https://steamcommunity.com/app/1162750/discussions/2/4637114871638452043/)).

### Majesty / Majesty 2 (closest genre match: indirect-control heroes)
- **Core mechanic:** the player places reward flags (explore, attack, protect, fear), and heroes decide for themselves whether to take them. Rangers lean toward explore flags and warriors toward attack flags ([Majesty 2 wiki](https://majesty2.fandom.com/wiki/Indirect_Control), [GameBanshee](https://www.gamebanshee.com/previews/29171-majesty-2-the-fantasy-kingdom-sim-preview/page-2.html)). The flag is the key map marker, and it reads as an "incentive" icon.
- **Criticism of Majesty 2:** a generic HUD, and key information hidden behind tabs, where the original showed it all in one main tab ([RPG Codex](https://rpgcodex.net/forums/threads/majesty-2-sucks-massive-multi-headed-dongs.36428/)).
- **Majesty Gold HD:** "cartoony" sprites. Classes are recognised by silhouette, and guild buildings map to classes ([GameFront](https://www.gamefront.com/news/majesty-gold-hd-the-gamefront-retro-review)).
- **Not confirmed:** sprite pixel sizes. **UNVERIFIED**.

### Kenshi
- **Map markers:** the world map draws only 8 marker types (Town, Village, Outpost, Camp, Workcamp, SmallPlace, Ruin, Nest) ([kenshi.zone](https://kenshi.zone/en/map-taxonomy)).
- **Criticism:** the vanilla icons are "too detailed and hard to look at, especially the camp icon". Mods replace them with simple, US National Park Service-style pictograms ([Pictographic Map Symbols](https://steamcommunity.com/sharedfiles/filedetails/?id=3380758937), [Simple Map Markers](https://steamcommunity.com/sharedfiles/filedetails/?id=1640096531)). Colour-blind players report trouble finding their own squad on the map ([Steam](https://steamcommunity.com/app/233860/discussions/0/6629936499882220705/)).
- **Lesson:** a small, closed set of map-marker kinds, each drawn as a pictogram.

### Dungeon Crawl Stone Soup
- **Tiles:** 32x32 in a top-down three-quarter view, with 3000+ tiles (6000+ with the supplemental set) based on RLTiles ([OpenGameArt](https://opengameart.org/content/dungeon-crawl-32x32-tiles), [tiles_creation.txt](https://crawl.akrasiac.org/docs/develop/tiles_creation.txt)).
- **Item colours by meaning:** white means random artefact, light blue means unrandart or highly beneficial, blue means unidentified magical, and light grey means plain ([CrawlWiki: Item](http://crawl.chaosforge.org/Item)).
- **Rarity in tiles:** artefacts get a tile change, not just a colour ([CrawlWiki: Tips](http://crawl.chaosforge.org/Tips_and_tricks)).

### Shattered Pixel Dungeon / Pixel Dungeon
- **Sizes:** Watabou's original art is tagged 16x16 (GPLv3) ([OpenGameArt](https://opengameart.org/content/pixel-dungeon-graphics-by-watabou)).
- **Recent work:** v3.1.0 tweaked colours on health bars, inventory buttons and flare effects for colour-blind players ([v3.1.0 blog](https://shatteredpixel.com/blog/shattered-pixel-dungeon-v310.html)). v4.0.0 redrew the consumables' sprites ([v4.0.0 blog](https://shatteredpixel.com/blog/shattered-pixel-dungeon-v400.html)).
- **Not confirmed:** buff icon size and the enchantment glow appearance. **UNVERIFIED**.

### Stardew Valley (the reference for quality overlays)
- **Sizes:** 16x16 tiles and items and 16x32 characters, rendered at 4x ([Stardew forums](https://forums.stardewvalley.net/threads/sprite-sizes-character-sheets-pixel-art.5597/)).
- **Quality:** shown as a coloured star in the bottom-left corner of the item icon. No star means basic, then silver, gold and iridium (purple) ([wiki: Item Quality](https://stardewvalleywiki.com/User:IBugOne/Item_Quality), [Crops](https://stardewvalleywiki.com/Crops)).
- **Lesson:** a corner badge that differs in both colour and shape, which suits our E..SSS grades.

### Darkest Dungeon
- **Status icons:** small icons under each hero. Bleed is a red drop and Blight a green drop (the same shape in a different colour). Stun is a yellow crescent with diamonds above the head, and buffs are two blue up-arrows. Hovering gives the details ([DD wiki: Status effects](https://darkestdungeon.fandom.com/wiki/Status_effects)).
- **Criticism:** players want important numbers visible without hovering ([Steam](https://steamcommunity.com/app/262060/discussions/0/618463106377603514/)).
- **Rarity:** trinket rarity is signalled by colour and description ([official wiki](https://darkestdungeon.wiki.gg/wiki/Trinkets_(Darkest_Dungeon))). The exact colours are **UNVERIFIED**.
- **Accessibility note:** bleed and blight differ only by colour, which is exactly what accessibility guidance warns against (see section 2).

### Loop Hero
- **Resolution:** native 960x540 with 16x16 tiles ([Steam thread](https://steamcommunity.com/app/1282730/discussions/0/3114771735680378568/)).
- **Palette:** a fan-derived palette has 16 colours ([Lospec](https://lospec.com/palette-list/loop-hero)).
- **Rarity:** grey, blue, yellow, orange, where each tier adds one more stat line ([Steam](https://steamcommunity.com/app/1282730/discussions/0/3115899349866538613/)). Players complain that higher rarity is not always better ([Steam](https://steamcommunity.com/app/1282730/discussions/0/3133918821799882499/)).
- **Lesson:** make sure the rarity colour means the same thing everywhere.

### Wildermyth
- **Style:** a papercraft look with "thickness" lines and comic panels ([Turn Based Lovers](https://turnbasedlovers.com/review/wildermyth-2/)). Overland events use icons such as a red sword for assaults ([wiki: Modding site activities](https://wildermyth.com/wiki/Modding_site_activities)).
- **Fit:** not pixel art, so it is relevant mainly for the event-marker vocabulary.

### Ultima IV and early CRPG overland maps
- **Tiles:** 256 tiles, each 16x16 at 4 bits per pixel (the 16-colour EGA palette). Towns, castles and dungeon entrances are single tiles on the world map ([Ultima Codex](https://wiki.ultimacodex.com/wiki/Ultima_IV_internal_formats), [jtauber](https://jtauber.github.io/game-hacking/ultima4_pc/)).
- **Relevance:** this is the direct precedent for points of interest drawn as a terrain-sized 16px tile.

### Other observer, colony and auto-hero sims
- **Kairosoft Dungeon Village:** adventurers act on their own and then visit town shops. Simple retro isometric pixel art ([Kairosoft wiki](https://kairosoft.fandom.com/wiki/Dungeon_Village), [Steam](https://store.steampowered.com/app/1859360/Dungeon_Village/)).
- **Legends of Idleon:** multiple, inconsistent rarity ladders (Bronze → Silver → Gold → Platinum → Dementia for obols) ([gist guide](https://gist.github.com/shnaps/161a370ed795e6141e0553eb30ddc8fa)). This is a counter-example for consistency.
- **Going Medieval:** thought icons whose meaning is carried by colour (green good, red bad) cause confusion, and players had to compile glossaries ([Steam](https://steamcommunity.com/app/1029780/discussions/0/796716542888816654/)).
- **Against the Storm:** the "pretty but unreadable" ornate UI was replaced with a cleaner one on dark backgrounds, and resource icons were updated for readability ([Eremite: Interface Update](https://eremitegames.com/interface-update/)).
- **"Hero Simulator":** not researched. **UNVERIFIED**.

---

## 2. Cross-cutting patterns

1. **Use a closed set of marker kinds and draw them as pictograms.** Kenshi's detailed icons were replaced by players with simple National Park Service-style glyphs. Ultima used one tile per point of interest.
2. **Use outline weight to set importance.** RimWorld uses a heavy outline for story-relevant things and little or none for background. Wesnoth's ellipse separates units from terrain.
3. **Signal quality and rarity with a redundant corner badge plus colour.** Stardew's star changes colour and position is fixed. DCSS changes the tile itself for artefacts. Keep one ladder for the whole game, unlike Idleon.
4. **Colour must never be the only cue.** Guidance: "Ensure no essential information is conveyed by a colour alone" ([Game Accessibility Guidelines via IGDA GA-SIG](https://igda-gasig.org/how/game-accessibility-top-ten-se/)). Darkest Dungeon's bleed/blight and Going Medieval's thought icons are the cautionary cases.
5. **Plan status overflow.** Wesnoth uses an ellipsis plus tooltip. Darkest Dungeon is criticised for hiding numbers behind hover.
6. **Respect minimum readable size.** Songs of Syx at about 10 px per person and Caves of Qud's "tiny" default show the floor. RimWorld notes that details under 3 px are wasted.
7. **Pair limited palettes with dark, plain UI backgrounds.** Against the Storm moved to dark backgrounds for readability. Caves of Qud uses 18 fixed colours.

---

## 3. Style directions for this project (16px tiles, observer sim)

### A. "Ultima/Loop Hero tile-native" (16px, low-colour pictograms)
- **Exemplars:** Ultima IV, Loop Hero, Pixel Dungeon, Stardew item art.
- **Icons:**
  - Map markers (enemy_camp, shrine, dungeon_entrance and so on) are drawn at **16x16** on the same grid as terrain.
  - Item and status icons are also 16x16, and UI tab icons are 16 px shown at 2x (32 on screen).
  - Use a 16 to 32 colour palette (Lospec-style), a 1 px dark outline, and integer scaling only.
- **Pros:** one grid; markers sit naturally on the map; cheap to draw in Aseprite; maximum coherence with the existing terrain-v1 set.
- **Cons:** 16 px is tight for distinguishing 6 classes, rarity frames and status effects, and needs hard simplification. Detail inside a 16 px marker is lost at zoomed-out map views.
- **Sizes:** 16 (map, items, status) and 16@2x (UI).

### B. "RimWorld/Kenshi-fix pictogram" (16px map glyphs plus 24px UI icons, heavy outline hierarchy)
- **Exemplars:** RimWorld's outline rules, the Kenshi pictographic-marker mods, Majesty's flags.
- **Icons:**
  - Map POIs and buildings are bold silhouette glyphs at 16 px with a 2 px outline or a backing plate (Wesnoth-ellipse-style) so they pop off busy terrain fringes.
  - Panel icons (items, buildings, classes) are **24x24**, and status icons are 12 or 16 px.
  - Outline weight encodes importance: heroes and bosses heaviest, buildings medium, decor none.
- **Pros:** the best readability at map zoom-out; it scales to React UI sizes (24 matches Lucide's default 24 px grid, which eases the swap from placeholders); colour-blind robust because shape carries the meaning.
- **Cons:** two size families to keep consistent; less "pretty", more diagrammatic.
- **Sizes:** 16 (map glyph and status) and 24 (UI and items).

### C. "Caves of Qud strict palette" (16px wide, 2–3 colours from a fixed ~16–18 colour palette)
- **Exemplars:** Caves of Qud, plus DCSS colour-by-meaning.
- **Icons:**
  - Every icon uses a primary, a detail and a transparent background.
  - Meaning is encoded by colour role (for example, all item rarity via the detail colour, mirroring DCSS white/blue/grey) **plus** a corner pip for colour-blind redundancy.
- **Pros:** extremely coherent; fast to produce; recolourable at runtime (Wesnoth TC-style magenta keys could drive grade colours E..SSS from one base sprite).
- **Cons:** the "tiny" and busy-surface criticisms; needs strong contrast against the 23 terrains; a hard colour budget limits class flavour.
- **Sizes:** 16 for everything, displayed at 2–3x.

### D. "Stardew/Darkest Dungeon badge system" (32px items and portraits, 16px overlays)
- **Exemplars:** Stardew's quality stars, Darkest Dungeon's under-bar status strip, Wesnoth's team-colour shifting.
- **Icons:**
  - Item, loot, class and building icons in panels are **32x32** for richer detail and rarity frames.
  - On the map, units and POIs stay at 16 px.
  - Grade and rarity is a corner badge whose shape changes with tier (dot, star, crown for S/SS/SSS) plus a frame colour.
  - Status effects are 8–10 px pips in a strip with ellipsis overflow.
- **Pros:** room for the E..SSS ladder and class identity; a familiar RPG feel; UI panels look good at web resolutions.
- **Cons:** the most drawing work (32 px is about 4x the pixels of 16); a risk of a style split between the 16px map and the 32px UI; badge sizes must be unified.
- **Sizes:** 16 (map), 32 (UI and items), 8 (status pips and grade badges).

**Overall:** B or a B/D hybrid fits an observer sim best. The user watches a zoomed-out map, so map glyphs must survive 16 px on busy Wesnoth-style fringes. Panel icons can go larger, and every tier and status needs a shape cue as well as colour.
