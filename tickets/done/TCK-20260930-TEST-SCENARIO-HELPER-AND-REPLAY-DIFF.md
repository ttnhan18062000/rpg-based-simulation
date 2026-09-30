---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-TEST-SCENARIO-HELPER-AND-REPLAY-DIFF

## Title
Shared scenario helper, synthetic worked examples and a replay-diff helper limited to the verified envelope

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Provide reusable harness patterns: a scenario helper, worked examples that each run green in their declared lane, and a replay-diff helper that only claims what determinism evidence supports.

## Scope
- `tests/helpers/` scenario helper (stage, run, observe, optional control arm).
- Worked examples, labelled synthetic (test-only toy, apart from feature tests), each declaring its lane and shown running green there.
- Replay-diff helper: envelope bounds taken from `tests/integration/kernel/test_determinism_suite.py::test_reproducibility` (cited, not restated); returns `outside-verified-scope` outside it.

## Out of Scope
- Confirmed-stable examples on real core-RPG rules (would require asking rpg-feature-planning first).
- Part 2 of the parent epic (scenario-lane CI rule, `HOLD — pending D-R2`); no `.github/workflows/` change.
- Bulk classification of existing tests; feature-specific proof commitments.

## Acceptance Criteria
1. Each worked example runs green in its declared lane and is labelled synthetic.
2. Replay-diff: one in-envelope case passes; one violation per dimension (not hand-built state, unseeded/different seed, 11 ticks, different profile) each returns `outside-verified-scope`.

## Related Tickets
- Parent epic: `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (parts 1 and 3 only).
- Depends on TCK-20260930-TEST-TAXONOMY-LEVEL-CONTRACTS.

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §4
- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3–4 (non-binding)
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tests/helpers/`; `tests/mechanic_scenarios/`

## Assumptions / Open Questions
- Examples are synthetic; no feature-team confirmation is available.

## Implementation Notes
Envelope bounds now live as module constants in `test_determinism_suite.py` (`REPRODUCIBILITY_SEED/TICKS/PROFILE`, values unchanged) and `replay_diff` imports them. The examples are synthetic, sit under `tests/mechanic_scenarios/synthetic_examples/`, declare lane `perf-cert-arena`, and a test checks that lane's CI step lists `tests/mechanic_scenarios`.

## Test Summary
`pytest tests/mechanic_scenarios -m "not slow and not extra_slow"` (the `perf-cert-arena` step's scenario path): green; replay-diff: 1 in-envelope case + 1 violation per dimension (not hand-built, unseeded, different seed, 11 ticks, different profile); determinism suite still green.

## Files Changed
tests/helpers/scenario.py; tests/helpers/replay_diff.py; tests/mechanic_scenarios/synthetic_examples/; tests/integration/kernel/test_determinism_suite.py (envelope constants only); tests/unit/tools/test_replay_diff.py; tests/unit/tools/test_scenario_examples_lane.py

## Completion Summary
Scenario helper, synthetic examples and envelope-limited replay-diff added. Part 2 of the parent epic (D-R2) untouched.
