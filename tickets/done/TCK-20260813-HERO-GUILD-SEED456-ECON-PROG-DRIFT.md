---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT
phase: done
date: 2026-08-13
tags: [simulation-quality, calibration, corpus, economy, progression]
---

# TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT

## Title
`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift beyond band/tolerance, plus a related
unannotated `simq_routing_test_seed456_500t` PROGRESSION score-tolerance drift found during
Implement — both disclosed but out of `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`'s
own named scope

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed as the required follow-up ticket for a finding explicitly deferred by
`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` (that ticket's Scope named only
AGENCY + the `seed123` COGNITION/AGENCY pair; this ECONOMY/PROGRESSION drift on a different
run_key was confirmed present in the same fresh committed report but deliberately not folded into
that ticket's recalibration — see its Scope Guards and plan.md Step 9b).

**(1) `hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION drift (named by the originating
ticket).** Fresh calibration at current HEAD (`tools/calibrate_simq.py --ticks 500 --seed 456
--name hero_guild_routing`) shows:
- ECONOMY: anchor grade B (`score=0.10972568578553615`) vs. actual `0.0` — outside score
  tolerance, no `score_ceilings.json` ceiling annotation covers this.
- PROGRESSION: anchor grade D (`score=-0.6212534059945504`) vs. actual `-0.3025210084033613` —
  outside score tolerance, no ceiling annotation.

**(2) `simq_routing_test_seed456_500t` PROGRESSION drift (newly found during the originating
ticket's Implement phase, not previously named by any ticket).** This run_key's PROGRESSION was
previously masked from view: the `test_grade_within_anchor_band` assertion order evaluates
`band_failures` before `score_failures`, and prior to the originating ticket's AGENCY recalibration
this run_key's AGENCY band-crossing failure short-circuited the test before its PROGRESSION
score-tolerance failure was ever surfaced. Once AGENCY was recalibrated, PROGRESSION became
visible: anchor `score=-0.6927374301675978` vs. actual `-0.15483870967741936` — outside score
tolerance, no `score_ceilings.json` ceiling annotation covers this run_key's PROGRESSION either.
`simq_routing_test_seed456_500t`'s own COMBAT drift in the same fresh run (`actual=0.0727...` vs
anchor `0.0`) IS already covered by an existing `flag_gated` ceiling annotation
(`ENABLE_COMBAT_ENGAGEMENT` corpus-wide OFF) — only PROGRESSION is new/unexplained.

Neither drift was fixed or recalibrated by the originating ticket — its own Scope Guards
explicitly forbid touching `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION fields, and
`simq_routing_test_seed456_500t`'s PROGRESSION drift was outside its named scope entirely (only
discovered as a side effect of that ticket's own AGENCY fix unmasking a previously-hidden
assertion).

## Scope
- Determine the root cause of `hero_guild_routing_seed456_500t`'s ECONOMY and PROGRESSION drift —
  confirm whether it shares the same commit-cluster cause as the AGENCY/COGNITION drift
  (`3d992dd0`/`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, or the `AdventureDecisionPhase`
  deletion) or is a distinct mechanism.
- Determine the root cause of `simq_routing_test_seed456_500t`'s PROGRESSION drift — confirm
  whether it is the same mechanism as (1), the same class of pre-existing `watchdog_variance` noise
  already documented for sibling run_keys' PROGRESSION fields, or something new.
- Recalibrate `grade_anchors.json` for whichever fields are confirmed genuine drift (not a bug to
  fix), or add a `score_ceilings.json` ceiling annotation if the root cause is the same
  low-event-count watchdog-throttle sensitivity already documented for sibling run_keys'
  PROGRESSION fields.

## Out of Scope
- AGENCY/COGNITION for any of the 6 run_keys `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`
  already recalibrated — already closed by that ticket.
- The `_1000t` guard test conversions — already closed by that ticket.
- `src/domains/adventure/`, `src/systems/strategic_systems/intelligence.py`, or any other
  production code — Investigate first; only fix source if a real code gap (not a stale anchor) is
  confirmed.

## Acceptance Criteria
- [x] Root cause of `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift confirmed via
      direct evidence, not assumed (investigation.md Finding 1 — DEBUG-trace of tier-5 goal
      arbitration, HARVESTING wins 1/371 evaluated ticks; disclosed in
      `docs/guidelines/intentional_divergences.md` §2.41's newest addendum)
- [x] Root cause of `simq_routing_test_seed456_500t`'s PROGRESSION drift confirmed via direct
      evidence, not assumed (investigation.md Finding 1 — HARVESTING wins 1/335 evaluated ticks —
      plus Finding 2 — genuine 2/5-vs-3/5 bimodal watchdog_variance jitter on top of the
      suppression, confirmed via 6 independent same-seed re-runs)
- [x] `grade_anchors.json` and/or `score_ceilings.json` updated to reflect confirmed current,
      correctly-classified values for both run_keys (3 `grade_anchors.json` pillar fields edited;
      1 new additive `score_ceilings.json` `watchdog_variance` entry added)
- [x] `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
      "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"` shows 0 unexplained
      failures (textual check: pytest exit code is non-zero — 2 failed, as explicitly predicted by
      plan.md/test_plan.md — but every line in both failures' `score_failures` output carries a
      trailing `[known ...]` annotation: COMBAT `[known flag_gated]` + WORLD `[known tick_budget]`
      for `hero_guild_routing_seed456_500t`; COMBAT `[known flag_gated]` + PROGRESSION
      `[known watchdog_variance]` for `simq_routing_test_seed456_500t`. Zero unannotated lines.)

## Related Tickets
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (originating ticket; disclosed (1) via
  its own Scope/investigation.md Risk #3, and (2) was found and disclosed during that ticket's own
  Implement-phase verification of its AGENCY recalibration)
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (established the `watchdog_variance`
  ceiling mechanism these fields may or may not qualify for)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.40, §2.41

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/ (once moved —
  investigation.md Finding 1's raw pytest evidence for (1); this ticket's own filing session for
  (2))

## Related Code Areas
- tests/simulation_quality/fixtures/grade_anchors.json (`hero_guild_routing_seed456_500t`,
  `simq_routing_test_seed456_500t` ECONOMY/PROGRESSION fields)
- tests/simulation_quality/fixtures/score_ceilings.json

## Assumptions / Open Questions
- Whether (1) and (2) share a single root cause or are two distinct mechanisms is not determined —
  Investigate's job.
- Whether either qualifies for the `watchdog_variance` ceiling mechanism (real run-to-run
  non-determinism at low event counts, per the precedent in
  `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) or represents a genuine anchor drift
  requiring recalibration is not determined here.

## Implementation Notes

Followed staging_artifacts/TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT/plan.md's 8 steps
exactly; no deviation from the plan's mechanics or scope guards.

**Step 1 (fresh clean calibration re-runs):** Ran `tools/calibrate_simq.py --ticks 500 --seed 456
--name hero_guild_routing` and `--name simq_routing_test` (`.venv/bin/python3`, no DEBUG log
handler attached to any logger). Results:
- `hero_guild_routing_seed456_500t`: ECONOMY `events=0, norm=0.0`; PROGRESSION `events=11,
  norm=-0.3025210084033613` — exact byte-match to investigation.md's cited clean-trial values. All
  other pillars (AGENCY, COGNITION, COMBAT, FACTION, INFORMATION, NARRATIVE, SOCIAL all 0.0;
  WORLD 0.32/57 events) matched investigation.md's report exactly — confirmed a clean,
  representative trial.
- `simq_routing_test_seed456_500t`: this fresh run's own single draw landed on the **minority
  (2/5-historical-rate) `21-event` state** (`norm=-0.15483870967741936`), not the majority state —
  this is explicitly expected per plan.md Step 1's own framing ("If this run also lands on the
  21-event state, that is expected... and not a reason to change the anchor value"). COMBAT
  (`0.07272727272727272`/6 events) and ECONOMY (`0.09523809523809523`/4 events) matched
  investigation.md's citations exactly. Per the plan's "Decision on Open Question" (based on the
  aggregate 5-trial modal distribution from investigation.md, 3/5 vs 2/5, not a single fresh draw),
  proceeded with Step 3's anchor value `-0.2359249329758713` regardless of which single state this
  run happened to land on.

**Steps 2-3 (`grade_anchors.json` edits):** Edited exactly 3 pillar fields across the 2 named
run_keys — `hero_guild_routing_seed456_500t.ECONOMY` (`B/0.10972568578553615` →
`C/0.0`), `hero_guild_routing_seed456_500t.PROGRESSION` (`D/-0.6212534059945504` →
`C/-0.3025210084033613`), `simq_routing_test_seed456_500t.PROGRESSION`
(`D/-0.6927374301675978` → `C/-0.2359249329758713`, the modal/3-of-5 state per the plan's
resolved Risk #1 decision). Confirmed via `git diff` that no other key/value in the file changed
and the file still has 84 total top-level keys (81 scenario entries + 3 metadata keys) after the
edit.

**Step 4 (`score_ceilings.json` new entry):** Appended one new `watchdog_variance` entry for
`("simq_routing_test_seed456_500t", "PROGRESSION")`, verbatim per plan.md's exact JSON, after the
existing 6 entries (now 7 total). `git diff --stat` confirms the change is purely additive (8
insertions, 0 deletions) — no existing entry was touched.

**Step 5 (`intentional_divergences.md` §2.41 addendum):** Inserted the HARVESTING-starvation
addendum verbatim (plan permitted tightening wording but every cited fact was preserved as-is), placed
after the existing "Restoration" bullet and before the "Verification"/"Status" lines, per the plan's
exact insertion point.

**Step 6 (`eval_matrix_results.md` NOTE blocks):** Inserted two dated NOTE blocks — one in the
`simq_routing_test` 500t subsection (after the existing
`TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` NOTE, before the section's `---`), one
in the `hero_guild_routing` 500t subsection (same insertion pattern). Both NOTE blocks state the
exact committed `grade_anchors.json` values copy-pasted from Steps 2-3 (not retyped by hand).
Historical table rows were left unrewritten per the plan's explicit instruction — disclosure via
NOTE block only.

**Step 7 (verification):** Ran the ticket's own AC4 command verbatim. As plan.md/test_plan.md
explicitly predicted, the command does NOT exit 0 (2 failed) — but the textual pass condition
holds: every line in both failures' `score_failures` output carries a trailing `[known ...]`
annotation (see Acceptance Criteria above for the full breakdown). Also ran the regression/anti-drift
guard sweep (`test_grade_anchor_file_exists_and_valid`, `test_grade_anchors_entry_count_unchanged`,
`test_score_tolerance_override_table_scoped_to_named_pillars`,
`test_score_tolerance_overrides_do_not_affect_unlisted_anchors`, all of
`tests/tools/test_score_ceilings.py`) — 10/10 passed, 0 failures. Additionally ran a full
`FAST_ANCHOR_KEYS` before/after sweep via `git stash push -- grade_anchors.json score_ceilings.json`
/ `git stash pop`: both before and after produced the identical 29-failure set (`comm -23`/`comm
-13` diff both empty) — confirms zero unrelated `(run_key, pillar)` pairs newly failed or newly
passed. The two named run_keys' own parametrizations remain in the failing set both before and
after (expected — COMBAT's `[known flag_gated]` failure alone keeps both `test_grade_within_
anchor_band` parametrizations red regardless of this ticket's edits, since the assertion is
all-pillars-at-once, not per-pillar), but their internal `score_failures` content changed from
partially-unannotated to fully-annotated, which is the actual acceptance signal per Step 7's
textual pass condition.

**Step 8 (parity ledger):** No edit made. Re-confirmed via a fresh grep
(`grep -rln "hero_guild_routing_seed456\|simq_routing_test_seed456" docs/parity_ledger/`) — zero
matches, consistent with investigation.md's and plan.md's own independent checks.

**Optional guard test not added:** test_plan.md flagged
`test_watchdog_variance_ceiling_present_for_simq_routing_test_seed456_progression` as optional,
"not a hard requirement." Not added — the existing `test_grade_within_anchor_band` parametrizations
and the 6 existing `test_score_ceilings.py` tests already provide full coverage of the new entry's
shape and the recalibrated values; a narrower duplicate test was judged unnecessary per the plan's
own framing.

No `src/` file was touched. No `SCORE_TOLERANCE_OVERRIDES` entry was added. No existing
`grade_anchors.json` run_key or `score_ceilings.json` entry was deleted, reordered, or edited beyond
the specified additive change.

## Test Summary

- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid
  tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors
  -q -m "not slow"` → 3 passed (Step 2/3 verification)
- `pytest tests/tools/test_score_ceilings.py -q -m "not slow"` → 6 passed (Step 4 verification)
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k
  "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"` → 2 failed (expected, textual
  pass — see Acceptance Criteria/Implementation Notes above for the full annotated breakdown)
- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid
  tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars
  tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors
  tests/tools/test_score_ceilings.py -q -m "not slow"` → 10 passed, 0 failed (Step 7 regression/anti-drift sweep)
- Full `FAST_ANCHOR_KEYS` sweep (`pytest tests/simulation_quality/test_grade_regression.py -m "not
  slow" -q`), before/after via `git stash`: both runs 29 failed / 39 passed / 3 skipped / 18
  deselected, identical failure sets (zero unrelated regressions or unrelated newly-passing keys)
- `tests/simulation_quality/test_economy_scorer.py`, `tests/simulation_quality/
  test_progression_scorer.py` were not touched or run (this ticket makes no `EconomyScorer`/
  `ProgressionScorer` source change per test_plan.md's own framing — unaffected by construction)

## Files Changed

- `tests/simulation_quality/fixtures/grade_anchors.json` — 3 pillar fields edited across 2 existing
  run_keys (`hero_guild_routing_seed456_500t.ECONOMY`, `.PROGRESSION`;
  `simq_routing_test_seed456_500t.PROGRESSION`)
- `tests/simulation_quality/fixtures/score_ceilings.json` — 1 new additive `watchdog_variance`
  entry appended (`simq_routing_test_seed456_500t`/PROGRESSION)
- `docs/guidelines/intentional_divergences.md` — §2.41 gained a fourth dated addendum disclosing
  the HARVESTING tier-5-starvation finding
- `docs/simulation_quality/eval_matrix_results.md` — 2 new dated NOTE blocks (one in the
  `simq_routing_test` 500t subsection, one in the `hero_guild_routing` 500t subsection)
- `tickets/inprogress/TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT.md` — this file (Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes)

No `src/` file changed. No new/removed `grade_anchors.json` run_key. No `SCORE_TOLERANCE_OVERRIDES`
entry added. No `docs/parity_ledger/*.yaml` file changed.

## Completion Summary

Recalibrated `grade_anchors.json` for the 3 named (run_key, pillar) pairs to their fresh,
clean-calibration-confirmed values, and added one additive `score_ceilings.json` `watchdog_variance`
entry disclosing genuine run-to-run jitter on `simq_routing_test_seed456_500t`'s PROGRESSION pillar.
Both drifts share a root cause with the sibling `ADVENTURE_ROUTE` tier-5-starvation finding but
affect a mechanistically distinct `GoalKind` (`HARVESTING`, distance-decayed, not scale-capped) —
disclosed in a new `docs/guidelines/intentional_divergences.md` §2.41 addendum and two dated NOTE
blocks in `docs/simulation_quality/eval_matrix_results.md`. No source code was changed; this is a
fixture-only recalibration-and-disclose ticket. AC4's scoped pytest command exits non-zero as
explicitly predicted by the plan (both run_keys carry pre-existing, already-`[known ...]`-annotated
COMBAT/WORLD failures out of this ticket's scope), but the textual pass condition — zero unannotated
`score_failures` lines — is fully satisfied.
