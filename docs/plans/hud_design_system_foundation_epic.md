---
status: active
layer: architecture
authority: P1
audience: developer
maturity: idea
date: 2026-08-22
tags: [idea, frontend, hud, design-system]
---

# Epic Plan — HUD Design System Foundation

**Tracking ticket:** none yet (this doc precedes epic ticket creation)
**Source:** direct conversation, following the research pass into `docs/plans/live_map_reconnection_epic.md`'s
deferred "no HUD/info-display work" scope item.
**Priority:** P1 — precedes and structurally constrains all future HUD content work (the panels researched in
the companion investigation below cannot be safely built until this chassis exists, or every new panel
re-litigates layout/theme decisions from scratch).

---

## Problem

Two prior investigations this session established:

1. **The HUD content itself** (`Sidebar.tsx`, `InspectPanel.tsx`, `EntityList.tsx`, and siblings) is
   already substantially built, unwired, and architecturally sound — mode-driven tabs, progressive
   disclosure via `CollapsibleSection`, color-coded scanning, tooltips for depth. Content design is not
   the blocker.
2. **The chassis underneath it is not designed as a system at all** — it is one hardcoded arrangement:
   - **Navigation** is a flat 2-button switch (`simulation` / `api-docs`) in `Header.tsx`
     (`PageView = 'simulation' | 'api-docs'`) — everything else is panel-level, not page-level, navigation.
   - **Layout** is hardcoded JSX in `App.tsx`: `Header` (fixed height) → `[GameCanvas (flex-1), Sidebar
     (fixed 360px)]`. There is no named-slot or config-driven layout primitive — trying a different
     top-level arrangement (bottom panel instead of right sidebar, a 3-column layout, a movable dock) means
     rewriting `App.tsx` directly, not swapping a config.
   - **Theming** is a single flat token layer: `frontend/src/index.css`'s `@theme` block defines 11 CSS
     custom properties (`--color-bg-primary`, `--color-bg-secondary`, `--color-bg-tertiary`,
     `--color-border`, `--color-text-primary`, `--color-text-secondary`, 5 `--color-accent-*`) consumed
     directly by components via Tailwind utility classes (`bg-bg-secondary`, `text-accent-blue`, etc.).
     There is no semantic indirection layer — components reference near-primitive names directly, so a
     second theme/design variant means editing every consuming class name, not remapping one file.
   - **No metrics exist to compare design candidates against.** Nothing in the frontend defines what "easy
     to find things" means in measurable terms — no task-success baseline, no click-depth budget, no
     navigation-success target.

The user's framing: don't jump straight to HUD content. Decide the navigation map, define how design
quality is measured, build the layout skeleton and the theme as swappable systems, and make individual
HUD components pluggable into that chassis — so future top-level design changes are a swap, not a rebuild.

---

## Idea

Bootstrap a genuine design-system foundation, in four sequenced parts, before resuming HUD content work.

### Part 1 — Navigation Map

Define the full set of top-level views and how a player moves between them, distinct from panel-level
navigation inside a view.

**Current state (verified):** exactly 2 top-level pages exist —
`simulation` (the live map + sidebar) and `api-docs` (`ApiDocsPage`) — switched by two buttons in
`Header.tsx`'s `<nav>`. All entity/building/loot/event inspection happens as panel-level state inside
`Sidebar.tsx` (`activeTab: 'info' | 'inspect' | 'events'`), not as separate pages.

**Open question this phase must resolve:** does deeper information (aggregate faction/economy/calamity
state, cross-entity comparison, a "World Overview" dashboard distinct from the live map) warrant new
top-level pages, or does everything stay panel-level within `simulation`? This is an information-architecture
decision, not a styling one, and it determines how large `Part 3 — Skeleton` needs to be.

### Part 2 — Metrics & Scoring

Define an explicit, reusable rubric to evaluate skeleton/theme/navigation candidates against, instead of
comparing them by aesthetic judgment. This project already has the right internal precedent to mirror:
SimQ's own grade-band convention (S/A/B/C/D/F, `docs/simulation_quality/quality_scoring_contract.md`) for
scoring simulation-quality dimensions objectively.

Candidate metrics, grounded in real UX-research practice (not invented from scratch — see References):
- **Task Success Rate** — for a small fixed set of representative tasks (e.g. "find the lowest-HP hero",
  "find which faction is at war", "check what a selected entity is currently doing"), can a player complete
  them, and in how many interactions?
- **Click/interaction depth budget** — a stated maximum (e.g. RimWorld's own design discipline: player is
  "never more than three button presses away" from any action or piece of information) that any given
  layout/navigation candidate must satisfy for the representative task set.
- **Screen real-estate allocation** — how much of the viewport is canvas vs. chrome vs. wasted space, per
  candidate skeleton.
- **Navigation/search success rate** — for candidates that introduce any list/search (see `EntityList.tsx`
  gap below), the standard UX metric for "did the player find the thing they were looking for."

This phase's deliverable is the rubric itself (a short scoring doc, mirroring `quality_scoring_contract.md`'s
shape), plus the 3–5 representative tasks it will be measured against — not yet a specific skeleton design.

### Part 3 — Skeleton (composable layout shell)

Replace `App.tsx`'s hardcoded `Header → [GameCanvas, Sidebar]` JSX with a named-slot layout primitive that
the navigation map (Part 1) and individual HUD panels (Part 5) compose into, so a different top-level
arrangement is a slot/config change, not a rewrite of `App.tsx`.

**Current state (verified):** `frontend/src/App.tsx` — single component, hardcoded `<div className="h-screen
flex flex-col overflow-hidden">` containing `<Header>` then a conditional `<GameCanvas>` +/- `<Sidebar>` row.
No abstraction between "what regions exist" and "what's currently docked in them."

### Part 4 — Theme (token system upgrade)

Upgrade `frontend/src/index.css`'s existing flat `@theme` block into a proper multi-layer token system, so
theming becomes a mapping swap rather than a component-by-component class-name edit. The 2026 industry-standard
shape (see References) is a three-tier strategy:
- **Layer 1 — Primitives**: raw values. This is what exists today (`--color-bg-primary: #0f1117`, etc.) —
  keep as-is, this layer doesn't change.
- **Layer 2 — Semantic tokens**: intent-based names (e.g. `surface-primary`, `text-critical`,
  `border-interactive`) that map onto Layer 1 primitives. This layer does not exist yet — components
  currently consume Layer-1-shaped names directly (`bg-bg-secondary`) rather than intent (`surface-panel`).
  Adding this layer is the actual unlock: swap a theme by remapping Layer 2 → Layer 1, components untouched.
- **Layer 3 — Component tokens**: fine-grained overrides for specific elements (e.g.
  `sidebar-width`, `navbar-height`) where needed, without breaking the semantic layer.

Note: `index.css` already has an unused `@custom-variant dark (&:is(.dark *))` declaration with no
corresponding dark-mode toggle wired anywhere — confirm during this phase whether that's a leftover
scaffold to build on or dead code to remove.

### Part 5 — Component wiring (slot-based composition)

The individual HUD components (`Sidebar.tsx`, `EntityList.tsx`, `InspectPanel.tsx`, `EventLog.tsx`,
`ControlPanel.tsx`, `Legend.tsx`, `BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`) are already
props-driven and reasonably self-contained — this is a real strength to preserve, not rebuild. The gap is
purely that they're hardwired into `App.tsx`'s fixed JSX rather than composed into Part 3's skeleton slots.
This phase is where they get re-plugged, not redesigned.

**Real content gap found during this same investigation, worth fixing in this pass since it's already
touched:** `EntityList.tsx` has zero search or filter — a hardcoded hero-first/ID sort over a flat scrolling
list. Given this session's own live-map-reconnection work targets ~10,000 entities at scale, this fails
Part 2's own "navigation/search success rate" metric before the design system work is even done. Flagging
as in-scope for whichever ticket eventually touches `EntityList.tsx` under this epic, not a separate concern.

---

## Explicitly Deferred (from the companion HUD-content investigation)

The actual HUD *content* work already researched this session — wiring `Sidebar`/`InspectPanel`/etc. to
real V2 data, and the "RimWorld/Crusader-Kings-style structured complexity, not EVE-style freeform
complexity" content-design direction — stays deferred until this chassis exists. Building content-first
into a chassis that gets redesigned underneath it would mean rebuilding that content work too.

---

## Related, Independent Work

- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (M1) — reconnects `GameCanvas.tsx`/`useCanvas.ts` to real data;
  explicitly out of scope for HUD work, `GameCanvas.tsx` itself untouched by either epic.
- `TCK-20260821-EPIC-WORLD-RENDERING-CORE` — server-side batch/QA rendering for visual-quality scoring, a
  distinct system (not player-facing), currently being implemented by a concurrent session
  (`TCK-20260821-WORLD-RENDER-CORE` observed in-progress during this session). Unrelated to this epic.

---

## Open Questions

- Does Part 1's navigation map conclude that new top-level pages are needed (e.g. a World Overview
  dashboard), or does the existing 2-page + panel-level-navigation shape hold? This determines Part 3's
  actual scope.
- Should Part 2's rubric produce a single composite score (like SimQ's grade bands) or stay as separate,
  uncombined metrics (Task Success Rate, click-depth, real-estate allocation) reported individually? SimQ's
  own precedent uses composite grade bands, but UX-research practice (System Usability Scale, individual
  scorecards) often keeps metrics separate to avoid masking a bad dimension behind a good average.
  Recommend deciding this explicitly in Part 2's own scoping, not silently defaulting to one or the other.
- Is `@custom-variant dark` in `index.css` a real, planned feature (light/dark toggle) or dead scaffold?
  Affects whether Part 4's semantic-token layer needs to support two concrete theme presets from day one
  or just the one dark palette that exists today.
- What are the 3–5 representative tasks Part 2's metrics get measured against? Needs direct input — this
  doc proposes examples ("find the lowest-HP hero," "find which faction is at war") but the real list
  should come from what the project's own simulation actually surfaces as meaningful (factions, quests,
  calamities, economy) rather than being invented here.

---

## References

- RimWorld's console-port UI discipline ("never more than three button presses away from an action or
  piece of information") — progressive disclosure in practice, cited as a direct precedent for Part 2's
  click-depth budget.
- Progressive disclosure (general UI pattern) — https://en.wikipedia.org/wiki/Progressive_disclosure
- Three-tier design token architecture (primitives → semantic → component tokens; theming as a Layer-2
  remap, not a component rewrite) — industry-standard shape as of 2026, cited for Part 4.
- UX scorecards / Task Success Rate / navigation-search-success-rate as measurable evaluation criteria for
  information architecture and navigation design — cited for Part 2.
- EVE Online's own community critique of freeform, fully-customizable-window UI ("players make worse
  choices when the interface demands too many micro-judgments at once") — the explicit anti-pattern this
  epic's chassis should avoid defaulting toward.
- This project's own `docs/simulation_quality/quality_scoring_contract.md` — internal precedent for
  grade-banded, rubric-based scoring, proposed as the shape for Part 2's own rubric.
