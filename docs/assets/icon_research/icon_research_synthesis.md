---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation, hud]
---

# Icon set: research synthesis (asset-planner, 2026-10-06)

Inputs: research_games.md, research_icon_craft.md, research_packs_palettes.md (same folder, `docs/assets/icon_research/`; every claim
sourced there). This file is the planner's reading of them plus repo facts.

## What needs icons (repo facts)
- Map locations (GameCanvas LOCATION_TYPE_ICONS, emoji today): enemy_camp, resource_grove, ruins,
  dungeon_entrance, shrine, boss_arena.
- Buildings (BuildingPanel, Lucide): store, blacksmith, guild, inn, hero_house, class_hall.
- Classes (ClassHallPanel, Lucide): warrior, ranger, mage, rogue.
- Grades E, D, C, B, A, S, SS, SSS (colour-only today: GRADE_COLORS). Loot rarity (colour-only: RARITY_COLORS).
- Status effects, UI tabs (stats, narrative, class, effects, quests, events, AI).
- Today grades and rarity break the project rule "no critical distinction is hue-only".

## Agreed across all three reports
1. Shape, not colour, carries meaning. Rarity, grades, buff/debuff and marker state each need a
   non-hue cue (frame shape, pips, letters, arrows, badges). GAG + Xbox 103 + our AM5-S agree.
2. Silhouette first; abstract concepts (AI, narrative, quest) keep a text label or tooltip.
3. Lock 3-5 key icons first, then draw the rest against them (same as terrain-v1's draft-set flow).
4. Integer scaling only. Map zoom currently steps 0.15 (GameCanvas.tsx:35), so tiles and markers
   render at fractional scales; pixels come out uneven. Affects terrain-v1 already.
5. Draw our own. Copyright protects expression, not style; reference is fine, redrawing a specific
   icon is copying.

## Style directions (from research_games.md section 3)
- A. Tile-native: everything 16px (Ultima IV, Loop Hero). Most coherent with terrain-v1; tight for tiers.
- B. Pictogram: 16px map glyphs on a backing plate + 24px panel icons; outline weight = importance
  (RimWorld, Kenshi map-marker mods, Majesty flags). Best map readability; 24 fits the Lucide grid.
- C. Strict palette: 16px, 2-3 colours per icon from a fixed palette (Caves of Qud). Fast, recolourable.
- D. Badges: 16px map, 32px panel art, 8px tier/status pips (Stardew, Darkest Dungeon). Richest, most work.

## Planner recommendation
B with D's badge ladder:
- Map: 16x16 glyph inside a shared per-category plate (location vs building), 1px safe margin,
  state shown by a badge (cleared, hostile), not a tint.
- Panels: 24x24 for buildings, classes, item types.
- Tiers: one 8x8 badge ladder, shape escalates (E-D plain, C-B pips, A frame, S/SS/SSS stars),
  colour secondary; the letter stays in text beside it.
- Status: 12 or 16px, buff and debuff frames differ in shape (up/down chevron), stack digit.
- Palette: terrain-v1 derived base + 3-4 step ramps + a small accent set, checked with a sheet-level
  colour-vision rule (an icon analogue of AM5-S; lint_sprite value_separation is per-sprite only).
- Outside art: reference only, recorded by title/author/source/licence; no direct reuse, no AI generators.

## Open decisions for the owner
1. Style direction (A/B/C/D or hybrid).
2. Palette basis.
3. Outside art policy.
4. Map zoom: snap to integer scales (a frontend change), or accept fractional.

## Known gaps in the research (UNVERIFIED in the reports)
Majesty/Kenshi/Wildermyth pixel sizes; Darkest Dungeon rarity colours; Pixel Logic book and
Brandon James Greer videos not readable; no published colour-blind analysis for any Lospec palette.
