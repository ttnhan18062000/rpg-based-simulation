---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE
phase: open
date: 2026-07-15
tags: [simulation-quality, calibration, determinism, corpus]
---

# TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE

## Title
Investigate the disclosed residual F6-class flake risk in
`tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` grade-stability guards and
`test_grade_regression.py`'s fixed-width score tolerance, both left explicitly unresolved by
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (closing this session) added 14
tolerance-based grade-stability guards to `tests/unit/worldassembly/test_corpus_diversity.py`
after confirming all 14 re-anchored `grade_anchors.json` pillars are genuinely F6-class
load/timing-sensitive (`docs/audits/D06_longrun_health.md` §F6). Its own Implementation Notes
and `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` disclose,
but explicitly do not resolve, two related residual risks:

1. Three named pillars (`urban_political_seed123_1000t` SOCIAL and ECONOMY;
   `frontier_marches_seed42_200t` NARRATIVE) showed real-world score variance, across
   4-7 independent samples each, close to or exceeding `test_grade_regression.py`'s
   `test_grade_within_anchor_band`/`_long_run` fixed-width tolerance formula
   (`max(SCORE_TOLERANCE_ABS_FLOOR, SCORE_TOLERANCE_REL_PCT * |anchor_score|)`, i.e.
   `max(0.05, 0.20 * |anchor|)`), which that ticket was forbidden from widening. A single
   unlucky future draw for these pillars could still fail the fast anchor-band check even with
   a correctly re-anchored value and a correct multi-trial guard in place.
2. Two independent, full, sequential `pytest tests/unit/worldassembly/test_corpus_diversity.py
   -m slow --resource-budget large -v` runs of the whole 32-test file (18 pre-existing + 14 new)
   each showed exactly one guard failing — a different anchor each time
   (`test_frontier_marches_seed42_200t_narrative_grade_stability` in Run 1,
   `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` in Run 2) —
   under cumulative session-load pressure from everything that ran earlier in the same
   ~13-minute sequential session. This is roughly a 1-in-16-tests observed failure rate across
   the 32-test file, and the mechanism (cumulative wall-clock compute pressure across a long
   sequential in-process session, not a per-anchor calibration defect) could in principle also
   affect the 2 pre-existing precedent guards
   (`test_urban_political_seed123_500t_cognition_bit_identical_under_load` and
   `test_generated_frontier_3_42_extended_population_stability`), not just the 14 new ones —
   though neither of those two failed in either of the parent ticket's 2 full runs.

The parent ticket's Step 14 explicitly states "a third live-widening round was deliberately not
attempted" for reason (2) above — this was a scope/time-bounded stopping point, not an
abandoned or dismissed finding, and the parent ticket's own text calls for exactly this kind of
follow-up ("A CI/verification process that runs this file's tests with appropriate parallelism
or isolation ... would not be expected to see this effect"). This ticket files that follow-up.

## Scope
- Investigate whether `test_grade_within_anchor_band`/`_long_run`
  (`tests/simulation_quality/test_grade_regression.py`, `_within_score_tolerance()`,
  `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`) needs an evidence-derived-width option
  for pillars with confirmed high real-world variance, informed by
  `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`'s actual
  measured per-anchor variance (Sections 2-8), specifically for the 3 named pillars above.
- Investigate whether `tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` guards
  (all 32: the 18 pre-existing plus the 14 new from the parent ticket) should run with test
  isolation or parallelism in CI (`.github/workflows/test.yml`'s `slow` job, which currently
  invokes `pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q` as one
  long sequential in-process run) to eliminate cross-test cumulative-load contamination as the
  root mechanism of the observed ~1-in-16 flake rate.
- Determine, with evidence, whether remedy (a), remedy (b), both, or neither is the right
  path — this is investigation-tier work. Do not pre-decide the remedy in this ticket; that
  determination belongs to this ticket's own future investigation/plan phase.
- If a remedy is adopted, assess its impact against the existing accepted-tolerance behavior for
  every other pillar/anchor (not just the 3 named ones), so a fix for these 3 does not silently
  loosen or tighten checks elsewhere.
- Update `docs/parity_ledger/infrastructure.yaml` (extend INFRA-273, or add a new entry) and
  `docs/simulation_quality/eval_matrix_results.md` if the investigation results in a behavior or
  process change.

## Out of Scope
- Re-opening `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`'s own 14 grade-stability guards
  or their re-anchored `grade_anchors.json` values — those are done and correct as-is; this
  ticket investigates the residual risk they disclosed, it does not re-litigate their content.
- Re-opening `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s original
  `test_urban_political_seed123_500t_cognition_bit_identical_under_load` guard — stays as-is
  unless this investigation's own evidence specifically implicates it (not assumed).
- Any change to `src/engine/kernel.py`'s tick-budget watchdog / mid-tick emergency throttle
  mechanism — same hard constraint as both parent tickets; F6 is documented, intentional engine
  behavior (`docs/audits/D06_longrun_health.md`, `docs/engine/kernel.md`,
  `docs/engine/performance_contract.md` §7). Only test-side / CI-process-side remedies are in
  scope.
- Re-tuning any `scoring_weights.yaml` value or any `simulation_quality` scoring formula outside
  the tolerance-comparison logic named above.
- Adding coverage for anchors/pillars not already named in this ticket's Scope (the 3 named
  score-tolerance-risk pillars, and the 32-test `-m slow` file's flake mechanism as a whole) —
  a broader corpus-wide sweep is not this ticket's job.

## Acceptance Criteria
- [ ] Investigation determines, with cited evidence from `repro_sweep.md` and this ticket's own
      analysis, whether remedy (a) (evidence-derived tolerance width), remedy (b) (CI test
      isolation/parallelism for the `-m slow` guard file), both, or neither is warranted, and
      records the rationale in this ticket's Implementation Notes.
- [ ] If remedy (a) is adopted: a concrete evidence-derived-width mechanism is designed for
      `test_grade_within_anchor_band`/`_long_run` and verified to not change pass/fail outcome
      for any pillar/anchor other than the 3 named ones, with a passing test proving
      `test_within_band_default_tolerance_unchanged`-equivalent protection still holds for the
      unaffected pillars.
- [ ] If remedy (b) is adopted: a concrete CI isolation/parallelism proposal for
      `.github/workflows/test.yml`'s `slow` job (or an equivalent scoped invocation) is designed
      and at least one controlled comparison run (isolated/parallel vs. sequential) is executed
      and its result recorded, testing whether it measurably reduces or eliminates the
      cumulative-load-driven flake.
- [ ] Whichever remedy(ies) are adopted, `docs/parity_ledger/infrastructure.yaml` and
      `docs/simulation_quality/eval_matrix_results.md` are updated to reflect the decision.
- [ ] If neither remedy is adopted, that determination is documented with explicit reasoning
      (not silently dropped), and the residual risk remains disclosed rather than papered over.
- [ ] No change is made to any of the 14 guards' anchors, the 2 pre-existing precedent guards,
      any `grade_anchors.json` value from `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`, or
      `src/engine/kernel.py`'s watchdog/throttle mechanism, unless this investigation's own
      evidence specifically requires it and that requirement is called out explicitly.

## Related Tickets
- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (closing this session) — parent ticket;
  its Implementation Notes' "Net honest state" paragraph and Test Summary are the direct source
  of this ticket's residual-risk disclosure.
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (done) — established the F6 root-cause
  finding, the repro methodology (`repro_sweep.md` precedent), and the original
  bit-identical-guard pattern (`test_urban_political_seed123_500t_cognition_bit_identical_under_load`)
  this ticket's flake-rate concern extends to.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — original precedent for the
  tolerance-based multi-trial guard pattern (`test_generated_frontier_3_42_extended_population_stability`)
  used by all 14 of the parent ticket's new guards.

## Related Docs
- `docs/audits/D06_longrun_health.md` §F6 — the documented load-sensitive divergence finding
  both parent tickets trace to; this ticket's investigation must stay consistent with its
  "reliably reproducible below ~tick 300-320" hedge, which `TCK-20260715` already sharpened.
- `docs/engine/kernel.md`, `docs/engine/performance_contract.md` §7 — watchdog/throttle
  mechanism F6 attributes the variance to (read-only reference; not to be modified).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-273` (F6 blast-radius confirmation,
  documents the `test_path` this ticket's `-m slow` flake concerns) and `INFRA-272` (14-anchor
  carve-out closure); this ticket updates or extends these as its own findings land.
- `docs/simulation_quality/eval_matrix_results.md` — "Anchor Reliability Verification, Part 2"
  subsection, the 14-entry record this ticket's findings may extend.

## Related Stored Artifacts
- `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` — source of
  the measured per-anchor variance data (Sections 2-8) this ticket's remedy (a) investigation
  must use. At time of filing this parent ticket is still open in `tickets/inprogress/`; expect
  this artifact to move to `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/`
  once that ticket closes — check both locations.
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` — the
  original repro methodology template both parent tickets and this investigation build on.

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py` — `_within_score_tolerance()`,
  `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (lines 46-47),
  `test_grade_within_anchor_band`/`_long_run`, `test_within_band_default_tolerance_unchanged`
  (the existing guard any remedy-(a) change must not silently break for unaffected pillars).
- `tests/unit/worldassembly/test_corpus_diversity.py` — the 32 `-m slow` grade-stability /
  population-stability guards (18 pre-existing + 14 from `TCK-20260715`), including the 2 named
  precedent guards.
- `.github/workflows/test.yml` — the `slow` job (`pytest tests/ -m "slow or extra_slow"
  --resource-budget large --tb=short -q`, currently one sequential in-process run with no
  isolation/parallelism flag), the CI surface remedy (b) would change.
- `tests/simulation_quality/fixtures/grade_anchors.json` — read-only reference for this
  investigation; not to be modified except as an explicit, called-out consequence of the
  adopted remedy.

## Assumptions / Open Questions
- Whether `pytest-xdist` or an equivalent parallelism/isolation tool is already available or
  acceptable in this repo's CI/test environment is unconfirmed — it is not currently listed as
  a dependency (checked `requirements.txt`, `pyproject.toml` at filing time). Investigation must
  establish this before proposing remedy (b) concretely.
- Whether an evidence-derived-width mechanism for `_within_score_tolerance()` can be scoped as
  a per-pillar/per-anchor override (touching only the 3 named pillars) rather than a global
  formula change is assumed but unverified — if it turns out to require a global formula change,
  that would directly interact with `test_within_band_default_tolerance_unchanged`'s existing
  guard and needs its own explicit resolution, not a silent widening.
- Whether the 2 pre-existing precedent guards genuinely share the new 14's flake exposure, or
  are meaningfully more robust for reasons not yet identified (e.g. narrower trial variance,
  different pillar characteristics), is open — the parent ticket observed zero failures for
  either across 2 full sequential runs, which is suggestive but not proof of either guard's own
  reliability.
- The ~1-in-16 observed rate is based on exactly 2 full-sequential-session samples (2 failures
  across 2 runs of 32 tests) — a small sample. This ticket's own investigation may need
  additional sequential-session runs (or the isolation/parallelism comparison from remedy (b))
  to firm up this estimate before concluding on a remedy.
- `layer: simulation` was inferred from the parent tickets' identical layer value and this
  ticket's SimQ-calibration-and-test-infrastructure scope; not flagged as uncertain.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
