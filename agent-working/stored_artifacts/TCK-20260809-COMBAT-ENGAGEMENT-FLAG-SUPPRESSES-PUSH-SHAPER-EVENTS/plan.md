---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS
artifact_type: plan
tags: [combat, simulation-quality, feature-flags]
---

# Plan — TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS

## Real fix: add the missing `.merge()` call

`src/engine/pipeline.py:258`, change:
```python
update = run_phase("combat_engagement", update, lambda u: CombatEngagementPhase.apply(state), "ENABLE_COMBAT_ENGAGEMENT")
```
to:
```python
update = run_phase("combat_engagement", update, lambda u: u.merge(CombatEngagementPhase.apply(state)), "ENABLE_COMBAT_ENGAGEMENT")
```
Real, minimal, one-line, directly matches the file's own already-established precedent (line 152,
`information_belief`'s own identical `lambda u: u.merge(...)` pattern).

## What is deliberately NOT touched
- `CombatEngagementPhase.apply()`'s own real posture-evaluation logic — untouched; the bug is
  entirely in how its own output gets chained, not in what it computes.
- The real, secondary, smaller tick-budget-pressure effect (6.2%→7.1%) — a real, disclosed,
  separate finding, not fixed here (fixing the merge bug is the real, primary, sufficient fix;
  the secondary effect doesn't independently warrant its own code change).
- The real, much bigger, disclosed-but-out-of-scope chronic tick-budget-exceeded condition
  (`persistence` phase's own dominant real cost) — a separate, real, systemic performance
  question, not this ticket's own scope.
- Any of the 17 real SimQ calibration profiles — none currently enable this flag; no profile
  change is needed to realize this fix's own real benefit (it activates automatically for any
  future scenario/test that turns the flag on).

## Rejected alternative
- **Also fixing the secondary tick-budget-pressure effect** (e.g. optimizing
  `CombatEngagementPhase.apply()`'s own real per-tick cost): rejected — the primary,
  deterministic merge bug fully explains the observed 100%→0% suppression on its own; the
  secondary effect is real but small and doesn't independently justify a performance-tuning
  change without its own separate justification.

## Verification plan
1. Unit test verifying `combat_engagement`'s own real phase registration preserves prior
   accumulated `StateUpdate` state (a hand-constructed `update` with a real, non-empty
   `entity_updates` entry for an entity NOT touched by `CombatEngagementPhase.apply()`'s own
   real filtering, confirming it survives the phase intact).
2. Full scoped pytest: wherever `pipeline.py`'s own existing tests live, plus
   `tests/domains/combat_engagement/` (or wherever that domain's own tests live),
   `tests/unit/combat/`, `tests/unit/tactical/`.
3. Real corpus re-verification (2000-tick, `dungeon_crawl_seed42`, `ENABLE_COMBAT_ENGAGEMENT=ON`
   explicitly forced, the exact condition that previously showed 100% suppression): confirm
   `combat_engagement_started/ended`/`combat_resolved`/`combat_damage`/`entity_killed` now fire
   alongside `combat_kill`, matching the corpus-default (flag-off) baseline's own real event
   presence.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md identifies the exact real mechanism | Done — a missing `.merge()` call, confirmed via direct source read and real corpus A/B testing |
| Concrete recommendation produced | Done — fix implemented |
| Real corpus re-verification | Test phase |
| Scoped pytest passes | Test phase |
