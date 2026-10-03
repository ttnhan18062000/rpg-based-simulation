---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-SCORE-CEILING-FIX
phase: done
date: 2026-07-13
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260713-SIMQ-SCORE-CEILING-FIX

## Title
Recalibrate the weight/normalization scale for WORLD, ECONOMY, PROGRESSION, INFORMATION — these
4 pillars structurally cannot reach grade A or S under any real-world condition

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Prompted by a direct question about whether SimQ's scoring multipliers need adjustment (not just
corpus coverage). Cross-referencing raw `normalized_score` values (from a full live corpus run,
`tmp/evaluate_simq_full_run_20260713.log`, session-local) against the grade-band thresholds
(`quality_scoring_contract.md` §4.5: `S >2.0`, `A 0.5-2.0`, `B 0.0-0.5`) across all 72 committed
anchor scenarios found that 4 of SimQ's 10 pillars structurally cannot reach A or S under the
current weight scale, regardless of how good the underlying world is:

| Pillar | Max normalized score seen (all 72 scenarios) | A threshold | Gap |
|---|---|---|---|
| WORLD | 0.30 (a 38-event run) | 0.5 | Never halfway there — the pillar's entire observed range (0.0-0.3) fits inside the B band alone |
| ECONOMY | 0.16 (a **69-event** run — genuinely rich activity) | 0.5 | 1/3 of the way even at its richest observed point |
| PROGRESSION | 0.13 (46-event run) | 0.5 | Same shape |
| INFORMATION | 0.04 (1-event run) | 0.5 | ~12x short |

This is a weight/normalization-scale problem, not a corpus-coverage problem: even the single
richest ECONOMY run in the whole corpus (69 scored events) only reached 1/3 of the way to A. The
scorer currently cannot ever register a world as *exceptional* on these 4 dimensions — a real gap
against SimQ's own stated balance/tuning-support goal (`quality_scoring_contract.md` §1), which
needs the top of the scale to be reachable to be useful. By contrast, NARRATIVE and COMBAT (the
other two "always-on", non-gated pillars) show real spread across all 4 grades and are not
exhibiting this pattern — confirming this is specific to these 4 pillars' weight/threshold
calibration, not a property of the normalization formula itself.

## Scope
- Investigate each affected pillar's scorer (`src/simulation_quality/scorers/world_dynamics.py`,
  `economy.py`, `progression.py`, `information.py`) and its weights
  (`config/simulation_quality/scoring_weights.yaml`) to understand exactly why per-event deltas
  are scaled so low relative to the `normalized_score` formula's denominator
  (`quality_scoring_contract.md` §4.4).
- Deliberately construct or identify one genuinely best-case and one genuinely worst-case scenario
  per affected pillar within the existing corpus (or a new minimal test scenario if none exists),
  run them through the current formula, and determine whether raising per-event weights, lowering
  grade thresholds for these 4 pillars specifically, or both, restores real discrimination.
- Re-anchor `grade_anchors.json` for whichever entries actually change under the corrected formula
  — full regression sweep required, since shared weight constants can move grades corpus-wide.

## Out of Scope
- ECONOMY's Gini-threshold mechanism itself, or COMBAT/NARRATIVE's formulas — these are not
  exhibiting the same ceiling pattern; not touched unless investigation finds otherwise.
- Authoring new content into any world — that's `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`, which
  depends on this ticket landing first.
- The `grade_anchors.json` schema extension for raw-score persistence
  (`TCK-20260713-SIMQ-RAWSCORE-PERSIST`) — sequenced to reuse this ticket's re-anchor pass, but is
  its own separate concern (schema/regression-test change, not a weight-formula change).
- Any of `quality_scoring_contract.md` §14's Non-Goals.

## Acceptance Criteria
- [x] For each of the 4 affected pillars, at least one real corpus scenario reaches grade A or S
      under the recalibrated formula.
- [x] Structurally-inert entries (e.g. INFORMATION in worlds with zero information content, or
      ECONOMY in worlds with no harvest/craft/trade activity) remain C — the fix must move the
      ceiling for genuinely active scenarios, not just inflate every score uniformly.
- [x] Full `evaluate_simq.py` (live mode) sweep shows 0 unattributed regressions — every anchor
      change is a deliberate, documented consequence of the weight/threshold change, not a side
      effect.
- [x] `docs/simulation_quality/current_state.md`'s grade-distribution table and discriminative-
      power section are updated to reflect the new, corrected state.

## Related Tickets
- `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` — depends on this ticket landing first.
- `TCK-20260713-SIMQ-RAWSCORE-PERSIST` — sequenced to share this ticket's re-anchor pass.
- `TCK-20260713-SIMQ-EVAL-PROFILE-BUG` (done) — landed first so this ticket's repeated live-mode
  sweeps (while tuning weights) weren't run against a tool with a known silent-corruption bug.
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (filed, open) — follow-up ticket for the
  load-sensitive COGNITION self-model loop-detection nondeterminism discovered as a side finding
  during this ticket's Step 12 live-mode sweep; confirmed unrelated to this ticket's own diff.

## Related Docs
- `docs/simulation_quality/current_state.md` — the discriminative-power finding this ticket
  addresses, with the full evidence table.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 1a, this ticket's source.
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 (normalized score formula), §4.5
  (grade bands), §1 (goals — balance/tuning support).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `config/simulation_quality/scoring_weights.yaml`
- `src/simulation_quality/scorers/world_dynamics.py`
- `src/simulation_quality/scorers/economy.py`
- `src/simulation_quality/scorers/progression.py`
- `src/simulation_quality/scorers/information.py`
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` (`_within_band`, `GRADE_ORDER`, line ~34/140)

## Assumptions / Open Questions
- Whether the fix should be "raise weights" or "lower thresholds" (or both, per-pillar
  differently) is explicitly left to the implementer's investigation — the roadmap and this
  ticket deliberately do not pre-decide this, since it requires empirical construction of best/
  worst-case scenarios that hasn't been done yet.
- The exact best-case/worst-case scenarios to construct per pillar are not yet identified — first
  investigation task.

## Implementation Notes

Followed `staging_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/plan.md`'s 12 steps in order. See
that file's new "Deviations" section for the full list of implementation-time findings; summarized
here.

**Steps 1-5 (weight derivation, `config/simulation_quality/scoring_weights.yaml`):** Identified each
pillar's richest anchor run_key by scanning `data/calibration/*/quality_report.json` restricted to
the 72 committed anchor keys (not the ~109 local directories, which include untracked trial/variant
runs). Computed per-pillar multipliers via `M = ceil((0.5 * denominator) / raw_score)`:
- WORLD: `frontier_marches_seed123_200t` (38 events, raw=60, denom=200) → M=2. Now A (0.60).
- ECONOMY: `urban_political_seed123_1000t` (69 events, raw=138, denom=841) → M=4. Now A (0.66).
- PROGRESSION: `generated_frontier_3_42_seed42_1000t` (44 events, raw=121, denom=993) → M=5. Now A (0.64).
- INFORMATION: escalation triggered (see below) → new world + M=5.

Only positive per-event weights changed; every negative/dormancy weight, `grade_thresholds.yaml`,
and `quality_report.py`'s formula are untouched (confirmed via `git diff` — no COGNITION/COMBAT/
NARRATIVE/SOCIAL/FACTION/AGENCY section touched either).

**INFORMATION escalation (Step 5) — why a second Unit-tier world was warranted alongside
`unit_information_source`:** Reaching 0.5 on the existing 1-event richest scenario would require a
single-event weight of 25 (for `belief_active`) — above the reference ceiling (PROGRESSION's
original `pillar_trait_milestone=15.0`), meaning one occurrence would dominate the entire pillar, a
discriminative-power problem in its own right per the plan's Anti-Drift Notes. Confirmed two
structural facts before building new content: (1) `paid_information_transaction` cannot fire under
the current engine at all — `InformationProviderState` (the record `PaidInformationTransactionSystem`
depends on) is never constructed anywhere in `src/` (confirmed by grep), so
`AuthoritativeState.information_providers` is always empty and that system's `enforce()` returns
immediately; (2) `decision_diverged_by_belief` has zero occurrences across the entire local
calibration corpus (event_count for INFORMATION is <=1 in every one of the 72 anchors). Given this,
built `unit_information_density` (`data/worlds/unit_information_density/world.yaml`) — same module
pair as `unit_information_source` (`frontier_village_core` + `hero_adventurers`, 16 entities/1
region) but with 3 `pending_information_responses` entries (pop_0/pop_1/pop_2, one per
`hero_adventurers` population slot) instead of 1, producing 3 one-shot `belief_assimilated` events
per run instead of 1 — the one empirically-reliable, content-driven lever available. This is
complementary to, not a replacement for, `unit_information_source`: that world is deliberately
minimal/event-starved by design as a pure isolation probe (per its own originating ticket,
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`); `unit_information_density` is purpose-built for
higher event *density* within the same Unit-tier discipline. Ran through the real calibration
pipeline (`calibrate_simq.py`, not hand-authored) at 3 seeds/200t: INFORMATION grades A (0.60,
identical across all 3 seeds) — committed as a permanent corpus entry per the ticket's recorded
human decision. `M_INFORMATION=5` was then computed against this new world's own richest run
(raw=6.0, denom=50) — the same order of magnitude as the other 3 pillars, non-degenerate.

**Step 6-9 (regeneration + full regression):** Regenerated all 72 pre-existing anchor run_keys'
calibration reports (broader than Step 6's literal 4-pillar-richest-run list, but necessary so
Step 9's full parametrized sweep checked live post-fix data rather than stale pre-fix reports — see
plan.md Deviations). 28 pillar-grade cells across 26 run_keys moved and were updated in
`grade_anchors.json`; 3 new `unit_information_density` entries added (`FAST_ANCHOR_KEYS` too). Zero
zero-activity (event_count=0) anchor changed grade, confirming AC 2 empirically. Found and corrected
one pre-existing, unrelated anchor drift (`urban_political_seed456_500t` WORLD, A→B — cannot be
caused by this ticket's strictly-positive weight change; pre-existing corpus/engine drift, documented
in `WORLD-110`). Full domain sweep: `pytest tests/simulation_quality/ -m "not slow"` (448 passed) and
`-m "slow"` (24 passed, 2 skipped Redis-unrelated) — both clean.

**Step 8 (zero-activity guard):** Confirmed 0 zero-event anchors exist for WORLD/PROGRESSION
anywhere in the corpus (every populated scenario generates baseline demographic/XP events) — nothing
to add for those two. ECONOMY (56) and INFORMATION (36) already have abundant zero-event anchor
coverage in the parametrized sweep.

**Step 10 (parity ledger):** Updated `WORLD-110` (world_dynamics.yaml) to describe the new expected
state and cite `frontier_marches_seed123_200t` as the scenario demonstrating the raised ceiling.
Updated `SIMQ-CALIBRATED-001` and cross-checked `INFRA-255` (infrastructure.yaml) to record the
weight-vs-threshold distinction. `INFRA-242/243/245/246` (event-coverage entries) left unmodified —
event types exercised did not change, only per-event weight magnitudes.

**Step 11 (docs):** `current_state.md`'s grade-distribution table, discriminative-power section, and
anchor-count citation updated to the post-fix state (75 real scenario entries / 18 worlds — corrected
from the previously-cited 72/17: the investigation's "74" figure had missed that `grade_anchors.json`
has 3 meta keys, `_note`/`_instructions`/`_grade_order`, not 1). `corpus_tier_taxonomy.md`'s Unit-tier
mapping table gained `unit_information_density`'s row, matching the other 4 Unit-tier rows' format.
`make knowledge-index-update` and `graphify update .` both run (docs and tests changed).

**Step 12 (live-mode sweep) — diff summary:** `python3 tools/evaluate_simq.py` (live mode):
"750 pillars checked — 1 regression — 0 missing" on first run. The 1 flagged regression
(`urban_political_seed123_500t` COGNITION: anchor B, live S) is **not attributable to this ticket**:
- `git diff` confirms zero changes to COGNITION's scorer or weights section.
- Reproduced the exact same scenario 3 separate times outside the live sweep (once during this
  ticket's own Step 6 regeneration, before Step 9 ran, and twice more standalone afterward): all 3
  gave `COGNITION: grade=B, raw_score=11.0, event_count=2` — bit-for-bit identical, matching the
  committed anchor. Only the live-sweep run (under sustained ~30-minute concurrent load, with
  repeated `WatchdogTrip`/tick-budget-exceeded warnings throughout its own log) produced the
  anomalous `grade=S, raw_score=3521.0, event_count=119` result, with `loop_detected=True` on
  `self_model_active`/`subjective_divergence` — a runaway-loop signature. This is a pre-existing,
  environment/load-sensitive nondeterminism in the self-model cognition subsystem's loop-detection
  path, unrelated to any weight or config this ticket touches, and it is real evidence the project's
  "do not break determinism" invariant is not currently holding for COGNITION under load — a
  genuine, separately-tracked concern (recommend a follow-up hotfix/investigation ticket), not
  something to silently fix or hide inside this ticket's diff.
- The anchor (`B`) was **not** changed — it already matches the true, stable, reproducible behavior
  (3/3 clean reproductions), unlike the `urban_political_seed456_500t` WORLD case above, which
  really was stale. Regenerated `urban_political_seed123_500t`'s on-disk calibration report back to
  the stable `B` state (matching the 3 clean reproductions) before final verification.
- Re-ran `pytest tests/simulation_quality/test_grade_regression.py` (`-m "not slow"` 58 passed,
  `-m "slow"` 18 passed) and `python3 tools/evaluate_simq.py --dry-run` (750 pillars checked, 0
  regressions, 0 missing) against the corrected on-disk state — clean.
- Every other changed scenario/pillar in the live sweep traces to Steps 2-8's weight changes; no
  other unattributed change found.

## Test Summary
- `pytest tests/simulation_quality/test_world_dynamics_scorer.py tests/simulation_quality/test_weights.py
  tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_timegate_penalties.py::TestEconomyTimegate
  tests/simulation_quality/test_progression_scorer.py tests/simulation_quality/test_timegate_penalties.py::TestProgressionTimegate
  tests/simulation_quality/test_information_scorer.py -v` — 99 passed, 1 failed then fixed (hardcoded
  literal in `test_getitem_known_key` updated to match ECONOMY's new `harvest_active=12.0`), 100
  passed on re-run.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — 58 passed.
- `pytest tests/simulation_quality/test_grade_regression.py -m "slow" -v` — 18 passed.
- `pytest tests/simulation_quality/ -m "not slow"` — 448 passed, 26 deselected.
- `pytest tests/simulation_quality/ -m "slow"` — 24 passed, 2 skipped (Redis broker, unrelated), 448 deselected.
- `python3 tools/evaluate_simq.py` (live mode) — 750 pillars checked, 1 regression (investigated,
  attributed to pre-existing COGNITION nondeterminism, not this ticket — see Implementation Notes).
- `python3 tools/evaluate_simq.py --dry-run` (post-correction) — 750 pillars checked, 0 regressions,
  0 missing.

## Files Changed
- `config/simulation_quality/scoring_weights.yaml` (WORLD x2, ECONOMY x4, PROGRESSION x5,
  INFORMATION x5 positive weights only; 4 separable diff hunks)
- `data/worlds/unit_information_density/world.yaml` (new)
- `data/worlds/unit_information_density/resolved/*` (new, generated via `cli resolve`/`compile`)
- `data/worlds/unit_information_density/world_compile_report.json` (new, generated)
- `config/simulation_quality/profiles/unit_information_density.yaml` (new)
- `tests/simulation_quality/fixtures/grade_anchors.json` (28 pillar-grade cell updates across 26
  existing entries + 3 new `unit_information_density` entries)
- `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS` +3)
- `tests/simulation_quality/test_weights.py` (1 hardcoded literal corrected to match new ECONOMY weight)
- `docs/parity_ledger/world_dynamics.yaml` (`WORLD-110`)
- `docs/parity_ledger/infrastructure.yaml` (`SIMQ-CALIBRATED-001`, `INFRA-255` cross-check note)
- `docs/simulation_quality/current_state.md` (grade-distribution table, discriminative-power section,
  anchor-count correction, Recommendation 1 marked done)
- `docs/simulation_quality/corpus_tier_taxonomy.md` (+1 Unit-tier row, intro sentence updated)
- `docs/REGISTRY.yaml` (regenerated)
- `data/calibration/*` (regenerated, gitignored — not committed)

## Completion Summary
Recalibrated WORLD/ECONOMY/PROGRESSION/INFORMATION's positive per-event scoring weights
(`config/simulation_quality/scoring_weights.yaml`, x2/x4/x5/x5 respectively), computed per-pillar
from each pillar's own richest-observed corpus scenario so that scenario crosses the grade-A
threshold (0.5) — leaving every negative/dormancy weight, `grade_thresholds.yaml`, and the
`normalized_score` formula untouched. INFORMATION additionally required a new, permanent Unit-tier
corpus world (`unit_information_density`, complementary to the existing `unit_information_source`
isolation probe) because its existing 1-event richest scenario could not be fixed by weight alone
without letting a single event dominate the pillar. All 4 pillars now have at least one real,
committed corpus scenario reaching grade A; structurally-inert (zero-activity) scenarios empirically
confirmed to remain grade C. Full regression (`pytest tests/simulation_quality/`, both fast and slow
tiers) and a live-mode `evaluate_simq.py` corpus sweep both came back clean after investigating and
attributing the sweep's one flagged regression to pre-existing, environment-load-sensitive
nondeterminism in COGNITION's self-model loop-detection (unrelated to this ticket's diff, confirmed
via 3 clean reproductions matching the anchor) rather than to this ticket's weight change. Parity
ledger (`WORLD-110`, `SIMQ-CALIBRATED-001`, `INFRA-255`) and `current_state.md`/
`corpus_tier_taxonomy.md` updated to reflect the corrected state, including a factual correction of
the anchor-scenario count (72→75, not the previously-miscounted 74/77).

**Known gaps, both explicitly stated, neither blocking this ticket's own scope:**
1. The COGNITION self-model loop-detection nondeterminism found during Step 12 (see Implementation
   Notes) is filed as its own follow-up ticket, `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`
   (open, standard tier) — not fixed here, since it's unrelated to this ticket's weight-only diff.
2. `config/simulation_quality/profiles/unit_information_density.yaml`'s profile-override values
   have no dedicated unit test (unlike `test_dungeon_crawl_profile_overrides`/
   `test_urban_political_profile_overrides` for the other two calibration profiles) — only
   indirectly exercised via the 3 `unit_information_density_seed{42,123,456}_200t` grade-anchor
   regression entries. Left as a minor, non-blocking test-coverage gap rather than expanding this
   ticket's scope further; a natural pickup for whichever ticket next touches
   `test_weights.py`'s profile-override test family.
