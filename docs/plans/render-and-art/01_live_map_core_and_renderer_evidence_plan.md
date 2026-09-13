---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, live-map, rendering, performance, experiments]
---

# Detailed Plan 01 — Live Map Core and Renderer Evidence

## Outcome

Close `LMSI-G1`: produce an independently testable, renderer-neutral Live Map Core and valid evidence for
the next browser-renderer decision. The result may be “retain Canvas.” Passing an experiment does not
adopt a dependency or authorize migration.

## Boundaries

Live Map Core owns presentation reduction consumers, scene projection, map-local camera/hover/selection,
picking feedback, minimap, visibility presentation, frame sampling, recovery, diagnostics and explicit
M2H emission. It owns no HUD route/history/focus, simulation outcome, observation authorization, or
renderer-specific cross-surface contract.

Canvas remains the control and rollback path. PixiJS is the next disposable browser experiment. Godot is
allowed only under its documented offline or live trigger. Existing Live Map M2 owns measured Canvas
optimization; M3 owns separately justified server interest management.

## Entry conditions

- G0 has approved protocol vocabulary, evidence rules and owners.
- Live experiments have coherent snapshot/delta/gap/resync fixtures and an authentication approach.
- The Canvas baseline environment and workloads are declared.
- Any work touching existing M2/M3 scope is routed to its current owner.

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G1-W01` | Protocol validator boundary | Typed validation result and named schema/version/catalog/bounds errors | Malformed or incompatible data never reaches reduction |
| `G1-W02` | Deterministic presentation reducer | Immutable coherent commits for snapshot/delta/gap/resync/restart | Replay produces identical semantic commits; no gameplay rule is duplicated |
| `G1-W03` | Reduced store and LM selectors | Atomic publication and render-safe spatial slices | No partial snapshot is visible; selectors contain no HUD state |
| `G1-W04` | Tick/frame policy | Previous/current projection sampling, bounded queue/coalescing and cosmetic interpolation rules | No invented authoritative state; gaps trigger declared resync |
| `G1-W05` | Map-local state boundary | Camera, hover, local selection, focus, minimap and picking facades | Functions without HUD; applied H2M effects remain map-owned |
| `G1-W06` | Renderer adapter seam | Framework-neutral scene/projection contract with Canvas adapter | Core has no PixiJS/Godot types and Canvas behavior remains available |
| `G1-W07` | LM-only harness | Recorded replay, fake clock/input, no-op M2H, missing-ID and disconnect cases | EX-X01 requirements pass and no HUD call occurs |
| `G1-W08` | Canvas control and bounded optimization | Valid baseline plus at most one approved profile-guided optimization round | Same fixture before/after; semantic/accessibility non-regression; M2 ownership respected |
| `G1-W09` | PixiJS EX-F/EX-P | Disposable candidate and complete result bundle | Identical fixture and declared browser matrix; every Must and numeric charter gate classified |
| `G1-W10` | Conditional Godot evidence | EX-W01 offline result or exact live Variant A/B result only after trigger | Claims remain limited to tested workflow/mapping; web C# path is excluded |
| `G1-W11` | Candidate disposition | Retain-Canvas, revise/rerun, stop, or recommend later adoption ADR | Raw evidence and costs are reviewable; no automatic production selection |

## Implementation order

1. Build fixture validity and validator/reducer/store seams (`W01–W03`).
2. Define tick/frame behavior and LM selectors before touching a candidate (`W04`).
3. Stabilize map-local and renderer ports (`W05–W06`). These ports can unlock G3/G4 work before G1 closes.
4. Prove LM-only behavior with Canvas (`W07`).
5. Capture Canvas control; run one bounded optimization only if the profile and existing M2 gate justify it
   (`W08`).
6. Run PixiJS against the unchanged semantic fixture/control (`W09`).
7. Run Godot only if its independent trigger passes (`W10`).
8. Produce a bounded disposition (`W11`).

Optional offline Godot authoring may run beside steps 1–5 using frozen fixtures. A live Godot experiment
waits for the protocol seam and one of: native desktop is a committed Must; optimized Canvas/PixiJS fails
a mandatory capability/performance gate; or offline evidence demonstrates a strategically required benefit.

## Renderer-neutral seam acceptance

- Validator, reducer and store are usable without React, Canvas, PixiJS or Godot.
- LM selectors expose semantic IDs and presentation values, never UI component references.
- Static/dynamic layers, entities, objects, visibility/fog, remembered state and missing definitions have
  explicit fallbacks.
- Camera and local selection are map-owned. Hover and minimap navigation emit no M2H.
- The LM harness runs with HUD absent and M2H disabled.
- Disconnect, stale, gap, resync and unavailable states are visible and recoverable.
- Capture/replay and diagnostics are observational and sanitized.

## Experiment matrix

| Experiment | Workload | Minimum decision gate | Retained evidence | Allowed conclusion |
|---|---|---|---|---|
| Protocol/replay | Snapshot, delta, duplicate, reorder, gap, restart, missing IDs | All semantic assertions pass | Fixtures, hashes, reducer traces | Seam is ready for renderer comparison |
| Canvas control | Normal, crowded, soak at native scale | Complete environment and raw distributions | Frame/backlog/memory/startup/payload captures | Baseline only |
| Canvas optimization | Same control with one measured change | Declared improvement plus zero semantic/accessibility regression | Before/after traces and patch notes | Retain or proceed to comparison |
| PixiJS EX-F | Same semantic and platform fixture | All required features and fallback behavior pass | Build manifest, captures, fault results | Functional candidate eligibility |
| PixiJS EX-P | Same workload/browser matrix | Predeclared frame, memory, startup and interaction budgets pass | Raw distributions and profiles | Comparative evidence only |
| Godot EX-W01 | Small disposable content workflow | Declared authoring/capability and reproducible build checks pass | Project manifest, captures, build timings | Offline workflow evidence only |
| Live Godot | Exact A/B integration question | Browser/platform, drift, reconnect, build and recovery gates pass | Raw result bundle and manifest | Evidence for the named mapping only |

## Failure, rollback, and cleanup

- Protocol/reducer failure blocks live candidate interpretation; fix the seam or classify inconclusive.
- Candidate failure removes or archives the disposable artifact and dependency.
- Canvas stays runnable and is restored as default after every experiment.
- A failed optimization restores the control patch; it does not trigger interest management.
- An invalid environment or missing threshold produces inconclusive evidence and a named rerun/stop choice.
- No candidate code becomes a shared production abstraction before a later ADR and ticket.

## Ticket-ready slicing after entry approval

Potential scopes: fixture/validator; reducer/store; LM selectors and tick/frame policy; map-local facade;
Canvas adapter and LM harness; Canvas evidence repair; PixiJS functional experiment; PixiJS performance
experiment; conditional Godot experiment; evidence review. Keep candidate experiments disposable and
separate from production adoption.

## Exit checklist

- [ ] Replay corpus and reducer continuity pass.
- [ ] Renderer-neutral store/selectors and map-owned local state pass.
- [ ] LM-only harness passes with no HUD and no-op M2H.
- [ ] Canvas control is valid and remains the rollback path.
- [ ] PixiJS result is pass, fail or inconclusive under a preapproved charter.
- [ ] Any Godot result stayed within its trigger and exact question.
- [ ] Performance, accessibility, security, recovery and observability evidence is retained.
- [ ] The disposition authorizes evidence review only, not production adoption.
