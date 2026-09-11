---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE
phase: done
date: 2026-08-08
tags: [simulation-quality, calibration]
---

# TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE

## Title
Add a `structural_ceiling` provenance layer alongside `grade_anchors.json` so a low/drifted pillar
score can be classified as a real regression, a scoring-method bug, or a legitimate scenario-level
ceiling — without re-doing manual archaeology every time

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A 2026-08-07/08 user discussion on SimQ status identified a recurring problem: when a pillar score
is low or drifts, there are three structurally different explanations that currently collapse into
the same number — (1) a genuine simulation/engine regression, (2) a bug in the scoring/extraction
logic itself, (3) a legitimate ceiling the scenario can never exceed by design (a feature flag is
off, the world lacks the content a pillar needs, or the tick budget is too short for a
threshold-based penalty to avoid firing). This session hit all three concretely: COMBAT was
simultaneously (2) — `event_extractor.py` double-classified hazard-drain damage as combat, fixed by
`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` — and (3) —
`ENABLE_COMBAT_ENGAGEMENT` is deliberately off corpus-wide
(`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`, DEV-002 ruling), so PP-16 never runs
anywhere and 26 COMBAT anchors are permanently capped near their `combat_dormant` floor
(`TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE`). NARRATIVE hit (2) separately
(`TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG`). Untangling each required re-deriving the causal chain
by hand from `git log`/ticket history — the same archaeology, repeated per finding, with no
structured place to record the answer once found.

This is deliberately **not** a new SimQ pillar — it fails the repo's own new-pillar-vs-new-rule
test (`docs/simulation_quality/quality_scoring_contract.md` §7.1 vs §7.2, already applied twice at
§7.5/§7.6 to reject "add a lifecycle pillar" in favor of extending existing pillars). A ceiling
classification answers "can I trust/interpret this number," not "is the simulation good at X" — a
different kind of question from what a pillar answers.

## Scope
1. **Investigate**:
   - Confirm `QualityHub.SCORER_REGISTRY`'s exact structure (`src/simulation_quality/quality_hub.py:125-129`,
     built per-instance from each scorer's own `EVENT_TYPES` class attribute) as the data source
     for a static "which event_types can this pillar ever score" map.
   - Confirm which of those event_types are only ever emitted by a feature-flag-gated phase (cross
     reference `src/domains/optimization/feature_flags.py`'s flag list against each phase's own
     gating check) — this is the `flag_gated` ceiling kind's exact computation.
   - Confirm `config/simulation_quality/detection_params.yaml`'s threshold constants (e.g.
     `zero_combat_by_tick: 200`) and which scorer rules key off them — the `tick_budget` ceiling
     kind's exact computation (a pure scenario-tick-count vs. threshold comparison).
   - Design the `content_threshold` ceiling kind's schema even though it can't be as cleanly
     automated (it's a documented judgment call, same class as the existing "no merchant NPCs"
     prose in `eval_matrix_results.md`'s "Zero-Pillar World Confirmation" sections) — decide what
     `world_compile_report.json` fields (entity count, distinct populated factions, resource nodes)
     back each judgment call, so the call is at least auditable even if not provably exact.
2. **Plan**: schema for the provenance file (likely a sibling to `grade_anchors.json`, e.g.
   `tests/simulation_quality/fixtures/score_ceilings.json`, keyed by `(run_key, pillar)` or just
   `pillar` for corpus-wide flag-gated cases) — fields: `ceiling_kind`
   (`flag_gated`/`tick_budget`/`content_threshold`), `reason` (free text + citation), `evidence`
   (flag name / threshold value / world-content field, as applicable), `since_ticket` (the ticket
   that established or last re-verified this ceiling).
3. **Implement**:
   - A static computation for `flag_gated` and `tick_budget` kinds (deterministic, no engine run
     needed) — likely a small module (`tools/simq_ceiling.py` or similar) callable from both a
     CLI report and `test_grade_regression.py`.
   - Backfill at least the 3 cases this session already diagnosed with real evidence: COMBAT
     (`flag_gated`, `ENABLE_COMBAT_ENGAGEMENT`, all 26 affected run_keys), and the 2 already-fixed
     `content_threshold`-adjacent NARRATIVE/PROGRESSION cases as `since_ticket`-only historical
     entries (not live ceilings — already-corrected drift, a 4th provenance state worth
     distinguishing: `corrected` vs. an ongoing `ceiling`).
   - Wire `test_grade_regression.py`'s score-tolerance failure message to look up and print the
     ceiling classification when one exists for the failing pair, so a future drift immediately
     shows "this pillar has a known flag_gated ceiling since TCK-X" instead of a bare number
     mismatch.
4. Do NOT attempt a fully automated `content_threshold` classifier in this ticket — per Scope
   item 1, that kind stays judgment-call-based; automating it is future work only if the manual
   backlog of cases becomes large enough to justify it.

## Out of Scope
- Any change to the 10-pillar architecture itself, `PillarId` enum, or `QualityHub` — this is a
  read-only diagnostic layer over the existing scoring system, never a scoring input.
- Automating `content_threshold` classification (see Scope item 4).
- Re-litigating the "no new pillar" ruling (§7.5/§7.6) — this ticket implements the alternative
  those rulings already chose, doesn't reopen the question.
- Large-scale world validation of whether these ceiling classifications hold at production-like
  entity counts — tracked separately, `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`.

## Acceptance Criteria
- [ ] investigation.md confirms the exact `flag_gated`/`tick_budget` computation sources and
      designs the `content_threshold` schema
- [ ] Provenance file schema implemented, with `ceiling_kind` distinguishing deterministic
      (`flag_gated`/`tick_budget`) from judgment-call (`content_threshold`) entries, plus a
      `corrected` state for already-fixed historical drift
- [ ] At least the 3 real cases from this session backfilled with real evidence/citations
- [ ] `test_grade_regression.py`'s failure output surfaces the ceiling classification when one
      exists for the failing (run_key, pillar)
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY, TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX,
  TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE (the COMBAT `flag_gated` case this ticket
  formalizes — all DONE)
- TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG (the NARRATIVE `corrected` case — DONE)
- TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC (established the §7.1-vs-§7.2 new-pillar test
  this ticket's own framing relies on — DONE)
- TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION (tests whether this ticket's ceiling
  classifications hold at scale — filed alongside this one)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §7.1/§7.2/§7.6 (the new-pillar-vs-new-rule
  test and the layer-lifecycle precedent this design follows)
- `docs/simulation_quality/eval_matrix_results.md` "Zero-Pillar World Confirmation" sections (the
  existing, prose-only precedent for `content_threshold`-style reasoning)
- `docs/simulation_quality/current_state.md`, `eval_matrix_results.md` (to update with a pointer to
  the new provenance file once it exists)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE/` (the fullest recent
  worked example of manual ceiling archaeology this ticket aims to make structured)

## Related Code Areas
- `src/simulation_quality/quality_hub.py` (`SCORER_REGISTRY`, read-only reference)
- `src/domains/optimization/feature_flags.py` (flag list)
- `config/simulation_quality/detection_params.yaml` (threshold constants)
- `tests/simulation_quality/fixtures/grade_anchors.json` (sibling file location)
- `tests/simulation_quality/test_grade_regression.py` (`_within_score_tolerance`,
  `SCORE_TOLERANCE_OVERRIDES`, failure-message integration point)

## Assumptions / Open Questions
- Exact provenance-file granularity — per `(run_key, pillar)` vs. per `pillar` for corpus-wide
  flag-gated cases (e.g. COMBAT's ceiling applies identically to all 26 affected run_keys, not a
  per-scenario fact) — not assumed; Investigate/Plan should settle this before implementing to
  avoid 26 duplicate entries for one shared cause.

## Implementation Notes
Subagent spawn cap (200/200) reached earlier this session — Investigate/Implement/Verify performed
directly.

Found `detection_params.yaml`'s `time_gates` block has 22 real threshold constants spanning nearly
every pillar, not just COMBAT's own `zero_combat_by_tick` — confirmed the exact pillar mapping for
19 of the 22 via direct grep of each scorer's own `self.weights.int_param(...)` call sites; the
remaining 3 (`war_without_conflict_window`, `zero_spawn_cadence_check`, `scenario_stall_default`)
were deliberately left unmapped rather than guessed at, since their consuming logic wasn't
confirmed to live directly in a scorer during this pass (plausibly consumed upstream in
`event_extractor.py`). `tick_budget` ceilings are therefore fully computed, deterministic, reusing
ticket 1's own `corpus_registry.yaml` for each run_key's tick count — no new engine runs needed.

`flag_gated` scoped to a small, explicit, hand-verified `FLAG_GATED_PILLAR_CEILINGS` table (one
real entry: COMBAT/`ENABLE_COMBAT_ENGAGEMENT`) rather than an automated engine-wide analyzer —
per the ticket's own Scope, tracing which event_types are exclusively producible by a gated phase
is real per-pillar work, not mechanical; the table is designed to grow incrementally as future
investigations confirm more cases.

Refactored `test_grade_regression.py`'s 4 near-duplicate score-tolerance failure-message
constructions (2 list-comprehension sites in the isolated-anchor tests, 2 for-loop sites in the
fast/slow parametrized tests) into one shared `_format_score_failures()` helper that calls
`lookup_ceiling()` — a real code-quality improvement found while wiring the ceiling lookup in,
not scope creep (all 4 sites needed the same change).

## Test Summary
`tests/tools/test_score_ceilings.py` (new): 6 passed — tick_budget computation, flag_gated lookup,
unclassified-pair None-return (no false positives), corrected-state lookup, and a direct
integration test confirming `_format_score_failures()` embeds the known-ceiling text in a real
failure line. `tests/simulation_quality/test_grade_regression.py -m "not slow"`: 68 passed, 1
failed (the pre-existing, already-disclosed `hero_guild_routing_seed42_500t`/COGNITION finding
from the predecessor ticket — correctly still unclassified, no false "known ceiling" annotation
appears on it, confirming the lookup doesn't produce false positives).

## Files Changed
- `tools/simq_ceiling.py` (new)
- `tests/simulation_quality/fixtures/score_ceilings.json` (new)
- `tests/tools/test_score_ceilings.py` (new)
- `tests/simulation_quality/test_grade_regression.py` (`_format_score_failures` helper, 4 call
  sites refactored to use it)
- `docs/simulation_quality/current_state.md` (score-provenance pointer)

## Completion Summary
Built the deterministic parts (`tick_budget`, 19/22 real thresholds mapped) fully automated and
tested; scoped the harder, real-tracing-required `flag_gated` kind to one hand-verified, real,
already-disclosed case rather than guessing at a full corpus-wide analysis. Wired the
classification into the actual regression gate's own failure output, not just a standalone tool
nobody would remember to run. Second of 5 tickets in this batch.
