---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
artifact_type: investigation
tags: [simulation-quality, grade-thresholds, calibration]
---

# Investigation — TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE

## Method (re-derived fresh, not copied from the filing investigation)

1. Kicked off a real, full fast-tier engine re-run (`python3 tools/evaluate_simq.py`, no
   `--dry-run`) against the exact current `m1-quick-wins` HEAD (no `src/` commits landed between
   this run starting and the pre-existing `data/calibration/` snapshot the filing investigation
   used — verified by comparing commit timestamps to file mtimes; all commits since are
   ticket-filing-only, no code). Completed in ~8 minutes: 71 scenarios total (61 `FAST_ANCHOR_KEYS`
   parametrized + 10 other `test_grade_regression.py` tests unrelated to the corpus loop),
   `evaluate_simq.py`'s own coarse grade-band-only tally: **630 pillars checked, 61 regressions**.
2. Wrote a standalone script (re-using the exact live helper functions imported from
   `tests/simulation_quality/test_grade_regression.py` itself — `_within_band`,
   `_within_score_tolerance`, `_score_tolerance_kwargs`, `_extract_pillar_grades/scores`,
   `_load_calibration_report` — and `tools/simq_ceiling.py::lookup_ceiling`) to reproduce the
   test suite's exact pass/fail verdict for **every** `(run_key, pillar)` pair across all 61
   `FAST_ANCHOR_KEYS`, in one deterministic pass, against the fresh `data/calibration/*/quality_report.json`
   data the re-run just produced. This avoids parsing pytest's aggregated per-run_key failure text
   and avoids `data/calibration/*/quality_scores.jsonl`, which was discovered during this pass to
   be **unsafe to read directly** — see Anti-Drift Hazards.
3. Cross-referenced against `git log --oneline main..m1-quick-wins` (60 commits) and the causing
   tickets' own `## Request Summary` sections.
4. Read `src/domains/cooperation/*.py` in full (phase.py, services.py, evaluators.py, providers.py,
   postures.py) and `src/simulation_quality/pillar_accumulator.py`/`quality_report.py` in full for
   the `loop_detected` due-diligence item.

## Current Behavior

**61/61 `FAST_ANCHOR_KEYS` currently fail** `test_grade_within_anchor_band` (some on the ±1 letter
band check, most on the independent score-tolerance check — see module docstring at
`tests/simulation_quality/test_grade_regression.py:1-29`). This exactly reconciles with the
filing investigation's "63/71" headline: `pytest --collect-only -m "not slow"` on this file
collects exactly 71 tests = 61 `FAST_ANCHOR_KEYS` (all failing) + 2 out-of-scope selfmodel-probe
tests (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`test_urban_political_selfmodel_execution_isolated_grade_anchor`, both dedicated test functions,
**not members of `FAST_ANCHOR_KEYS`** — confirmed by direct membership check, so they are
structurally impossible to accidentally touch by iterating `FAST_ANCHOR_KEYS`) + 8 structural/meta
tests (anchor-file-validity, override-table-scoping, etc. — all passing, untouched by this ticket).

### Full per-`(run_key, pillar)` classification (211 failing combos across the 61 run_keys)

Pillar-level failing-combo counts and their `tools/simq_ceiling.py::lookup_ceiling` classification
(computed live against this run's fresh data, not assumed):

| Pillar | Failing combos | known tick_budget | known flag_gated | known watchdog_variance | known corrected | **uncovered (real drift)** |
|---|---|---|---|---|---|---|
| SOCIAL | 50 | 0 | 0 | 0 | 0 | **50** |
| PROGRESSION | 36 | 29 | 0 | 2 | 0 | **5** |
| WORLD | 35 | 35 | 0 | 0 | 0 | 0 |
| COMBAT | 32 | 23 | 9 | 0 | 0 | 0 |
| ECONOMY | 32 | 23 | 0 | 1 | 0 | **8** |
| AGENCY | 12 | 0 | 0 | 0 | 0 | **12** |
| NARRATIVE | 9 | 8 | 0 | 0 | 1 | 0 |
| COGNITION | 5 | 0 | 0 | 0 | 0 | **5** |
| **Total** | **211** | 118 | 9 | 3 | 1 | **80** |

**Correction to the filing investigation's framing**: it described "smaller patterns in
PROGRESSION, COMBAT, ECONOMY, NARRATIVE, COGNITION, AGENCY" without singling out WORLD, and did
not state that COMBAT and NARRATIVE are **100% pre-existing-ceiling-covered** (zero real M1
drift in either pillar) while WORLD is **also 100% pre-existing-ceiling-covered** (35/35, all
`tick_budget`) despite being the 3rd-largest failing-combo count. This re-derivation refines that:
of the 8 pillars with failures, only **SOCIAL, PROGRESSION (partial), ECONOMY (partial), AGENCY,
COGNITION** carry any genuinely new (uncovered) drift; COMBAT, NARRATIVE, and WORLD's failures are
entirely pre-existing structural noise unrelated to the M1 batch (see next section).

**Run-key-level rollup** (matches the filing investigation's headline counts exactly):
- **6/61 run_keys are FULLY explained by a pre-existing `simq_ceiling.py` classification** — every
  failing pillar in that run_key has a known ceiling, i.e. zero uncovered drift:
  `sandbox_world_seed137_200t` (WORLD), `urban_political_seed42_200t` (COMBAT, ECONOMY,
  PROGRESSION), `urban_political_seed456_500t` (COMBAT, ECONOMY, WORLD),
  `frontier_living_world_seed42_200t` (COMBAT, ECONOMY, PROGRESSION, NARRATIVE),
  `highland_traverse_seed123_200t` (WORLD), `highland_traverse_seed456_200t` (WORLD).
- **55/61 run_keys have at least one uncovered (real) failing pillar**, needing per-cause
  attribution below.

## Root Cause 1 — SOCIAL (50/50 uncovered failing combos, the dominant driver)

Confirmed directly: `src/domains/optimization/feature_flags.py:37` (`ENABLE_BELIEF_ASSIMILATION`)
and `:52` (`ENABLE_SOCIAL_COOPERATION`) are both `FeatureMode.ON` on this HEAD — flipped by
`TCK-20260824-ROLLOUT-FLAG-DECISIONS`. `CooperationPhase.execute()`
(`src/domains/cooperation/phase.py:35-141`) now runs its help-need → partner-candidate →
cooperation-decision pipeline for real every tick for every eligible entity, where it previously
never fired live content. All 50 uncovered SOCIAL combos move **upward** (anchor mostly near-zero
or moderate → actual materially higher), consistent 1:1 with cooperation content going from
dormant to real. All 50 are grade-band-safe (within ±1 letter) — they fail only the independent
score-tolerance check, i.e. this is a magnitude shift within the same quality tier, not a
qualitative regression.

## Root Cause 2 — COGNITION (5/5 uncovered failing combos)

Same root flag: `src/simulation_quality/scorers/cognition.py:52-68` scores the `belief_updated`
event type → `belief_active` tag (positive weight) whenever `ENABLE_BELIEF_ASSIMILATION` allows
belief updates to actually occur. All 5 uncovered COGNITION combos move upward from a near-zero
anchor (0.024–0.18) to a materially higher actual (0.55–1.34) — same "previously dormant → now
live" signature as SOCIAL, same causing ticket (`TCK-20260824-ROLLOUT-FLAG-DECISIONS`).

## Root Cause 3 — AGENCY (12/12 uncovered failing combos)

All 12 move from anchor=0.000 to a small, remarkably consistent actual value (0.140 in 8/12 cases,
0.065–0.280 in the rest) across otherwise-unrelated worlds (`simq_scale_stress`,
`unit_information_source` ×3 seeds, `unit_selfmodel_pilot` ×3 seeds, `unit_information_density` ×3
seeds, `generated_frontier_3_42`, `lifecycle_full_coverage_world`). All pass the ±1 band check
(C→B) — only the score-tolerance check fails, and only because `anchor_score=0.0` makes the
absolute-floor tolerance (0.05) trivially tight for any nonzero result.
`src/domains/cooperation/phase.py` mutates entity `EntityUpdate`s (locomotion/route/contract
intent) every tick once cooperation posture resolves — this is the same class of "previously
gated to no-op, now produces real `AgencyScorer`-visible `action_executed`/`route_selected`
activity" effect as Root Causes 1–2, downstream of the same `TCK-20260824-ROLLOUT-FLAG-DECISIONS`
flag flip rather than a directly-read belief/cooperation tag in `agency.py` itself. Not traced to
line-level certainty (would require an event-trace diff of a single tick, out of proportion for a
re-baseline ticket) but the evidence (identical run_key set as the cooperation-affected worlds,
identical small fixed-weight signature, zero prior firings) is consistent and non-contradictory.

## Root Cause 4 — PROGRESSION and ECONOMY, 500t-only uncovered drift (5 + 8 combos)

All 5 uncovered PROGRESSION combos and all 8 uncovered ECONOMY combos occur **exclusively in 500t
scenarios** (`urban_political`, `hero_guild_routing`, `dungeon_crawl`, `simq_routing_test`).
PROGRESSION moves mostly negative (4/5; wound-penalty-driven, see Root Cause 5 below); ECONOMY
moves consistently positive (8/8, mostly from a `0.0` anchor to a modest 0.09–0.33 actual) — a
plausible secondary effect of the same cooperation wiring (successful cooperation frequently
includes joint economic tasks/trades, see `contract_expired_offer`/`cooperation_event` handling in
`src/domains/cooperation/services.py`), surfacing only once a scenario runs long enough (500t) for
compounding trade activity to clear ECONOMY's near-zero floor. Traced with the same confidence
level as Root Cause 3 (consistent, non-contradictory, not line-level-certain).

## PROGRESSION Sign-Flip — Ticket Due-Diligence Item #2 (confirmed real)

Confirmed directly from fresh data — `urban_political` PROGRESSION moves in **opposite directions**
depending on run length:

| run_key | anchor_score | actual_score | delta | `simq_ceiling.py` classification |
|---|---|---|---|---|
| `urban_political_seed42_200t` | -0.1569 | **+0.3545** | **+0.5114 (UP, sign flips)** | `tick_budget`: `progression_frozen_by_tick=200` == this scenario's own tick count |
| `urban_political_seed42_500t` | -0.1269 | -0.3122 | -0.1853 (DOWN) | none (real drift) |
| `urban_political_seed123_500t` | -0.1871 | -0.3726 | -0.1855 (DOWN) | none (real drift) |
| `urban_political_seed456_500t` | -0.0202 | -0.0171 | +0.0031 (flat, passes) | `watchdog_variance` (pre-existing, `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) |

**One-line explanation**: the 200t variant lands exactly on `config/simulation_quality/detection_params.yaml`'s
`progression_frozen_by_tick=200` threshold — a pre-existing, M1-unrelated structural ceiling
(`tools/simq_ceiling.py`'s own registered `TIME_GATE_PILLAR` entry) whose dormant/frozen-progression
detector is documented as noisy exactly at that boundary regardless of true behavior, which is
sufficient on its own to explain a sign flip at 200t without contradicting the consistent,
~-0.185-magnitude negative drift both 500t seeds show once well past that threshold — the negative
500t drift is attributed to the severity-scaled wound/scar penalty formula going live
(`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`, `TCK-20260824-WOUND-THRESHOLD-DECISION`,
`TCK-20260824-TACTICAL-WOUND-SCAR-WIRING`) compounding more over a longer run (more ticks for
wound accumulation to suppress combat/XP-adjacent PROGRESSION events) than a 200t run has time to
manifest before the tick-budget ceiling artifact dominates instead. This is not re-centered
silently — both the 200t ceiling artifact and the 500t real drift are documented above as distinct
causes, not folded into one blanket explanation.

## `loop_detected` Due-Diligence — Ticket Item #3 (mixed result, one real finding disclosed)

Read `src/simulation_quality/pillar_accumulator.py` in full first. **Correction to the filing
investigation's framing**: `loop_detected`/`loop_flags` (`_check_loop_detection()`,
`pillar_accumulator.py:60-70`) is **purely a diagnostic flag** surfaced in `quality_report.json` —
no code path in `quality_report.py::QualityReportBuilder.build()` multiplies, caps, or otherwise
reduces `raw_score`/`normalized_score` based on `loop_flags`. There is no "dampener" in the current
code; calling it that overstates what the mechanism does. Any real score decrease in these 3
run_keys comes from plain linear accumulation of `offer_dead` (`config/simulation_quality/scoring_weights.yaml:116`,
weight -1.0) events, which can outweigh `cooperation_active` (weight +4.0) events if the
offer-expiry rate is high enough — a genuine mechanism, just not the one named.

Checked all 3 named run_keys against the fresh data:

| run_key | anchor SOCIAL | actual SOCIAL | tolerance | **currently fails?** | loop_flags |
|---|---|---|---|---|---|
| `urban_political_seed42_200t` | 16.815 | 13.85 | ±3.363 (20%) | **NO — passes, within tolerance** | `["cooperation_active"]` |
| `highland_traverse_seed42_200t` | 6.875 | 5.045 | ±1.375 (20%) | **YES — fails** | `["cooperation_active"]` |
| `lifecycle_full_coverage_world_seed42_200t` | 6.19 | 5.05 | ±1.238 (20%) | **NO — passes, within tolerance** | `["cooperation_active"]` |

**Only 1 of the 3 named run_keys (`highland_traverse_seed42_200t`) is an actual current test
failure.** The other 2 show the same directional decrease and the same `loop_flags` diagnostic,
but stay inside the 20% score-tolerance band, so no anchor change is needed for SOCIAL in either —
they are not touched by this ticket's anchor update. This is disclosed here rather than silently
treated as "all 3 need re-baselining," per the ticket's own instruction not to blindly copy the
filing investigation's classification.

Also notable in all 3 cases: `loop_flags` names `cooperation_active` (the **positive**-weight tag),
not `offer_dead` — the >70%-of-200-event-window threshold is being tripped by the volume of
*successful* cooperation, not spam. This on its own would support "legitimate — cooperation is
just genuinely dense now," consistent with the ticket's stated alternative hypothesis.

**However, digging into `highland_traverse_seed42_200t` specifically** (the one that actually
fails) surfaced a real, disclosable finding, not a false alarm:

- `negative_count=213` of `event_count=516` SOCIAL events (~41%) are `offer_dead`.
- The report's own `worst_events` sample (fresh, single-run-scoped, not the stale
  append-only `quality_scores.jsonl` — see Anti-Drift Hazards) shows **the same entity firing
  `contract_expired_offer` on every single consecutive tick with zero gaps** — e.g. entity 13:
  ticks 50–72 (23 consecutive ticks), entity 8: ticks 54–73 (20 consecutive ticks).
- Read `src/domains/cooperation/phase.py`, `services.py`, `evaluators.py`, `providers.py`,
  `postures.py` in full: **there is no cooldown, backoff, or pending-offer state tracking
  anywhere in the cooperation domain package.** `CooperationPhase.execute()` re-evaluates and can
  re-issue a cooperation decision for every eligible entity on every single tick with no memory of
  a just-expired offer.

**Conclusion: this looks like a real tuning gap, not expected dense-cooperation behavior.**
Genuinely dense cooperation (many *different* entities cooperating, or the same entity trying
different partners) would not produce a single entity retrying against a presumably-unavailable
partner on 20+ literally consecutive ticks with a 100% failure rate. Per the ticket's explicit
instruction, **this is disclosed as a separate finding and NOT fixed inline** — see
`trial_evidence` note below and the ticket's Completion Summary. `SOCIAL` for
`highland_traverse_seed42_200t` is **left failing, not re-baselined**, so the gap stays visible
rather than being silently absorbed.

**Disclosed finding (not actioned by this ticket)**: `src/domains/cooperation/phase.py`'s
per-tick cooperation-decision loop has no cooldown/backoff after a `contract_expired_offer` —
the same entity can re-attempt and re-fail every tick indefinitely. Recommend a follow-up ticket
to add a minimum retry interval (or per-partner-pair backoff) after an offer expires unaccepted.

## Docs Requiring Update

- `docs/testing/regression_policy.md`: this ticket is a second, directly analogous worked example
  to §9 (`TCK-20260824/TCK-20260828 Re-Baseline`) — same shape (legitimate upstream behavior
  change → hardcoded test-fixture drift → re-verify per-key before blanket re-baselining, one
  real disclosed gap left un-touched rather than force-fit). Recommend `doc-updater` append a new
  `## 10. TCK-20260824-ROLLOUT-FLAG-DECISIONS / TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE
  Re-Baseline (Worked Example)` section summarizing: dominant SOCIAL/COGNITION driver, the
  PROGRESSION 200t/500t sign-flip nuance, and the one disclosed-not-fixed `highland_traverse`
  cooperation-cooldown gap, as future re-baseline-ticket precedent.

No `docs/mechanics/` or `docs/engine/` chapter needs updating — this ticket does not change any
simulation law, formula, or pipeline behavior; it only re-baselines a test fixture to match
already-shipped, already-documented (via the cited tickets' own investigation/completion
summaries) behavior.

## Parity Ledger Overlap

None. This ticket touches no `src/` file and introduces no new behavior — `implementation.files_changed`
will contain only `tests/simulation_quality/fixtures/grade_anchors.json` (+ possibly
`docs/testing/regression_policy.md`), so the Parity phase's skip-eligibility condition
(`files_changed` has no `src/` path AND `behavior_changed=false`) applies. No P0 parity entries
intersect a test-fixture-only change (verified: `find_p0_intersection` will be run mechanically by
the orchestrator regardless, per the workflow's own lazy P0 safeguard).

## Prior Work

- `TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` — direct methodological precedent
  (`docs/testing/regression_policy.md` §9): re-verify per-test before blanket re-baselining; some
  failures may not be floor drift at all.
- `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` — covers the 2 excluded
  selfmodel-probe tests; confirmed structurally unreachable from this ticket's `FAST_ANCHOR_KEYS`
  iteration (they are not members of that list at all).

## Risks and Open Questions

- The `highland_traverse_seed42_200t`/SOCIAL disclosed finding means `test_grade_regression.py -m
  "not slow"` will **not** be 100% green after this ticket — one test will remain a known,
  disclosed failure (see Acceptance Criteria's own allowance for "any remaining failure is
  independently new and disclosed as its own finding"). This is a deliberate deviation from a
  blanket "all green" close, consistent with the Gate Integrity rule and the CORPUS-DIVERSITY
  precedent (which also left some failures deliberately un-touched).
- AGENCY's and ECONOMY's uncovered drift is traced with high confidence but not line-level
  certainty (see Root Causes 3–4) — if this is later found wrong, the anchors are still evidence-
  backed against real fresh data either way, just the causal narrative would need a correction.

## Anti-Drift Hazards

- **`data/calibration/*/quality_scores.jsonl` is append-only** (`src/simulation_quality/persistence.py:23`,
  `open(jsonl_path, "a", ...)`) — it accumulates records across every historical run against that
  `run_dir`, never truncated. Reading it directly (as this ticket's own Implementation Notes
  originally suggested) without disambiguating by run produces double-counted/stale tag
  distributions — confirmed empirically (initial raw read of `urban_political_seed42_200t`'s
  SOCIAL tag counts was off by ~2x vs. the authoritative `quality_report.json`). **Always prefer
  `quality_report.json`'s own `event_count`/`negative_count`/`worst_events` fields** (rebuilt fresh
  and atomically per run via `write_report()`'s tmp+rename) for any single-run analysis; treat
  `quality_scores.jsonl` only as a corroborating raw log, never as the source of truth for counts.
- Do not re-run `tools/evaluate_simq.py` again before writing anchors — the anchor-writing step
  must read the exact same fresh `data/calibration/` snapshot this investigation was derived from,
  or the investigation's evidence and the written anchors could silently diverge.
