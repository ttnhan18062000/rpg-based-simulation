---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, live-map, hud, interaction, accessibility]
---

# Detailed Plan 04 — Minimum Live-Map-to-HUD Inspection Interaction

## Outcome and boundary

Close `LMSI-G4` for exactly `InspectEntity`, `InspectWorldObject(family=building)`, and
`InspectGroundStack`. Only deliberate “inspect in HUD” emits M2H. Hover, camera, minimap and ordinary
map-local selection emit nothing. The map supplies semantic identity/picking source; HUD re-resolves it
and owns investigation history, navigation and focus.

Excluded: generic location/event inspection, accessible map summary, viewport telemetry, React route
names, and automatic H2M echo.

## Entry conditions

- G0 envelope/identity rules and inspect-gesture/focus decision are approved.
- Map explicit-inspect output and HUD navigation destination are stable; full G1/G2 closure is not required.
- Initial world-object family is exactly `building`.
- Live tests have stable world/session/stream/map identities; fixture tests may start sooner.

## Contract obligations

| Concern | Requirement |
|---|---|
| Identity | Discriminated entity, building-family object or ground-stack identity |
| Source | Pointer, keyboard, accessible target list or controller |
| Resolution | HUD uses current permitted projection and names stale/missing/unsupported |
| History | Accepted transition preserves/appends history; duplicate never duplicates history |
| Focus | Pointer need not steal focus; keyboard/accessibility has declared destination and announcement |
| Results | Accepted, duplicate/no-op, stale/missing, wrong-world, unsupported, unavailable or timed out |

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G4-W01` | Gesture/picking decision | Pointer/keyboard/controller interaction rule | Local selection and inspect are distinguishable |
| `G4-W02` | Version types | Three intent/result schemas and compatibility fixtures | Exact roster/building discriminator only |
| `G4-W03` | Map origin | Explicit semantic picked-target API | Hover/camera/minimap/local selection emit zero |
| `G4-W04` | M2H route | Validation, dedup, ordering, timeout, restart, capability checks | Adds no H2M route/domain state |
| `G4-W05` | HUD destination | Re-resolution into navigation facade and focus result | HUD owns context/history/focus |
| `G4-W06` | No-op and switch | Default-off route and fake endpoints | Disables independently |
| `G4-W07` | EX-X04 | Picking, transition and accessibility traces | One inspect yields at most one HUD transition |
| `G4-W08` | EX-X05 | Duplicate/reorder/loss/restart/cycle workload | Zero duplicate history/loop; bounded termination |

## Sequence

Close gesture/accessibility; version schemas/fakes; build map and HUD adapters independently; add only the
M2H route; then run first-slice and delivery experiments. G4 may run beside G3 but must coordinate file
ownership with HUD M2/M3.

## Test matrix

| Case | Expected result |
|---|---|
| Explicit entity/building/ground-stack inspect | One accepted transition or named semantic failure |
| Hover, drag, zoom, minimap or local selection | No M2H traffic |
| Duplicate | No duplicate navigation/history |
| New inspect while pending | Declared supersession without erased history |
| Wrong world/session or unsupported family | Fail closed or named unsupported |
| Pointer source | Declared panel behavior without forced focus |
| Keyboard/accessibility source | Predictable focus and announcement |
| M2H apply | No automatic H2M emission |
| Disabled route | Map local interaction and HUD Core remain useful |

## Rollback and ticket slicing

Disable M2H, expire pending intents, restore no-op, retain map-local selection and HUD Core, and never
replay expired navigation after restart. Suggested later scopes: gesture/accessibility; schemas; map
origin/picking; route; HUD destination; EX-X04; EX-X05/rollback. Do not add extensions to fill a ticket.

## Exit checklist

- [ ] Exact three-intent roster is preserved.
- [ ] Explicit inspect differs from local selection.
- [ ] Hover/camera/minimap emit nothing.
- [ ] HUD owns navigation/history/focus and re-resolves identity.
- [ ] Accessibility, dedup, timeout, restart and loop tests pass.
- [ ] No automatic H2M echo occurs.
- [ ] Independent disable and rollback pass.
