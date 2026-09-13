---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, live-map, hud, native, conditional]
---

# Detailed Plan 06 — Conditional Native Topology Validation

## Status and activation rule

This plan describes `LMSI-G6` but is dormant until product/release owners declare native delivery a Must
or otherwise formally justify it and select exactly one N1, N2 or N3 topology question. Its existence does
not authorize Godot, native packaging, dependency installation, or a ticket.

## Topology candidates

| Topology | Projection shape | Principal question |
|---|---|---|
| N1 | Godot owns presentation; embedded React HUD receives bounded view models | Can bridge volume, focus, reducer and whole-host recovery meet the requirement? |
| N2 | Godot and React HUD use separate projections/clients | Can drift, fan-out, auth and independent recovery remain bounded? |
| N3 | Shared local presentation service feeds both surfaces | Is the extra service lifecycle/security/operations cost justified? |

N3 has the highest complexity and needs affirmative evidence. N1 never provides HUD survival after a
whole-host crash. N2 process isolation is not assumed merely because clients are logically separate.

## Entry conditions

- Native scenario, target environment, sponsor and support lifetime are approved.
- One exact topology and, if Godot is involved, one Variant A/B live-integration question are named.
- Renderer-facing protocol, snapshot/delta/reconnect fixtures and authentication approach are stable.
- Shared logical LM/HUD/H2M/M2H contracts are stable.
- Build, startup, package, bridge/copy/drift, security, accessibility and recovery budgets are approved.
- Experiment artifact is disposable and has a cleanup owner.

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G6-W01` | Charter exact topology | Process map, ownership, requirement and prohibited inference | No generic “native” experiment |
| `G6-W02` | Reproducible build | Headless CI build/export, package manifest and target install/start procedure | No developer GUI dependency; versions pinned |
| `G6-W03` | Projection/data path | Chosen reducer/client/service mapping and coherent fixtures | No duplicated gameplay authority; drift policy explicit |
| `G6-W04` | Physical adapters | WebView/CEF/plugin/IPC boundary as applicable | Typed/versioned, bounded and authenticated |
| `G6-W05` | Input/accessibility | Keyboard, pointer/controller, focus, screen reader and reduced motion across boundary | Predictable focus and non-hue semantics |
| `G6-W06` | Performance/cost | Startup, artifact, memory, copy, queue, message rate and drift measurements | Every predeclared threshold classified |
| `G6-W07` | Security/operations | Local-boundary threat review, updates, diagnostics and ownership | No arbitrary path/code execution; secrets and logs bounded |
| `G6-W08` | EX-X08 faults | Scene, reducer, WebView, bridge and whole-host failure campaign | Results match exact topology guarantees |
| `G6-W09` | Cleanup and disposition | Artifact removal/archive and exact pass/fail/inconclusive report | Prior host restored; conclusion cannot generalize |

## Topology-specific evidence

| Area | N1 | N2 | N3 |
|---|---|---|---|
| Reducer failure | Godot presentation and HUD view-model staleness | One or both clients and convergence | Service failure affects both |
| Bridge | View-model/query volume and focus | Small interaction IPC; possibly shared host | Local RPC plus interaction ports |
| Drift | Bridge freshness/revision | Tick/stream convergence and visible stale policy | Service/client version and subscription lag |
| Whole-host failure | Map and embedded HUD both lost | Depends on proven process map | Depends on service/surface supervision |
| Recovery | Renderer/WebView generations, no blind replay | Each client reauth/resync and interaction re-handshake | Service lifecycle plus client resubscription |

## Experiment order

1. Review the charter and topology diagram.
2. Produce the minimum reproducible build.
3. Validate semantic fixture equivalence before performance claims.
4. Exercise input/focus/accessibility and security boundaries.
5. Measure startup/package/copy/queue/drift under the declared workload.
6. Inject all applicable failures and rehearse recovery.
7. Remove/archive the artifact and write the topology-specific disposition.

Browser evidence can seed fixtures but cannot substitute for native measurements. A live Godot experiment
performed earlier under G1 can be reused only where its exact mapping, platform and workload match.

## Failure and rollback

Any topology guarantee, security gate, accessibility requirement or numeric threshold failure is fail.
Unverified process boundaries, non-equivalent fixtures or incomplete build evidence are inconclusive.
Disable physical adapters, expire pending work, remove/archive native artifacts and dependencies, and
restore the prior browser/host path. Choosing another topology requires a new charter.

## Ticket-ready slicing

Only after activation: charter/build skeleton; projection mapping; physical adapter; accessibility/input;
performance evidence; security/operations; fault/recovery; cleanup/review. Never scope all three
topologies or combine experiment and production migration.

## Exit checklist

- [ ] Native requirement and one topology are explicitly approved.
- [ ] Process/failure boundaries are demonstrated, not inferred.
- [ ] Build, protocol, accessibility, security and operational evidence pass.
- [ ] Copy/queue/drift/startup/package budgets pass.
- [ ] All applicable failure domains and rollback pass.
- [ ] Result applies only to the named topology.
- [ ] No Godot/Unity production selection or browser replacement is implied.

