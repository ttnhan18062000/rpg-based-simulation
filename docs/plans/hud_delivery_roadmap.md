---
status: active
layer: frontend
authority: P1
audience: agent
tags: [architecture, hud, design-system]
---

# Roadmap — HUD: Thin Foundation, Vertical Slice, Then Extraction

**Purpose**: this player-facing HUD effort spans more work than one epic can hold cleanly. This doc ties
the milestones together and states the sequencing/gating rule once, instead of repeating it in each epic —
the same structure `docs/plans/live_map_scaling_roadmap.md` established for the live-map effort, applied
here.

**Revision (2026-08-22):** the original plan here was chassis-first — build the full navigation map,
scoring rubric, named-slot skeleton, three-tier theme tokens, and component-slot convention before any HUD
content work. An external design review (`tmp/hud_review.md`) made a well-grounded case against that
ordering: with only ~9 panels and no demonstrated need for multiple layouts/themes, a full chassis risks
encoding this project's own possibly-wrong existing panel/navigation boundaries (`Sidebar` mixing
navigation, selection, and automatic mode-switching; `EntityList` assuming "all entities in one flat list"
is the right default) into a technically-cleaner but still-wrong abstraction. This directly echoes this
project's own CLAUDE.md engineering philosophy ("don't design for hypothetical future requirements," "a
premature abstraction is worse than a little duplication") better than the original chassis-first plan did.
User decision: adopt a **hybrid** — ship the pieces of the chassis that are justified regardless of
sequencing now (cheap, low-risk), then validate everything else against one real end-to-end workflow before
committing further.

**Design principle carried through every milestone below, per direct user instruction:** default views and
layout must prioritize by *information volatility and attention-worthiness*, not by static/alphabetical
order. What an observer actually watches is what's currently changing or unusual — recent events, entities
whose state just shifted, anomalies, whatever's in the current map viewport — not a full static roster.
What rarely changes (an entity's class, base attributes, full historical log) belongs behind drill-down,
not in the default view. This directly replaces `EntityList.tsx`'s current hardcoded hero-first/ID sort,
and shapes what the M2 vertical slice's default entry point actually shows.

## Milestones

### M1 — Thin Foundation & Baseline (gated on nothing)

**Tracking epic**: `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (revised scope — see its own ticket).

Ships only what the external review itself confirms is justified immediately, regardless of which way the
rest of the roadmap goes:
- A **two-tier** semantic token layer (primitives, already present in `index.css`, plus a new semantic
  layer — `surface-panel`, `text-critical`, etc.) — not the originally-planned three-tier system;
  component-level tokens are added later only where a real independent contract emerges (M3), not declared
  as a mandatory third tier up front.
- A **minimal** layout wrapper around the current `Header` / `GameCanvas` / `Sidebar` arrangement — not a
  full named-slot/config-driven skeleton engine.
- A **durable selection/navigation state model** — route, active workspace, camera, selection, open
  inspector/tab, and filter/search state kept explicit and separated, so the existing
  `isBuildingView`/`isLootView`/`isSpectating` auto-switch in `Sidebar.tsx` stops silently destroying
  scroll position, active tab, and prior entity context when it fires (a concrete failure mode the external
  review identified against the *current* code, not a hypothetical).
- `EntityList.tsx`'s basic text search/filter (necessary regardless of sequencing), with its default view
  changed from hardcoded hero-first/ID sort to something ranked by the information-volatility principle
  above (recently-changed / currently-visible / anomalous first) — the fuller entity-exploration system
  (facets, grouping, saved views) is deferred to M3, informed by what M2's slice actually needs.
- A **baseline measurement pass**: 3-5 representative observer tasks, measured against the *current*,
  unmodified HUD, recorded before any further redesign — so M4 has real evidence of improvement instead of
  a rubric with nothing to compare against.

### M2 — Entity Investigation Vertical Slice (gated on M1)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (revised scope — see its own ticket).

Ships one complete, real, end-to-end observer workflow — not a batch of independently-wired panels:
notice an event or anomaly → locate the entities involved (ranked by the volatility principle, not a flat
alphabetical list) → open one entity's inspector → see current and recent state → follow a relationship or
causal link to a related entity/event/location → return to the prior context (map position, selection,
filters intact) without it being silently lost. Built through the real panels (`Sidebar.tsx`,
`InspectPanel.tsx`, `EntityList.tsx`, `EventLog.tsx`) using only M1's thin foundation — no chassis piece
gets used here that M1 didn't already ship.

**This is the milestone that produces real evidence**, not analytical estimate, for whether the deferred
chassis pieces (full slot engine, component tokens, workspace presets) are actually needed — M3 extracts
from what this slice proves, it does not re-derive speculatively.

### M3 — Chassis Extraction & Remaining Panel Migration (gated on M2)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (revised scope — see its own ticket).

Two halves, sequenced together rather than as independent parallel epics (this is the biggest structural
change from the original roadmap — M3 no longer starts alongside M2, it starts *after* M2 because it
depends on M2's output):
1. **Extract only the chassis patterns M2's slice actually demonstrated** — a named-slot layout only if
   the slice showed a real need to rearrange regions; component-level tokens only where a panel proved a
   genuinely independent contract; panel-header/navigation conventions; instrumentation hooks. Not a
   speculative superset.
2. **Migrate the remaining panels** — the mode-triggered contextual ones (`BuildingPanel.tsx`,
   `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`, `Legend.tsx`) plus whatever M2's slice didn't
   already cover — onto the now-validated (not speculative) chassis pieces from step 1, grouped by
   observer workflow (event monitoring, building/location investigation, loot/inventory, simulation
   control) rather than by their current technical/file grouping.

### M4 — Measurement Against Baseline & Consolidation (gated on M3)

**Tracking epic**: `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (revised scope — see its own
ticket).

Measures the finished HUD against M1's own recorded baseline (real before/after evidence, not a first-time
score), runs a cross-panel consistency pass (progressive disclosure, color/tooltip layering, the
information-volatility default-view principle applied uniformly), and evaluates — only with real evidence
in hand, not speculatively — whether further investment (resizable/pinnable panels, curated workspace
presets) is actually justified.

## Sequencing rules

- **M1 is a hard prerequisite for M2, M3, and M4.** None may start before M1 ships.
- **M2, M3, and M4 are now strictly sequential**, not the M2/M3-parallel shape the original roadmap used —
  M3 depends on M2's slice for what to extract, and M4 depends on M3's migration being complete to measure
  the full HUD.
- **Detailed child-ticket breakdown for M2, M3, and M4 is deliberately not done yet.** All three remain
  scope-only at the epic tier — this roadmap and the three epic tickets capture milestone structure and
  design intent, not implementation detail to plan before each prior milestone's real evidence exists.
- **Cross-roadmap note, not a gate:** this HUD roadmap is independent of `docs/plans/live_map_scaling_roadmap.md`
  (the live-map renderer effort) — different components, no file overlap. The one soft connection: M2's
  entity/event-focused slice benefits from live-map M1's real-time entity broadcast once it ships, rather
  than relying on full-snapshot polling — worth checking that effort's status before M2 starts, but not a
  hard dependency, since `/api/v1/state` already returns full entity/event data today.

## References

- `docs/plans/hud_design_system_foundation_epic.md` — M1's full plan doc (revised).
- `tmp/hud_review.md` — the external design review that prompted this roadmap's revision.
- `docs/plans/live_map_scaling_roadmap.md` — the sibling roadmap this doc's structure was originally
  mirrored from; the sequencing shape has since diverged (see Sequencing rules above).
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1's ticket.
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2's ticket.
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3's ticket.
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4's ticket.
