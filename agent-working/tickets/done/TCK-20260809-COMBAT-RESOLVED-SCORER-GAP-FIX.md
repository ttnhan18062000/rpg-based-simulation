---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
phase: done
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX

## Title
Wire `combat_engagement_ended`'s `KILL`/`ESCAPED` outcomes into the real, already-defined but
never-emitted `combat_resolved` COMBAT-pillar scorer signal (+3, the largest positive weight in
the pillar) — the pillar-scoring decision deferred by
`TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct continuation of the user's own 3-thread combat request from earlier this session. Thread
#3 ("decide whether `combat_engagement_started`/`ended` should be promoted from
`unscored_intentional` to real COMBAT pillar scoring") was explicitly deferred pending real combat
volume existing to evaluate against — now real (if still low-volume) combat exists in
`dungeon_crawl` after this session's own identity-resolver and pursuit-tracking fixes
(`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`, `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`).

Investigating this surfaced a more precise, higher-value finding than a generic "promote or
don't" decision: `docs/simulation_quality/quality_scoring_contract.md`'s own COMBAT pillar §5
table already defines `combat_resolved` as a real, scored event type — **weight +3, the single
largest positive signal in the whole pillar** ("Combat resolved (clear winner, loser retreats or
dies)") — and `CombatScorer` (`src/simulation_quality/scorers/combat.py:71-72`) already has a
real, ready handler for it. But `combat_resolved` has **never had a real producer anywhere in
`src/`** — confirmed via direct grep, and already self-disclosed in `CombatShaper`'s own class
docstring (`event_shapers.py:96`: "combat_resolved / attrition_threshold_crossed — dead code,
never emitted by any path in this repo; nothing exists to migrate"). This is a real,
long-standing `engine_emission_gap` (per `event_type_coverage.md`'s own classification scheme),
not previously connected to this session's own new `combat_engagement_ended` event by any prior
ticket.

`combat_engagement_ended`'s own 4 real outcomes semantically map onto `combat_resolved`'s exact
definition for 2 of them:
- `KILL` — "loser dies," an unambiguous match.
- `ESCAPED` — "loser retreats," an unambiguous match (the target cleanly disengaged).
- `CAUGHT_FLEEING` — NOT a match: the fight isn't over, no clear winner established, already
  separately captured by `combat_damage`.
- `PURSUIT_ABANDONED` — NOT a match: an inconclusive disengagement (anti-stalemate/leash-return),
  not "the loser retreats" in the sense of a real, successful escape.

Separately, `combat_engagement_started` is **not** a promotion candidate at all: it fires on the
exact same real gate as the already-scored `combat_initiated` (`combat_active`, +2) — promoting
it would double-count the identical real-world event, not add new signal. This is a real,
deliberate decision (documented here, matching this repo's own DA-ruling precedent for
`ENABLE_ADVENTURE_ROUTING`/AGENCY), not an oversight.

## Scope
1. **Investigate**: re-confirm the `combat_resolved` emission gap against current source; confirm
   the `KILL`/`ESCAPED` semantic mapping is sound against the pillar contract's own wording; check
   whether `attrition_threshold_crossed` (the other event named alongside `combat_resolved` in the
   same "dead code" comment) is in scope too or a separate question.
2. **Plan**: design the real, minimal event addition — `CombatShaper` emits a real
   `combat_resolved` event alongside `combat_engagement_ended` specifically for the `KILL`/
   `ESCAPED` outcomes (not a new event type from scratch — reusing the already-defined,
   already-scored `combat_resolved` contract).
3. **Implement**: the minimal addition in `event_shapers.py`.
4. **Document**: register `combat_resolved` as no longer an `engine_emission_gap` in
   `event_type_coverage.md`; explicitly document the `combat_engagement_started`
   non-promotion decision.

## Out of Scope
- Promoting `combat_engagement_started` to scored — explicitly decided against, documented above.
- Promoting `combat_engagement_ended`'s `CAUGHT_FLEEING`/`PURSUIT_ABANDONED` outcomes to
  `combat_resolved` — explicitly decided against per the semantic mismatch above.
- `attrition_threshold_crossed`'s own emission gap — a separate event type with a separate
  question of whether/how to wire it; not bundled here unless Investigate finds it trivially
  shares the same fix.
- Any change to combat resolution logic itself, or to the already-implemented
  `combat_engagement_started`/`ended` events from the sibling ticket.

## Acceptance Criteria
- [x] investigation.md re-confirms the `combat_resolved` emission gap and the semantic mapping
      against current source
- [x] `combat_resolved` gets a real, minimal producer for the `KILL`/`ESCAPED` outcomes
- [x] `docs/simulation_quality/event_type_coverage.md` corrected: `combat_resolved` no longer
      listed (if it currently is) as an unfilled `engine_emission_gap` — added the missing §3.10
      Combat subsection (the doc had never audited this pillar's own emission gaps at all)
- [x] `combat_engagement_started`'s non-promotion decision is explicitly documented (not silently
      left as an open question)
- [x] Real corpus re-verification: **`combat_resolved` fires naturally at real, non-zero volume**
      (1x `dungeon_crawl`, 4x `urban_political`, 2000-tick corpus-default runs), 1:1 correlated
      with the real `KILL`/`ESCAPED` count in each world, zero leakage into the excluded outcomes
- [x] Scoped pytest passes — 1017 passed, 6 skipped, zero regressions

## Related Tickets
- TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY (DONE, same session — built
  `combat_engagement_started`/`ended`, explicitly deferred the pillar-scoring decision to this
  ticket)
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE, TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
  (DONE, same session — the 2 fixes that made real combat volume exist to evaluate this decision
  against)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT (the real, authoritative pillar
  definition `combat_resolved` is drawn from)
- `docs/simulation_quality/event_type_coverage.md` (the event-registration contract)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX/` during implementation.

## Related Code Areas
- `src/observability/event_shapers.py` (`CombatShaper.shape()`, where the new emission lands)
- `src/simulation_quality/scorers/combat.py` (`CombatScorer`, the already-real, already-ready
  `combat_resolved` handler — not modified, just finally given a producer)

## Assumptions / Open Questions
- Whether `attrition_threshold_crossed` shares enough of this ticket's own investigation to be
  worth a trivial follow-up fix here, or is a genuinely separate question — left to Investigate
  phase judgment, per the Uncertainty Rule.

## Implementation Notes
- `src/observability/event_shapers.py::CombatShaper.shape()` — added a real
  `SimulationEvent(event_type="combat_resolved", ...)` at the exact 2 sites that already
  construct `combat_engagement_ended` for the `KILL` outcome and the `ESCAPED` outcome (the
  `combat_escape` property-tag branch). `CombatScorer.score()` requires no specific payload
  fields — a flat `+3` on event-type match alone — so this is a minimal, additive change with no
  new payload contract to design.
- `CAUGHT_FLEEING`/`PURSUIT_ABANDONED` deliberately do NOT get a `combat_resolved` emission —
  neither represents "a clear winner, loser retreats or dies" per the pillar contract's own
  wording (confirmed via investigation.md's own semantic analysis).
- `combat_engagement_started` confirmed NOT a promotion candidate — fires on the exact same real
  gate as the already-scored `combat_initiated`; promoting it would double-count the identical
  real-world event. Documented as a deliberate decision in
  `docs/simulation_quality/event_type_coverage.md` §5's own entry for it, matching this repo's
  own `ENABLE_ADVENTURE_ROUTING`/AGENCY DA-ruling precedent.
- `attrition_threshold_crossed` confirmed genuinely separate (population-wide attrition-rate
  tracking, not a single combat-outcome signal) — not bundled into this ticket.
- `docs/simulation_quality/event_type_coverage.md` had never audited the COMBAT pillar's own
  emission gaps at all (§3 jumped from Economy to Narrative, no COMBAT subsection existed) — a
  real, previously-undisclosed documentation gap, corrected alongside the code fix by adding
  §3.10 Combat.

## Test Summary
- 4 new unit tests in `tests/unit/observability/test_event_shapers.py`
  (`test_combat_resolved_fires_alongside_kill`, `test_combat_resolved_fires_alongside_escaped`,
  `test_combat_resolved_not_emitted_for_caught_fleeing`,
  `test_combat_resolved_not_emitted_for_pursuit_abandoned`) — all pass (38/38 in that file).
- Full scoped re-run: `tests/unit/observability/ tests/simulation_quality/test_combat_scorer.py`
  — 1017 passed, 6 skipped, zero regressions.
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop, corpus-default flags,
  both worlds, all 3 of this session's own combat fixes active): `combat_resolved` fires at
  real, non-zero volume — 1x in `dungeon_crawl` (matching its 1 real `KILL`), 4x in
  `urban_political` (matching its 4 real `ESCAPED` occurrences) — a clean, exact 1:1 correlation
  confirming zero double-counting or leakage into the excluded outcomes.

## Files Changed
- `src/observability/event_shapers.py` — `combat_resolved` emission for `KILL`/`ESCAPED`.
- `tests/unit/observability/test_event_shapers.py` — 4 new tests.
- `docs/simulation_quality/event_type_coverage.md` — new §3.10 Combat subsection; updated §5
  entries for `combat_engagement_started`/`ended` with the real pillar-scoring decision.
- `docs/simulation_quality/quality_scoring_contract.md` — added a real producer citation to the
  COMBAT pillar's own `combat_resolved` row.
- `docs/parity_ledger/combat_movement.yaml` — COMB-305.

## Completion Summary
Closed the user's own thread #3 (pillar-scoring decision for the combat-lifecycle events) with a
more precise finding than a generic promote-or-don't call: `combat_resolved`, the largest positive
weight in the entire COMBAT pillar, had a real, ready scorer handler since the pillar's own
original design but had literally never had a producer anywhere in the repo. Wired
`combat_engagement_ended`'s `KILL`/`ESCAPED` outcomes into it — both are literal semantic matches
for the pillar contract's own definition — while explicitly deciding against promoting
`combat_engagement_started` (redundant with the already-scored `combat_initiated`) or the
`CAUGHT_FLEEING`/`PURSUIT_ABANDONED` outcomes (neither represents a clear resolution). Real corpus
re-verification confirms clean, exact 1:1 correlation with zero leakage. Also corrected a
previously-undisclosed gap in `event_type_coverage.md` itself — the COMBAT pillar had never been
audited in that doc's own §3 Engine Emission Gaps section at all.
