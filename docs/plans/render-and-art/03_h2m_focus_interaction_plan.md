---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, hud, live-map, interaction, accessibility]
---

# Detailed Plan 03 — Minimum HUD-to-Live-Map Focus Interaction

## Outcome and boundary

Close `LMSI-G3` for exactly `FocusEntity` and `FocusLocation`. An explicit HUD action creates a semantic
request; the map re-resolves the target against its permitted projection and owns applied camera/focus.
H2M carries no OBS, HRC, PREF, diagnostics, renderer type, React component, raw callback, or automatic
reverse event.

Excluded: highlight, follow, restore/bookmark, observation switching, UI-owned coordinates, and generic
`selectionChanged` messages.

## Entry conditions

- G0 identity/envelope rules and owners are approved.
- HUD explicit-action origin and map focus destination ports are stable; full G1/G2 closure is not required.
- `FocusLocation` semantic identity is resolved before its live implementation.
- Live tests have stable world/session/stream/map identity; fixture tests may begin sooner.

## Contract obligations

| Concern | Requirement |
|---|---|
| Identity | Discriminated entity/location plus required world/session scope |
| Intent | Explicit workflow reason and requested behavior, not renderer coordinates |
| Results | `applied`, `deferred`, `superseded`, `timed_out`, or named rejected/unavailable/unsupported |
| Time | Waiting runtime uses monotonic elapsed time; wall clock is diagnostic only |
| Coalescing | Same viewport/behavior key; newer pending focus supersedes older |
| Safety | Wrong world/session fails closed; client never expands visibility |

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G3-W01` | Version types | Two command/result schemas and compatibility fixtures | Unknown version/type fails clearly |
| `G3-W02` | HUD origin | Explicit-action API, pending state and result presentation | No map/engine dependency |
| `G3-W03` | H2M route | Validation, ordering, dedup, coalescing, timeout, restart, capability checks | Owns no domain state |
| `G3-W04` | Map destination | Semantic re-resolution and focus-facade invocation | Camera/focus remains map-owned |
| `G3-W05` | No-op and switch | Default-off route and fake endpoints | Disables without affecting cores or M2H |
| `G3-W06` | EX-X03 | Entity/location success and named-failure traces | One action yields at most one apply |
| `G3-W07` | EX-X05 | Duplicate/reorder/loss/restart/cycle workload | Zero duplicate apply/loop; bounded pending termination |

## Sequence

Version schemas/fakes; build origin and destination independently; add only the H2M route; prove
`FocusEntity`; add `FocusLocation` when its identity closes; then run restart, timeout, loop and rollback
evidence. G3 may run beside G4 after both of its own ports stabilize.

## Test matrix

| Case | Expected result |
|---|---|
| Current permitted target | Applied with destination projection revision |
| Synchronizing within deadline | Bounded deferred, then terminal result |
| New same-key focus | Older pending request superseded |
| Unavailable/missing/malformed/unauthorized | Named result; HUD remains useful |
| Different world/session | Fail closed |
| Duplicate retry | At most one destination apply |
| Restart | Inappropriate pending work expires; no replayed camera action |
| H2M apply | No automatic M2H emission |
| Disabled route | No-op/unsupported result; both cores remain useful |

Pointer, keyboard and screen-reader initiation expose equivalent semantic outcomes. Critical results do not
use hue alone. Diagnostics retain bounded type/result/latency/origin/capability metadata.

## Rollback and ticket slicing

Disable H2M, expire pending requests, restore no-op, and preserve both core states. Never reverse an
already applied camera action because an acknowledgement timed out. Suggested later scopes: schemas;
origin; route; destination; EX-X03; EX-X05/rollback. Keep `FocusLocation` gated if identity remains open.

## Exit checklist

- [ ] Exact two-command roster is preserved.
- [ ] Endpoints are semantic and renderer/UI neutral.
- [ ] Results, dedup, coalescing, timeout, restart and loops are tested.
- [ ] Map owns applied camera/focus.
- [ ] No automatic M2H echo occurs.
- [ ] Independent disable and rollback pass.

