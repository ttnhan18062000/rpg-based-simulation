---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE
phase: done
date: 2026-08-30
tags: [testing, corpus, calibration, social]
---

# TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE

## Title
Re-baseline `test_urban_political_seed42_1000t_social_grade_stability`'s SOCIAL Floor (Real Drift,
Not a Backpressure Artifact)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Filed from `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`. That ticket fixed the
persistence-phase backpressure bug that previously made this test fail with
`CalibrationIntegrityError`/timeout. With the fix, the test now completes cleanly (3/3 trials, no
integrity error) but fails on a genuine, now-visible floor/tolerance drift:

```
SOCIAL: mean_score=36.8373 vs anchor_score=15.45 (tolerance abs_floor=6.5052)
per-trial values: [32.3, 34.424, 43.788]
```

This is a large, consistent upward drift (all 3 trials well above the anchor + tolerance band),
not test flakiness. It is very likely the same root-cause pattern already established by
`TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE` (44/61 corpus-wide SOCIAL-pillar drifts
traced to `ENABLE_SOCIAL_COOPERATION`/`ENABLE_BELIEF_ASSIMILATION` now being ON by default plus
several M1-batch tickets wiring real content behind previously-dormant cooperation/belief paths)
— but that ticket only covered `test_grade_regression.py`'s fast-tier (`FAST_ANCHOR_KEYS`)
corpus, which does NOT include this slow-tier (1000t) `test_corpus_diversity.py` test. This ticket
exists because this specific test was never in scope for that rebaseline and needs its own
evidence-backed floor update using `test_corpus_diversity.py`'s own established multi-batch
tolerance-band methodology (see `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s
precedent for exactly this kind of re-baseline).

## Scope
- Confirm the SOCIAL drift's root cause (do not assume it's identical to the fast-tier corpus
  pattern without checking — `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` has also
  landed since the original drift was measured, which could itself move this score further;
  re-measure fresh on current HEAD, not the numbers quoted above).
- Re-run `test_corpus_diversity.py`'s multi-batch trial methodology for this specific test and
  derive a new evidence-backed `SCORE_TOLERANCE_OVERRIDES`/floor entry.
- Update the floor with the same rigor and documentation style as
  `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`.

## Out of Scope
- Any other `test_corpus_diversity.py` test not named here.
- The persistence-phase performance fixes already landed by the filing ticket.
- Re-touching `grade_anchors.json` (a different fixture entirely, already handled by the separate
  fast-tier corpus rebaseline).

## Acceptance Criteria
- `test_urban_political_seed42_1000t_social_grade_stability` passes with a fresh, evidence-backed
  floor.
- The floor update documents its reasoning (root cause, evidence) inline, matching the file's
  existing documentation conventions for prior re-baselines.

## Related Tickets
- TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION (filing ticket, disclosed this
  finding by fixing the bug that was masking it)
- TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE (precedent methodology, different fixture)
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (precedent methodology, same fixture)
- TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING (may affect the fresh measurement)

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py

## Assumptions / Open Questions
Whether this is the same SOCIAL-drift root cause as the fast-tier corpus rebaseline, or something
specific to the 1000-tick window — not yet confirmed, to be resolved during investigation.

## Implementation Notes
Root cause confirmed fresh on current HEAD, not assumed: `SocialScorer` (`src/simulation_quality/scorers/social.py:19-31`)
scores `contract_offer_created`/`contract_expired_offer`/`contract_offer_accepted`/`cooperation_event`
heavily. Two sibling tickets landed after the filing ticket's 36.8373 measurement —
`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` and
`TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST` — both gate that same event volume.

Re-measured via a standalone probe script reusing this test's own exact
`_run_engine`/`_build_hub`/`_replay_jsonl_through_hub` call sequence: 9 independent fresh trials
across 3 batches of 3 (following `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s
established "2 batches combined for the anchor, 3rd batch as independent verification"
methodology). All 9/9 landed grade S with `normalized_score` in `[33.151, 36.539]`
(~10% spread) and `event_count` in `[8484, 9381]` (~10% spread) — both dramatically tighter
than the ~40%/~31% spreads already documented pre-fix, and 0/9 hit `CalibrationIntegrityError`
or a timeout (confirming the persistence-backpressure fix remains effective).

Combined 6-draw pool (batches 1+2): mean=35.1038, largest single-sample deviation from that
mean=1.9528 (batch 2 trial 1) → `abs_floor = 1.3 * 1.9528 = 2.5387`. Verified against the
held-out 3rd batch: mean=35.0767, delta=0.0271 from the derived anchor — comfortably inside
tolerance. New anchor: `{"grade": "S", "score": 35.1038, "abs_floor": 2.5387}` (grade unchanged).

This is a further, real, evidence-backed drift from the filing ticket's own already-superseded
36.8373 measurement — not identical to the fast-tier `test_grade_regression.py` corpus pattern
(different fixture, out of scope) but the same underlying root-cause *class* (cooperation-offer
event volume). Not ambiguous: evidence is clean and consistent (9/9 same grade, tight
clustering), fully explained by the two disclosed cooperation-offer fixes — no
`NEEDS_HUMAN_INPUT` escalation warranted.

Updated: the test's own docstring (full derivation), the module docstring's §5 section
(cross-reference addendum, not a rewrite), and `docs/testing/regression_policy.md` (new §11
worked-example note). No `src/` file touched — `behavior_changed=false`, this is a test-fixture
calibration change only.

## Test Summary
`pytest tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability -v --tb=short --resource-budget large`
— **final/authoritative invocation: 1 passed** (103.54s).

**Full disclosure of real-invocation reliability observed during this session** (Gate Integrity —
reporting truthfully, not cherry-picking): the target test was run 12 times total via real pytest
invocations during this ticket's Test-phase work (in addition to the 9 standalone-script
calibration trials that fed the anchor derivation above). **10/12 passed cleanly; 2/12 failed.**
The one failure whose detail was captured: `SOCIAL: mean_score=43.5800` (per-trial
`[33.522, 51.082, 46.136]`) — 2 of 3 trials spiked well above every other trial observed in this
session (the 9 calibration trials + 4th verification batch run afterward, 12 draws total, all in
`[30.278, 36.539]`). Cross-checked against `sar -q` historical load data: this failure's timestamp
falls exactly in a window where machine-wide `ldavg-1` climbed from 0.38 to 2.70 (confirmed via
`sar -q` 10-minute samples spanning the relevant window) — a real, external, machine-wide
contention spike from other concurrent sessions on this shared 4-core box (`ps aux` confirmed 4+
other active `claude`/`claude --resume` processes at the time), not something in this ticket's own
scope. This matches the already-known, already-accepted `Kernel` wall-clock mid-tick-throttle
nondeterminism finding this file's own docstring already documents (§5's "16-vs-13" discussion,
and `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s own Verify-phase experience of
the identical pattern under "4+ concurrent Claude/Codex sessions") — not a new, different bug.

**Deliberately not widened further to cover this outlier**: incorporating the 51.082 sample into
the floor derivation would require `abs_floor ≈ 18` (1.3x its ~13.87 deviation from a 12-draw
mean), which would gut the test's value as a regression guard (effective tolerance would span
roughly [19, 55] around a ~35 anchor). This single-invocation, load-spike-correlated outlier is
treated the same way the precedent ticket treated its own analogous Verify-phase load-driven
flakes: disclosed, attributed to the already-known/deferred class, not chased into the floor.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py` — updated `SOCIAL` anchor in
  `test_urban_political_seed42_1000t_social_grade_stability`'s `anchors` dict from
  `{"grade": "S", "score": 15.45, "abs_floor": 6.5052}` to
  `{"grade": "S", "score": 35.1038, "abs_floor": 2.5387}`; updated that test's own docstring with
  the fresh 9-trial evidence and derivation; added a short cross-reference addendum to the module
  docstring's §5 section.
- `docs/testing/regression_policy.md` — added §11, a worked-example cross-reference note for this
  re-baseline event, following §9's established pattern.

## Completion Summary
Re-baselined `test_urban_political_seed42_1000t_social_grade_stability`'s SOCIAL anchor using
fresh, 9-trial (3-batch), evidence-backed measurement taken after both
`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` and
`TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST` had landed — the ticket's own
originally-quoted 36.8373 figure was confirmed stale (measured before those two fixes) and was
not reused. New anchor: `{"grade": "S", "score": 35.1038, "abs_floor": 2.5387}`, derived and
verified per `test_corpus_diversity.py`'s own established 2-batch-combined-plus-verification-batch
methodology. Root cause confirmed as the same cooperation-offer-volume class already established
elsewhere in this file, with no residual unexplained component.
