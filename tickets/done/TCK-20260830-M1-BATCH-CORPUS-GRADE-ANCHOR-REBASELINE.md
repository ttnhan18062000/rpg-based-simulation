---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
phase: done
date: 2026-08-30
tags: [simulation-quality, grade-thresholds, calibration, social, feature-flags]
---

# TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE

## Title
Re-baseline `grade_anchors.json` After M1 Batch's Real Behavior Changes (63/71 Fast Corpus Tests
Now Failing)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
This is the "verify with SimQ" step requested after the M1 Quick Wins batch (22 tickets) and its
~10 follow-up tickets landed on `m1-quick-wins`. Running `make simq-full-audit-full` (real engine
re-run across all 71 fast (≤500t) corpus scenarios, diffed against
`tests/simulation_quality/fixtures/grade_anchors.json`) found **63 of 71 tests failing** — nearly
the entire corpus.

Root-caused via a dedicated read-only investigation (evidence-based, not guessed — verified
against real `data/calibration/*/quality_scores.jsonl` event data and `git log`):
`tests/simulation_quality/fixtures/grade_anchors.json` has **zero commits** anywhere in the
entire M1 batch, despite the batch landing multiple real, intentional behavior changes:
`TCK-20260824-ROLLOUT-FLAG-DECISIONS` flipped `ENABLE_BELIEF_ASSIMILATION` and
`ENABLE_SOCIAL_COOPERATION` `ON` by default corpus-wide (independently confirmed:
`src/domains/optimization/feature_flags.py:37,52` both now `FeatureMode.ON`), and several other
tickets wired real production content behind those and other previously-dormant paths
(`TCK-20260824-WIRE-ORPHANED-MECHANISMS`, `TCK-20260824-TOWN-CENTER-POINTER-FIX`,
`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`, `TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING`, and
others — see the investigation's full ticket list below).

Of the 61 non-already-tracked failures (2 others are already covered by
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`), the investigation found:
- **0 confirmed real regressions.**
- **~55/61** legitimate M1-batch-caused drift, each traced to a specific causing ticket and
  verified against real event data (dominant pattern: 44/61 involve `SOCIAL` drifting sharply
  upward — cooperation/belief content firing for the first time; smaller patterns in
  `PROGRESSION`, `COMBAT`, `ECONOMY`, `NARRATIVE`, `COGNITION`, `AGENCY`).
- **~6/61** already fully covered by the pre-existing `tools/simq_ceiling.py` known-tolerance
  mechanism (tick-budget / flag-gated / watchdog-variance noise), i.e. not new drift at all.

Full per-run_key classification, evidence, and causing-ticket mapping is preserved in this
ticket's own investigation.md (see Implementation Notes for where the raw investigation output
was captured).

## Scope
- Re-run `make calibrate` (or the file's own documented anchor-regeneration procedure — see
  `tests/simulation_quality/fixtures/grade_anchors.json`'s own module docstring / the
  `test_grade_regression.py` module docstring, lines ~23-30) for all `FAST_ANCHOR_KEYS` on the
  current `m1-quick-wins` HEAD.
- Regenerate `grade_anchors.json` with the fresh values.
- In `investigation.md`, explicitly document (not silently re-center):
  1. The `SOCIAL`/cooperation-wiring root cause for the ~44 `SOCIAL`-pillar entries.
  2. The wound-penalty-driven `PROGRESSION` sign-flip specifically observed in the two
     `urban_political_*_500t` worlds (the investigation found `PROGRESSION` moves the *opposite*
     direction there vs. the 200t worlds — same wound-penalty wiring, opposite-sign effect
     depending on run length; this needs a one-line explanatory note, not silent re-centering).
  3. A due-diligence check (not necessarily a fix) on the three `loop_detected` `SOCIAL`-decrease
     cases (`urban_political_seed42_200t`, `highland_traverse_seed42_200t`,
     `lifecycle_full_coverage_world_seed42_200t`) — these show very high per-entity
     cooperate/expire event cadence (some entities firing every tick) triggering
     `pillar_accumulator.py`'s anti-spam `loop_detected` dampener. Confirm this reads as
     legitimate (cooperation content going from dormant to real, expected to be dense) rather
     than a tuning problem, before accepting the new lower score as the anchor. If it looks like
     a real tuning issue (e.g. cooperation offers should have a cooldown and don't), disclose it
     as a separate finding — do not silently fix cooldown logic inline as part of a re-baseline
     ticket.
- Re-run `test_grade_regression.py -m "not slow"` after regeneration and confirm it passes clean
  (mirroring `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`'s precedent for a
  legitimate-fix-caused batch of anchor drift, `docs/testing/regression_policy.md` §9).

## Out of Scope
- The 2 already-tracked `urban_political_selfmodel*_probe` failures — covered by
  `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`, do not duplicate that work
  here.
- Slow-tier (`-m slow`, 1000t/2000t) corpus tests — out of this ticket's scope; run separately if
  warranted after this lands.
- Fixing any actual code defect uncovered during due diligence on the `loop_detected` cases (per
  above, disclose rather than fix inline).
- Changing any feature flag default — this ticket only re-baselines anchors to match already-
  decided, already-shipped defaults; it does not revisit the ROLLOUT-FLAG-DECISIONS verdicts.

## Acceptance Criteria
- `make simq-full-audit-full`'s `test_grade_regression.py -m "not slow"` step passes clean (or
  any remaining failure is independently new and disclosed as its own finding, not silently
  absorbed into the re-baseline).
- `grade_anchors.json`'s diff is reviewed for genuine content (not a raw full-file rewrite
  artifact) — confirm the diff touches only the run_keys this ticket's investigation named.
- The three `loop_detected` cases and the `PROGRESSION` sign-flip nuance are explicitly written up
  in investigation.md, not silently absorbed into a blanket re-baseline.

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (flipped ENABLE_BELIEF_ASSIMILATION/ENABLE_SOCIAL_COOPERATION ON)
- TCK-20260824-WIRE-ORPHANED-MECHANISMS
- TCK-20260824-TOWN-CENTER-POINTER-FIX
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
- TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING
- TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH (precedent for this kind of ticket)
- TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION (covers the 2 excluded failures)

## Related Docs
- docs/testing/regression_policy.md (§9)
- tests/simulation_quality/test_grade_regression.py (module docstring, anchor-regeneration procedure)

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json
- src/simulation_quality/pillar_accumulator.py (loop_detected dampener)
- tools/simq_ceiling.py

## Assumptions / Open Questions
Whether the 3 `loop_detected` cooperation-cadence cases represent a real tuning gap (cooperation
offers should have a cooldown) or expected behavior for newly-live content — to be resolved
during this ticket's own due-diligence check, not assumed either way going in.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE/plan.md`
exactly, no deviations. Used the frozen `data/calibration/*/quality_report.json` snapshot on disk
(the same one `investigation.md`'s evidence table was built from) — did not re-run
`tools/evaluate_simq.py`, per the plan's explicit anti-drift instruction.

Wrote and ran a throwaway one-off script (`/tmp/write_anchors_impl.py`, not committed to `tools/`
— mirrors how there's no durable writer for `grade_anchors.json`, unlike
`tools/parity_ledger_writer.py` for parity YAML) that re-uses the live helper functions imported
directly from `tests/simulation_quality/test_grade_regression.py` itself (`_within_band`,
`_within_score_tolerance`, `_score_tolerance_kwargs`, `_extract_pillar_grades/scores`,
`_load_calibration_report`) to reproduce the test suite's own pass/fail verdict for every
`(run_key, pillar)` pair across all 61 `FAST_ANCHOR_KEYS`, and overwrite only the failing entries'
`{grade, score}` fields with fresh actual values from `quality_report.json`. This updated exactly
**210** `(run_key, pillar)` entries (verified independently by diffing the old and new JSON
key-by-key with a separate script, not just trusting the writer's own printed count) and left
**1** entry (`highland_traverse_seed42_200t` / SOCIAL) deliberately un-rebaselined per the plan's
explicit disclosure carve-out. Both out-of-scope `urban_political_selfmodel*_probe` run_keys show
zero diff (`git diff ... | grep -c urban_political_selfmodel` returns 0), confirming the exclusion
set worked as intended.

The `highland_traverse_seed42_200t`/SOCIAL entry is left failing on purpose: full investigation
(see `investigation.md`'s `loop_detected` Due-Diligence section) found a real tuning gap in
`src/domains/cooperation/phase.py` — the per-tick cooperation-decision loop has no
cooldown/backoff after a `contract_expired_offer`, so the same entity can re-attempt and re-fail
every tick indefinitely (confirmed from `quality_report.json`'s `worst_events`: entity 13 fires
`contract_expired_offer` on 23 consecutive ticks, entity 8 on 20). Per this ticket's explicit
scope guard, this was disclosed, not fixed inline — `src/domains/cooperation/` was not touched.
Recommend a follow-up ticket to add a minimum retry interval / per-partner-pair backoff.

Diff verified surgical: only `grade`/`score` value fields changed inside existing pillar objects;
key order, JSON structure, and 2-space indent formatting are byte-for-byte unchanged elsewhere in
the file (`git diff tests/simulation_quality/fixtures/grade_anchors.json` spot-checked, confirms
no full-file reformat artifact).

**Deviation from the literal Step 4 expectation (disclosed, not silently absorbed)**: the
`test_grade_regression.py -m "not slow"` run after the anchor update has **3** failing tests, not
the single `test_grade_within_anchor_band[highland_traverse_seed42_200t]` expected. The other 2
(`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`) are dedicated test functions —
not members of `FAST_ANCHOR_KEYS`, structurally unreachable from this ticket's anchor-writing
loop, and already covered by `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` per
this ticket's own Out-of-Scope section. Verified via `git stash` that both were already failing,
with byte-identical assertion output, **before** this ticket's diff — i.e. genuinely pre-existing
and unrelated to this change, not a new regression introduced by the anchor rewrite. This matches
the ticket's actual Acceptance Criteria wording ("or any remaining failure is independently new
and disclosed as its own finding, not silently absorbed into the re-baseline") — both are
independently pre-existing and already disclosed/tracked elsewhere, not new. Not force-fit; not
silently treated as the single expected failure — recorded here for traceability.

## Test Summary
`.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`
→ **68 passed, 3 failed, 18 deselected**.

Failures (all expected/disclosed, none a new regression from this change):
1. `test_grade_within_anchor_band[highland_traverse_seed42_200t]` — in-scope, deliberately left
   failing per this ticket's own disclosure decision (real cooperation-cooldown gap, not
   re-baselined; see Implementation Notes above).
2. `test_urban_political_selfmodel_cognition_isolated_grade_anchor` — out of scope, pre-existing
   (confirmed unchanged before/after this ticket's diff via `git stash`), owned by
   `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`.
3. `test_urban_political_selfmodel_execution_isolated_grade_anchor` — same as above.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` (210 of 211 failing `(run_key, pillar)`
  entries updated to fresh actual values; `highland_traverse_seed42_200t`/SOCIAL and both
  selfmodel-probe run_keys left untouched)
- `tickets/inprogress/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE.md` (this file —
  Implementation Notes / Test Summary / Files Changed / Completion Summary / Status)
- `staging_artifacts/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE/investigation.md`,
  `plan.md`, `test_plan.md` (created/substantively written during this run's own
  Investigate/Plan phases, prior to Implement)
- `docs/testing/regression_policy.md` — **not yet changed by this phase**; the plan's Step 5
  worked-example section is the Document-Update phase's responsibility, not Implement's.

## Completion Summary
Re-derived the M1-batch grade-anchor drift fresh against a frozen `data/calibration/` snapshot and
found it exactly matches the filing investigation's headline 55/6 split (55 run_keys with real,
evidence-traced M1-batch drift; 6 fully explained by pre-existing `simq_ceiling.py` tolerances),
while correcting its framing on two points: WORLD's 35 failing combos are 100%
pre-existing-ceiling noise (not new drift, previously unstated), and the `loop_detected` mechanism
is a diagnostic-only flag with no scoring effect (not a "dampener" as originally described). Wrote
and ran a one-off script that updated exactly 210 of 211 failing `(run_key, pillar)` anchor entries
in `tests/simulation_quality/fixtures/grade_anchors.json` to fresh actual values, leaving 1 entry
(`highland_traverse_seed42_200t`/SOCIAL) deliberately failing and disclosed — it traces to a real,
unfixed cooperation-cooldown gap in `src/domains/cooperation/phase.py` (no backoff after an offer
expires), reported as a follow-up-ticket recommendation rather than fixed inline, per this
ticket's explicit scope guard. No `src/` file was touched. The fast-tier suite now shows 68
passed / 3 failed (1 in-scope disclosed + 2 pre-existing out-of-scope failures owned by a separate
ticket), matching the Acceptance Criteria's allowance for disclosed remaining failures.
