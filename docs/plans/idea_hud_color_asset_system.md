---
status: active
layer: frontend
authority: P2
audience: developer
maturity: idea
date: 2026-08-23
tags: [idea, hud, design-system]
---

# Idea: Redesign the Frontend's Data-Visualization Palette — a New Baseline, Not a Consolidation of the Old One

> **Maturity: IDEA** — Not scheduled. Raised while checking whether the HUD design-system effort had
> considered "assets or coloring, palette and scheme" beyond `TCK-20260822-SEMANTIC-TOKEN-LAYER`'s narrow
> scope (the 11 CSS custom properties in `index.css`, used for UI chrome only). Direct investigation found
> a much larger, disconnected color system this project already has, with at least one confirmed,
> already-realized duplication bug and at least one confirmed accessibility failure baked into the current
> values themselves.
>
> **Revision (2026-08-23):** an earlier draft of this doc proposed *consolidating* the existing ~200 hex
> values into one source-of-truth file, preserving their current values. Per direct user instruction —
> reuse isn't a default when a fresh baseline is genuinely better; rebuilding is worth it when it is — this
> is now reframed. The confirmed `COMBAT`/`ALERT` contrast collision (§ below) is a defect *in the current
> values*, not in how they're organized; consolidating them into one file would just centralize a broken
> palette, not fix it. The primary recommendation is now a **newly, systematically generated palette**,
> informed by the real theory/technique researched below, with the file-consolidation architecture as a
> secondary, still-worthwhile structural fix that happens either way.

---

## Problem

`TCK-20260822-SEMANTIC-TOKEN-LAYER` (M1's first child ticket) scopes a Layer 2 semantic token block on top
of `index.css`'s 11 primitive CSS custom properties — but those 11 primitives only cover UI chrome
(panel backgrounds, text, borders, accent colors). They say nothing about, and were never meant to cover,
the much larger color system used for map/entity/game-state visualization, which lives entirely outside the
CSS token system in plain TypeScript constant objects.

**Full inventory, confirmed by direct file reads, not estimated:**

| File | Color tables |
|---|---|
| `frontend/src/constants/colors.ts` (204 lines) | `TILE_COLORS` (23), `TILE_COLORS_DIM` (23), `KIND_COLORS` (~28), `STATE_COLORS` (~17), `RARITY_COLORS` (3), `RESOURCE_COLORS` (~20), `LEGEND_ITEMS` (32 entries), `hpColor()` (3 hardcoded thresholds inline) |
| `frontend/src/components/InspectPanel.tsx` | `HERO_CLASS_COLORS`, `DMG_TYPE_COLORS`, `TRAIT_COLORS`, `TAG_COLORS` — 4 more tables, defined locally in a component file, not the shared constants file |
| `frontend/src/components/EventLog.tsx` | `CATEGORY_COLORS` |
| `frontend/src/components/GameCanvas.tsx` | `BUILDING_COLORS` (module-level) **and a second, separate inline `bColors`** inside a function body |
| `frontend/src/components/BuildingPanel.tsx` | Its own independent `BUILDING_COLORS` |
| `frontend/src/hooks/useCanvas.ts` | Its own independent inline `bColors` |
| `frontend/src/components/ClassHallPanel.tsx` | `CLASS_COLORS`, `GRADE_COLORS`, `GRADE_BG`, `ATTR_COLORS` |

That is at least **9 distinct color-constant tables** across **7 files**, roughly 200+ raw hex values total,
with zero connection to the semantic-token work already merged.

**A confirmed, already-realized duplication bug, not a hypothetical one:** the building-type-to-color
mapping (`store`, `blacksmith`, `guild`, `class_hall`, `inn`, `hero_house`) is independently hardcoded in
**four separate places** — `GameCanvas.tsx`'s module-level `BUILDING_COLORS`, `GameCanvas.tsx`'s own inline
`bColors` inside a different function, `BuildingPanel.tsx`'s independent `BUILDING_COLORS`, and
`useCanvas.ts`'s inline `bColors`. Directly compared all four: three carry identical values for all six
building types including `class_hall: '#c084fc'`; **`BuildingPanel.tsx`'s copy is missing `class_hall`
entirely** — already out of sync, not a future risk. `colors.ts`'s `LEGEND_ITEMS` table separately
re-hardcodes the same hex values a third+ time (e.g. `'Store', '#38bdf8'` duplicates the exact value all
four building-color copies share) rather than referencing any of them.

**`TILE_COLORS_DIM` is a hand-baked duplicate of a simple formula, not an independent design:** computed
the exact RGB-channel ratio between `TILE_COLORS` and `TILE_COLORS_DIM` for 9 sampled pairs (FLOOR, WALL,
WATER, FOREST, MOUNTAIN, LAVA, SNOW, JUNGLE) — every channel of every pair falls in a tight 0.667–0.733
band (mean ≈0.70). This is a ~30%-darken operation, hand-computed once and pasted as a second static
23-entry table, instead of being derived at render time from the single source table.

## Idea

### Frame this as a second, sibling token layer — data-visualization tokens, not UI-chrome tokens

`TCK-20260822-SEMANTIC-TOKEN-LAYER`'s Layer 2 (`surface-panel`, `text-critical`, etc.) is a theming
concern — intent-based names for chrome. The color tables inventoried above are a **categorical-encoding**
concern — mapping a fixed, enumerable domain (terrain type, entity kind, AI state, building type, damage
type, hero class) onto perceptually-distinguishable colors so a player can decode meaning at a glance. These
are different problems with different correctness criteria (a theme just needs internal consistency; a
categorical encoding needs the colors to actually be distinguishable from each other, including under color
vision deficiency) and should not be forced into one token system.

### Why redesign, not just consolidate — the current values are a real baseline to beat, not preserve

Every one of these domains (terrain, entity-kind, AI-state, building-type, etc.) is a genuinely fresh
palette-design problem, not a migration problem: pick each domain's actual category count, generate colors
using a real method (see Technique subsections below — ColorBrewer-style hue spacing, WCAG contrast checked
against this project's real dark background, colorblind-simulation checked before shipping, not after), and
only then decide file layout. The current values were hand-picked incrementally over time with no such
process — that's *why* `COMBAT`/`ALERT`/`GUARD_CAMP` collapsed into near-identical reds and why 28 entity
kinds got 28 individually-chosen hues instead of a structured hue/shade system. A newly-generated palette,
built with the real constraints already researched below, is a much better baseline than anything reachable
by patching the existing values pair-by-pair as collisions get found. The consolidation into one
source-of-truth file (collapsing the confirmed 4-way building-color duplication, the `LEGEND_ITEMS`
triplication, and deriving `TILE_COLORS_DIM` from `TILE_COLORS` via the confirmed ~0.70 formula instead of
hand-maintaining a second table) is still worth doing regardless — it's just the *architecture*, not the
*values*, and happens either way once a real palette exists to put in it.

### Technique: categorical palette size is a real, checkable constraint — and this project already exceeds it

Verified directly against ColorBrewer (colorbrewer2.org, the standard cartography/data-viz categorical
palette tool): its qualitative-palette picker tops out at **12 data classes**. This project's `KIND_COLORS`
table has **~28 entries** and `STATE_COLORS` has **~17** — both well past the point where hue alone can
reliably distinguish categories for a human observer. The practical technique this implies: past ~8-12
categories, color cannot be the *only* encoding channel — pair it with a secondary channel already
available in this codebase (icon shape via `lucide-react`, already used in 10 files; text label; grouping)
rather than expecting 28 individual hues to all read as distinct at a glance.

### Technique: WCAG contrast is a real, computable check — run against this project's real colors, not assumed

Verified the exact WCAG 2.1 non-text-contrast success criterion directly against the W3C source: **"The
visual presentation of ... User Interface Components [and] Graphical Objects [has] a contrast ratio of at
least 3:1 against adjacent color(s)."** Implemented the exact WCAG relative-luminance/contrast-ratio formula
(sRGB channel linearization, `L = 0.2126R + 0.7152G + 0.0722B`, `contrast = (L_light+0.05)/(L_dark+0.05)`)
and ran it against this project's real `STATE_COLORS` values:

- Every tested state color passes 3:1 contrast against the actual background (`#0f1117`) comfortably
  (5.0–11.3:1) — background legibility is not the problem.
- **Pairwise contrast between semantically-adjacent "danger" states is a real, confirmed problem**:
  `COMBAT` (`#f87171`) vs. `ALERT` (`#ff6b6b`) computed at **contrast ratio 1.00** — functionally
  luminance-identical, distinguishable only by a small hue shift both being reddish. `ALERT` vs.
  `GUARD_CAMP` (`#ef4444`) computes to 1.36, `COMBAT` vs. `GUARD_CAMP` to 1.36 — also low. Three distinct
  states a player needs to instantly read as different ("my hero is fighting" vs. "my hero is alarmed but
  not fighting" vs. "a camp guard is on alert") currently render as near-identical shades of red. This is
  a real, computed finding against this project's actual shipped color values, not an inferred risk.

### Technique: colorblind simulation is a real, named, correctly-citable algorithm — not run here, but namable

Verified the correct citation (an earlier casual mention got the year wrong): **Brettel, H., Viénot, F., &
Mollon, J.D. (1997), "Computerized simulation of color appearance for dichromats," Journal of the Optical
Society of America A, 14(10), 2647–2655** — not 1999. This is the standard confusion-line-based algorithm
real colorblind-simulation tools implement (e.g. `daltonlens.org`'s open documentation of the same
technique). Not run against this project's palettes in this pass — flagged as the concrete follow-up check
once a real simulation implementation or tool is chosen (see Open Questions), since the WCAG-luminance
check above already surfaced a real problem using a simpler, fully-verified method first.

### Assets — checked, not a gap

Icons come from `lucide-react` (confirmed dependency, used in 10 files) — React SVG-icon components, no
raster images or loose SVG files checked into the repo, no asset pipeline needed. This part of "assets or
coloring" is in reasonable shape already; the color/palette half is where the real gap is.

## Architecture Constraints

- This is a data-visualization/categorical-encoding concern, distinct from `TCK-20260822-SEMANTIC-TOKEN-LAYER`'s
  UI-chrome theming concern — must not be folded into that ticket's Layer 2 semantic tokens as if they were
  the same problem.
- The *category assignments* must be preserved (which terrain types, entity kinds, and AI states exist, and
  which one a player currently associates with "roughly this color family" — e.g. danger states staying in
  the red/orange family, resource nodes staying green-ish) — but the *exact hex values* are explicitly not
  preserved as a constraint, per the revision above. A newly-generated, verified-distinguishable palette
  within the same rough color families a player already recognizes is the goal, not bit-for-bit hex
  preservation.
- Frontend-only (`frontend/src/**`) — no backend/`AuthoritativeState` changes implied.

## Relationship to Planned Tickets

- `TCK-20260822-SEMANTIC-TOKEN-LAYER` — sibling, not overlapping: that ticket's Layer 2 tokens are UI-chrome
  theming; this idea's data-visualization tokens are categorical encoding. Both could eventually live under
  the same `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` umbrella as separate scope, but that's a future
  decision, not made here.
- `docs/plans/idea_hud_quality_measurement.md` — sibling idea doc from the same investigation thread;
  that doc's Density Legibility metric family and this doc's WCAG-contrast findings are related (both are
  about whether the HUD reads correctly at a glance) but distinct concerns (one is layout/information
  density, this one is the underlying color encoding).
- No ticket created or modified by this doc.

## Open Questions

- Whether `frontend/src/constants/palette.ts` (or wherever unification lands) should be organized by
  *domain* (terrain, entity-kind, state, building) as separate exported tables, or as one larger structured
  object — not decided here, a real design choice for whoever picks this up.
- Whether the confirmed `COMBAT`/`ALERT`/`GUARD_CAMP` near-collision should be fixed by changing one or more
  of those three colors, or by adding a secondary cue (icon/pattern) instead of relying on color alone —
  both are valid fixes, not decided here.
- Whether a real colorblind-simulation pass (Brettel-Viénot-Mollon, correctly cited above) should run
  against all ~200 color values in this project, or only the ones proven high-stakes by the WCAG-contrast
  check first (the approach this doc itself took, computing the simpler check before proposing the more
  expensive one) — the latter seems more consistent with this project's own "real evidence before broad
  claims" discipline, but not decided here.
- No frontend tooling exists today to run either WCAG-contrast or colorblind-simulation checks
  automatically (e.g. as a lint rule or CI check) — whether this becomes a one-time audit or a standing
  automated gate is a real follow-up question, not investigated here.
- `KIND_COLORS`'s ~28 entries and `STATE_COLORS`'s ~17 both exceed ColorBrewer's practical ~12-class
  qualitative ceiling — whether the fix is a secondary encoding channel (icon/shape, as suggested above) or
  grouping related kinds under fewer parent hues (e.g. all goblin variants share a hue family, distinguished
  by shade) is a real design decision, not made here.

---

## References

- `frontend/src/constants/colors.ts`, `InspectPanel.tsx`, `EventLog.tsx`, `GameCanvas.tsx`,
  `BuildingPanel.tsx`, `useCanvas.ts`, `ClassHallPanel.tsx` — all read directly to build the inventory above.
- WCAG 2.1 Success Criterion 1.4.11 (Non-text Contrast) — **verified directly against the W3C source**
  (`w3.org/WAI/WCAG21/Understanding/non-text-contrast.html`), exact quote captured above.
- ColorBrewer (`colorbrewer2.org`) — **verified directly**: qualitative-palette picker's practical ~12-class
  ceiling, colorblind-safe filter option confirmed present; the tool's underlying palette-generation
  algorithm itself was not exposed by the fetched page and is not claimed as verified.
- Brettel, H., Viénot, F., & Mollon, J.D. (1997), "Computerized simulation of color appearance for
  dichromats," *Journal of the Optical Society of America A*, 14(10), 2647–2655 — **year corrected** from an
  initial casual "1999" reference to the verified real publication year.
- `docs/plans/idea_hud_quality_measurement.md` — the sibling idea doc this one follows from, including its
  own fact-checking discipline (verify claims against primary sources before citing them as fact), applied
  here from the start rather than as a later correction pass.

*Raised: 2026-08-23, following a direct question about whether the HUD design-system effort had considered
assets/coloring/palette, and a subsequent investigation that found a real, previously-uncatalogued gap.*
