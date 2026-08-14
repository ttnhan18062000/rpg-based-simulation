---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE
phase: done
date: 2026-07-16
tags: [simulation-quality, calibration, determinism, corpus]
---

# TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE

## Title
Investigate and remedy the disclosed, unresolved `urban_political_seed123_1000t`/NARRATIVE
score-tolerance exposure found (but explicitly not fixed, per scope guard) during
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`

## Status
DONE

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

Followed `staging_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE/plan.md`'s
7 steps (as amended after the first architecture-review round) in order, no deviations from
the plan's substance.

1. **Conclusion (F6-class, confirmed).** Investigation.md's 6-draw evidence base (3 from the
   parent ticket + 3 fresh this session, deviations 0.031-0.246 from anchor 0.6603206412825652)
   is fully consistent with `INFRA-273`'s already-confirmed "cascading divergence" mechanism:
   NARRATIVE is explicitly named among the delta-gated pillars, `hero_death_unrecorded`'s
   construction in `src/observability/event_extractor.py` is architecturally identical to the
   other named events' this-tick-vs-prior-tick pattern, and `NarrativeScorer.score()` is a
   deterministic pure accumulator with no scorer-side defect found. No distinct root cause.
2. Regenerated fresh calibration data at the default path
   (`data/calibration/urban_political_seed123_1000t/quality_report.json`) via
   `.venv/bin/python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`.
   Result: NARRATIVE `normalized_score=0.5711422845691383`, delta from anchor `0.0892`, well
   inside the recommended `0.3197` floor (sanity check passed).
3. Added the 3rd `SCORE_TOLERANCE_OVERRIDES` entry to
   `tests/simulation_quality/test_grade_regression.py`:
   `("urban_political_seed123_1000t", "NARRATIVE"): 0.3197`, derived via
   `round(1.3 * 0.2459, 4) = 0.3197` (max observed deviation across 6 draws, anchor not
   re-centered — matches the ECONOMY precedent). Updated the module comment block to document
   this entry's derivation (no corresponding `grade_stability` guard existed to reuse a floor
   from, unlike the 2 existing entries). The 2 existing entries and the SOCIAL-exclusion
   sentence were left byte-identical.
4. Updated `test_score_tolerance_override_table_scoped_to_named_pillars`'s hard-coded
   expected-set assertion from the 2-tuple set to the 3-tuple set (added
   `("urban_political_seed123_1000t", "NARRATIVE")`).
5. Ran the fast-tier/structural regression surface (Step 4 of plan.md): all 5 named
   anti-drift/structural tests passed except `test_grade_anchor_file_exists_and_valid`, which
   fails with `TypeError: 'NoneType' object is not subscriptable` due to missing
   `hero_guild_routing_seed42_1000t` calibration data (a different anchor entirely — not
   regenerated in this ticket's scope). Confirmed via `git stash` that this failure reproduces
   identically against the pre-ticket, unmodified code — pre-existing local-calibration-data
   gap, not caused by this ticket's diff. The 56-case fast-anchor sweep
   (`-k "test_grade_within_anchor_band and not long_run"`) all skipped cleanly (no local
   fast-tier calibration data present), which is structurally expected per the plan.
6. Exercised `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` under
   `-m slow --resource-budget large` against the real Step-2 calibration data: `1 passed`
   (not skipped). Also ran the 2 named `grade_stability` guards
   (`test_urban_political_seed123_1000t_social_economy_grade_stability`,
   `test_frontier_marches_seed42_200t_narrative_grade_stability`) under the same flags:
   `2 passed in 179.97s`, confirming both remain structurally untouched.
7. Appended a `RESOLVED 2026-07-16 (TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE)`
   paragraph to `docs/parity_ledger/infrastructure.yaml::INFRA-272`, plus a new
   `HONEST DISCLOSURE, NOT RESOLVED (SOCIAL)` paragraph disclosing the SOCIAL finding and
   citing the concrete follow-up ticket `TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`
   by name (per the plan's amendment). Both paragraphs are append-only; existing text
   unmodified. YAML parses cleanly after the edit.
8. Appended "Anchor Reliability Verification, Part 4" to
   `docs/simulation_quality/eval_matrix_results.md`, documenting the NARRATIVE resolution and
   the SOCIAL disclosure, citing the same follow-up ticket.

**SOCIAL finding disposition:** per the plan's "SOCIAL Finding Decision" section, the SOCIAL
finding (1 of 3 fresh draws exceeding the existing default tolerance, delta 3.8485 vs. width
3.5931) is disclosed in `INFRA-272` and `eval_matrix_results.md` Part 4 but **not** folded
into this ticket's diff — `urban_political_seed123_1000t`/SOCIAL received no override, no
guard edit, no anchor change in this ticket. A concrete stub follow-up ticket,
`TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP`, was filed prior to this
implementation (during the plan's amendment round) and is out of this ticket's scope to
implement.

No new `grade_stability` guard was added for NARRATIVE — 6 real draws already ground the
floor, and the `frontier_marches` guard's own precedent shows a guard is not immune to the
same session-load drift, per investigation.md's recommendation.

`git diff --stat -- src/engine/kernel.py` is empty (verified before and after implementation).
`git diff --stat -- tests/unit/worldassembly/test_corpus_diversity.py
tests/simulation_quality/fixtures/grade_anchors.json Makefile .github/workflows/test.yml` is
also empty — the 14 `grade_stability` guards, `grade_anchors.json`, and the CI isolation lane
were not touched.

Ephemeral `data/calibration/urban_political_seed123_1000t/` data was regenerated locally for
this ticket's verification and removed afterward per Definition of Done (it is gitignored
scratch space, not committed).

## Test Summary

- `pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars -v` — PASSED
- `pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors -v` — PASSED
- `pytest tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged -v` — PASSED
- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged -v` — PASSED
- `pytest tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid -v` — FAILED, pre-existing, unrelated to this ticket's diff (confirmed via `git stash` reproduction against unmodified code): `hero_guild_routing_seed42_1000t` calibration data absent locally, not regenerated in this ticket's scope.
- `pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v` — PASSED
- `pytest tests/simulation_quality/test_grade_regression.py -k "test_grade_within_anchor_band and not long_run" -v` — 56 SKIPPED (no local fast-tier calibration data; structurally expected), 27 deselected
- `pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v` — 1 PASSED (against real, freshly-regenerated calibration data, non-skip)
- `pytest "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" "tests/unit/worldassembly/test_corpus_diversity.py::test_frontier_marches_seed42_200t_narrative_grade_stability" -m slow --resource-budget large -v` — 2 PASSED in 179.97s

`.venv/bin/python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` — succeeds (YAML parses after Step 6's append).

## Files Changed

- `tests/simulation_quality/test_grade_regression.py` — added the 3rd `SCORE_TOLERANCE_OVERRIDES` entry (`("urban_political_seed123_1000t", "NARRATIVE"): 0.3197`) and its derivation comment; updated `test_score_tolerance_override_table_scoped_to_named_pillars`'s expected-set assertion to the 3-tuple set.
- `docs/parity_ledger/infrastructure.yaml` — appended a `RESOLVED` pointer and a `HONEST DISCLOSURE, NOT RESOLVED (SOCIAL)` paragraph to `INFRA-272` (append-only).
- `docs/simulation_quality/eval_matrix_results.md` — appended "Anchor Reliability Verification, Part 4" section.

No source (`src/`) files were changed. `data/calibration/urban_political_seed123_1000t/` was regenerated locally for verification and removed afterward (gitignored, not committed).

## Completion Summary

Confirmed via 6 total independent fresh calibration draws (3 from the parent ticket, 3 this
session) that `urban_political_seed123_1000t`/NARRATIVE's score-tolerance exposure is
F6-class cascading divergence, consistent with `INFRA-273`, not a distinct bug. Added a 3rd
`SCORE_TOLERANCE_OVERRIDES` entry (`abs_floor=0.3197`, derived via the same
`1.3x max-observed-deviation` formula as the 2 existing entries, anchor not re-centered) and
updated the anti-drift guard's expected-entry-set assertion accordingly.
`test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` now passes (`1
passed`) against fresh, real, non-skip calibration data, and the 2 named `grade_stability`
guards remain unmodified and green. Appended `RESOLVED` and SOCIAL-disclosure text to
`INFRA-272` and a new Part 4 to `eval_matrix_results.md`, both citing the concrete follow-up
stub ticket `TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP` for the incidentally
discovered SOCIAL finding rather than a vague prose recommendation. `src/engine/kernel.py`,
the 14 `grade_stability` guards, `grade_anchors.json`, the 2 pre-existing
`SCORE_TOLERANCE_OVERRIDES` entries, and the CI isolation lane were all confirmed untouched.
