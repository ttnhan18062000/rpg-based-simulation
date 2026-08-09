---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX

## Real fix: emit `combat_resolved` alongside `combat_engagement_ended(KILL|ESCAPED)`

In `src/observability/event_shapers.py`'s `CombatShaper.shape()`, at the same two real sites that
already construct `combat_engagement_ended` for the `KILL` outcome (inside the
`outcome_kind == "KILL"` block) and the `ESCAPED` outcome (the new `combat_escape` property-tag
branch), also append a real `SimulationEvent(event_type="combat_resolved", event_category="combat",
...)`. `CombatScorer.score()` requires no specific payload fields (`src/simulation_quality/
scorers/combat.py:71-72` — flat `+3` on event-type match alone), so the payload can carry the
same real snapshot data already computed for `combat_engagement_ended` (defender/attacker
snapshots, outcome) for traceability, without inventing new fields.

`CAUGHT_FLEEING`/`PURSUIT_ABANDONED` do **not** get a `combat_resolved` emission — confirmed
semantic mismatch in investigation.md.

## Doc corrections
- `docs/simulation_quality/event_type_coverage.md` §3 — the section currently has no COMBAT
  subsection at all (a real, pre-existing gap in the doc's own completeness, not previously
  disclosed). Add `### §3.6 Combat (CombatScorer)` (renumbering subsequent sections if needed, or
  inserting between §3.4 Economy and the existing §3.5 Narrative — check current numbering at
  Implement time) documenting `combat_resolved` as now-resolved, matching the doc's own
  established "All previously listed gaps resolved by..." pattern for other pillars.
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT — add a real producer citation
  next to the `combat_resolved` row for traceability, matching this doc's own existing citation
  style elsewhere in the same table.

## What is deliberately NOT touched
- `combat_engagement_started`'s own registration in `event_type_coverage.md` §5 (Unscored
  Intentional) — stays as-is; add a one-line addition to its existing entry explaining the
  non-promotion decision (already partially covered by that entry's own "deferring the real
  pillar-scoring integration decision to a later ticket" language — this ticket is that later
  decision, for this specific event; update the wording to reflect the decision was made, not
  still deferred).
- `attrition_threshold_crossed` — untouched, confirmed genuinely separate in investigation.md.
- Any change to `CombatScorer`'s own scoring logic — it is already correct and ready; this ticket
  only adds the missing producer.

## Verification plan
1. Unit tests in `tests/unit/observability/test_event_shapers.py`: `combat_resolved` fires
   alongside `combat_engagement_ended(KILL)` and `(ESCAPED)`; does NOT fire for
   `CAUGHT_FLEEING`/`PURSUIT_ABANDONED`.
2. Full scoped pytest.
3. Real corpus re-verification (2000-tick, corpus-default flags, both worlds, with all 3 combat
   fixes from this session active): confirm `combat_resolved` fires at real, non-zero volume
   wherever `combat_engagement_ended(KILL|ESCAPED)` itself fires; if it doesn't fire naturally at
   this scale in a given world, disclose honestly per this session's own established precedent
   rather than force a claim.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms gap + mapping | Done |
| combat_resolved gets a real producer | Implement phase |
| event_type_coverage.md corrected | Document-Update phase |
| combat_engagement_started decision documented | Document-Update phase |
| Real corpus re-verification | Test phase |
| Scoped pytest passes | Test phase |
