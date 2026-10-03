---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER
artifact_type: test_plan
tags: [simulation-quality, calibration, corpus, testing]
---

# Test Plan — TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER

## Scope
No `src/` code was changed by this ticket (see `investigation.md`/`plan.md` — the root cause is a
stale calibration anchor, not a live emission-path defect). The "test plan" for this ticket is
therefore verification that (a) the 5 named tests still fail with the exact, expected,
already-documented signature (proving nothing regressed further and nothing was silently patched
around), and (b) the broader observability/corpus-diversity suite is unaffected, since a
zero-code-change ticket must not be assumed risk-free without checking.

## Tests run

### 1. Isolated reproduction of the 5 named failing tests (one at a time, per
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`'s documented concurrency caution)
- `test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability` — real `pytest -m
  slow` run: FAILED, `NARRATIVE grade=C` (anchor `A`) in all 3 trials. Matches pre-investigation
  report exactly.
- `test_frontier_extended_seed42_200t_narrative_grade_stability` — reproduced via the same
  production code path (`tools/calibrate_simq._run_engine`/`_replay_jsonl_through_hub`) as a
  standalone script; raw JSONL confirms all 10 NARRATIVE event types absent, matching the failing
  signature (full `pytest` run not repeated a second time for this one — script-level repro is the
  same underlying engine/scoring code the test itself calls).
- `test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability` — not
  independently re-run; same profile/world family as the two above, same conclusion applies per
  the investigation's stated (not independently re-verified) inference.
- `test_frontier_living_world_seed123_200t_combat_narrative_grade_stability` — not independently
  re-run in this session; noted as an open item in `investigation.md`'s cross-world check.
- `test_frontier_marches_seed42_200t_narrative_grade_stability` — real `pytest -m slow` run:
  FAILED, `NARRATIVE grade=C` (anchor `A`) in all 3 trials. Matches pre-investigation report
  exactly.

Both real `pytest -m slow` runs above were executed individually (not batched with each other or
with any other `-m slow` test), consistent with the session-load-flake guard.

### 2. Broader regression check
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m "not slow" -q` — run to confirm the
  non-slow half of this file is unaffected (no code was touched, but this test file itself is the
  one under discussion, so it is verified rather than assumed).
- Targeted observability/event-shaper unit tests found via context-scan (`tests/unit/
  observability/test_event_shapers_narrative.py`, `tests/unit/observability/
  test_event_extractor_agency2.py`, `tests/unit/observability/test_event_shapers.py`) — run to
  confirm the NarrativeShaper/QuestEvent/translation mechanics this investigation relied on as
  "already correct" are still passing, since the investigation's conclusion depends on them.

## Expected outcome
All of the above are expected to show **no change from pre-investigation state**: the 5 named
tests remain failing (correctly, per the ticket's own instruction not to force them green), and
the rest of the suite is green, proving this ticket's zero-code-change conclusion did not
introduce any regression while investigating.
