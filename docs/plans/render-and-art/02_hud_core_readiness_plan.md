---
status: active
layer: frontend
authority: P1
audience: agent
date: 2026-09-09
tags: [architecture, hud, accessibility, planning]
---

# Detailed Plan 02 — HUD Core Readiness

## Outcome

Close `LMSI-G2` by proving the HUD-owned investigation core against fixtures while the map is absent and
H2M is disabled. This is an integration-facing supplement to the existing HUD roadmap, not a parallel HUD
redesign.

## Existing owner and boundaries

The [HUD roadmap](../hud_delivery_roadmap.md) remains authoritative for delivery:
`HUD M1 → M2 → M3 → M4`. M1 owns the thin foundation and durable navigation; M2 owns the investigation
vertical slice; M3 extracts demonstrated patterns and migrates remaining panels; M4 measures and
consolidates. This plan consumes only outputs needed for G2 and does not pull M3/M4 forward.

HUD Core owns workspace/route, investigation history, selected/list subject, inspector/tab,
filters/search, return context, DOM focus and accessible announcements. It may issue explicit H2M requests
through a port. It does not own camera, map focus, hover, map-local selection, renderer lifecycle,
observation policy, or simulation state.

## Entry conditions

- HUD M1 provides the durable navigation/state boundary required by HUD M2.
- G0 provides fixture identity vocabulary and a recording/no-op H2M result contract.
- Changes to HUD-owned files are sequenced through the existing HUD ticket owner.
- Fixture provenance and stale/unavailable states are declared before live-data claims.

## Work packages

| ID | Work | Deliverable | Acceptance |
|---|---|---|---|
| `G2-W01` | Map roadmap output to G2 | Note naming exact M1/M2 outputs and deferred M3/M4 work | No duplicate backlog or conflicting sequence |
| `G2-W02` | HUD selector fixtures | Deterministic entity/object/event/connection/observation fixtures | No renderer or map-state dependency |
| `G2-W03` | Navigation facade | Semantic open/resolve/history/return/focus operations | No React component names in M2H contracts |
| `G2-W04` | H2M origin port | Recording/no-op port with every named result | Explicit user action only; no direct canvas call |
| `G2-W05` | Truthful failure UI | Pending, rejected, stale, missing, unsupported and map-unavailable states | Investigation remains usable; no implied success |
| `G2-W06` | HUD-only harness | Map-absent, H2M-disabled fixture workflow | EX-X02 navigation, history, focus, filter and accessibility assertions pass |
| `G2-W07` | Live-data check | Protocol sufficiency report for selected workflow | Fixtures are not mislabeled as live readiness |

## Sequence and parallelism

1. Confirm M1/M2 ownership and file boundaries (`W01`).
2. Build fixture selectors and navigation facade in parallel where M1 permits (`W02–W03`).
3. Add recording/no-op H2M and truthful outcomes (`W04–W05`).
4. Run HUD-only isolation (`W06`).
5. Verify, but do not silently repair, the live data path (`W07`).

HUD fixture work may run beside G1 renderer experiments. G2 does not wait for PixiJS, Canvas
optimization, map availability, or M2H. Stable ports may unlock G3/G4 before all G2 acceptance closes.

## Required scenarios

- Notice/anomaly → locate → inspect → follow semantic relation → return.
- Duplicate/stale input and missing/unsupported object family.
- Map unavailable before or during a pending request, timeout and late result.
- Search/filter, scroll/return context and history preservation.
- Pointer action without forced DOM focus; keyboard/screen-reader action with predictable focus and announcement.
- No-op H2M and applied/rejected/deferred/superseded/timeout/unavailable/unsupported outcomes.

## Acceptance and rollback

- HUD remains useful with the map absent and never mutates map-owned state.
- Selectors/navigation are renderer-neutral; only explicit actions issue H2M.
- DOM keyboard, focus, announcement and non-hue requirements pass.
- Live-data gaps are reported separately.
- Rollback restores the recording/no-op H2M adapter while preserving HUD navigation and fixtures.
- If integration facade work conflicts with an owning HUD ticket, pause/revert only the facade.

## Ticket-ready slicing

Use existing HUD tickets for declared work. New scopes may cover fixture selectors, navigation facade,
recording/no-op H2M, HUD-only isolation, or live-data verification. Do not create M3/M4 children early.

## Exit checklist

- [ ] Required M1/M2 outputs are named and owned.
- [ ] Fixture selectors and navigation facade are stable.
- [ ] Recording/no-op H2M is independently switchable.
- [ ] HUD-only workflow and accessibility evidence pass.
- [ ] Map-unavailable and all named results are truthful.
- [ ] No renderer or map-owned-state dependency exists.

