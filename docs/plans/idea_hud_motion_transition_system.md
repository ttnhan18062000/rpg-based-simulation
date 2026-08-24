---
status: active
layer: frontend
authority: P2
audience: developer
maturity: idea
date: 2026-08-23
tags: [idea, hud, design-system]
---

# Idea: A Motion/Transition Token System — a Real Gap, Corrected From an Earlier Overstatement

> **Maturity: IDEA** — Not scheduled. Raised after a closing sweep of the HUD/frontend visual-quality
> investigation thread flagged UI-chrome transition/animation as the one genuinely uncovered corner across
> five prior idea docs. **Correction on investigation, not just on claim**: the initial framing ("zero
> transition/animation exists") was checked against the actual code, not just the idea docs, and turned out
> to be overstated — real usage exists, just uncoordinated. This doc reflects the corrected finding.

---

## Problem

**There is existing transition usage today, not zero — the earlier "genuinely uncovered" framing was wrong
about the code, even though it was right about the docs.** Direct grep across every HUD component confirms:
28 uses of `transition-colors` (hover-state color changes on rows/buttons — `Sidebar.tsx`, `EntityList.tsx`,
and 8 other files), plus `transition-all`/`transition-opacity` (3 uses), plus a `transition-[width]
duration-200` pattern used consistently for HP-bar fill animation (`EntityList.tsx:55` and 6 other sites, all
at the same `200`ms value). This is real usage — the actual gap is narrower than "nothing exists":

- **No semantic duration/easing token layer** — `duration-200` happens to be used consistently for HP bars,
  but that's incidental (every site independently chose the same Tailwind utility class), not backed by a
  named token (`--motion-duration-standard`, etc.) the way `TCK-20260822-SEMANTIC-TOKEN-LAYER` is building
  for color. Most `transition-colors` usages specify no duration at all, silently relying on Tailwind's
  150ms default.
- **No larger structural transitions exist at all** — panel show/hide (the Sidebar mode-switch
  `TCK-20260822-DURABLE-SELECTION-STATE` is fixing the *state* bug on), tab switching, and the phased-loading
  state machine's five states (`TCK-20260821-PHASED-LOADING-STATE-MACHINE`) all currently render as instant,
  hard cuts — confirmed by reading those components directly, no CSS transition or animation wraps any of
  them.
- **`index.css` has zero motion-related declarations** — no `@keyframes`, no motion custom properties, no
  `prefers-reduced-motion` media query anywhere in the frontend, confirmed by direct grep.

## Idea

### A third token tier, sibling to color — not folded into `SEMANTIC-TOKEN-LAYER`'s existing scope

`TCK-20260822-SEMANTIC-TOKEN-LAYER` is explicitly scoped to *color* tokens only (its own Out of Scope: "No
Layer 3 tokens are introduced anywhere in the change" refers to color's own third tier, a different axis
entirely). Motion is a structurally separate token category — duration, easing, and (per the real external
convention below) size/complexity-scaled timing — that deserves its own semantic layer rather than being
squeezed into the color ticket's scope. Proposed shape, informed by real design-system practice (see
References): a small set of named duration tokens (e.g. `motion-micro` ~100-150ms for hover/toggle-scale
interactions, `motion-standard` ~200ms for same-element state changes — matching the HP-bar pattern already
in use, `motion-panel` ~300-400ms for panel/modal-scale transitions) plus two named easing curves
(`ease-out` for elements entering, `ease-in` for elements exiting — the real, standard convention, not
invented here), consumed via Tailwind's existing `duration-*`/`ease-*` utilities rather than raw values.

### Accessibility is not optional research here — checked directly against the real standard, with the correct conformance level stated

Verified directly against the real W3C source (not inferred from a search summary): **WCAG 2.3.3
"Animation from Interactions"** — *"Motion animation triggered by interaction can be disabled, unless the
animation is essential to the functionality or the information being conveyed."* This is a real, correct
citation, but it is **AAA-tier (the highest, optional conformance level)**, not a baseline AA requirement —
important to state precisely rather than overclaim this project must comply. Regardless of formal
conformance-level ambition, the `prefers-reduced-motion` CSS media query is the standard, low-cost mechanism
to honor it, and this project currently has zero references to it anywhere in `frontend/`. Given this
project has already invested real effort in accessibility-adjacent work this session (the WCAG contrast
check on `idea_hud_color_asset_system.md`), a motion system that ships without `prefers-reduced-motion`
support from day one would be a real, avoidable gap in an otherwise-considered effort.

### What actually needs a transition, prioritized by what already has a *state* fix but no *motion* to go with it

Not proposing motion for its own sake — prioritized by what this session's own prior tickets already
identified as needing a state transition, which currently has no accompanying visual transition:

1. **The phased-loading state machine** (`TCK-20260821-PHASED-LOADING-STATE-MACHINE`) — five real states
   (`INITIALIZING → FETCHING_WORLD_DATA → CONNECTING_LIVE → SYNCING → READY`) that ticket gives distinct,
   inspectable status to, but says nothing about how the loading screen visually communicates a state
   change. A `motion-panel`-scale crossfade between states is the natural fit — small, bounded, not the
   glow/pulse "effects" `idea_frontend_canvas_render_tiers.md` already covers for canvas entities.
2. **Sidebar mode-switching** (`TCK-20260822-DURABLE-SELECTION-STATE`) — that ticket fixes the *state* bug
   (context silently lost on switch); once fixed, the panel content still swaps instantly. A short
   `motion-standard` crossfade would make the now-correct state change visually legible as a change, not
   just correct underneath an still-instant cut.
3. **HP-bar width changes** — already animated (`transition-[width] duration-200`), cited here only as the
   existing precedent the semantic `motion-standard` token should formalize, not a new gap.

### What this is *not* proposing

Not the canvas-entity "effects" (glow/pulse/particles) `idea_frontend_canvas_render_tiers.md` already
covers — this doc is UI-chrome motion (panels, tabs, state transitions), that doc is game-world visual
effects on rendered entities. Different layer, different doc, no overlap intended.

## Architecture Constraints

- A sibling token tier to color, not folded into `TCK-20260822-SEMANTIC-TOKEN-LAYER`'s existing scope.
- Must ship `prefers-reduced-motion` support from the first real transition added, not as a retrofit —
  given this project already has zero references to it today, adding motion without it would be introducing
  a new accessibility gap rather than just leaving an old one unaddressed.
- Consume Tailwind's existing `duration-*`/`ease-*`/`transition-*` utility classes via named tokens, not a
  new animation library — no new frontend dependency implied by this idea.
- Frontend-only (`frontend/src/**`) — no backend implications.

## Relationship to Planned Tickets

- `TCK-20260822-SEMANTIC-TOKEN-LAYER` — sibling, not overlapping: that ticket is color tokens only; this
  idea is a separate motion-token tier.
- `TCK-20260821-PHASED-LOADING-STATE-MACHINE`, `TCK-20260822-DURABLE-SELECTION-STATE` — both already ship
  the *state* this idea would attach visual transitions to; this idea doesn't change either ticket's own
  scope, it's a candidate follow-on once they land.
- `docs/plans/idea_frontend_canvas_render_tiers.md` — explicitly a different layer (canvas game-world
  effects vs. this doc's UI-chrome motion); cross-referenced to make the boundary explicit, not because
  either doc's scope needs to change.
- No ticket created or modified by this doc.

## Open Questions

- Exact duration/easing token values are proposed as directionally-reasonable defaults from real external
  convention (Material Design's 200ms/300ms reference points), not calibrated against this project's own
  usage — the existing `duration-200` HP-bar precedent is the one value with real in-project grounding.
- Whether `prefers-reduced-motion` support should disable transitions entirely or just shorten them to
  near-zero duration (both are valid real-world approaches) is not decided here.
- Whether this becomes its own ticket under `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (a 6th child
  ticket) or folds into a later milestone is not decided — that epic's own child-ticket set was already
  fully scoped when this gap was found; whether to add a 6th ticket retroactively or treat this as `M3`-tier
  content-polish work is a real open call, not resolved here.

---

## References

- `frontend/src/components/*.tsx`, `frontend/src/index.css` — read directly; the real inventory of existing
  transition usage (28 `transition-colors`, `duration-200` HP-bar pattern, zero `prefers-reduced-motion`)
  this doc's Problem section is grounded in, not estimated.
- WCAG 2.3.3 "Animation from Interactions" — **verified directly against the real W3C source**: AAA-tier,
  exact success-criterion text quoted above, not inferred from a search summary.
- Material Design motion guidance (200ms standard reference duration, 300ms inter-screen transitions,
  ease-out-for-entry/ease-in-for-exit convention) — real, established design-system precedent for the
  proposed token value defaults.
- `docs/plans/idea_hud_color_asset_system.md`, `TCK-20260822-SEMANTIC-TOKEN-LAYER` — the direct sibling
  precedent (a token tier for one design axis) this idea proposes replicating for motion.

*Raised: 2026-08-23, correcting an earlier overstated closing-sweep claim ("zero transition/animation
exists") after checking the actual frontend code directly rather than only the prior idea docs.*
