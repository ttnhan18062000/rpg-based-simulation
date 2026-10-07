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
