---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
phase: open
date: 2026-07-16
tags: [simulation-quality, calibration, determinism, corpus]
---

# TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP

## Title
Full-pillar `SCORE_TOLERANCE_OVERRIDES` sweep for `urban_political_seed123_1000t`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
This is a proactive, disclosed-gap stub ticket filed for traceability during the Plan/Review
phase of `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` (not yet implemented at the
time this stub was filed). That ticket's `plan.md` ("SOCIAL Finding Decision" section)
disclosed a new out-of-scope finding: during its own investigation (gathering fresh
calibration draws to derive a NARRATIVE tolerance override for `urban_political_seed123_1000t`),
1 of 3 fresh draws showed the SOCIAL pillar (delta `3.8485`) exceeding its own existing
default score tolerance (`3.5931`) for this same anchor — new evidence directly contradicting
the immediate parent ticket's (`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`)
conclusion that SOCIAL needed no override. This is the 2nd consecutive ticket in this chain to
organically surface exactly one new at-risk pillar on this exact anchor while investigating a
different, previously-named pillar (1st: NARRATIVE, surfaced while `CORPUS-DIVERSITY-SESSION-
LOAD-FLAKE` investigated ECONOMY/SOCIAL; 2nd: SOCIAL again, surfaced while `URBAN-POLITICAL-
NARRATIVE-TOLERANCE` investigated NARRATIVE). `INFRA-273` confirms the underlying mechanism
(delta-gated "cascading divergence" via `event_extractor.py`, itself downstream of `kernel.py`'s
wall-clock tick-budget watchdog/throttle — F6, `docs/audits/D06_longrun_health.md`) spans
SOCIAL/COMBAT/PROGRESSION/NARRATIVE/WORLD collectively for this class of anchor, not just the
2 pillars discovered incidentally so far. Of this anchor's 10 tracked pillars (`grade_anchors.
json`: COGNITION, AGENCY, COMBAT, FACTION, ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD,
NARRATIVE), COMBAT, PROGRESSION, and WORLD — all named by `INFRA-273` as sharing the identical
confirmed mechanism — have never been swept for this anchor at all.

Per `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`'s plan.md explicit recommendation,
this ticket breaks the repeating one-pillar-per-ticket pattern by scoping a single full-pillar
sweep of `urban_political_seed123_1000t` instead of spinning out a 5th single-pillar ticket.

## Scope
- Gather 5+ independent fresh calibration draws of `urban_political_seed123_1000t`
  (`python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`, each to a
  distinct non-colliding `--output` path), given how much variance single/triple draws have
  already shown across the prior 2 tickets in this chain.
- Check **every** one of this anchor's 10 tracked pillars' (COGNITION, AGENCY, COMBAT, FACTION,
  ECONOMY, PROGRESSION, SOCIAL, INFORMATION, WORLD, NARRATIVE) score-tolerance exposure against
  `grade_anchors.json` in one investigation pass — not just SOCIAL, and not assuming only the
  `INFRA-273`-named pillars (SOCIAL, COMBAT, PROGRESSION, NARRATIVE, WORLD) are at risk; confirm
  or rule out each pillar via real evidence.
- For whichever pillars the fresh evidence shows genuinely exceed their current tolerance
  (default or already-overridden), apply the established `SCORE_TOLERANCE_OVERRIDES` mechanism
  in `tests/simulation_quality/test_grade_regression.py` using the same `1.3x max-observed-
  deviation` formula already verified against the 3 existing table entries (anchor not
  re-centered, following the ECONOMY precedent, unless the fresh evidence specifically supports
  re-centering for a given pillar — call out and justify explicitly if so).
- Update the anti-drift guard (`test_score_tolerance_override_table_scoped_to_named_pillars`)
  to reflect the final entry set.
- Exercise `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` against real
  regenerated calibration data to prove the fix, not just structural table presence.
- Append resolution/disclosure text to `docs/parity_ledger/infrastructure.yaml` (`INFRA-272`
  append-only, cross-reference `INFRA-273`) and `docs/simulation_quality/eval_matrix_results.md`
  summarizing per-pillar findings (both overridden and confirmed-fine).

## Out of Scope
- The 3 already-added/landing `SCORE_TOLERANCE_OVERRIDES` entries: ECONOMY on
  `urban_political_seed123_1000t`, NARRATIVE on `frontier_marches_seed42_200t`, and NARRATIVE
  on `urban_political_seed123_1000t` (once `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-
  TOLERANCE` lands) — these are done and correct; do not re-derive or second-guess them without
  new evidence specifically implicating them.
- Any anchor besides `urban_political_seed123_1000t` — no corpus-wide sweep.
- The CI isolation lane (`.github/workflows/test.yml`'s `slow` job,
  `simq-corpus-diversity-slow-isolated` Makefile target,
  `tests/static/test_corpus_diversity_ci_isolation.py`) — separate, already-closed concern.
- Changing `src/engine/kernel.py`'s tick-budget watchdog / mid-tick emergency throttle
  mechanism — F6 is documented, intentional engine behavior; same hard constraint as every
  ticket in this chain.
- Widening the module-level `SCORE_TOLERANCE_ABS_FLOOR` / `SCORE_TOLERANCE_REL_PCT` defaults —
  any fix stays scoped to the per-`(run_key, pillar)` override table.
- Adding a new dedicated `grade_stability` guard for any pillar unless this ticket's own
  investigation evidence specifically shows the tolerance-override alone is inadequate (mirrors
  `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`'s own reasoning for NARRATIVE).
- Assuming every pillar needs an override — the request is to confirm via real evidence per
  pillar, not to pre-apply overrides to all 10.

## Acceptance Criteria
- [ ] 5 or more independent fresh calibration draws of `urban_political_seed123_1000t`
      collected via `tools/calibrate_simq.py`; all 10 pillars' scores recorded per draw in a
      table in this ticket's investigation.md.
- [ ] For each of the 10 pillars, the max deviation from its `grade_anchors.json` anchor is
      computed and compared against its current tolerance (default or already-overridden);
      each pillar has an explicit pass/fail determination with cited evidence.
- [ ] Every pillar whose fresh evidence exceeds its current tolerance gets a
      `SCORE_TOLERANCE_OVERRIDES` entry added via the `1.3x max-observed-deviation` formula,
      with derivation shown (mirroring the 3 existing entries' documented derivations).
- [ ] `test_score_tolerance_override_table_scoped_to_named_pillars` is updated to the final
      entry set and passes.
- [ ] `pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v`
      reports `1 passed` (not skipped, not failed) against freshly regenerated real calibration
      data.
- [ ] `docs/parity_ledger/infrastructure.yaml::INFRA-272` has an appended (not edited)
      resolution paragraph naming this ticket, summarizing which pillars got overrides and
      which were confirmed to need none, with evidence pointers; `INFRA-273` is cross-referenced
      (updated only if this sweep's evidence adds to or contradicts its mechanism claim).
- [ ] `docs/simulation_quality/eval_matrix_results.md` has an appended summary section
      (following the existing Part 1-4 style) covering this sweep's per-pillar results.
- [ ] `git diff --stat -- src/engine/kernel.py tests/unit/worldassembly/test_corpus_diversity.py tests/simulation_quality/fixtures/grade_anchors.json`
      shows no unjustified changes: `kernel.py` untouched; the 14 existing `grade_stability`
      guards' logic untouched; any `grade_anchors.json` re-centering is explicitly justified in
      Implementation Notes with cited evidence, not incidental.

## Related Tickets
- `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` — immediate parent; disclosed this
  ticket's founding SOCIAL finding and explicitly recommended this ticket's full-pillar-sweep
  scoping (see its plan.md's "SOCIAL Finding Decision" section). **Not yet done** as of this
  stub's filing — currently in `tickets/inprogress/` / `staging_artifacts/`.
- `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` — grandparent; established the
  `SCORE_TOLERANCE_OVERRIDES` mechanism and derivation formula this ticket reuses; its
  "SOCIAL needs no override" conclusion is the one this chain's fresh evidence has since
  contradicted.
- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` — great-grandparent; established the
  `1.3x max-observed-deviation` derivation methodology and the 14-anchor `grade_stability`
  guard precedent this ticket's methodology follows.
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` — origin of this chain; the pillar-scoped
  weight-lookup fix whose full-corpus validation first surfaced this anchor's load-sensitivity
  as a distinct, separately-tracked investigation thread.

## Related Docs
- `docs/parity_ledger/infrastructure.yaml::INFRA-272` — the disclosure block naming
  `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` and (once that ticket appends its own
  resolution) the SOCIAL disclosure this ticket resolves.
- `docs/parity_ledger/infrastructure.yaml::INFRA-273` — confirms the cascading-divergence
  mechanism scope (SOCIAL/COMBAT/PROGRESSION/NARRATIVE/WORLD) this ticket's sweep is scoped
  against.
- `docs/audits/D06_longrun_health.md` §F6 — "Wall-Clock-Dependent Non-Determinism at Long Tick
  Counts", the documented, intentional root-cause engine behavior underlying this whole chain.
- `docs/engine/kernel.md` §"Emergency Throttling" — canonical hash `"SKIPPED"` in `DEGRADED`
  mode; confirms this class of non-determinism is already contract-known, not newly revealed.
- `docs/simulation_quality/quality_scoring_contract.md` — pillar scoring/accumulator contract.
- `docs/simulation_quality/eval_matrix_results.md` — "Anchor Reliability Verification" Parts
  1-4, the append target for this ticket's Part 5.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` — Section 8,
  the derivation-methodology precedent (`1.3x` max-observed-deviation, optional re-centering)
  this ticket's investigation should reuse verbatim.
- `stored_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` — origin of the
  `SCORE_TOLERANCE_OVERRIDES` mechanism itself.
- `stored_artifacts/TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION/` — chain origin.
- `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` is **not yet done** as of this stub's
  filing — its artifacts currently live in
  `staging_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE/` (`plan.md`,
  `investigation.md`), not yet in `stored_artifacts/`. Check `stored_artifacts/` for it once it
  closes, and re-verify this ticket's baseline assumption (3 existing `SCORE_TOLERANCE_
  OVERRIDES` entries: ECONOMY, `frontier_marches_seed42_200t`/NARRATIVE, `urban_political_
  seed123_1000t`/NARRATIVE) against the actual committed state before this ticket's own
  implementation begins.

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py` — `SCORE_TOLERANCE_OVERRIDES` dict,
  `_score_tolerance_kwargs()`, `_within_score_tolerance()`,
  `test_score_tolerance_override_table_scoped_to_named_pillars`,
  `test_score_tolerance_overrides_do_not_affect_unlisted_anchors`,
  `test_grade_within_anchor_band_long_run`.
- `tests/unit/worldassembly/test_corpus_diversity.py` —
  `test_urban_political_seed123_1000t_social_economy_grade_stability` and the other 13
  `grade_stability` guards (precedent/pattern reference only; not to be edited unless new
  evidence specifically requires it).
- `tests/simulation_quality/fixtures/grade_anchors.json` — this anchor's 10-pillar anchor
  values.
- `src/observability/event_extractor.py` — the delta-gated, this-tick-vs-prior-tick event
  construction mechanism underlying the cascading-divergence variance (read-only reference).
- `src/simulation_quality/scorers/` — per-pillar scorer implementations (read-only reference
  for confirming any newly-implicated pillar's scorer has no independent defect, mirroring how
  `TCK-20260716`'s investigation ruled out a `NarrativeScorer` defect).
- `tools/calibrate_simq.py` — calibration draw generation.
- `src/engine/kernel.py` — read-only reference only (F6 root cause); explicitly out of scope to
  modify.

## Assumptions / Open Questions
- Assumes `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` lands materially as planned
  (3rd `SCORE_TOLERANCE_OVERRIDES` entry: `("urban_political_seed123_1000t", "NARRATIVE"):
  0.3197`, anchor not re-centered) before this ticket's implementation begins. If that ticket's
  actual committed diff differs from its plan.md, this ticket's baseline must be re-verified
  against the real committed state, not this assumption — see Related Stored Artifacts.
- Assumes 5+ fresh draws is sufficient to converge on a stable `1.3x`-floor per pillar. If
  COMBAT/PROGRESSION/WORLD/SOCIAL show wider variance than NARRATIVE's 6-draw spread
  (`0.0313`-`0.2459`), more draws may be warranted — the investigator should flag if 5 draws is
  visibly insufficient (e.g., still trending upward at draw 5) rather than force a conclusion.
- Assumes the `SCORE_TOLERANCE_OVERRIDES` `1.3x`-max-deviation mechanism remains the correct
  remedy shape for whichever pillars need one. If evidence suggests a pillar needs a different
  remedy (e.g., a dedicated `grade_stability` guard, or a genuine scorer/engine defect rather
  than F6-class variance), that is a deviation requiring explicit justification in
  Implementation Notes, not a silent substitution.
- `INFRA-273` names SOCIAL, COMBAT, PROGRESSION, NARRATIVE, and WORLD as sharing the confirmed
  cascading-divergence mechanism; this anchor also tracks COGNITION, AGENCY, FACTION, ECONOMY,
  and INFORMATION. Per the request's "check EVERY pillar" instruction, this ticket's
  investigation should sweep all 10, but if a pillar **outside** `INFRA-273`'s named list shows
  drift, that is new evidence requiring its own mechanism explanation (do not assume it
  automatically matches F6 without checking) — flagged as an open question for the investigator,
  not pre-resolved here.
- If, after gathering evidence, zero additional pillars actually need an override (i.e., the
  SOCIAL finding that triggered this ticket does not reproduce at 5+ draws, and no other pillar
  shows drift), the correct outcome is a documented "swept, no changes needed" resolution in
  `INFRA-272`/`eval_matrix_results.md`, not a forced override — this ticket's scope explicitly
  calls for confirming via real evidence, not assuming every pillar needs one.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

