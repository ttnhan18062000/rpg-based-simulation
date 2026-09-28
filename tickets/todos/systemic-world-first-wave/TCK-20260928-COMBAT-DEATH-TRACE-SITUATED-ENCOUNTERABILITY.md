---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY
phase: open
date: 2026-09-28
tags: [cognition, simulation-quality, root-cause]
---

# TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY

## Title
Which traces does a combat death leave in an ordinary corpus run, and which of them could a
co-located or bonded observer legitimately receive?

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Observation of current behaviour only. Given a combat death in an ordinary corpus run, answer two
questions **separately**: which world-state changes or events it leaves behind, and which of those a
specified situated observer could legitimately receive — from where, and when.

A trace that exists but **cannot be encountered** is a valid outcome, reported as such. **This is
not a player-experience proof**, and nothing here claims `PLAYER-EXPERIENCED`.

Implements Card B0 of `docs/plans/systemic_world/ticket_planner_handoff.md` (branch
`systemic-world-roadmap-proposal` @ `43db4a7fc`, PR #249, unmerged) — **minus its first question**,
which is already owned; see Scope.

## Scope
- **Specified event, not substitutable:** a combat death in an ordinary corpus run — an entity
  killed in combat and recorded with `death_reason == "COMBAT"`. It does **not** depend on natural
  aging. If ordinary runs produce no combat death, the event question closes
  `BLOCKED_WITH_REASON`. **Do not substitute another event** — a replacement is a scoping decision
  returned to the roadmap.
- **Answer 2 — trace existence.** Which world-state changes or events does that death leave behind?
- **Answer 3 — situated encounterability.** Which of those traces could a co-located or bonded
  observer legitimately receive, from where, and when?
- Identify which surfaces are **developer-only and must be excluded** — event logs, inspectors, API
  presenters.
- Identify whether any existing path **leaks hidden truth**, e.g.
  `cognition.motivation.named_intention`, `strategic.blockers`, or location-independent reads.

## Out of Scope
- **Card B0's question 1 — "is perception live in production at runtime?" — is NOT in this ticket.**
  It is already owned by the open P1 ticket
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`, which answers it in more depth than a
  fresh runtime check would: it documents **three** distinct perception-shaped things and that
  nothing declares which is meant to be real. Adopt that ticket's findings; do not re-derive them.
  See Assumptions for why this matters.
- **Building or wiring perception.** If perception is inactive at runtime, record it as an engine
  foundation finding and close that strand with that result. The roadmap then proposes a separate
  perception-foundation epic. **Do not expand this ticket into building perception.**
- Turning on or changing perception in production. Any runtime check must observe current behaviour
  without altering it.
- Any player-facing projection, presentation, or UI work.

## Acceptance Criteria
1. Answers 2 and 3 are reported **separately**, never collapsed into one verdict.
2. The specified combat-death event was used, or the strand closed `BLOCKED_WITH_REASON` because an
   ordinary run produced no combat death. No substitute event was used.
3. Developer-only surfaces are explicitly enumerated and excluded from any encounterability claim.
4. Any hidden-truth leak found is named with its path, at minimum covering the private
   cognition/strategic fields listed in Scope.
5. No production behaviour was turned on or altered — the check is observation only, and this is
   evidenced.
6. `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s existing findings are cited for the
   perception-liveness question rather than re-derived, and any place where this ticket's runtime
   observation **contradicts** that ticket is reported as a contradiction rather than silently
   overriding it.
7. **Findings are NEVER recorded against SCP rows `PERC-01` / `KNOW-01`.** Those rows map only
   Combat's `tactical_decision`; observer evidence there would corrupt Combat's mapping. Record in
   roadmap §7.2 and §11 item 3 instead.
8. If a perception mechanism's real state differs from its registry entry, the entry is corrected
   through the registry process.
9. Findings are routed back to the systemic-world roadmap track (`world-rule-catalog-design`).

## Related Tickets
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — **open, P1, adopted for Card B0's
  question 1.** Explicitly framed as a scope-of-concept decision for the roadmap session, and
  deliberately reframed by peer review *away from* "just wire it up". Do not undo that framing.
- `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` — parallel wave item, independent.
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — parallel wave item; also concerns combat
  death, but at the authority/ordering level rather than the trace level.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card B0 (@ `43db4a7fc`).
- `docs/plans/systemic_world/roadmap.md` §7.2.
- `docs/plans/systemic_world/first_wave_plan.md` §2 Epic B0.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-inheritance-observer-encounter-findings.md` (on the
  unmerged branch above).

## Related Code Areas
- `src/core/cognition.py:28-33` — the perceived-entity record: id, kind, position, salience,
  confidence only. **No item fields.**
- `src/observability/event_extractor.py:1722-1762` — the grief trigger for trusted allies;
  location-independent, and carries the death rather than any inheritance.
- `src/systems/lifecycle_systems/lifecycle.py:252-257` — inheritance transfer, which carries **no
  origin marker**.
- `src/domains/perception/` — `filter.py::PerceptionFilterService`, `phase.py::PerceptionUpdatePhase`
  (the abstraction with no production caller).
- `src/world/perception/gate.py::PerceptionGate` — live and wired via `src/engine/tactical.py:181,199`.

## Assumptions / Open Questions
- **Why question 1 was split out rather than scoped here.** Card B0 states its own evidence limit:
  *"'Perception not live' comes from a grep and is `UNKNOWN` until a run confirms it. Perception may
  run through another path."* That other path is **already identified** in
  `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`: strategic cognition sources situational
  awareness through a direct `SpatialQueryService.nearby_entities()` call, and `PerceptionGate` does
  raw sense-detection for tactical targeting. Scoping question 1 fresh here would re-derive one of
  that ticket's three findings, eight days later and less completely — and risks landing the
  "just wire it up" conclusion it was explicitly reframed to prevent.
- **Q1.** Do combat deaths actually occur in an ordinary corpus run? This gates everything below and
  may itself close `BLOCKED_WITH_REASON`.
- **Q2.** Which traces could a co-located *or bonded* observer legitimately receive — and does the
  distinction between co-located and bonded change the answer? The grief trigger is
  location-independent, which makes this non-obvious.
- **Q3.** Is a trace that exists only in an event log a trace at all, for this ticket's purposes?
  Default: no — that is a developer-only surface. State the reasoning rather than assuming.
- **Contract-level risk.** Any runtime check must not turn on or change perception in production.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
