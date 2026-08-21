---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260821-LIVE-MAP-PERF-VALIDATION
phase: open
date: 2026-08-21
tags: [performance]
---

# TCK-20260821-LIVE-MAP-PERF-VALIDATION

## Title
Measure live-map render FPS and broadcast payload size at CLASS_B/CLASS_C scale

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants an explicit, measured validation step once the live map is actually connected to real data: observed FPS/update latency against a running world at CLASS_B and CLASS_C hardware-class scale, confirming broadcast payload size stays near the V1-measured ~75KB baseline, and confirming/documenting whether the frontend's interpolation math is genuinely delta-time-based -- investigation found no interpolation exists at all today, so this becomes a factual-finding item rather than a verification of an existing mechanism.

## Scope
- Run a measured session of >=1000 sampled render frames under bounded-viewport load at CLASS_B (2500 entities) and separately CLASS_C (500 entities), reporting p50/p95/p99 frame time and %frames>16.6ms, with full Scoped Claims discipline (Runtime Profile/Hardware Class/Scenario/Execution Mode/RuntimeMode stated)
- Measure per-update broadcast payload size (JSON and msgpack if the delta broadcast routes through it) at both classes, compared like-for-like against the ~75KB V1 baseline (stating explicitly that the V1 baseline was a full-state poll of ~360 entities, not a per-tick delta)
- Build the minimal frontend perf/e2e measurement harness needed (headless browser + rAF sampling + percentile aggregation) since none exists today (vitest only)
- Confirm and document whether interpolation exists in the frontend rendering path; investigation already found it does not (zero lerp/deltaTime/requestAnimationFrame hits in frontend/src/) -- report that entities currently snap to latest position on each data update, with no interpolation, as a factual finding
- Document any budget miss as a finding with root-cause hypothesis, explicitly deferred to a separate future ticket

## Out of Scope
- Fixing any performance issue this ticket finds (measurement and reporting only)
- Building an interpolation/lerp system -- none exists today; building one is new feature work, not in scope here
- Any change to production frontend/backend code paths

## Acceptance Criteria
- [ ] with a live world at CLASS_B (2500 entities) and separately CLASS_C (500 entities), a measured session of >=1000 sampled render frames under bounded-viewport load reports p50<=8ms,p95<=12ms,p99<=16.6ms plus %frames>16.6ms, reported with full Scoped Claims discipline
- [ ] measured per-update broadcast payload size (JSON and msgpack if the delta broadcast routes through it) at both classes stays within an explicitly stated tolerance of the ~75KB V1 baseline, comparing like-for-like (full-state-equivalent, not naive per-delta)
- [ ] report explicitly states that no interpolation system exists in the frontend today (entities snap to latest position on data update) as a factual finding, without proposing or building one
- [ ] any budget miss is documented as a finding with root-cause hypothesis, explicitly deferred to a separate future ticket

## Related Tickets
- TCK-20260821-PRESENT-MAP-STATIC
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-REST-MAP-STATIC-STATS
- TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/performance/perf_baseline_policy.md
- docs/engine/performance_contract.md
- docs/archive/performance/performance-report-api-payload.md

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/src/hooks/useSimulation.ts
- frontend/src/hooks/useCanvas.ts
- frontend/src/components/GameCanvas.tsx
- frontend/src/test/useSimulation.test.tsx
- src/api/ws/stream.py

## Assumptions / Open Questions
- perf_baseline_policy.md's CLASS_B/CLASS_C thresholds conflict with certification_contract.md §3's AND-rule (cores AND RAM) -- pre-existing unresolved conflict, not this ticket's job to fix, just state which definition was used
- fully blocked on the other four tickets landing -- nothing to measure until the live connection exists

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
