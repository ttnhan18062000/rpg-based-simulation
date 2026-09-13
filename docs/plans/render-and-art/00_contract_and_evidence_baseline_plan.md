---
status: active
layer: architecture
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, live-map, hud, protocol, planning]
---

# Detailed Plan 00 — Contract, Ownership, and Evidence Baseline

## Outcome

Close `LMSI-G0` by making the renderer and surface work safe to scope. This plan resolves ownership,
semantic identity, interaction boundaries, evidence governance, and known planning contradictions. It
creates no runtime component and approves no renderer.

## Authority and reuse

- Parent: [milestone plan](../live_map_rendering_and_surface_integration_milestone_plan.md), `LMSI-G0`.
- Planning/evidence inputs: the P2 [renderer architecture](../../brainstorm/render-and-art/live_map_rendering_engine_architecture_proposal.md)
  and P1 [surface architecture](../../brainstorm/render-and-art/live_map_hud_surface_integration_architecture.md).
  They govern this package's planning assumptions after review but remain proposals: neither owns delivery,
  promotes itself to P1, or authorizes a production decision.
- Existing delivery owners remain the [HUD roadmap](../hud_delivery_roadmap.md), the
  [Live Map scaling roadmap](../live_map_scaling_roadmap.md), and their tickets.
- The server and 39-phase mutation pipeline remain authoritative; client contracts never authorize
  visibility or mutate simulation state.

## Entry conditions

1. A human accepts the milestone structure as a planning basis.
2. An owner is available to resolve each decision below.
3. The current Canvas path and existing reconnect evidence remain available as the control history.

## Work packages

| ID | Work | Required output | Acceptance |
|---|---|---|---|
| `G0-W01` | Incorporate and cross-link planning inputs | Recognized document authority chain and generated-index regeneration task | No proposal is mistaken for implementation authority; no generated registry is hand-edited |
| `G0-W02` | Assign accountable roles | Named owner map for projection, protocol, LM, HUD, H2M, M2H, OBS, HRC/PREF, accessibility, evidence, release and privacy | Every later package has one accountable decision route; architecture docs are not labeled delivery owners |
| `G0-W03` | Fix projection identity vocabulary | Versioned glossary for world, session, stream, map, projection revision, tick and semantic target identities | Cross-world/session input fails closed; snapshot/delta/reconnect terminology is unambiguous |
| `G0-W04` | Resolve first-slice interaction decisions | `FocusLocation` identity; local-selection versus explicit-inspect gesture; pointer and keyboard focus behavior | H2M and M2H schemas can be scoped without UI-component or renderer details |
| `G0-W05` | Define envelope and capability baseline | Minimal common envelope fields, version policy, capability negotiation, monotonic timeout rule and per-origin dedup rule | H2M/M2H can share mechanics without becoming a generic bidirectional event bus |
| `G0-W06` | Separate support families | Owner/schema sketches for OBS, HRC, PREF and diagnostics | None routes through H2M/M2H; OBS remains server-authorized |
| `G0-W07` | Approve evidence governance | Charter template, result model, storage location, environment manifest and reviewer roles | Thresholds and allowed conclusions are fixed before results are inspected |
| `G0-W08` | Repair Canvas control evidence | Reproducible current-browser baseline or explicit inconclusive report with rerun owner | Raw timing/backlog/memory/startup/payload evidence is retained; prior DONE status is not rewritten |
| `G0-W09` | Reconcile active-plan overlaps | Written routing for HUD M1–M4, Live Map M2/M3, QA renderer and new seam work | No duplicate implementation scope or contradictory sequencing remains |

## Decision register

| Decision | Owner | Blocks | Does not block |
|---|---|---|---|
| Accountable people for all capability families | Frontend architecture lead | Any implementation-ticket approval | Review and documentation |
| World/session/stream/map identity | Protocol/session owner | Live contracts, renderer continuity and OBS transition proof | Fixture-only reducer design |
| `FocusLocation` semantic identity | HUD workflow + map schema owners | Final H2M location schema | `FocusEntity` work |
| Explicit inspect gesture and focus result | UX + accessibility owners | M2H implementation/acceptance | Map-local selection and HUD fixture work |
| Numeric latency, frame, payload, queue, copy and drift budgets | Product/performance/operations | Production-facing exits | Functional fake-port tests |
| Diagnostic redaction/retention/cardinality | Operations/privacy | Production diagnostics | Sanitized local fixtures |
| Version rollout policy | Deployment/protocol | Production compatibility | Isolated contract tests |

## Sequence and parallelism

1. `W01–W02` establish authority and ownership.
2. `W03–W06` may proceed in parallel, with a joint vocabulary review before closure.
3. `W07` must close before `W08` or any candidate benchmark is interpreted.
4. `W08` and `W09` may run in parallel.
5. G0 closes only after unresolved items have an exact downstream blocker classification.

Stable LM and HUD ports may be scoped as soon as the relevant identity, envelope, and owner decisions
close; they do not wait for every G0 measurement to finish. Live candidate conclusions still wait for the
valid Canvas control.

## Evidence charter minimum

Every experiment charter records: question; owner; candidate/control; immutable fixture and hash;
environment; warm-up and repetitions; functional assertions; numeric thresholds and rationale; raw output
location; pass/fail/inconclusive rules; allowed and prohibited conclusions; dependency cleanup; reviewer;
and rerun/stop rule. An incomplete run is inconclusive, never a pass.

## Verification

- Contract glossary review against both source architectures.
- Schema examples for wrong-world, gap/resync, duplicate, timeout and unsupported-capability cases.
- Fake-port routing proof that OBS/HRC/PREF traffic never appears on H2M/M2H routes.
- Canvas baseline capture validated for declared browser/hardware, native scale and workload.
- Cross-plan review confirming Live Map M2 remains measured Canvas optimization and M3 remains
  independently bandwidth-gated.

## Rollback and cleanup

This is documentation and evidence work. Withdraw unaccepted contract wording, archive invalid result
bundles as inconclusive, and preserve the prior Canvas baseline. Do not rewrite historical ticket outcomes.
Any experimental dependency discovered during baseline repair must be removed unless separately approved.

## Ticket-ready slicing after G0 approval

Suggested independent scopes are ownership/contract decisions, fixture-corpus preparation, evidence
harness repair, and support-family fake ports. Do not combine these with PixiJS adoption or directional UI
behavior. The normal ticket workflow must still investigate real files and conflicts before implementation.

## Exit checklist

- [ ] All capability and evidence owners are named.
- [ ] Projection and semantic identity vocabulary is accepted.
- [ ] `FocusLocation` and explicit-inspect decisions are resolved or narrowly blocked.
- [ ] H2M, M2H, OBS, HRC, PREF and diagnostics remain distinct.
- [ ] Evidence charter and result retention are approved.
- [ ] Canvas control evidence is valid or has a named rerun path.
- [ ] Existing-roadmap overlaps are reconciled.
- [ ] No unresolved item is treated as a global blocker without cause.
