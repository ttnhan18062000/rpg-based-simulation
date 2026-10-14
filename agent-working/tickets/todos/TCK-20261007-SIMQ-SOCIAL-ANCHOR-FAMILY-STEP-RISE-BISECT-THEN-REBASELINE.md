---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE
phase: open
date: 2026-10-07
tags: [simulation-quality, social, regression]
---

# TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE

## Title
Five SOCIAL corpus anchors went red in step changes (about 17-22 rising to 25-39). Bisect each onset to one PR, rebaseline the intended rises and file a fix for any that start on a neutral PR.

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found by testing's classification in `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` (PR #408). That pass measured 205 completed main runs between 2026-08-26 and 2026-10-07, plus 3 local rounds. On each of these five anchors, SOCIAL rose as a step: before a bracket of merges it passed on almost every run, and after it failed on almost every run. The brackets are run-level, not bisected:
- `urban_political_selfmodel_probe_seed42_200t`: onset #144. It first crashed; it now reads SOCIAL 26.1 against 17.9, and WORLD 0.66 against 0.21.
- `urban_political_seed42_200t`: #164/#165.
- `frontier_living_world_seed42_200t`: #172 (party formation, trust).
- `urban_political_seed123_1000t`: about #146.
- `urban_political_seed42_1000t`: not attributable from CI. Both 1000t anchors were already intermittent before the step.

rpg-planner's ruling (2026-10-07, relayed to testing and recorded on #408): **provisionally class (a), each pending a bisect.** #144 (dormant mechanisms wired on purpose), #165 (the survivor last-known-position fix) and #172 (the JOIN_PARTY accept path, where trust accumulating is the goal) are intended social activity. #146 (dead Doctrine chain removed) and #164 (frontmatter and pinning) must be behaviour-neutral. An onset that bisects onto either of them is **class (b)**: it gets its own fix ticket, not a rebaseline.

Twin of `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE`, which is widened to the NARRATIVE family.

## Scope
1. Bisect each anchor's onset to a single merge commit on main, using the anchor's own test and trial count.
2. Classify each one: (a) when the onset is a deliberate behaviour PR; (b) when it is #146, #164 or any other PR whose stated contract is neutral. Each (b) gets its own fix ticket, filed through rpg-planner.
3. For each (a) anchor: take a fresh measurement on the landing base at the evidence bar of `docs/testing/regression_policy.md` §9-11 (2 combined batches plus a verification batch), derive the new anchor and tolerance, and record the derivation in the test's docstring.

## Out of Scope
- The 6 flaky anchors (3 COGNITION, 3 population). Testing owns them.
- The NARRATIVE family (its twin ticket).
- Any change to SOCIAL scoring.

## Acceptance Criteria
- [ ] Each of the 5 anchors has a single-PR onset, or a stated reason it cannot be bisected.
- [ ] Each one is classified (a) or (b) with that evidence, and every (b) has a filed fix ticket.
- [ ] Every (a) anchor is rebaselined at the §9-11 bar, measured fresh on a base that contains #407, SURV-07 and decision 25.
- [ ] #408's known-reds entries for these anchors are retired or repointed.

## Related Tickets
- `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` (PR #408, classification)
- `TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE` (NARRATIVE twin)
- `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` (gating)
- `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT` (decision 25, gating)

## Related Docs
- `docs/testing/regression_policy.md` §9-11
- `src/simulation_quality/scorers/social.py`

## Related Stored Artifacts
- `agent-working/staging_artifacts/TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED/investigation.md` (on #408's branch `testing-anchor-classification`; stored on close)

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- **Deferred:** do not start the rebaseline until #407 (biology), SURV-07 (need escalation) and decision 25 (whole-tile movement) are on main. All three move these worlds, and §11's lesson is to re-measure fresh after related fixes. The bisect (scope 1-2) may run earlier, since it measures history.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

## Batch 3 measurement (2026-10-11, treasury batch / memo row 61; batch3-treasury, paired table in the stored artifacts of TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C/probes)
Re-measured the anchored SOCIAL/ECONOMY/COGNITION/NARRATIVE tests of `test_corpus_diversity.py` on current origin/main (20f67b744, run in isolation, three trials each) and on batch 3 (tip after the merge of fc0bf4fbb).
- The family is ALREADY red on main and batch 3 does not cause it: urban_political seed42 200t SOCIAL reads 36.08 (trials 31.7, 30.9, 45.7) on main against the anchor 16.8, and 30.34 (31.6, 28.2, 31.2) on batch 3. Other SOCIAL reads on main: 29.9 (anchor 17.9), 42.7 (anchor 35.1), 46.8 (anchor 21.4); ECONOMY 1.43 (anchor 0.15) and 2.72 (anchor 0.66); NARRATIVE 0.19 (anchor 0.0). The test's own text says the same: the SOCIAL event count ranges 710-770 across trials even in the smallest repro, i.e. a drift in the anchor-recording shape, which predates this batch.
- A first full-suite pass of main (one long session) showed 9 of the 11 tests as passing and the same tests failing on batch 3; an isolated re-run of those 11 on main fails 9 of them (not failing in isolation on main: frontier_living_world seed42 200t SOCIAL, simq_routing 1000t COGNITION). So "extra red on batch 3" was run-order noise, not a batch-3 effect. All 11 are either already listed in slow_known_reds.yaml with their own entry or covered by the class-(c) catch-all; no new entry is added.
- The mechanism question (is SOCIAL ~30 intended?): batch 3 keeps every town open and the treasury solvent (every building functional at every 250-tick sample; hero treasury flat), which can only add town events (meals, beds, sales) compared with the previous drained-and-closed towns, but the main figure is already higher than batch 3's, so the step rise is not from the economy chain. Recorded as a hypothesis for the bisect, not a finding; the bisect (this ticket) remains the way to attribute it.
- Per testing-planner's policy nothing is re-anchored in batch 3; the whole family re-anchors once after the economy chain settles.

## Investigation note: same-SHA nondeterminism of the SOCIAL reading (for TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2)
On origin/main 20f67b744, run in isolation three times in one process, `test_urban_political_seed42_200t_social_grade_stability` reads SOCIAL per-trial values 31.705, 30.875 and 45.665 (mean 36.08), and its own failure text records `SOCIAL event_count ranged 710-770 across trials` for the same code and seed. On batch3-treasury (b6468a5b2) the three trials read 31.595, 28.23 and 31.195 (mean 30.34). So one SHA gives different SOCIAL readings run to run (a spread of about 15 score points and 60 events); the anchors' evidence-derived tolerances (abs_floor 4.2) are narrower than that spread. Consequence for the re-anchor: the family must be re-anchored from SEVERAL isolated runs (trial means and their spread), never from one session's reading, and the determinism cause stays parked under TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2.

## simq_routing_test seed42 1000t COGNITION: isolated pass/fail grid (testing-planner's rule, 2026-10-11)
Three isolated runs each, alternating arms: origin/main 20f67b744 = FAIL, pass, FAIL; batch3-treasury b6468a5b2 = pass, FAIL, FAIL. A mix on both arms, so it is the same-SHA nondeterminism, not a batch-3 shift: it stays under the class-(c) catch-all and slow_known_reds.yaml is unchanged.
