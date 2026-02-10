# Epic 14: Frontend UX Improvements

## Summary

Polish the frontend viewer with quality-of-life features: smooth entity interpolation, combat animations, notification system, keyboard shortcuts, entity search/filter, and accessibility improvements. Transform the viewer from a debug tool into an engaging observation experience.

Inspired by: Factorio map viewer, Rimworld camera controls, RTS spectator modes, modern dashboard UX.

---

## Motivation

- Current rendering is functional but utilitarian — entities teleport between tiles
- No visual feedback for combat, skill use, or level-ups beyond event log text
- No keyboard shortcuts for common actions (pause, speed, select)
- Entity list is a flat scroll with no search or filter
- Missing accessibility features (screen reader support, color-blind mode)
- Aligns with project goals — the frontend is the primary window into the simulation

---

## Features

### F1: Smooth Entity Movement
- Interpolate entity positions between poll cycles (lerp from old pos to new pos)
- Movement animation over 80ms (one poll cycle) instead of instant teleport
- Entities that move multiple tiles appear to slide smoothly
- Interpolation disabled during step mode (instant position update)

### F2: Combat Animations
- Floating damage numbers rise above entities when hit (red for damage, green for healing)
- Critical hit numbers are larger and have a flash effect
- Miss text ("MISS") appears in grey
- Skill use shows a brief colored flash on the caster (color matches element)
- Death shows a fade-out animation (opacity → 0 over 200ms)

### F3: Notification Toasts
- Important events shown as brief toast notifications in the corner:
  - Level up: "Hero reached Level 5!"
  - Boss defeated: "Goblin Chief defeated!"
  - Quest completed: "Quest complete: Hunt the Wolves"
  - Rare loot: "Hero found Enchanted Blade!"
- Toasts auto-dismiss after 3 seconds; click to dismiss early
- Notification types filterable in settings

### F4: Keyboard Shortcuts
- **Space:** Toggle pause/resume
- **S:** Step (when paused)
- **R:** Reset simulation
- **1–4:** Switch sidebar tabs
- **Escape:** Deselect entity / close panel
- **+/-:** Adjust simulation speed
- **Arrow keys:** Pan camera
- **Tab:** Cycle through entities (next/prev)
- Shortcut reference shown in a help overlay (press `?`)

### F5: Entity Search & Filter
- Search bar at top of entity list — filter by name, kind, or ID
- Filter buttons: Heroes, Goblins, Wolves, Bandits, Undead, Orcs
- Sort options: by level (desc), by HP (asc), by distance from hero
- Filtered entities highlighted on canvas with a subtle pulse

### F6: Camera Auto-Follow
- "Follow" button that locks camera to the selected entity
- Camera smoothly pans to keep the entity centered
- Auto-follow disables on manual pan (click to re-enable)
- Follow mode indicator shown in corner

### F7: Entity Trail Visualization
- Optional toggle: show the last N positions of the selected entity as fading dots
- Trail color matches entity color
- Useful for understanding movement patterns and patrol routes

### F8: Color-Blind Mode
- Alternative color palette option with pattern/shape differentiation
- Entities use distinct shapes per faction (in addition to color)
- HP bars use pattern fills (stripes for medium, crosshatch for low)
- Toggle in settings panel

### F9: Performance Mode
- For large maps (128×128) with many entities, offer a performance toggle:
  - Skip fog-of-war overlay rendering
  - Reduce entity detail (no HP bars, no state borders)
  - Lower poll frequency (200ms instead of 80ms)
  - Skip minimap entity rendering

### F10: Simulation Statistics Dashboard
- Expandable dashboard showing:
  - Entity count over time (mini sparkline chart)
  - Kills per faction
  - Hero progression summary (level, gold, items crafted)
  - Most dangerous area (highest death density)
  - Simulation speed (actual TPS vs configured TPS)

---

## Design Principles

- All animations are frontend-only — no backend changes needed
- Interpolation works with the existing poll-based data flow
- Keyboard shortcuts use standard React event handling (no external library)
- Color-blind mode is a CSS variable swap + shape changes
- Performance mode degrades gracefully — simulation still runs at full fidelity

---

## Dependencies

- Existing canvas rendering system (useCanvas)
- Existing polling system (useSimulation)
- Existing sidebar component architecture

---

## Estimated Scope

- Frontend: ~15 files new/modified
- Backend: 0 changes
- Assets: Alternative color palette definitions
