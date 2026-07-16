---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE
phase: open
date: 2026-07-16
tags: [simulation-quality, calibration, determinism, corpus]
---

# TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE

## Title
Investigate and remedy the disclosed, unresolved `urban_political_seed123_1000t`/NARRATIVE
score-tolerance exposure found (but explicitly not fixed, per scope guard) during
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` (closing this session) added
`SCORE_TOLERANCE_OVERRIDES` to `tests/simulation_quality/test_grade_regression.py` for
exactly 2 evidence-derived (run_key, pillar) pairs: `urban_political_seed123_1000t`/ECONOMY
and `frontier_marches_seed42_200t`/NARRATIVE. While regenerating fresh local calibration
data for `urban_political_seed123_1000t` to prove the ECONOMY override (3 independent fresh
draws via `tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`), all 3
draws also showed a 4th, previously-unnamed pillar on that same anchor — NARRATIVE — landing
well outside the fixed-width default tolerance:

- Anchor score: `0.6603`
- Fresh draws: `0.5210`, `0.4340`, `0.4144`
- Deltas: `0.139`–`0.246` (band check unaffected; grade stays B on every draw)

This is disclosed verbatim in that ticket's Implementation Notes ("New out-of-scope
finding (disclosed, not fixed)"), `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-
SESSION-LOAD-FLAKE/plan.md`'s Deviations §1, and
`docs/parity_ledger/infrastructure.yaml::INFRA-272`'s "HONEST DISCLOSURE, NOT RESOLVED"
block. That ticket's own Out of Scope explicitly forbade adding coverage for any
(run_key, pillar) pair beyond the 2 named ones, so no 3rd `SCORE_TOLERANCE_OVERRIDES` entry
was added and `grade_anchors.json` was not touched — this was a scope-guard compliance
decision, not an oversight. Consequence: on a fresh checkout with regenerated calibration
data, `pytest "tests/simulation_quality/test_grade_regression.py::
test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow
--resource-budget large -v` deterministically FAILS on NARRATIVE (ECONOMY and SOCIAL both
pass against the same calibration data). This ticket files the authorized follow-up.

## Scope
- Confirm, with fresh evidence, that the `urban_political_seed123_1000t`/NARRATIVE
  single-draw variance is genuinely F6-class load/timing-sensitivity
  (`docs/audits/D06_longrun_health.md` §F6 — "Wall-Clock-Dependent Non-Determinism at Long
  Tick Counts (Tick-Budget Throttle)") and not a distinct bug, using the same
  evidence-gathering approach the two prior tickets in this chain used: multiple
  independent fresh calibration draws (`tools/calibrate_simq.py --name urban_political
  --seed 123 --ticks 1000`), cross-referenced against §F6's characterization and against
  `INFRA-273`'s "cascading divergence" mechanism for delta-gated non-COGNITION pillars
  (NARRATIVE is one of the pillars INFRA-273 names as confirmed load-sensitive via
  `event_extractor.py`'s delta-gated event firing).
- If confirmed F6-class: add a 3rd entry to `SCORE_TOLERANCE_OVERRIDES`
  (`tests/simulation_quality/test_grade_regression.py`) for
  `("urban_political_seed123_1000t", "NARRATIVE")`, deriving its `abs_floor` from real,
  freshly-gathered evidence in this ticket's own investigation (do not reuse or guess a
  value without deriving it the same way the existing 2 entries were derived — e.g. from a
  corresponding `grade_stability`-style guard's own evidence-derived floor, or from direct
  analysis of the fresh draws' observed range with an appropriate safety margin, documented
  either way).
- If investigation finds the NARRATIVE exposure does NOT fit the existing
  `SCORE_TOLERANCE_OVERRIDES` pattern (e.g. genuinely distinct root cause, or variance
  magnitude/behavior meaningfully unlike the 2 existing entries), determine and document an
  alternative fix — do not force-fit a mismatched remedy just to reuse the mechanism.
- Verify the fix (whichever form it takes) makes
  `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` pass reliably
  against fresh, real (non-skip) calibration data — not just structurally present, actually
  exercised, per the pattern the parent ticket used for the ECONOMY override (3/3 clean
  draws).
- Update `docs/parity_ledger/infrastructure.yaml::INFRA-272`'s "HONEST DISCLOSURE, NOT
  RESOLVED" block with a `RESOLVED` pointer (append, do not remove the existing text) and
  `docs/simulation_quality/eval_matrix_results.md`'s "Anchor Reliability Verification, Part
  3" subsection (append a note or new Part 4, per that doc's existing append convention) to
  reflect the resolution.
- If a new anti-drift guard test is warranted (mirroring
  `test_score_tolerance_override_table_scoped_to_named_pillars` /
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`), update those tests'
  expected-entry-set assertions to include the 3rd pair, and confirm they still pass for
  every other (run_key, pillar) not in the table.

## Out of Scope
- Re-opening the 2 already-added `SCORE_TOLERANCE_OVERRIDES` entries
  (`urban_political_seed123_1000t`/ECONOMY, `frontier_marches_seed42_200t`/NARRATIVE) or
  their `abs_floor` values — those are done and correct as-is; this ticket adds a 3rd entry
  alongside them, it does not re-litigate their content.
- Re-opening `urban_political_seed123_1000t`/SOCIAL — `TCK-20260715-SIMQ-CORPUS-DIVERSITY-
  SESSION-LOAD-FLAKE`'s investigation already confirmed by direct arithmetic that its
  existing 20%-relative default (3.5931) exceeds the guard's own evidence-derived floor
  (2.9568), so no override is needed there; do not re-derive or second-guess that finding
  without new evidence specifically implicating it.
- Re-opening the CI isolation lane (`Makefile`'s `simq-corpus-diversity-slow-isolated`
  target, `.github/workflows/test.yml`'s `slow` job wiring) — a separate, already-closed
  concern from the same parent ticket; nothing in this ticket's scope touches CI wiring.
- Any change to `src/engine/kernel.py`'s tick-budget watchdog / mid-tick emergency throttle
  mechanism — same hard constraint as all 3 prior tickets in this chain (`TCK-20260714-
  SIMQ-WEIGHTS-PILLAR-COLLISION`, `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`,
  `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`). F6 is documented, intentional
  engine behavior (`docs/audits/D06_longrun_health.md`, `docs/engine/kernel.md`,
  `docs/engine/performance_contract.md` §7). Only test-side score-tolerance remedies are in
  scope.
- Widening `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (the global default
  constants) — any fix must remain scoped to a per-`(run_key, pillar)` override, consistent
  with the existing table's design.
- Adding a `grade_stability`-style multi-trial guard to `tests/unit/worldassembly/
  test_corpus_diversity.py` for this pillar, or re-anchoring `grade_anchors.json` — unless
  this ticket's own investigation evidence specifically requires it and that requirement is
  called out explicitly (mirrors the scope-guard discipline of all 3 prior tickets).
- Sweeping any other anchor/pillar not named in this ticket for similar undisclosed
  exposures — a broader corpus-wide sweep is out of scope; this ticket is narrowly targeted
  at the one disclosed, named finding.

## Acceptance Criteria
- [ ] At least 2 additional independent fresh `urban_political_seed123_1000t` calibration
      draws (beyond the 3 already recorded in the parent ticket) are collected and their
      NARRATIVE scores recorded, to strengthen the evidence base before committing a fix.
- [ ] Investigation concludes, with cited evidence, whether the NARRATIVE exposure is
      F6-class (consistent with §F6 and `INFRA-273`'s cascading-divergence mechanism) or a
      distinct root cause, and the conclusion is recorded in this ticket's Implementation
      Notes.
- [ ] If F6-class: a 3rd `SCORE_TOLERANCE_OVERRIDES` entry for
      `("urban_political_seed123_1000t", "NARRATIVE")` is added with a documented,
      evidence-derived `abs_floor`, and
      `pytest "tests/simulation_quality/test_grade_regression.py::
      test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow
      --resource-budget large -v` passes against fresh, real (non-skip) calibration data.
- [ ] If not F6-class or not a fit for the override pattern: an alternative fix is designed,
      implemented, and verified, with its rationale documented.
- [ ] Existing anti-drift guard tests (`test_score_tolerance_override_table_scoped_to_named_pillars`,
      `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`, or their updated
      equivalents) pass and correctly reflect the 3-entry table.
- [ ] `test_within_band_default_tolerance_unchanged` and
      `test_grade_anchors_entry_count_unchanged` still pass unmodified in behavior (no
      regression to unaffected anchors/pillars).
- [ ] `docs/parity_ledger/infrastructure.yaml::INFRA-272` is updated with a `RESOLVED`
      pointer for this finding (existing text preserved, per append-only convention) and
      `docs/simulation_quality/eval_matrix_results.md` is updated to reflect the resolution.
- [ ] `git diff --stat` confirms no change to `src/engine/kernel.py`, the 14
      `grade_stability` guards or 2 precedent guards in `test_corpus_diversity.py`, the 2
      existing `SCORE_TOLERANCE_OVERRIDES` entries' values, or
      `urban_political_seed123_1000t`/SOCIAL, unless explicitly justified by new evidence
      and called out in Implementation Notes.

## Related Tickets
- `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` (closing this session) — direct
  parent; its Implementation Notes ("New out-of-scope finding (disclosed, not fixed)") and
  `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/plan.md`'s
  Deviations §1 are the exact source of this ticket's finding and the 3 fresh-draw values
  cited above.
- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (done) — established the 14-anchor
  F6 confirmation, the `repro_sweep.md` evidence-gathering methodology this ticket reuses,
  and the original 2-pillar `SCORE_TOLERANCE_OVERRIDES` precedent this ticket extends.
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (done) — root of this ticket's lineage;
  surfaced the original 14-anchor carve-out (`INFRA-272`) that both prior tickets and this
  one trace back to.

## Related Docs
- `docs/audits/D06_longrun_health.md` §F6 — the documented load-sensitive divergence
  finding this ticket's investigation must cross-reference and stay consistent with (the
  "reliably reproducible below ~tick 300-320" hedge).
- `docs/engine/kernel.md`, `docs/engine/performance_contract.md` §7 — watchdog/throttle
  mechanism F6 attributes the variance to (read-only reference; not to be modified).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-272` (the "HONEST DISCLOSURE, NOT
  RESOLVED" block naming this exact finding: anchor 0.6603, draws 0.5210/0.4340/0.4144,
  deltas 0.139-0.246) and `INFRA-273` (the cascading-divergence mechanism confirming
  NARRATIVE as one of the load-sensitive delta-gated pillars); this ticket updates or
  extends INFRA-272 as its own findings land.
- `docs/simulation_quality/eval_matrix_results.md` — "Anchor Reliability Verification, Part
  3" subsection (the parent ticket's summary of the 2-entry override table and this
  finding's disclosure); this ticket's resolution should be appended here.

## Related Stored Artifacts
- `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` (still in
  `staging_artifacts/`, not yet moved to `stored_artifacts/` at time of filing since its
  parent ticket is still open) — `plan.md`'s Deviations §1 is the direct source of this
  ticket's finding; expect this to move to
  `stored_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` once that
  ticket closes — check both locations.
- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` — the
  evidence-gathering methodology template (multiple fresh draws, per-anchor variance
  tables) this ticket's own investigation should follow.
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` —
  the original repro methodology precedent both parent tickets and this investigation
  build on.

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py` — `SCORE_TOLERANCE_OVERRIDES` (lines
  ~65-68), `_score_tolerance_kwargs()`, `_within_score_tolerance()`,
  `test_grade_within_anchor_band_long_run` (the failing parametrized case), and the 2
  anti-drift guard tests (`test_score_tolerance_override_table_scoped_to_named_pillars`,
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`, ~line 610) whose
  expected-entry-set assertions must be updated if a 3rd entry is added.
- `tools/calibrate_simq.py` — used to regenerate fresh `urban_political_seed123_1000t`
  calibration data for this investigation's evidence gathering
  (`--name urban_political --seed 123 --ticks 1000`).
- `tests/simulation_quality/fixtures/grade_anchors.json` — read-only reference for this
  investigation; not to be modified except as an explicit, called-out consequence of the
  adopted remedy.
- `src/engine/event_extractor.py` — the delta-gated event-firing mechanism `INFRA-273`
  attributes NARRATIVE's (and other non-COGNITION pillars') cascading-divergence
  sensitivity to; read-only reference for confirming the F6-class classification, not a
  file this ticket's scope permits modifying.

## Assumptions / Open Questions
- Whether the eventual `abs_floor` for `("urban_political_seed123_1000t", "NARRATIVE")`
  should be derived directly from fresh draw evidence (this ticket's own analysis), or
  whether a `grade_stability`-style guard should be added first to derive the floor the
  same way the 2 existing override entries were derived, is open — this ticket's Scope
  authorizes either path, whichever the investigation evidence supports; not pre-decided
  here. Investigation must confirm before committing a specific value, per the request's
  explicit instruction not to guess one. If the guard-first path is taken, the "adding a
  `grade_stability`-style guard" line in Out of Scope must be revisited with explicit
  justification recorded in Implementation Notes, not silently crossed.
- Whether the NARRATIVE exposure is genuinely the same F6 mechanism as the 2 existing
  override entries, or a distinct-but-superficially-similar issue, is assumed likely
  (per `INFRA-273`'s existing confirmation that NARRATIVE is one of the delta-gated
  pillars with confirmed load/timing sensitivity) but not yet verified with this ticket's
  own fresh evidence — if wrong, the remedy shape (override-table entry) would not apply
  and the ticket's Scope's "alternative fix" branch would govern instead.
- `layer: simulation` was inferred from the 3 lineage tickets' identical layer value and
  this ticket's SimQ-calibration-and-test-infrastructure scope; not flagged as uncertain.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
