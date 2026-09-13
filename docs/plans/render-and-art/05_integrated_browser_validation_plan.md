---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, live-map, hud, browser, validation]
---

# Detailed Plan 05 — Integrated Browser Validation

## Outcome

Close `LMSI-G5` by proving Live Map Core, HUD Core, minimum H2M, minimum M2H, and only the required support
families together in the browser. The result supports a later human adoption decision; it is not a
production rollout and gives no native-readiness claim.

## Entry conditions

- G1 and G2 independently pass.
- G3 and G4 independently pass with their exact first-slice rosters.
- A support-family applicability record exists: HRC is required; PREF is required at least for reduced
  motion; OBS is required only when the selected workflow changes observed subject/scope, otherwise it has
  an explicit not-applicable rationale and uses an already authorized projection.
- Diagnostics has an owner, bounded/redacted schema, failure policy and focused evidence.
- `G5-DR-01` names the renderer used for this integration run and cites eligible G1 evidence. Canvas is
  eligible only under a retain-Canvas disposition and after passing the G5 charter's functional/numeric
  control thresholds. PixiJS or live Godot is eligible only after passing the renderer proposal's
  [Section 16.3 browser/live gates](../../brainstorm/render-and-art/live_map_rendering_engine_architecture_proposal.md#163-browserlive-experiment-passfail-gates).
  This decision selects an EX-X07 test candidate only, not a production renderer.
- Canvas fallback, both directional switches and rollback owners are available.
- Production-facing numeric thresholds, environment matrix and evidence retention are approved before run.

## Browser topology

One browser application uses one validated reducer and reduced presentation store. LM and HUD consume
separate selectors and own separate interaction state. In-process H2M and M2H use direction-specific ports.
OBS, HRC, PREF and diagnostics remain separate. A browser-tab/process crash removes both surfaces; this
plan does not claim process-level independence.

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G5-W01` | Compose four capabilities | Integration shell using stable LM/HUD selectors and direction-specific ports | No shared-selection authority or direct cross-callback |
| `G5-W02` | OBS integration | Server-validated authorize/deny/revoke and projection-transition path | No optimistic reveal or H2M/M2H routing |
| `G5-W03` | HRC integration | Resize/DPR/suspend/resume/readiness-generation path | No false readiness; stale renderer generation rejected |
| `G5-W04` | PREF integration | Versioned reduced-motion and approved setting fan-out | Partial failure visible; critical semantics preserved |
| `G5-W05` | Diagnostics integration | Bounded/redacted metrics, trace correlation, evidence export and unavailable/backpressure policy | Observational only; no command routing or unbounded IDs; loss cannot corrupt core state |
| `G5-W06` | Six-mode harness | Reproducible mode matrix and controls | Every isolation mode runs without corrupting another capability |
| `G5-W07` | Integrated workflow | Focus and explicit inspect across current projection | Exact rosters, truthful outcomes and no echo loops |
| `G5-W08` | Fault/recovery campaign | Component, route, projection, coordinator, diagnostics and control-family faults | Surviving capability and recovery match declared domain |
| `G5-W09` | Browser quality campaign | Performance, accessibility, security, observability and native-scale readability evidence | All applicable Must and predeclared thresholds classified |
| `G5-W10` | Rollback rehearsal | Canvas restoration and independent direction/support-family disablement | Prior usable browser path restored without state corruption |
| `G5-W11` | Adoption-review bundle | Compatibility matrix, raw evidence, costs, risks and disposition | Recommends retain/revise/proceed only; no automatic migration |

## Mandatory six modes

| Mode | LM | HUD | H2M | M2H | Required proof |
|---|---:|---:|---:|---:|---|
| Live Map Core only | On | Absent/stub | Off | No-op | Rendering, local input, recovery; zero HUD dependency |
| HUD Core only | Absent/stub | On | No-op | Off | Investigation/accessibility; zero map dependency |
| Both cores, interaction off | On | On | Off | Off | Shared projection without interaction-state coupling |
| H2M only | On | On | On | Off | Focus roster/results and zero reverse echo |
| M2H only | On | On | Off | On | Inspect roster/focus behavior and zero reverse echo |
| Full integration | On | On | On | On | First-slice workflows plus required OBS/HRC/PREF |

## Fault and recovery matrix

| Fault | Required surviving behavior | Recovery gate |
|---|---|---|
| Map unavailable/reinitializing | HUD stays usable; H2M unavailable/deferred; M2H absent | New renderer generation and HRC handshake |
| HUD unavailable/reloading | Map-local use remains; M2H unavailable/local | New HUD generation; no expired-intent replay |
| Projection gap/stale stream | Shells show stale truthfully; wrong world/session fails closed | Protocol resync and pending-work invalidation |
| One direction fails | Both cores and other direction remain | Disable/restart only failed adapter |
| Coordinator fails | Cores and separate support families may remain | New generation; pending work terminates; no blind replay |
| OBS denied/revoked | No new information revealed | Re-auth/request/resync to permitted projection |
| HRC fails | No fake renderer readiness | Re-handshake before renderer-dependent interaction |
| PREF fails | Last safe preference remains; failure visible | Apply latest version after readiness |
| Diagnostics sink fails/backpressures | Cores and interactions continue; bounded drop/count is visible locally | Reset sink/export path; never block or mutate domain state |
| Whole tab/process fails | No in-runtime capability survives | Browser/session restart and authoritative resync |

## Quality evidence

- Protocol correctness: version, snapshot consistency, gaps, duplicates, dictionary and resync.
- Renderer: native-scale crowded semantics, picking order, visibility revocation and fallback.
- Performance: frame distributions, long frames, tick-to-visible latency, queues, memory, startup,
  reconnect, payload and selected scale counters.
- Accessibility: keyboard path, predictable focus, screen-reader results, reduced motion and no hue-only
  critical distinction.
- Security: opaque identities, server-side authorization, bounded schemas/rates and sanitized telemetry.
- Recovery: every fault above, directional rollback, Canvas fallback and state continuity.
- Build/operations: reproducible browser artifact, dependency manifest and diagnostic bundle.

## Sequence

Approve `G5-DR-01` and the support-family applicability record; compose with interactions off; integrate
and prove each applicable support family and diagnostics separately; run H2M-only and
M2H-only; run full workflow; inject faults; execute quality workloads; rehearse rollback; then assemble the
review bundle. Do not enable both directions first and infer their independent readiness afterward.

## Failure and rollback

Any mandatory mode, security, accessibility or rollback failure is a failed G5 run. Missing environment or
raw evidence is inconclusive. Restore Canvas, turn both directional adapters off, reset coordinator
generation and retain truthful unavailable states. Candidate artifacts may be archived/removed without
reverting either core. A rerun requires a new/updated charter, not post-result threshold changes.

## Ticket-ready slicing

Potential scopes: G5 renderer/applicability decision; four-capability composition; applicable OBS; HRC;
PREF; diagnostics; six-mode harness; integrated workflow; fault campaign; quality campaign; rollback
rehearsal; evidence review. Keep production adoption, default switch and Canvas deletion out of these
tickets.

## Exit checklist

- [ ] All six modes pass.
- [ ] G1–G4 evidence remains independently valid.
- [ ] `G5-DR-01` names an eligible test renderer without selecting production technology.
- [ ] Support-family applicability is explicit; HRC, reduced-motion PREF and diagnostics pass.
- [ ] Applicable OBS/HRC/PREF and diagnostics are separate and emit no H2M/M2H traffic.
- [ ] Fault, performance, accessibility, security and observability gates pass.
- [ ] Canvas and directional rollback rehearsal passes.
- [ ] Result supports only a later browser adoption review.
- [ ] No native, final-art or production-migration claim is made.
