---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE
phase: done
date: 2026-10-07
tags: [strategy, cognition, bug]
---

# TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE

## Title
The project-switch comparison sets a live candidate utility against the current project's creation-time score, so a need that has grown looks weaker and a project can replace itself with a duplicate

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`evaluate_project_switch` compares `candidate_project.score` (the live, personality-modified utility of the winning goal) against `current.score + retention_margin`, where `current.score` is the utility its goal had when the project was created and is never refreshed. Planner ruling 2026-10-07 (ii-a): comparing a live score against a creation-time score is a correctness bug, not a priority choice; refresh the current project's score from its live scorer before the comparison (engineering), measured, in its own commit. Found tracing why the fatigue project was replaced (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`): there the stored score (50.5) and the live one (52.5) differ by little, so the refresh alone does not keep the project; the larger gap is the flat-80 `resolve_blocker` goal, a rule question with the designer. What the stale score does do, measurably, is let a project replace itself with a duplicate of the same kind: with the fix those same-kind switches go from 16 and 20 to 0 and 0.

## Scope
- `with_live_current_score(entity, live_scores)` in `src/core/strategic.py`: for the switch comparison only, the current project's `score` is its goal's live utility when the project's kind is a `GoalKind` (the generic branch stores a utility); a `ProjectKind` project (adventure route, contract, stabilization: raw score on another scale) and a project whose goal has no live score this evaluation are left alone.
- Tests; a before and after measurement on one tree (project-kind wins, switches by kind, eat and sleep events, deaths by cause); divergence 2.79, parity STRAT-279, Bible 04 note.

## Out of Scope
- Whether a standing biological need may outrank a flat-80 `resolve_blocker` goal (a rule question, with the designer); the scorer magnitudes are unchanged.
- Persisting the refreshed score on a kept project: only the comparison sees the live score.
- The REST and SLEEP action semantics (Lane B).

## Acceptance Criteria
- [x] The switch comparison uses the current project's live utility for a generic (`GoalKind`) project and leaves `ProjectKind` projects and projects without a live score alone
- [x] A regression test fails on the old comparison: a grown need no longer replaces its own project with a duplicate
- [x] Measured before and after on one tree, including the effect on every project kind's switching (divergence 2.79); the campaign tests pass
- [x] The scorer magnitudes are unchanged

## Related Tickets
- TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (umbrella, open)
- TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG (the scale mismatch this respects)

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.79; `docs/mechanics/04_strategic_cognition.md` section 4

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-PROJECT-SWITCH-COMPARES-A-LIVE-CANDIDATE-SCORE-TO-THE-CURRENT-PROJECTS-CREATION-TIME-SCORE/`

## Related Code Areas
- `src/systems/strategic_systems/intelligence.py` (`evaluate_strategic_intent`, `evaluate_project_switch`, `_score_scale_max`)

## Assumptions / Open Questions
- When the switch happens, the suspended project is built from the refreshed copy, so it carries its last live score (it was already a stale value before). Nothing is written for a kept project.

## Implementation Notes
- One helper and a two-line change at the single call site of `evaluate_project_switch` in `evaluate_strategic_intent`; `evaluate_project_switch` itself is unchanged.

## Test Summary
- New `tests/unit/strategic/test_project_switch_uses_live_current_score.py` (6 tests); with the old comparison restored the duplicate-replacement test fails.
- Corpus before and after: see divergence 2.79 (same-kind duplicate switches 16 / 20 to 0 / 0; eat and sleep still 0).
- CI directory lists, run locally with `-m "not slow and not extra_slow"` on the final branch: unit-core 1839 passed, 1 skipped; unit-domain 1480 passed, 1 skipped; integration plus `tests/integrity` plus `tests/architecture` 1225 passed, 7 skipped, 1 xfailed (the known strict deliberate-attack xfail); unit-infra including `tests/unit/tools` 3330 passed, 1 skipped; `tests/integration/campaigns` (slow, outside those lists) 28 passed, 1 xfailed. Not run locally: the full Tools job's remaining files and the slow suites.
- Gates (scratch venv): code-health ratchet 0 new, 0 worse (the first placement of the helper in `intelligence.py` grew its module, class and function lengths, so it moved to `src/core/strategic.py` next to the live-project predicates; a separate new module was rejected because it became a new unbound mechanism-registry target and moved a pinned count); parity-ledger schema 0 rose, 0 new; mypy baseline nothing in `core/strategic.py` or `intelligence.py`. A 1500-tick crowded_frontier run on the final tree is identical to the measured after-run on every metric. CI is the first real run.

## Files Changed
`src/systems/strategic_systems/intelligence.py`; the new test; `docs/guidelines/intentional_divergences.md`, `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`; this ticket, its artifacts and `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`.

## Completion Summary
The project-switch comparison now sees the current project's live utility, so a grown need no longer replaces its own project with a duplicate (16 and 20 such switches become 0 and 0) and a met need no longer holds a project on a stale high score. Eating and sleeping are unchanged; the priority of a need against a flat-80 goal is a rule question with the designer.
