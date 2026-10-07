---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS
phase: open
date: 2026-10-07
tags: [regression, testing]
---

# TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS

## Title
Rebaseline the behavioral_5k regression (urban_political) once the starvation chain is on main, attributing every metric that moves.

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Successor to `TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC`, which #407 closed as measurement only. It found that `alive_avg` and `gold_avg` moved at #303, where the world-clock raid was retired. The 2026-08-19 baseline's survivors were raiders, and that baseline starved too. `quest_active_count` moved in steps at #182, #291 and #333. Its recommendation was not to rebaseline until the starvation chain lands. This ticket owns that rebaseline and the `tests.regression.test_behavioral_5k*` entry in `tools/test_architecture/slow_known_reds.yaml`.

The starvation chain (Tier 1 of the decision-core epic): #403 (capacity gate), #404 (arrival), #406 (live project score) and #407 (SURV-05/06 biology, merged as 0a03c2448) are on main. Still to land: SURV-07 need escalation (Lane A) and decision 25, whole-tile movement (Lane A, `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-...`), which re-baselines walking routes.

## Scope
1. When both are on main, run behavioral_5k fresh at the evidence bar of `docs/testing/regression_policy.md` §9-11.
2. Attribute each metric's move to a named PR. A move on a PR whose contract is neutral is class (b) and gets its own fix ticket, filed through rpg-planner.
3. Rebaseline the class (a) metrics, record the derivation, and retire the known-reds entry.

## Out of Scope
- The SimQ corpus anchor families, which have their own tickets.
- Any change to simulation behaviour.

## Acceptance Criteria
- [ ] Measured on a main that contains SURV-07 and decision 25, with the commit stated.
- [ ] Every moved metric is attributed (a) or (b), and every (b) has a fix ticket.
- [ ] The baseline is updated for the (a) metrics, and the slow known-reds entry is removed.

## Related Tickets
- `TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC` (predecessor, done)
- `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` (umbrella)
- `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT` (decision 25)

## Related Docs
- `docs/testing/regression_policy.md` §9-11

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC/`

## Related Code Areas
- `tests/regression/test_behavioral_5k*`
- `tools/test_architecture/slow_known_reds.yaml` (testing owns the entry)

## Assumptions / Open Questions
- If SURV-07 still leaves mass starvation, rebaseline anyway on the then-current main and disclose it. Do not hold the gate red waiting on Tier 2.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
