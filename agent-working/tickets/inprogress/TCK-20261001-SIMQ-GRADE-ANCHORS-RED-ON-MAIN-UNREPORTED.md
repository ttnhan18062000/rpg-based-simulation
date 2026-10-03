---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED
phase: open
date: 2026-10-01
tags: [simulation-quality, grade-thresholds]
---

# TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED

## Title
13 of 15 SimQ grade-anchor tests in `tests/unit/worldassembly/test_corpus_diversity.py` fail on
untouched `origin/main` (measured 2026-10-01 @ `e9db40f0a`; supersedes the unverified "11 of 16"
lead), and nothing reports it because the whole family is `@slow` and CI does not gate on it —
the anchors currently protect nothing

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found 2026-10-01 while landing `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND`
(PR #269). That batch's fix caused 16 grade-anchor tests to fail, so a control run was done on
untouched `origin/main` (`73cbf116b`) to separate fix-caused drift from pre-existing red.

**The control run is the finding.** Of the 16, **11 also fail on untouched `main`** — they were
already red, independent of any change in that batch. Only 5 failed solely with the fix, and of
those, 2 passed on re-run, 1 was a per-test resource `TimeoutError`, 1 was noise confirmed by a
5-vs-5 trial (see below), and exactly **1** was a genuine fix-caused shift (tracked separately in
`TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE`).

**Why nobody noticed:** the whole family is marked `@slow`, and CI does not gate on `@slow`. So
these anchors can be red on `main` indefinitely with no signal to anyone. Their failure is only
observable to someone who runs them deliberately — which, in this case, happened by accident,
because a batch needed a control run for an unrelated reason.

**The consequence is what makes this P1, not the 11 failures themselves.** A grade anchor exists to
detect unintended drift in simulation quality. An anchor that has been failing on `main` for an
unknown period cannot do that: it cannot distinguish "this change broke something" from "this was
already broken", and every future change that touches these pillars inherits an unreadable signal.
That is precisely the cost paid in PR #269 — a real fix produced 16 red tests and the batch had to
spend a full control run establishing that 11 of them were not its fault. **Every future batch
touching ECONOMY/NARRATIVE/SOCIAL pays that same tax until this is resolved.**

> **The contrast with the gating lane, observed the same day, in the same PR.** PR #269's gating CI
> caught a real defect on its first run — a `tests/simulation_quality/` test that had pinned the
> exact collision the PR was fixing, asserting `yields_item == 'frost_shard_cluster'` with a
> docstring claiming no `frost_shard` item existed when the catalog defines one. One run, real
> signal, acted on immediately. In the same repository on the same day, 11 grade anchors had been
> failing on `main` for an unknown period with no signal reaching anyone, because `@slow` is
> excluded from the gating lane. **The difference is not test quality — it is whether anything
> reads the result.** An unread assertion and an absent assertion are the same thing operationally,
> and the anchors have been in the first category for long enough that nobody knows when it
> started. This is the concrete case for the reporting-path requirement in Scope, and it is why
> visibility (not gating) is the minimum bar: the gating lane's value here came from someone being
> *told*, within minutes, by a mechanism that does not depend on anyone choosing to look.

**Provenance and verification status — read before acting.** The 11-of-16 measurement was made by
`rpg-implementer (2)` during PR #269's control run, not by this ticket's author, and **has not been
independently re-verified**. It is recorded here because it was load-bearing for that PR's merge
decision and would otherwise exist only in a session transcript. **Re-run the 16 before acting on
the count** — the first task below. The qualitative claim (some anchors are red on `main` and
nothing reports it) is what this ticket rests on; the exact number is not yet confirmed.

## Verified Measurement — 2026-10-01 (supersedes the unverified 11-of-16)

**Re-run done, and it is worse than the lead claimed.** The first Scope item is complete; the rest
of the ticket is untouched and still OPEN.

- **Conditions.** `origin/main` @ `e9db40f0a`; worktree tree identical to that SHA for all `src/`
  and `tests/` paths (only a ticket move and monitoring-shard rows differed, neither of which the
  tests read). `python -m pytest tests/unit/worldassembly/test_corpus_diversity.py
  -k "grade_stability or population_stability" -v -rA`. 32 selected / 61 deselected. Wall clock
  **25m59s**. Seeds and tick budgets are per-test, as encoded in each test name.
- **Result: 15 failed, 17 passed, 1 error.**
- **Of the 15 `*_grade_stability` anchors, 13 fail.** Only two pass:
  `test_simq_routing_test_seed42_1000t_cognition_grade_stability` and
  `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`.
- Plus 2 `population_stability` failures: `[frontier_marches]` (already classified **confirmed
  noise** in Out of Scope — not re-investigated here) and
  `test_generated_frontier_3_42_extended_population_stability`.
- The **1 error is not an anchor failure**: it is a session-teardown `QueueDrainWorker` leak
  sentinel firing at teardown of the last test. Recorded separately so it is not miscounted as a
  14th red anchor; it may deserve its own ticket.

**Full red list** (13 grade + 2 population):
`test_urban_political_seed123_500t_cognition`, `test_simq_routing_test_seed42_500t_cognition`,
`test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative`,
`test_urban_political_seed42_1000t_social`, `test_urban_political_seed123_1000t_social_economy`,
`test_urban_political_selfmodel_probe_seed42_200t_social_world`,
`test_generated_frontier_3_42_seed123_200t_combat_narrative`,
`test_urban_political_seed42_200t_social`, `test_frontier_extended_seed42_200t_narrative`,
`test_frontier_extended_seed123_200t_combat_progression_narrative`,
`test_frontier_living_world_seed42_200t_social`,
`test_frontier_living_world_seed123_200t_combat_narrative`,
`test_frontier_marches_seed42_200t_narrative`;
`test_population_stability[frontier_marches]`,
`test_generated_frontier_3_42_extended_population_stability`.

**What this does and does not establish.** The qualitative claim the ticket rests on is
**confirmed**: anchors are red on untouched `main` and nothing reports it. The count is now
measured rather than inherited — **13 of 15 grade anchors**, not 11 of 16. What remains entirely
**unaddressed**: how long they have been red, the per-anchor (a)/(b)/(c) classification, the
reporting path, and the other-`@slow`-families audit. **No anchor value was touched**, per Out of
Scope.

**Provenance.** Measured by `rpg-feature-planning`, run alongside
`TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` as a verification-only re-run on the
recommendation of `world-rule-catalog-design`. Single run per anchor — **flakiness was not
re-tested here**, so class (c) remains open for every one of the 13.

## Scope
- Re-run the 16 sampled anchors on current `origin/main` and record which fail, with counts and
  conditions (seed, flags, world, tick budget). Establish the real number rather than inheriting 11.
- Determine **how long** they have been red. Bisect or sample historical commits — an anchor red for
  two days is a different problem from one red for two months, and the answer decides whether the
  fix is "repair the anchors" or "repair what the anchors were watching".
- For each failing anchor, classify: (a) the anchor's expected value is stale and the current
  behaviour is correct, (b) the simulation genuinely regressed and the anchor is right, or
  (c) the anchor is non-deterministic / flaky by construction and never protected anything.
  **These have different fixes and must not be resolved as one batch edit.**
- Decide and implement a reporting path so a red `@slow` anchor becomes visible without waiting for
  someone to trip over it — e.g. a scheduled (non-gating) lane, a periodic report, or promoting a
  deterministic subset out of `@slow`. Design call, not pre-decided.
- Audit whether other `@slow`-marked families have the same blind spot. This ticket was found by
  accident; the same failure mode may be sitting in test families nobody has had reason to run.

## Out of Scope
- **Editing any anchor's expected value to make it pass.** Re-baselining a specific anchor against
  evidence is legitimate and is handled per `docs/testing/regression_policy.md` §9-11 in its own
  ticket; blanket-adjusting 11 anchors to green is not, and would destroy the only record of what
  broke.
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` — the one genuine fix-caused
  shift from PR #269, already filed and owned separately.
- Making CI gate on `@slow`. That is a cost/runtime decision with its own trade-offs; this ticket
  needs the failures to be *visible*, which is a weaker and cheaper requirement. Raise gating as a
  separate proposal if the investigation concludes visibility is insufficient.
- The `frontier_marches` population_stability anchor — investigated during PR #269 and **confirmed
  noise**, not a regression: 5-vs-5 trials at t300 gave fix-tree 46/36/47/41/43 (mean 42.6) and
  untouched main 42/46/47/36/39 (mean 42.0) against a 37.2 floor. Both scatter across the floor and
  main dips below it too. Recorded here so it is not re-investigated; it may still qualify as
  class (c) above.

## Acceptance Criteria
- The real current count of failing anchors on `origin/main` is measured and recorded, with
  conditions, superseding the unverified 11.
- Each failing anchor is classified (a)/(b)/(c) with evidence, not assumed.
- How long the anchors have been red is established, at least to the nearest few weeks.
- A reporting mechanism exists such that a newly-red `@slow` anchor is surfaced without a human
  happening to run it, and there is a test or check proving the mechanism reports a seeded failure.
- Any anchor whose expected value changes cites its evidence per
  `docs/testing/regression_policy.md` §9-11.
- A statement on whether other `@slow` families share the blind spot.

## Related Tickets
- `TCK-20260930-RESOURCE-NODE-YIELDS-ITEM-COLLIDES-WITH-RESOURCE-KIND` (PR #269 — the batch whose
  control run surfaced this)
- `TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE` (the one real fix-caused
  shift, filed in PR #269)

## Related Docs
- `docs/testing/regression_policy.md` §9-11 — the re-baselining procedure any anchor value change
  must follow.
- `docs/testing/test_taxonomy.md` — test classification rules, including what `@slow` is meant to
  signify.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` — the grade-anchor family itself.
- `src/simulation_quality/` — the scorers producing the ECONOMY / NARRATIVE / SOCIAL pillar values
  the anchors assert against.
- CI workflow definitions — wherever the `@slow` marker is excluded from the gating lane.

## Assumptions / Open Questions
- **The 11 count is unverified by this ticket's author** (see Request Summary). Treat it as a lead,
  not a measurement.
- Whether the right fix is "repair the anchors" or "repair the simulation" is genuinely unknown
  until the (a)/(b)/(c) classification is done, and the answer may differ per anchor. **Do not
  assume stale anchors** — that is the comfortable conclusion, and the one that would quietly erase
  a real regression if it is wrong.
- Whether a non-gating reporting lane is sufficient, or whether anything unreported eventually goes
  unread too, is a design question for the investigation.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
