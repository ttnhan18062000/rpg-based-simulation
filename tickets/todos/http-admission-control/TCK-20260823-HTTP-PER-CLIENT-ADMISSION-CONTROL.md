---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL
phase: open
date: 2026-08-23
tags: [architecture, observability, api-design]
---

# TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL

## Title
Per-client HTTP admission control extending `ObservabilityMode`'s NORMAL/PRESSURE/DEGRADED/SURVIVAL vocabulary

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/api/server.py` has no rate limiting or admission control — a single client (malicious,
buggy, or just noisy) can degrade service for every other tenant. Item 2 of 2 extracted from
`TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC` — depends on `TCK-20260823-HTTP-API-KEY-AUTH` landing
first, since per-client admission state is keyed by the client identity that ticket establishes.
The mode vocabulary to extend is `ObservabilityMode` (`NORMAL/PRESSURE/DEGRADED/SURVIVAL`,
`src/observability/event_recorder.py`) — **not** `RuntimeMode`
(`NORMAL/CONSTRAINED/DEGRADED/SURVIVAL`, `src/core/governance.py`), a second, differently-named,
easily-confused vocabulary serving an unrelated subsystem. This ticket's own acceptance criteria
match `ObservabilityMode`'s exact naming.

## Scope
- Extend `ObservabilityMode`'s vocabulary/pattern to the HTTP layer, **per-client** (not just a
  single global mode) — reuse the mode names and the `observability_status()`/`reset_mode()`
  accessor-pattern shape (`src/observability/event_recorder.py` §5,
  `docs/architecture/observability_hot_path_safety_contract.md` §5) as the template for an
  equivalent `admission_status()`/`reset_admission_mode()` pair, scoped per-client.
- Reuse `ResourceGovernor`'s hysteresis pattern (`src/engine/governor.py::evaluate()`/
  `_can_recover()`) — NOT `PhaseBudgetGovernor`, which has no hysteresis logic of its own (a
  factual correction from this ticket's parent investigation; do not propagate the doc's own
  mis-attribution into new code/comments). Escalation is immediate on any mode increase; recovery
  requires `dwell_time_ticks` elapsed plus `confidence_window_ticks` consecutive good samples,
  stepping down one level at a time. Reuse `RuntimeProfile`'s existing tunables
  (`recovery_watermark`, `dwell_time_ticks`, `confidence_window_ticks`,
  `src/config/profiles.py:42-44`) rather than inventing new ones.
- **Per-client state bounding**: a dict keyed by client ID holding each client's own
  mode/dwell-tick/confidence-window state is new, previously-unbounded state — this ticket must
  design and implement an eviction/TTL policy for stale/inactive client entries (this is flagged
  by the parent investigation as the single largest genuinely new design surface in this whole
  epic; do not treat it as an afterthought).
- Single-process in-memory token-bucket/sliding-window limiter — sufficient at current scale per
  the source audit's own explicit recommendation.
- Wire into `src/api/server.py` as FastAPI middleware or `Depends()` (Plan decision), reading the
  authenticated client identity `TCK-20260823-HTTP-API-KEY-AUTH` establishes — never reaching into
  `src/engine/governor.py` internals directly from `src/api/` (the existing API/engine module
  boundary is read-through-`V2EngineManager` only).
- Confirm and use `SURVIVAL` as the 4th tier name (matching `ObservabilityMode` and this ticket's
  own acceptance criteria) — `docs/audits/D23_architecture_resilience.md` §L is internally
  inconsistent and calls it `EMERGENCY` in one place; that is the source doc's own drafting error,
  not a real naming option to reconcile.

## Out of Scope
- Any new distributed/shared rate-limit infrastructure (Redis-backed or otherwise) — `redis` being
  an existing dependency is not license to use it here; single-process in-memory only.
- Modifying `ObservabilityMode`/`ObservabilityController` itself, or `RuntimeMode`/
  `PhaseBudgetGovernor`/`ResourceGovernor` — read/reuse their pattern, do not alter the existing,
  already-tested (`tests/unit/observability/test_obs_backpressure.py`, parity entry INFRA-199, P1)
  subsystems. If a shared parallel controller for the HTTP layer touches the same module as
  `ObservabilityController`, `test_obs_backpressure.py` becomes part of this ticket's own
  regression surface and must stay green.
- Auth itself (delivered by the sibling ticket this one depends on).

## Acceptance Criteria
- [ ] HTTP requests are admitted/throttled/shed **per-client**, keyed by the authenticated client
      identity from `TCK-20260823-HTTP-API-KEY-AUTH`.
- [ ] The mode vocabulary is exactly `NORMAL/PRESSURE/DEGRADED/SURVIVAL` (matching
      `ObservabilityMode`), never `RuntimeMode`'s `CONSTRAINED` naming or a third invented
      vocabulary.
- [ ] Escalation is immediate; recovery is gated by dwell-time + confidence-window, one mode level
      at a time — mirroring `ResourceGovernor`'s real hysteresis pattern.
- [ ] Per-client state has an explicit, tested eviction/TTL policy — no unbounded growth from an
      ever-increasing set of distinct client IDs.
- [ ] `tests/unit/observability/test_obs_backpressure.py` (the existing `ObservabilityMode`
      regression suite) stays green — confirmed if this ticket's implementation touches the same
      module, or confirmed inapplicable if it builds a fully parallel HTTP-side controller.
- [ ] `tests/api/` gains real, in-process `TestClient`-based tests covering per-client throttling
      behavior across at least 2 distinct simulated clients (one throttled, one unaffected).

## Related Tickets
- TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC (parent — extracted from here, 2026-08-23)
- TCK-20260823-HTTP-API-KEY-AUTH (sibling — this ticket depends on it; implement first)

## Related Docs
- docs/plans/http_admission_control_epic.md
- docs/architecture/observability_hot_path_safety_contract.md
- docs/audits/D23_architecture_resilience.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC/investigation.md (parent epic's
  shared investigation — read first; do not re-derive its findings)

## Related Code Areas
- src/api/server.py
- src/observability/event_recorder.py (read/reuse pattern, do not modify)
- src/engine/governor.py (read/reuse hysteresis pattern, do not modify)
- src/config/profiles.py
- expected: src/api/admission_control.py (or equivalent new module — exact name is a Plan decision)
- expected: tests/api/test_admission_control.py

## Assumptions / Open Questions
- Exact new module/file naming is a Plan decision, not fixed here.
- Whether this ticket builds a fully independent HTTP-side mode controller or literally reuses
  `ObservabilityController`'s class (parameterized per-client) is a Plan decision — Investigate
  should weigh both against `test_obs_backpressure.py`'s existing regression surface.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
