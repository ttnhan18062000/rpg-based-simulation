---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-URBAN-POLITICAL-1000T-SOCIAL-ANCHOR-STALE
phase: open
date: 2026-08-18
tags: [simulation-quality, calibration, testing, bug]
---

# TCK-20260818-HOTFIX-URBAN-POLITICAL-1000T-SOCIAL-ANCHOR-STALE

## Title
`test_urban_political_seed123_1000t_social_economy_grade_stability`'s SOCIAL anchor was left
unsynced with `grade_anchors.json`'s already-correct value since `TCK-20260810-SIMQ-CORPUS-
ROLE-FACTION-DRIFT-VERIFICATION`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
User requested a full local reproduction of the `-m slow` corpus-diversity suite (all 32 tests,
fresh clean clone, matching CI exactly) rather than trusting individual error fixes against real
GitHub Actions retries. That reproduction surfaced this test failing 5 of 7 total attempts across
both contended and calm system-load conditions (2 more independent full-detail runs confirmed real
score-tolerance misses, not infrastructure/PRESSURE-mode errors) — a persistent, real drift, not
transient session-load flakiness (unlike a sibling test in the same reproduction run,
`test_simq_routing_test_seed42_1000t_cognition_grade_stability`, which passed cleanly 3/3 on
isolated retry and was confirmed to be exactly the kind of "confirmed-rare residual variance"
its own docstring already documents — left untouched).

Root cause: `grade_anchors.json`'s `urban_political_seed123_1000t.SOCIAL` is already `{"grade":
"S", "score": 21.374}`, committed by `TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`
(2026-08-10) to correct a real, confirmed behavioral-drift cause (a role/faction-mistagging fix
cascading through deterministic RNG-consumption order corpus-wide, affecting SOCIAL among other
pillars). That ticket recalibrated `grade_anchors.json` across 17 run_keys but this specific
test's own separate local literal (`tests/unit/worldassembly/test_corpus_diversity.py`) was never
updated to match — the exact same "unsynced literal" pattern already found and fixed 4 times
earlier in this session (`TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH`), just
from a different source commit.

## Scope
Sync the `SOCIAL` anchor entry (only) in `test_urban_political_seed123_1000t_social_economy_
grade_stability`'s `anchors = {...}` dict to `grade_anchors.json`'s committed value (`21.374`,
grade unchanged at `S`), with a fresh `abs_floor` derived from real trial evidence gathered
during this investigation (6 fresh trials across 2 full-detail runs:
`[18.156, 25.608, 23.748, 21.059, 24.359, 26.606]`; max deviation from 21.374 is 5.232;
`abs_floor = 1.3 * 5.232 = 6.8016`, following this file's own established methodology).

## Out of Scope
- The `ECONOMY` anchor in the same test — untouched, already passing.
- `test_simq_routing_test_seed42_1000t_cognition_grade_stability` — investigated as a second
  candidate failure from the same full-suite reproduction, confirmed transient (3/3 clean isolated
  passes), not a real drift, left untouched.
- The temporary performance-threshold warning-not-failure policy change requested separately by
  the user (`tests/perf/`, `tests/arena/`, certification perf-only assertions) — handled by a
  separate, dedicated ticket.
- Any `src/` change — the drift is already confirmed correct/intentional (the same role/faction
  fix already resolved and recalibrated once via `grade_anchors.json`); only this test's own
  unsynced copy needed fixing.

## Acceptance Criteria
- [x] New anchor value traced directly to `grade_anchors.json`'s already-committed, already-
      causally-explained value — not guessed.
- [x] Fresh `abs_floor` derived from real trial data gathered during this investigation.
- [x] Test passes reliably: 3/3 clean isolated runs post-fix (in addition to the 2 full-detail
      pre-fix failures that provided the real evidence).
- [x] No `src/` file changed.

## Related Tickets
- `TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION` (the real cause and the source of
  the correct, already-committed `grade_anchors.json` value)
- `TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH` (same-shape precedent for the
  unsynced-literal pattern, from a different source commit)
- `TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP` (the original, now-stale July source of
  this test's literal)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Confirmed via direct comparison that `grade_anchors.json`'s SOCIAL entry for this run_key was
already correct (matching the July investigation's own historical range being superseded by the
Aug 10 recalibration) — this is a pure test-literal sync, not a new investigation into causation.

## Test Summary
- Pre-fix (2 full-detail runs, real evidence): both FAILED with real score-tolerance
  AssertionErrors (`mean_score=22.5040`/`24.0080` vs stale `anchor_score=17.9655`).
- Pre-fix retry sweep (5 additional isolated attempts, mixed contended/calm system load): 2
  passed, 3 failed — consistent with a real drift exceeding the stale tolerance, not pure noise
  (contrast with the sibling `simq_routing_test` candidate, which passed 3/3 clean).
- Post-fix: 3/3 clean isolated passes (`133.54s`, `121.82s`, `120.19s`).

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Completion Summary
Full local reproduction of the entire `-m slow` corpus-diversity suite (requested explicitly by
the user instead of trusting individual CI-error fixes) surfaced this real, persistent drift that
the original 10-test CI-failure batch never caught (since it wasn't among those originally
failing tests). Traced to a stale test-literal left unsynced with an already-correct,
already-causally-explained `grade_anchors.json` value from an earlier, unrelated ticket.
Recalibrated using real evidence gathered directly during this investigation.
