# Pixel-art technique guide for the Aseprite MCP tools

What the researched guidance says, which tool applies it, and where the sources disagree. Researched
2026-10-02 from public tutorials (links at the end). This is drawing guidance for agents using the tools;
it does not freeze the project's art direction (palette, resolution and style stay human decisions, see
`docs/plans/aseprite-mcp-pixel-art/README.md` "Decisions deliberately unfrozen").

## Recommended workflow for a 16-32px game sprite

1. **Silhouette first.** Block the shape in flat colours (`apply_ops`: `rect`, `ellipse`, `pixels`,
   `stroke`). Check it reads with `silhouette` on a `branch_sprite` copy and `preview` at scale 1.
   If the single-colour shape is not recognisable, shading will not fix it.
2. **Pick ramps before shading.** `make_ramp` per material, 3-5 steps. Reuse one ramp across materials
   where you can.
3. **Shade by light direction.** `shade` with `target: {"color": <flat colour>}`, light `tl`, 3 bands.
4. **Outline.** `auto_outline` (`full` for maximum readability on any background, `selout` for a softer look).
5. **Check.** `lint_sprite`, then `preview` at scale 1 (native) and 8, and `ascii_view` if you cannot see images.
6. **Variants.** `branch_sprite` + `grayscale` / `replace_color` / `remap_palette`; compare with `stamp`.

## Rules and the tool that applies them

| # | Rule | Numbers | Tool |
|---|---|---|---|
| 1 | Ramps shift hue as well as brightness: shadows toward blue/purple, highlights toward yellow/orange | Slynyrd: 9 swatches, +20 degrees per swatch; here default 5 steps, 14 degrees per step, clamped at the target hue | `make_ramp` |
| 2 | Brightness rises steadily along a ramp; saturation peaks mid-ramp and falls at the bright end; never high saturation with high brightness | saturation -40% at the light end, -10% at the dark end | `make_ramp` |
| 3 | Small sprites need few colours | 16px: 3-8 (item 3-4, character 5-6, detailed 7-8); 64px about 16; larger 24+ | `lint_sprite` (`palette_budget`: 8 / 12 / 16 / 24 by canvas side) |
| 4 | Hard value steps, not gradients, at small sizes | exactly 3 levels at 16px: light, mid, dark | `shade` (`bands=3`; 5 for larger forms) |
| 5 | One light direction, usually top-left, used for every sprite | default `light="tl"` | `shade`, `auto_outline` |
| 6 | No pillow shading (shading that follows the outline inward instead of the light) | shading derives from surface normal vs light vector | `shade` |
| 7 | Avoid orphan pixels / noise; think in clusters | a band shared with no 4-neighbour is merged into its neighbours | `shade` (built in), `lint_sprite` (`orphan_pixels`) |
| 8 | Ordered (Bayer) dithering for structured, predictable texture | 2x2, 4x4, 8x8 threshold maps | `dither` |
| 9 | Pixel-perfect lines: no L-shaped double pixels | middle pixel of each L dropped from freehand trace; end points and vertices next to a longer-than-1px segment are kept as intentional corners | `stroke` |
| 10 | Outlines cost pixels at 16px; never double-thick | 1px, 4-neighbour ring | `auto_outline` |
| 11 | Critical distinctions must survive without hue (project rule, ART-W06) | adjacent luma difference under 12/255 is flagged | `lint_sprite` (`value_separation`), `grayscale` |
| 12 | Leave room for overlays at native scale (project rule, ART-W04) | artwork touching the canvas edge is flagged | `lint_sprite` (`touches_edge`) |

## Where the sources disagree (the tools support both; a human decides)

- **Selective vs all-or-nothing outlines.** One source recommends restrained, selective outlines at 16px
  (outline only complex curves, omit straight edges). Another says "either every edge outlined or none, mixed
  reads as unfinished". `auto_outline` offers `mode: full | selout` and `lit_edges: outline | skip`;
  `lint_sprite` reports the dark-edge fraction as *info* (`mixed_outline`), never as a failure.
- **Dithering at 16px.** Guidance for tiny sprites favours hard steps over dithering; dithering is described
  for larger surfaces, tiles and UI. `dither` exists for those; do not reach for it on a 16px character.

## Lessons from using the tools (measured here, not from the web)

- Shading three materials with three bands each gives 9 colours before any detail; a 16px knight shaded this
  way had 12 colours against a budget of 8. Shade the one or two materials that matter, or share a ramp.
- An outline that invents a darkened colour per neighbour multiplied the same knight to 19 colours.
  `auto_outline selout` now reuses a darker colour already in the sprite and only invents one when none exists.
- Greys have no meaningful hue, so "shift toward blue" must set the hue rather than rotate from 0 degrees
  (which walks through magenta). `make_ramp` handles near-neutral bases this way.
- Pixel-perfect cleanup must tell intent from trace. Protecting every vertex you pass in made it a no-op for all inputs (fuzzed: identical output with and without it); the rule is now: ends of an open stroke and vertices next to a segment longer than one pixel are intentional (a closed box keeps its corners), vertices between two single-pixel steps are trace and get cleaned.

## Limits of these tools

Readers (`shade` with a colour target, `dither target_color`, `auto_outline`, `remap_palette`, `lint_sprite`,
`ascii_view`) see the **flattened** frame, not one layer. `remap_palette` therefore refuses sprites with
pixels on more than one layer; the others paint onto the layer you name. Batches are capped at 8192 pixels.
Not provided: anti-aliasing (guidance says avoid it at these sizes), rotation, per-layer readback,
sub-pixel animation, palette-indexed mode.

## Sources

- [Pixelblog 1 - Color Palettes (Slynyrd)](https://www.slynyrd.com/blog/2018/1/10/pixelblog-1-color-palettes): ramp length, hue shift per swatch, saturation and brightness curves
- [How to create 16x16 pixel art sprites (sprite-ai.art)](https://www.sprite-ai.art/guides/how-to-create-16x16-pixel-art): colour counts, three shade levels, top-left light, outline strategies
- [How to make pixel art: a beginner's guide (sprite-ai.art)](https://www.sprite-ai.art/guides/pixel-art-fundamentals): palette size by sprite size, pillow shading, all-or-nothing outlines
- [Ordered dithering (Wikipedia)](https://en.wikipedia.org/wiki/Ordered_dithering): Bayer matrices and threshold formula
- [Aseprite API: Image](https://www.aseprite.org/api/image): drawImage, drawSprite, pixel access
- [Lospec palette tutorials](https://lospec.com/pixel-art-tutorials/tags/palette), [Color Theory for Pixel Art (pixel-editor.com)](https://www.pixel-editor.com/articles/color-theory-for-pixel-art), [Pixel Art Outlines & Anti-Aliasing (pixel-editor.com)](https://www.pixel-editor.com/articles/pixel-art-outlines): search summaries only; the pages themselves did not return readable content, so no specific number here is attributed to them
