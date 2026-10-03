---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD
phase: done
date: 2026-09-07
tags: [architecture, simulation-quality]
---

# TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD

## Title
Carry region_loyalty_pressure/region_culture_states/entity_legend_facts across ticks in ApplyPath.apply_generation()

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while implementing `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO`
(Dormant Mechanism Closure epic, child 6): `ApplyPath.apply_generation()`
(`src/engine/apply.py`) is the single authoritative per-tick `AuthoritativeState(...)`
reconstruction site (per `docs/guidelines/design_patterns.md` Pattern 6's own "known pitfall"
section). Its constructor call does not carry forward `region_loyalty_pressure`,
`region_culture_states`, or `entity_legend_facts` — all three silently reset to their dataclass
default (`{}`) after the very first `Kernel.tick_once()` call, verified directly:

```
before any tick: region_culture_states= {'r1': CultureState(fatalism=0.8, ...)}
before any tick: entity_legend_facts= {'1': LegendFact(subject_id='1', fame=0.9, ...)}
after tick 1: region_culture_states= {}
after tick 1: entity_legend_facts= {}
```

All three fields were added by tickets closed **today** (`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`,
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`, `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`),
each populated once per episode by `CampaignOrchestrator._build_initial_state()`, explicitly to
feed `GroupPhase.resolve()`/`AdventureGoalScorer.score()` **every tick** of a real multi-tick
campaign episode — none of the three has (or should have) Pattern 6's documented "Bounded,
single-fire" semantic (unlike `information_source_profiles`/`pending_information_responses`,
which Pattern 6's own "known pitfall" section explicitly documents as **intentionally** not
carried forward — see this ticket's own Out of Scope). This is a real, undocumented gap in the 3
closing tickets' own implementations, not a deliberate divergence: none of their own Implementation
Notes/parity ledger entries decided this question explicitly, which Pattern 6's own guidance
requires ("Do not leave this question implicit").

**Real-world impact**: Culture Drift and Living Legend route-bias — both shipped and closed as
DONE today with passing tests — only ever produce their intended effect on tick 0/1 of any real
campaign episode; from tick 2 onward both bias branches are silently inert (bridged dict always
empty), even though every test that exercised them called `AdventureGoalScorer.score()`/
`AdventureRouteScorer.score()` directly against a hand-constructed `AuthoritativeState`, bypassing
`Kernel.tick_once()`/`apply_generation()` entirely — so no existing test caught this.
`region_loyalty_pressure` (idea 56, `GroupPhase.resolve()`) has the identical exposure.

## Scope
- Add `region_loyalty_pressure=prior_state.region_loyalty_pressure`,
  `region_culture_states=prior_state.region_culture_states`,
  `entity_legend_facts=prior_state.entity_legend_facts` to `ApplyPath.apply_generation()`'s
  existing `AuthoritativeState(...)` constructor call (`src/engine/apply.py`) — mirrors the
  identical `prior_state.<field>` carry-forward pattern already used for `town_tiles`/
  `building_tiles`/`terrain`/`town_center`/`blocked_tiles`/`town_entity_ids` immediately above in
  the same constructor call. Pure additive carry-forward: these fields are never mutated
  mid-episode by any `StateUpdate`, only read, so a straight `prior_state.<field>` passthrough is
  correct and matches `factions`' own already-carried-forward precedent (Pattern 6's own cited
  positive example).
- Add a real, direct test proving each of the 3 fields survives a real `Kernel.tick_once()` call
  unchanged (mirrors this ticket's own investigation script).
- Update each of the 3 fields' own doc comment in `src/core/state.py` to note they now genuinely
  persist across ticks (removing any implication they were previously durable-for-the-episode when
  they were not).
- Amend `tickets/done/TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE.md`,
  `tickets/done/TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE.md`, and
  `tickets/done/TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING.md`'s own Implementation Notes with a
  short disclosure of this real regression and a link to this ticket's own fix — per this repo's
  own disclosure discipline, a defect found in already-closed work must not be silently patched
  without a trace back to the original ticket.

## Out of Scope
- `information_source_profiles`/`pending_information_responses` — Pattern 6's own "known pitfall"
  section explicitly documents these as **intentionally** not carried forward (rationale class
  Bounded, `docs/guidelines/intentional_divergences.md`) — a deliberate, already-verified,
  single-fire-per-episode design, not a bug. Do not touch.
- `pending_self_model_information_events` — same single-fire event-queue shape as
  `pending_information_responses` (its own docstring: "the third application of the compile-time-seed
  pattern, following information_source_profiles and pending_information_responses"), and even if
  made persistent it would not unblock `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO`'s own goal
  (see that ticket's own Implementation Notes) since `information_source_profiles` — genuinely
  Bounded — is the actual blocker there, not this field. Leave as-is, consistent with its sibling.
- Any other `AuthoritativeState` field not explicitly named in Scope above.

## Acceptance Criteria
- [ ] `region_loyalty_pressure`/`region_culture_states`/`entity_legend_facts` all survive a real
      `Kernel.tick_once()` call unchanged, confirmed via a direct test.
- [ ] `information_source_profiles`/`pending_information_responses`/
      `pending_self_model_information_events` remain untouched (still Bounded/single-fire) —
      confirmed no regression to their own existing tests.
- [ ] The 3 already-closed tickets' Implementation Notes are amended with a disclosure + link.

## Related Tickets
- `TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO` (the ticket that found this)
- `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`,
  `TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (`tickets/done/` — the 3 tickets whose own bridges
  this fixes; each gets an Implementation Notes amendment)

## Related Docs
- `docs/guidelines/design_patterns.md` (Pattern 6, "The known pitfall: compile-time seeding is not
  automatically persistent across ticks")

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `src/engine/apply.py` (`ApplyPath.apply_generation()`)
- `src/core/state.py` (doc comments for the 3 fields)

## Assumptions / Open Questions
None — this is a narrow, mechanical, well-evidenced fix; no open design questions.

## Implementation Notes
Added the 3 missing `prior_state.<field>` carry-forwards to `ApplyPath.apply_generation()`'s
existing `AuthoritativeState(...)` constructor call (`src/engine/apply.py`), immediately after the
existing `feature_flags` carry-forward. Verified directly (before/after) via a standalone script
driving a real `Kernel.tick_once()` call against a hand-seeded `AuthoritativeState`: all 3 fields
went from resetting to `{}` after tick 1 to surviving unchanged.

Deliberately did **not** touch `information_source_profiles`/`pending_information_responses` —
`docs/guidelines/design_patterns.md` Pattern 6's own "known pitfall" section explicitly documents
these as intentionally single-fire/Bounded (verified, correct-as-shipped), a real, already-decided
architecture choice distinct from this ticket's 3 target fields, which have no such rationale and
whose own designed intent (feed a per-tick scorer for the whole episode) clearly requires
persistence. Also did not touch `pending_self_model_information_events` — same single-fire
event-queue shape as its sibling, and (confirmed via investigation for
`TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO`) making it persist would not actually unblock that
ticket's own goal, since `information_source_profiles` remains the real blocker there and is
correctly left alone.

Amended the 3 already-closed tickets whose own bridge fields this fixes
(`TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE`, `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE`,
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`) with a "Post-Closure Disclosure" section each,
explaining the real gap, why none of their own tests could have caught it (all exercise the
consuming scorer directly against a hand-constructed `AuthoritativeState`, never through a real
`Kernel.tick_once()` round-trip), and that no change to their own implementation/tests was needed.

Updated the parity ledger entries that document these fields' own "persists for the episode"
claims (`docs/parity_ledger/social_narrative.yaml` SOC-276, `docs/parity_ledger/
strategic_cognition.yaml` STRAT-227) with a correction note and this ticket's new test citation.

## Test Summary
New: `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py` (5 tests) — proves
each of the 3 fields survives one and multiple `ApplyPath.apply_generation()` calls unchanged, and
a no-content baseline state stays empty (no spontaneous-content regression).

Regression sweep (broad, since this touches the one shared per-tick state-reconstruction site):
`tests/unit/engine/`, `tests/unit/domains/campaigns/`, `tests/unit/ai/goals/
test_adventure_goal_scorer.py`, `tests/unit/domains/adventure/`, `tests/unit/domains/fame/`,
`tests/unit/domains/culture/`, `tests/unit/social/test_groups.py`, `tests/unit/social/
test_loyalty_drift.py`, `tests/integration/culture/test_loyalty_drift_campaign.py`,
`tests/architecture/`, `tests/unit/domains/information/` (`-m "not slow"`) — **645 passed, 1
skipped (pre-existing, unrelated), 0 failed**. `information_source_profiles`/
`pending_information_responses`'s own existing tests (`tests/unit/domains/information/`) pass
unchanged, confirming their Bounded behavior was not disturbed.

Determinism: no new iteration order introduced — this is a straight `prior_state.<field>`
passthrough for 3 already-existing, already-deterministically-populated dict fields.

## Files Changed
- `src/engine/apply.py` — `ApplyPath.apply_generation()` carries `region_loyalty_pressure`/
  `region_culture_states`/`entity_legend_facts` forward
- `src/core/state.py` — doc comments for the 3 fields updated to reflect real persistence
- New test: `tests/unit/engine/test_apply_generation_episode_bridge_carryforward.py`
- `docs/parity_ledger/social_narrative.yaml` — SOC-276 correction note
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 correction note
- `tickets/done/TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE.md`,
  `tickets/done/TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE.md`,
  `tickets/done/TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING.md` — Post-Closure Disclosure sections
  added

## Completion Summary
Fixed a real, disclosed gap where 3 episode-scoped bridge fields (all added by tickets closed
earlier today) silently reset to empty after the first tick of any real campaign episode, making
Culture Drift and Living Legend route-bias — and idea 56's loyalty-pressure signal — inert beyond
tick 1 in production despite passing tests (all of which bypassed the real `Kernel.tick_once()`
round-trip). Fixed with a 3-line additive carry-forward, matching the exact pattern already used
for `factions`/`feature_flags` in the same constructor. Explicitly did not touch the genuinely
Bounded/single-fire `information_source_profiles`/`pending_information_responses`/
`pending_self_model_information_events` fields — confirmed via Pattern 6's own documentation and
direct investigation that persisting those would be wrong (or, for the third, ineffective) rather
than a fix. The 3 already-closed tickets whose own work this regression affected were amended with
disclosure sections, not silently patched around. Not pushed — left as local commits on
`dormant-mechanism-closure` per this session's own fork-execution constraints.
