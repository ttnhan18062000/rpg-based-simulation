---
status: active
layer: frontend
authority: P2
audience: developer
maturity: idea
date: 2026-08-23
tags: [idea, hud, design-system, rendering]
---

# Idea: Frontend Canvas Render Tiers — Shared Pipeline, Not Three Separate Renderers

> **Maturity: IDEA** — Not scheduled. Sits between two existing efforts without being either: the HUD
> design-system work (`docs/plans/hud_delivery_roadmap.md`) explicitly does not touch `GameCanvas.tsx`/
> `useCanvas.ts`; the live-map reconnection/scaling work (`docs/plans/live_map_scaling_roadmap.md`) is
> about performance and data-plumbing, not visual fidelity. This doc is the map-canvas visual-quality
> question neither covers, raised directly by the user: better visuals (icons/effects) for the live canvas,
> with multiple render tiers that share components rather than tripling the renderer.

---

## Problem

**The live frontend canvas has zero icon/sprite rendering today — confirmed by reading the real draw calls,
not assumed.** Every `ctx.` draw call in `GameCanvas.tsx` and `useCanvas.ts` is a primitive: `arc()` for
entity dots, `fillRect()` for tiles/buildings/HP-bar backgrounds, `fillText()` for ID labels and building
initials, `beginPath()`/`moveTo()`/`lineTo()`/`stroke()` for fog-of-war and attack-range grid lines. The
only `drawImage()` call in either file targets the pre-rendered off-screen minimap terrain cache — not a
single entity, building, or item is drawn from an image or icon anywhere.

**This directly corrects a claim in a sibling doc.** `docs/plans/world_rendering/idea_world_rendering_core.md`'s
drawing-tool comparison table lists "Reconnecting/extending the existing React+Canvas frontend" as
"Already has entity icons, HP bars, interpolation, a minimap." HP bars, interpolation, and the minimap are
real and confirmed. **Entity icons are not** — verified directly against the actual draw calls above. Worth
fixing in that doc too if this idea is picked up, since it's an inaccurate premise for anyone deciding
whether to extend vs. replace the frontend.

**A server-side "fast, simple, no polish" render mode already exists — just not for the frontend.**
`src/rendering/render.py` (shipped, `TCK-20260821-WORLD-RENDER-CORE`) renders `AuthoritativeState` to flat
per-tile pixel colors — no icons, no anti-aliasing, no effects, deterministic, benchmarked fast (10.87x
speedup via `DirtySet` incremental caching, 7.5x via numpy if adopted). This is exactly the "best
performance, simplest, for visual measurement" tier — it just lives server-side, batch-only, for
SimQ-sibling automated quality scoring (`docs/plans/world_rendering/idea_world_render_validation.md`), not
as a frontend-selectable live view.

**The architecture principle for this is already chosen — just not yet applied to the frontend.**
`idea_world_rendering_core.md` explicitly picked "Option C — shared core, two modes (batch PNG generator or
live streaming/delta feed), one renderer, thin clients" specifically to avoid "every client... re-implementing
tile decoding and entity drawing independently, repeating the exact duplication this project's own
architecture principle already warns against." That reasoning applies without modification to render
*tiers* within the frontend itself, which is exactly what this idea proposes extending it to.

## Idea

### Not three renderers — one pipeline, tier flags

Directly reusing the real pattern game engines actually use for quality settings (Unity's Built-in Render
Pipeline: tiers select which features are enabled within *one* pipeline via shader-variant flags, not
separate pipelines per tier) — the fix here is a single draw pipeline with per-layer feature toggles, not
three parallel component trees:

| Tier | Icons/sprites | Effects (glow, transitions, particles) | Anti-aliasing/gradients | Primary use |
|---|---|---|---|---|
| **Measurement** (mirrors `src/rendering/render.py`'s existing shape) | off | off | off | Automated visual-quality metrics, debug view, lowest CPU cost |
| **Current** (what exists today) | off | off | off (flat fills) | Baseline — this is `GameCanvas.tsx`/`useCanvas.ts` as they are now |
| **Polish** | on | on | on | Default player-facing experience once built |

Not fixed at exactly three — the table above is a proposed default informed by what's already real
(measurement mode already exists server-side; current mode is what's shipped), not a hard ceiling. A fourth
"reduced-motion/accessibility" tier (effects off, icons on) is a real candidate once real usage data exists,
not proposed as scope here.

**Shared abstraction, reused across every tier:** the existing server-side `DRAW_ORDER = ("terrain",
"buildings", "blocked_outline", "entities")` convention (`src/rendering/render.py`) — an explicit, fixed
compositing order, not implicitly derived from iteration order — is the right shared contract for the
frontend pipeline too. A tier-aware frontend renderer would walk the same ordered layer list, with each
layer's *draw function* swapped by tier (flat-fill vs. sprite-blit) while the *layer order and selection
logic* (which tiles/entities are visible, what to composite over what) stays identical across all tiers.
This is the concrete mechanism for "reuse, not triplicate": one iteration/selection layer, pluggable draw
functions per tier.

### Icons don't have to cost performance — verified, not assumed

The naive assumption ("primitives are cheap, images are expensive") is backwards at scale for canvas
rendering, confirmed against real web-performance research: canvas *path* operations (the `arc()` calls this
project's entity dots use today) are CPU-bound per-call, while `drawImage()` blits are comparatively cheap —
especially when the source image itself is pre-rendered once to an off-screen canvas and reused every frame,
the exact caching pattern this project's own minimap terrain cache already uses for a different layer. At
this project's real ~10,000-entity target scale (cited throughout the HUD/live-map roadmaps), a "polish"
tier built on pre-rendered sprite caching is not guaranteed to be slower than today's per-entity `arc()`
calls — it needs real measurement once built, but the assumption that icons are inherently a performance
tax on top of "current" mode doesn't hold up against how canvas rendering actually performs.

### What "icon" should mean here — reuse what already exists, don't add a new asset pipeline

`lucide-react` (confirmed dependency, used in 10 HUD-panel files) is React-component-based, not directly
usable inside a raw canvas `drawImage()` call — but the same icon set can be pre-rendered to an off-screen
canvas once (rendering the SVG to a bitmap) and cached, reusing exactly the caching pattern above, rather
than introducing a second icon library or a sprite-sheet asset pipeline this project doesn't have today
(confirmed: no image/SVG asset files exist in `frontend/src` or `frontend/public`, per the sibling color-
system investigation). This keeps "assets" a non-gap, consistent with what that investigation already found.

### Effects — genuinely open, not researched in this pass

"Effect" (glow, transitions, particle-style flourishes) wasn't investigated in this pass — flagged as a
real, separate follow-up rather than bundled into this doc's icon findings, since effects are a different
technical problem (temporal/animation, not a static-draw-call question) from icons.

## Architecture Constraints

- Must reuse the server-side renderer's `DRAW_ORDER` compositing-order convention as the shared contract
  across frontend tiers, not invent a separate ordering scheme.
- Must not introduce a new image-asset pipeline (sprite sheets, checked-in SVG/PNG files) — pre-render the
  existing `lucide-react` icon set to cached off-screen canvases instead, consistent with the existing
  minimap-caching pattern and the sibling color-system doc's confirmed "assets are fine, no gap" finding.
- Any performance claim about icon rendering must be measured against this project's real ~10,000-entity
  target scale, not assumed from general canvas-performance research alone.
- Frontend-only (`frontend/src/**`) — no backend/`AuthoritativeState` changes implied; this is purely about
  how the live client draws data it already receives.

## Relationship to Planned Tickets

- **`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1 of `docs/plans/live_map_scaling_roadmap.md`) is a hard
  prerequisite this idea was missing an explicit note on.** Confirmed by reading that epic directly: it
  explicitly keeps `GameCanvas.tsx`/`useCanvas.ts` untouched (data-layer reconnection only —
  `useSimulation.ts` and backend routes/broadcast) and, as of 2026-08-23, is still `OPEN` in
  `tickets/todos/`, not started. Until M1 ships, `GameCanvas.tsx` renders nothing live — there is no real
  entity/building data flowing to apply any render tier to yet. This idea is not blocked in the sense of
  needing M1's own scope changed (no conflict — M1's untouched-`GameCanvas.tsx` boundary is exactly
  compatible with this idea living as a separate, later effort), but it is premature to sequence before M1,
  the same "measure/ship the data path before the visual layer" ordering the HUD roadmap already applies
  elsewhere in this repo.
- `docs/plans/hud_delivery_roadmap.md` — explicitly does not cover `GameCanvas.tsx`; this idea fills that
  gap without proposing changes to that roadmap's own scope.
- `docs/plans/live_map_scaling_roadmap.md` — M2 (Rendering Performance at Scale, gated on M1) is about
  chunked terrain caching and dirty-rect entity rendering for raw performance at scale; this idea's
  "Measurement" and "Current" tiers are compatible with that work (both care about not paying for what you
  don't render), but visual-tier selection itself is a distinct concern M2 doesn't cover.
- `src/rendering/render.py`, `docs/plans/world_rendering/idea_world_render_validation.md` — the direct
  precedent for the Measurement tier; no code changes proposed to that module by this doc.
- `docs/plans/idea_hud_color_asset_system.md` — this doc's "no new asset pipeline" constraint and the
  confirmed lack of image assets in `frontend/src`/`frontend/public` both come directly from that
  investigation, reused here rather than re-derived.
- No ticket created or modified by this doc.

## Open Questions

- Whether tier selection is a player-facing setting (a real UI toggle), a fixed default with no user
  control, or an automatic choice based on measured client performance — not decided here.
- Whether the "Measurement" tier should become genuinely shared code between `src/rendering/render.py`
  (Python) and the frontend (TypeScript), or stay two independent implementations of the same simple
  flat-fill logic in two languages — a real architecture decision given the two are different runtimes,
  not resolved here.
- Real performance measurement of pre-rendered-sprite icon rendering at this project's actual target scale
  is unexecuted — the "icons aren't necessarily slower" finding above is grounded in general canvas-
  performance research, not this project's own benchmark.
- Effects (glow, transitions, particles) are entirely unresearched in this pass, flagged but not scoped.
- Whether `idea_world_rendering_core.md`'s "Already has entity icons" claim should be corrected in that doc
  directly, given this investigation found it doesn't hold — a small fix, not done here since it's a
  different doc's content, flagged for whoever picks either idea up next.

---

## References

- `frontend/src/components/GameCanvas.tsx`, `frontend/src/hooks/useCanvas.ts` — read directly; every draw
  call enumerated to confirm no icon/sprite rendering exists today.
- `src/rendering/render.py` — read directly; the real, shipped "Measurement" tier precedent and its
  `DRAW_ORDER` compositing convention.
- `docs/plans/world_rendering/idea_world_rendering_core.md` — source of the "Option C: shared core, thin
  clients" architecture principle this doc extends to frontend render tiers, and of the corrected
  "entity icons" claim.
- Unity Built-in Render Pipeline graphics-tier documentation — real precedent for "one pipeline, tier flags"
  instead of parallel per-tier implementations.
- Canvas 2D performance research (MDN's Optimizing Canvas guide and related sources) — verified finding that
  path-based primitives are CPU-bound per-call while cached `drawImage()` blits are comparatively cheap,
  the basis for "icons aren't necessarily a performance cost."

*Raised: 2026-08-23, directly following investigation into `docs/plans/idea_hud_color_asset_system.md`,
extended per direct user request to cover canvas/map visual rendering rather than just HUD chrome and
color palette.*
