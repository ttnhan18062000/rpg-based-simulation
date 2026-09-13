---
status: active
layer: frontend
authority: P2
audience: designer
maturity: proposal
tags: [rendering, live-map, hud, art, overview]
---

# Project Rendering Overview

Status: planning overview  
Scope: player-facing live-game rendering, HUD, and their visual-art inputs  
Boundary: this document summarizes desired features and existing plans; it does not freeze an art style, production specification, or implementation design.

## Intended Experience

The project should present its turn-based RPG simulation as a readable live world rather than as raw state.
The map is the spatial view of what is happening; the HUD is the investigation view for understanding what
changed, who is involved, and why it matters. Both should remain useful at native scale, under crowded
conditions, and as the simulated population grows.

The rendering direction has three connected parts:

1. **Live world canvas** — a navigable map that clearly communicates terrain, entities, buildings,
   resources, loot, visibility, combat, selection, and other important world state.
2. **Observer HUD** — a consistent information layer for noticing events, locating subjects, inspecting
   current and recent state, following relationships, and returning without losing context.
3. **Visual and art language** — reusable silhouettes, icons, markers, colors, and restrained effects that
   make the map and HUD easier to read without assigning unique art to every runtime-generated identity.

The deterministic server-side world renderer remains a separate QA and measurement surface. It can inform
visual validation, but it is not a substitute for the player-facing live canvas or HUD.

## Live-Game Rendering Features We Want

- A stable connected map with clear loading, reconnect, pause/resume, camera, zoom, hover, selection,
  minimap, fog, and remembered-world behavior.
- Legible world layers for terrain, static objects, moving entities, combat and targeting information,
  objectives, conditions, and important events.
- Reliable one-cell character recognition on the current 16-pixel grid, including crowded native-scale
  compositions and cues that do not rely on hue alone.
- Responsive rendering on large maps and at high entity counts, with client-side optimization work added only when measurement shows it is needed.
- Network updates that remain relevant to the current view or observed subject as entity and viewer counts grow, with spatial filtering added only when measured load justifies it.
- Possible measurement, baseline, and polished presentation modes within one frontend canvas pipeline, including optional icons or sprites, restrained effects, and smoother visual motion. All mode, animation, and asset choices remain idea-level.

## HUD Features We Want

- A thin, consistent visual foundation: semantic interface tokens, a simple layout wrapper, and reusable
  conventions only where real workflows prove they are useful.
- Durable navigation and selection state so camera position, selected subjects, inspector context, tabs,
  filters, search, and scroll position survive normal investigation flows.
- Search, filtering, and attention-oriented ranking that prioritize visible, recent, changing, or anomalous
  information over static identifier order.
- One complete investigation path: notice an event or anomaly, locate the subjects, inspect current and
  recent state, follow a related entity/event/location, and return with prior context intact.
- Scalable entity exploration through facets, grouping, saved views, and aggregate-to-detail navigation for very large populations. This is desired, but its final roadmap placement remains unresolved.
- Contextual support for buildings and locations, loot and inventory, class/progression information,
  simulation controls, legends, and the remaining inspector subjects after the core workflow is proven.
- Progressive disclosure and consistent visual semantics across panels, including a dedicated
  data-visualization palette, redundant non-color cues, helpful labels/tooltips, and restrained motion with
  reduced-motion support.
- Before/after evaluation of representative observer tasks, followed by evidence-based decisions about
  optional investments such as resizable or pinnable panels and workspace presets.

## Roadmap and Todo Map

| Track | Desired outcome | Planning state | Source |
|---|---|---|---|
| Live-map foundation | A working player-facing map connected to live simulation state | Foundation complete; retained as context | [`live_map_scaling_roadmap.md`](../../plans/live_map_scaling_roadmap.md) |
| Live-map rendering performance | Responsive client rendering at real map and entity scale | Open and evidence-gated | [`TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE`](../../../tickets/todos/live-map-rendering-performance/TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE.md) |
| Live-map interest management | Relevant updates and controlled bandwidth at high scale | Open and evidence-gated | [`TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`](../../../tickets/todos/live-map-interest-management/TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT.md) |
| HUD M1: thin foundation | Semantic tokens, minimal layout, durable context, search/ranking, and a baseline | Open | [`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`](../../../tickets/todos/hud-design-system-foundation/TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION.md) |
| HUD M2: investigation slice | A complete notice-to-return observer workflow through the core panels | Open; follows M1 | [`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`](../../../tickets/todos/hud-core-panel-wiring/TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING.md) |
| HUD M3: extraction and migration | Proven shared conventions plus remaining contextual panels grouped by workflow | Open; follows M2 | [`TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING`](../../../tickets/todos/hud-contextual-panel-wiring/TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING.md) |
| HUD M4: polish and measurement | Cross-panel consistency and comparison with the M1 baseline | Open; follows M3 | [`TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT`](../../../tickets/todos/hud-content-polish-measurement/TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT.md) |

The HUD sequence and its gates are summarized in
[`hud_delivery_roadmap.md`](../../plans/hud_delivery_roadmap.md). The live-map performance and interest
management tracks are independent after the common live-map foundation and should begin only when real
measurements justify them.

For HUD dependency order, this overview follows the current roadmap sequence M1 → M2 → M3 → M4; any conflicting dependency wording in an individual epic is stale.

## Unscheduled Directions

The following active idea documents describe possible follow-on features, not committed production scope:

- [`idea_frontend_canvas_render_tiers.md`](../../plans/idea_frontend_canvas_render_tiers.md) — one shared
  canvas pipeline with selectable fidelity, optional sprites/icons and effects, and smoother presentation.
- [`idea_hud_color_asset_system.md`](../../plans/idea_hud_color_asset_system.md) — a structured
  data-visualization palette distinct from general HUD chrome.
- [`idea_hud_motion_transition_system.md`](../../plans/idea_hud_motion_transition_system.md) — semantic,
  accessible transitions for meaningful HUD state changes.
- [`idea_hud_quality_measurement.md`](../../plans/idea_hud_quality_measurement.md) — possible repeatable
  measures for findability, detection, context preservation, and density legibility beyond the initial
  manual baseline.

## Art Handoff

[`visual-system-planning.md`](visual-system-planning.md) inventories the preliminary visual-language needs
across the RPG systems. [Detailed Plan 07](../../plans/render-and-art/07_manual_art_experiment_execution_plan.md)
defines the small manual drawing tests, while the
[program review handoff](render-and-art-review-handoff.md) explains how that evidence fits the three major
epics. Those experiments should validate readability before any sprite resolution, palette, style,
status/effect roster, full skill roster, Place representation, or faction-emblem breadth is treated as final.
