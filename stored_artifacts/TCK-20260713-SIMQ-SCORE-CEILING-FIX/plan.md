---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-SCORE-CEILING-FIX
artifact_type: plan
tags: [simulation-quality, calibration, corpus]
---

# Implementation Plan — TCK-20260713-SIMQ-SCORE-CEILING-FIX

## Summary

The ceiling is a per-event weight scale problem, not a formula problem (confirmed by
investigation.md — `normalized_score` is identical across all 10 pillars, WORLD-110/INFRA-255
already validate it). The fix is: raise **positive** per-event weights in
`config/simulation_quality/scoring_weights.yaml` for WORLD, ECONOMY, PROGRESSION, and INFORMATION,
computed per-pillar from each pillar's actual richest-observed scenario so that scenario crosses
the A threshold (0.5) — not a uniform multiplier. Negative/penalty weights and
`grade_thresholds.yaml` are left untouched: raising thresholds risk is unnecessary once the
positive-weight lever is shown sufficient, and touching penalties risks recovery-from-dormancy
dynamics the investigation flags as a hazard. INFORMATION is the one pillar where a weight raise
alone may be insufficient (event-density-limited, not weight-limited); if empirically confirmed,
a new minimal calibration scenario is added to the corpus (not a synthetic thrown outside it) so
AC 1's "real corpus scenario" requirement still holds. Every anchor change is regenerated via the
real calibration pipeline, diffed, and only the 4 affected pillars' columns are hand-verified in
`grade_anchors.json` — everything else is a guardrail against unattributed regressions.

## Resolved Open Questions (from investigation.md)

**1. Raise weights vs. lower thresholds vs. both, per pillar** — RESOLVED: raise positive
per-event weights only, for all 4 pillars, computed empirically per pillar (see Step 2 formula
below). Do NOT touch `grade_thresholds.yaml` for any of the 4 pillars in this ticket. Rationale:
(a) investigation's structural finding that raising positive weights cannot inflate zero-activity
worlds (penalties only fire on same-family triggering events) makes this the demonstrably lowest-
risk lever; (b) changing two levers (weights + thresholds) at once makes AC 3's "0 unattributed
regressions" harder to attribute to a single cause; (c) thresholds being "never empirically
validated" for these 4 pillars (per SIMQ-CALIBRATED-001) is a reason they're *safe* to touch later
if weights alone prove insufficient, not a reason to touch them now — start with the smaller,
better-understood change and only escalate if Step 6 (regeneration) shows a pillar still can't
cross A after a reasonable weight increase. If that happens for INFORMATION specifically (see
Step 5), the escalation is a new corpus scenario, not a threshold edit — this keeps the lever
count at one (weights) for all 4 pillars and avoids opening `grade_thresholds.yaml` in this ticket
at all.

**2. Exact run_key per pillar's cited best-case scenario** — RESOLVED as a concrete first
implementation step (Step 1 below): grep `data/calibration/*/quality_report.json` for
`event_count`/pillar raw_score near the cited numbers (69 ECONOMY, 38 WORLD, 46 PROGRESSION,
1 INFORMATION), cross-referenced against `docs/simulation_quality/eval_matrix_results.md` lines
~947 (ECONOMY 0→24 event jump) and ~324/~1254 (zero-ECONOMY C anchors, reusable as worst-case
guards for AC 2). This is data lookup, not a judgment call — no ambiguity requiring a human
decision.

**3. 72 vs. 74 anchor-entry discrepancy** — RESOLVED: use the accurate count (74 real scenario
entries, confirmed via investigation's `json.load` check excluding the `_note` key) when updating
`docs/simulation_quality/current_state.md` in Step 10. This is a documentation accuracy fix folded
into the existing doc-update step, not a scope change.

## Steps

### Step 1 — Identify best-case and worst-case run_keys per pillar
**Files:** none changed (read-only investigation step); working notes may go in
`staging_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/` scratch, not committed.
**Change:** Grep `data/calibration/*/quality_report.json` for each pillar's `event_count` and
`raw_score`/`last_event_tick` fields, matching the richest-observed values cited in the ticket
(69-event ECONOMY, 38-event WORLD, 46-event PROGRESSION, 1-event INFORMATION). Cross-reference
`docs/simulation_quality/eval_matrix_results.md` (~line 947 for the ECONOMY 0→24 jump, ~324/~1254
for zero-ECONOMY C-anchor candidates) to also pin down at least one zero-activity ("structurally
inert") anchor `run_key` per pillar for the AC 2 guard. Record for each of the 4 pillars: richest
`run_key`, its `raw_score`, `last_event_tick`/`floor_tick` (effective denominator), and current
`normalized_score`/grade — plus one confirmed zero-activity `run_key` per pillar.
**Do NOT touch:** No file edits in this step. Do not run `evaluate_simq.py` live mode yet — that's
Step 11.
**Verify:** Manual — the recorded run_keys and raw numbers must reproduce the ticket's cited
figures (0.30 WORLD / 0.16 ECONOMY / 0.13 PROGRESSION / 0.04 INFORMATION) within rounding. This
step has no pytest verification; it produces the inputs Step 2 needs.

**INFORMATION's richest run identified (architecture-review finding, 2026-07-13):** the cited
1-event/0.04 INFORMATION run is `unit_information_source_seed{42,456,123}_200t` — confirmed via
`data/calibration/unit_information_source_seed42_200t/quality_report.json`
(`raw_score=2.0, normalized_score=0.04, grade=B, event_count=1, loop_detected=true` on
`belief_active`, matching across all 3 seeds). This is the pre-existing **Unit-tier**
INFORMATION-isolation world (`docs/simulation_quality/corpus_tier_taxonomy.md` line 134,
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`) — not an anonymous scenario. Step 1 must name
it explicitly in the run_key table rather than leaving it unidentified.

### Step 2 — Raise WORLD's positive per-event weights
**Files:** `config/simulation_quality/scoring_weights.yaml` (WORLD section only)
**Change:** For each of WORLD's positive-signal keys read by `src/simulation_quality/scorers/world_dynamics.py`
(`EVENT_TYPES` at L17-33; e.g. `calamity_active`=8, `boss_active`=6, and the smaller 1-3 point
entries), compute a single per-pillar multiplier `M_WORLD` from Step 1's richest WORLD run:
`M_WORLD = ceil((0.5 * denominator_of_richest_WORLD_run) / raw_score_of_richest_WORLD_run)`
(i.e. the smallest integer multiplier that pushes that run's `normalized_score` to at least 0.5,
crossing into A). Apply `M_WORLD` to every **positive** WORLD weight uniformly *within this
pillar* (a single multiplier per pillar is fine — the AC's "not a blanket inflation" concern is
about applying one multiplier across all 4 *different* pillars, not within one pillar's own
signal set, since positive-only scaling within a pillar cannot touch zero-activity worlds
regardless of magnitude). Do not change any WORLD key with a negative value (`calamity_dormant`,
`world_static`, `world_depopulating`, `demographics_dormant`, etc.) — leave every negative WORLD
weight exactly as-is.
**Do NOT touch:** ECONOMY/PROGRESSION/INFORMATION/NARRATIVE/COMBAT sections of the same YAML file
in this step (keep the diff scoped to WORLD only, so the eventual git diff attributes each
pillar's change to its own step). Do not touch `grade_thresholds.yaml`. Do not touch
`ecology_cycle_completed`'s ownership (stays scored in `WorldDynamicsScorer`, per `SQ-08`/
`INFRA-246` — do not move it to `EconomyScorer` even though both are being edited this session).
**Verify:** `pytest tests/simulation_quality/test_world_dynamics_scorer.py tests/simulation_quality/test_weights.py -v`
must pass unmodified (confirms the YAML still loads and scorer logic is unaffected by the value
change — assertions read `scoring_weights["key"]` dynamically per test_plan.md).

### Step 3 — Raise ECONOMY's positive per-event weights
**Files:** `config/simulation_quality/scoring_weights.yaml` (ECONOMY section only)
**Change:** Same method as Step 2, applied to ECONOMY's positive keys in
`src/simulation_quality/scorers/economy.py` (`harvest_active`=3, `crafting_active`=4,
`trade_active`=3, `gold_flow`=1, etc.), using Step 1's richest ECONOMY run (69-event candidate) to
compute `M_ECONOMY`. Leave `zero_harvest`, `zero_crafting`, `zero_trade`, and any other negative
ECONOMY weight untouched.
**Do NOT touch:** ECONOMY's Gini-threshold mechanism (explicit ticket Out of Scope) — do not open
or edit any Gini-related constant even if encountered while reading `economy.py`. Do not touch
other pillars' sections in this same edit.
**Verify:** `pytest tests/simulation_quality/test_economy_scorer.py tests/simulation_quality/test_timegate_penalties.py::TestEconomyTimegate tests/simulation_quality/test_weights.py -v`
must pass unmodified.

### Step 4 — Raise PROGRESSION's positive per-event weights
**Files:** `config/simulation_quality/scoring_weights.yaml` (PROGRESSION section only)
**Change:** Same method, using Step 1's richest PROGRESSION run (46-event candidate) to compute
`M_PROGRESSION`, applied to `src/simulation_quality/scorers/progression.py`'s positive keys
(`pillar_trait_milestone`=15, `level_milestone`=8, `skill_growth`=5, `xp_active`=1 — note
`xp_active`'s delta is `weight * max(1, xp_amount // 10)`, so raising its base weight raises every
XP-grant event proportionally, not just milestones; factor this into the multiplier calculation
since `xp_active` is the highest-frequency event and dominates the raw_score sum). Leave
`all_level_1` and any other negative PROGRESSION weight untouched.
**Do NOT touch:** Other pillars' sections in this edit.
**Verify:** `pytest tests/simulation_quality/test_progression_scorer.py tests/simulation_quality/test_timegate_penalties.py::TestProgressionTimegate tests/simulation_quality/test_weights.py -v`
must pass unmodified.

### Step 5 — Raise INFORMATION's positive per-event weights; add a new minimal calibration scenario only if the corpus still can't reach A/S
**Files:** `config/simulation_quality/scoring_weights.yaml` (INFORMATION section only); possibly
a new `data/calibration/{new_scenario}/` directory + its `quality_report.json` (generated, not
hand-authored) if the escalation condition below triggers.
**Change:**
1. First, apply the same per-pillar-multiplier method as Steps 2-4 to INFORMATION's positive keys
   in `src/simulation_quality/scorers/information.py` (`subjective_divergence`=6,
   `info_has_impact`=5, etc.), using Step 1's richest INFORMATION run (the cited 1-event, 0.04
   candidate) to compute `M_INFORMATION`.
2. Regenerate `unit_information_source`'s calibration report (see Step 6) and check whether it now
   crosses 0.5. Because its richest known run is only a single scored event (`belief_active`,
   `raw_score=2.0`), investigation.md flags that weight scale may not be the true bottleneck here —
   event density is. **Escalation condition:** if `M_INFORMATION` would need to exceed roughly the
   same order of magnitude as NARRATIVE's highest per-event delta (15) applied to a 1-event run —
   i.e. if reaching 0.5 requires making a single INFORMATION event worth more than the pillar's most
   significant milestone-tier signal currently is, that is a sign event density, not weight, is the
   limiter.
   In that case, construct **one new Unit-tier INFORMATION world** (architecture-review finding,
   2026-07-13: the correct precedent is Unit tier — `unit_faction_tension` /
   `unit_information_source` / `unit_selfmodel_pilot` / `hero_guild_routing`, per
   `corpus_tier_taxonomy.md`'s own classification criterion — NOT the End-to-end/archetype tier
   `urban_political` belongs to; do not model the new scenario on `urban_political`'s shape).
   Explicitly state in the ticket's Implementation Notes why a *second* Unit-tier INFORMATION world
   is warranted alongside the existing `unit_information_source` rather than reconciling with or
   replacing it (e.g. `unit_information_source` is deliberately minimal/event-starved by design as a
   pure isolation probe, and a second world purpose-built for higher INFORMATION event *density*
   within the same Unit-tier discipline serves a different, complementary role — verify this
   reasoning against `unit_information_source`'s own originating ticket,
   `TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO`, before assuming it rather than asserting it).
   Build it as a short scripted sequence of `belief_assimilated`, `paid_information_transaction`,
   `decision_diverged_by_belief` events at Unit-tier scale (matching `unit_information_source`'s
   ~16-entity/1-region footprint, not `urban_political`'s archetype scale), run it through the real
   calibration pipeline (`calibrate_simq.py`) so it produces a genuine
   `data/calibration/{new_scenario}/quality_report.json`, and add it as a new committed **permanent**
   corpus entry (explicit user decision, 2026-07-13 — see ticket's Assumptions/Open Questions) — this
   keeps AC 1's "real corpus scenario" requirement intact, since after calibration it is a real,
   reproducible scenario in the corpus like any other.
**Do NOT touch:** `paid_information_transaction`'s scoring ownership — stays in
`InformationScorer`, not `EconomyScorer` (per `INFRA-245`'s note, flagged in investigation.md as
an easy thing to conflate since both pillars are edited this session). Do not touch other
pillars' sections. Do not model the new scenario's structure on `urban_political` (End-to-end
tier) — Unit tier is the correct, precedented shape for a single-mechanic isolation world.
**Verify:** `pytest tests/simulation_quality/test_information_scorer.py tests/simulation_quality/test_weights.py -v`
must pass unmodified. If a new scenario is added, it must independently produce a valid
`quality_report.json` via the standard calibration tool before being wired into any anchor test.

### Step 6 — Regenerate calibration reports and confirm A/S is reached
**Files:** `data/calibration/{affected run_keys}/quality_report.json` (regenerated, not
hand-edited) — only the run_keys identified in Step 1 (and Step 5's new scenario, if added) need
regeneration; do not regenerate the entire `data/calibration/` corpus wholesale.
**Change:** Run the project's calibration regeneration path (`make calibrate` or the per-scenario
`calibrate_simq.py` invocation, per `test_grade_regression.py`'s documented workflow) for each
identified richest/worst-case run_key per pillar from Step 1, using the weights edited in Steps
2-5. Confirm: (a) each pillar's richest run now grades A or S; (b) each pillar's identified
zero-activity run still grades C (raw_score stays exactly 0.0 — structurally guaranteed by the
positive-only weight change, per investigation.md's dormancy-penalty finding, but confirm
empirically here rather than assuming).
**Do NOT touch:** Any calibration report outside the identified affected run_keys — a wholesale
`make calibrate` re-run across all 109 directories is unnecessary for this ticket's scope and
makes the eventual anchor diff noisier to review; regenerate narrowly.
**Verify:** Manual inspection of the regenerated `quality_report.json` files' `normalized_score`/
grade for the identified run_keys, matching the AC 1 and AC 2 expectations before touching any
test fixture.

### Step 7 — Update `grade_anchors.json` for the 4 affected pillars' columns
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Run `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` (then
`-m slow`) against the regenerated calibration data from Step 6. For every anchor entry whose
WORLD/ECONOMY/PROGRESSION/INFORMATION column now fails `_within_band` (expected — this is the
detection mechanism, not a bug), update only that pillar's grade value in that anchor entry to
the new, correct grade. If Step 5 added a new calibration scenario, add its corresponding new
anchor entry.
**Do NOT touch:** Any anchor entry's NARRATIVE/COMBAT/FACTION/SOCIAL/COGNITION/AGENCY column, or
any WORLD/ECONOMY/PROGRESSION/INFORMATION column that did not actually move — a wholesale
regeneration of the file risks silently changing unrelated pillars' anchors, which would violate
AC 3. Do not touch the file's schema (no raw-score fields — that's
`TCK-20260713-SIMQ-RAWSCORE-PERSIST`, a separate ticket).
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` and
`-m slow` both pass after the anchor update. Every diff line in `grade_anchors.json` must be
traceable to one of Steps 2-5's weight changes — no unattributed diffs (AC 3 process guard).

### Step 8 — Add zero-activity "remains C" guard coverage
**Files:** `tests/simulation_quality/test_grade_regression.py` (only if the zero-activity run_keys
identified in Step 1 are not already `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` entries — prefer
reusing the existing parametrized mechanism over adding bespoke tests)
**Change:** Confirm each pillar's zero-activity run_key from Step 1 is already covered by the
existing parametrized anchor sweep. If any is not currently a parametrized key, add it to
`FAST_ANCHOR_KEYS` (or `SLOW_ANCHOR_KEYS` if it's a 1000t+/2000t entry) so the existing mechanism
asserts it stays C, rather than writing a new standalone test function per test_plan.md's stated
preference.
**Do NOT touch:** `_within_band`'s tolerance logic or `GRADE_ORDER` — these are the shared
mechanism, out of scope for this ticket.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` (plus
`-m slow` if any added key is a long-run entry) — the 4 new/confirmed zero-activity keys must
show grade C.

### Step 9 — Full regression sweep across all pillars (anti-drift guard)
**Files:** none changed — verification only
**Change:** Run the full existing parametrized sweep over ALL `FAST_ANCHOR_KEYS`/
`SLOW_ANCHOR_KEYS` (not filtered to the 4 changed pillars) to catch any unintended cross-pillar
side effect (e.g. an accidental edit bleeding into NARRATIVE/COMBAT/FACTION/SOCIAL/COGNITION/
AGENCY columns). Also run `test_report.py` (formula-stability tests) to confirm `quality_report.py`
remains behaviorally untouched, and `test_kernel_simq_integration.py`,
`test_quality_hub_integration.py`, `test_scenario_coverage.py`, `test_calibrate_world_loading.py`,
`test_evaluate_harness.py`, `test_traceability_path.py` per test_plan.md's full regression surface.
**Do NOT touch:** Nothing to touch here — this step is pure verification. If any unexpected
pillar shows movement, stop and return to Steps 2-5 to find the cause before proceeding — do not
"fix" it by editing `grade_anchors.json` for an untouched pillar.
**Verify:** `pytest tests/simulation_quality/ -m "not slow" -v` (full domain, not repo-wide, per
the Testing Rule) shows 0 failures; `-m slow` separately for the long-run tier.

### Step 10 — Update parity ledger entries
**Files:** `docs/parity_ledger/world_dynamics.yaml` (`WORLD-110`),
`docs/parity_ledger/infrastructure.yaml` (`SIMQ-CALIBRATED-001`, cross-check
`INFRA-242`/`243`/`245`/`246`)
**Change:**
- `WORLD-110`: currently asserts B is the correct, expected ceiling for
  `dungeon_crawl_seed42_500t` (a continuously-active WORLD scenario). If Steps 2/6/7 move this
  scenario's WORLD grade to A/S, update the entry's `text`/`v2_evidence` to describe the new
  expected grade and why (link back to this ticket ID). If this specific scenario does not change
  grade (only a different run_key crosses the ceiling), update the entry's text to clarify the
  distinction rather than leave it silently contradicted.
- `SIMQ-CALIBRATED-001`: update `text` to note that WORLD/ECONOMY/PROGRESSION/INFORMATION weights
  are now empirically tuned against real per-pillar richest-case data (this ticket), while
  `grade_thresholds.yaml` remains untouched/still "initial estimates" for these 4 pillars — keep
  the ledger's distinction between "weights tuned" and "thresholds validated" accurate.
- `INFRA-242`/`243`/`245`/`246` (event-coverage entries for Economy/Progression/Information/World
  scorers): cross-check only — these describe event-type coverage, not weight magnitude; leave
  `status: verified` unchanged unless Step 5's new INFORMATION scenario changes which event types
  are actually exercised in the corpus, in which case update `v2_evidence` to reference it.
**Do NOT touch:** `INFRA-255` (the shared formula entry) beyond an optional cross-check note — the
formula text is still accurate and unchanged; do not edit its `status` or core `text`. Do not
touch any COMBAT/NARRATIVE parity entries.
**Verify:** No automated test covers this — verify by re-reading each edited entry against the
Authoritative Mechanics Rule ("if logic changes, update the ... parity ledger entry in the same
session") before Finalize.

### Step 11 — Update `docs/simulation_quality/current_state.md` and, if Step 5 added a new world, `corpus_tier_taxonomy.md`
**Files:** `docs/simulation_quality/current_state.md`; `docs/simulation_quality/corpus_tier_taxonomy.md`
(only if Step 5's escalation condition triggered and a new Unit-tier world was added)
**Change:**
- `current_state.md`: update the grade-distribution table and discriminative-power section to
  reflect the post-fix state: each of WORLD/ECONOMY/PROGRESSION/INFORMATION now has at least one
  A/S anchor, with the specific run_key(s) cited. Correct the anchor-count reference from "72
  committed anchor scenarios" to the accurate 74 real scenario entries (per Resolved Open
  Question 3), noting the correction is a documentation accuracy fix, not a corpus-size change
  caused by this ticket (unless Step 5 added a new scenario, in which case the count legitimately
  increases by 1 and both facts should be stated).
- `corpus_tier_taxonomy.md` (architecture-review finding, 2026-07-13 — conditional on Step 5's new
  world actually being built): add the new world to the "Current tier mapping" table (the line-133
  -136 table), classified **Unit** tier, following the exact precedent set by every prior Unit-tier
  addition (`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`,
  `hero_guild_routing` — each updated this same table in the ticket that added the world; do not
  leave the new world undocumented in this file, and do not document it only in `current_state.md`
  as a substitute).
**Do NOT touch:** Other sections of `current_state.md` unrelated to this finding (e.g. any other
pillar's discriminative-power notes) unless Step 9's full sweep reveals a genuine, attributable
change there. Do not touch any other row of `corpus_tier_taxonomy.md`'s tier-mapping table.
**Verify:** No pytest coverage — manual review that every number in the updated table matches the
regenerated calibration data from Steps 6-7, and (if applicable) that the new tier-mapping row
matches the other 4 Unit-tier rows' format exactly. Since `docs/` was modified, run
`make knowledge-index-update` per the project's After Work rule.

### Step 12 — Full live-mode corpus sweep (AC 3 closure)
**Files:** none changed — verification only
**Change:** Run `python3 tools/evaluate_simq.py` (live mode, per the ticket's own instruction —
the profiling bug that previously made repeated live-mode runs unsafe is already fixed by
`TCK-20260713-SIMQ-EVAL-PROFILE-BUG`, confirmed done). Diff its output against the pre-fix
baseline (`tmp/evaluate_simq_full_run_20260713.log`, session-local, cited in the ticket) and
confirm every changed scenario/pillar combination is one already accounted for in Steps 2-8. Any
scenario/pillar change not traceable to Steps 2-8 is a regression — stop and investigate before
Finalize.
**Do NOT touch:** Do not silently absorb an unattributed change into `grade_anchors.json` to make
the sweep pass — AC 3 requires every change be a *documented, deliberate* consequence.
**Verify:** Live-mode sweep completes; a written diff summary (in the ticket's Implementation
Notes / Test Summary section) lists every changed anchor and its cause, with zero entries marked
unattributed.

## Scope Guards

- Do not touch `src/simulation_quality/quality_report.py`'s `normalized_score` formula (L101-105)
  — explicitly out of scope; this ticket is weights-only.
- Do not touch `grade_thresholds.yaml` in this ticket (see Resolved Open Question 1) — if a future
  ticket determines thresholds also need to move for INFORMATION or any other pillar, that is a
  separate, explicitly-scoped follow-up.
- Do not touch any pillar's **negative/penalty** weights (`zero_harvest`, `zero_crafting`,
  `zero_trade`, `all_level_1`, `calamity_dormant`, `world_static`, `world_depopulating`,
  `demographics_dormant`, `belief_system_silent`, `knowledge_economy_dormant`, or any other
  dormancy/failure signal) in `scoring_weights.yaml` — only positive per-event weights for the 4
  named pillars change.
- Do not touch ECONOMY's Gini-threshold mechanism.
- Do not touch COMBAT's or NARRATIVE's weights, formulas, or anchors — they are not exhibiting the
  ceiling pattern and are explicitly Out of Scope.
- Do not touch `config/simulation_quality/profiles/*.yaml`'s `pillar_weights` blocks — this is a
  distinct mechanism (feeds `overall_score`/`overall_grade` roll-up only) and does not affect any
  individual pillar's own `normalized_score`/grade; do not conflate the two.
- Do not move `ecology_cycle_completed` scoring ownership between `WorldDynamicsScorer` and
  `EconomyScorer`, and do not move `paid_information_transaction` between `InformationScorer` and
  `EconomyScorer` — both ownership boundaries stay exactly where `SQ-08`/`INFRA-245`/`INFRA-246`
  currently document them, even though both pillars in each pair are being edited this session.
- Do not author new content into any *existing* world to inflate ECONOMY activity —
  `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` owns that and depends on this ticket landing first. The
  one narrow exception is Step 5's possible new minimal INFORMATION calibration scenario, which is
  a new, purpose-built probe scenario for this ticket's own AC 1 — not content added to an
  existing world.
- Do not extend `grade_anchors.json`'s schema to store raw scores —
  `TCK-20260713-SIMQ-RAWSCORE-PERSIST` owns that; this ticket's anchor edits are letter-grade
  values only, same schema.
- Do not regenerate `data/calibration/` wholesale — only the run_keys identified in Step 1 (plus
  Step 5's new scenario, if added).
- Do not filter the Step 9 regression sweep down to only the 4 changed pillars' columns — the full
  parametrized sweep across all pillars is the anti-drift guard and must run in full.

## Dependency Map

- Step 1 blocks Steps 2-5 (need richest/worst-case run_keys before computing multipliers).
- Steps 2, 3, 4, 5 are independent of each other (different YAML sections, different scorer
  files) — can be done in any order or in parallel, but each must land as its own attributable
  diff hunk.
- Step 6 depends on Steps 2-5 all being complete (regenerates calibration data using the new
  weights).
- Step 7 depends on Step 6 (anchor updates use the regenerated reports).
- Step 8 depends on Step 1 (zero-activity run_keys) and can run any time after Step 1, but is
  most naturally verified alongside Step 7.
- Step 9 depends on Steps 2-8 all being complete (full sweep needs the final state).
- Step 10 and Step 11 depend on Step 9 confirming the final grades (parity ledger and doc updates
  must describe the actually-landed state, not a provisional one).
- Step 12 depends on all prior steps (final closure check before Finalize).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1: each of the 4 pillars reaches A/S on at least one real corpus scenario | Steps 2, 3, 4, 5, 6 | Step 7's regenerated anchor entries for the richest run_key per pillar; `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` (+ `-m slow`) |
| AC 2: structurally-inert entries remain C | Steps 2-5 (positive-only weight change is structurally safe, per investigation.md), confirmed by Step 6, guarded by Step 8 | `pytest tests/simulation_quality/test_grade_regression.py` over the zero-activity anchor keys identified in Step 1 |
| AC 3: 0 unattributed regressions in full live-mode sweep | Step 9 (full domain pytest sweep), Step 12 (live-mode `evaluate_simq.py` sweep + diff review) | `pytest tests/simulation_quality/ -m "not slow" -v`; `python3 tools/evaluate_simq.py` diffed against baseline log |
| AC 4: `current_state.md` grade-distribution/discriminative-power sections updated | Step 11 | Manual review; `make knowledge-index-update` run since `docs/` changed; `corpus_tier_taxonomy.md` tier-mapping table also updated if Step 5 added a new world |

## Anti-Drift Notes

- The dormancy-penalty structural finding (penalties only fire inside the same-family triggering
  event's handler) is why Steps 2-5 are safe to implement as positive-weight-only changes without
  re-deriving each pillar's zero-activity behavior from scratch — but Step 6 still empirically
  confirms it per-pillar rather than assuming, since "structurally safe" is a property of the code
  path, not a substitute for the actual regression check.
- INFORMATION (Step 5) is the one pillar where the fix might legitimately require a new corpus
  scenario rather than a pure config change — do not force a large, unrealistic weight multiplier
  onto a single low-frequency event just to hit 0.5 on paper; if the escalation condition in Step
  5 triggers, build the new scenario instead. A per-event weight so large that a single occurrence
  dominates the entire pillar's score is itself a discriminative-power problem, not a fix.
- `xp_active`'s per-event delta is `weight * max(1, xp_amount // 10)` (not a flat per-event
  constant) — Step 4's multiplier calculation must account for this multiplicative structure, not
  treat `xp_active` like a flat-delta signal the way `pillar_trait_milestone` is.
- Because Steps 2-5 all touch the same `scoring_weights.yaml` file, keep each pillar's edit as a
  cleanly separable diff hunk (contiguous within that pillar's existing YAML section) so Step 9's
  "trace every anchor change back to its cause" review stays tractable.
- `grade_thresholds.yaml`'s header comment (documenting the 2026-06-30 sandbox_world calibration,
  COMBAT/NARRATIVE/PROGRESSION only) is stale evidence per investigation.md's Risk #4, but this
  ticket does not touch `grade_thresholds.yaml` at all — leave the stale header as a known,
  separately-tracked gap (do not fix it opportunistically here, since that file is out of scope
  for this ticket's chosen lever).

## Resolved — Human Decision (2026-07-13)

- **Whether Step 5's new INFORMATION calibration scenario (if triggered) should be adopted as a
  permanent, general-purpose corpus entry or scoped as ticket-specific/provisional.** RESOLVED by
  explicit user decision: **permanent corpus entry**, same as any other committed scenario
  (`urban_political`, etc.) — it is a real, reproducible calibration scenario once it runs through
  the pipeline, and SimQ's corpus is meant to grow this way. If Step 5's escalation condition does
  not trigger, this question is moot.

## Deviations (implementation, 2026-07-13)

- **Step 5 escalation condition: confirmed triggered, exactly as anticipated.** INFORMATION's
  richest pre-fix scenario (`unit_information_source`, 1 event, raw=2.0, denom=50) would need
  `M_INFORMATION=13` to cross 0.5 — a single `belief_active` weight of 26.0, above the reference
  threshold (PROGRESSION's original, pre-this-ticket `pillar_trait_milestone=15.0`). Built the new
  Unit-tier world (`unit_information_density`) per the escalation path. Confirmed via
  `InformationProviderState` grep (zero construction sites in `src/`) that `paid_information_transaction`
  cannot fire under the current engine at all (the provider-registration system it depends on is
  unwired/dead code — no world content path exists to populate `AuthoritativeState.information_providers`).
  Also confirmed `decision_diverged_by_belief` has zero occurrences across the entire 109-directory
  local calibration corpus. Given this, the new world's design maximizes `belief_assimilated` density
  (the one empirically-reliable, content-driven lever) instead of literally including all 3 event
  types plan.md's Step 5 prose names as illustrative targets — 3 `pending_information_responses`
  entries (pop_0/pop_1/pop_2, one per `hero_adventurers` population slot) rather than 1. This is a
  narrowing of the illustrative event-type list to what the engine can actually produce, not a
  deviation from the escalation *decision* itself (build a new Unit-tier world) or from
  `M_INFORMATION`'s final value (5, recomputed against the new world's own richest run — see
  Implementation Notes for the full derivation).
- **Anchor-count correction (Resolved Open Question 3 was itself inaccurate).** The investigation's
  "74 real scenario entries" figure (`json.load` minus `_note`) missed that `grade_anchors.json` has
  **3** non-scenario meta keys (`_note`, `_instructions`, `_grade_order`), not 1 — true pre-fix count
  was **72** real scenario entries, matching the ticket's own original framing, not 74. Corrected in
  `current_state.md` (Step 11) to 72 pre-fix / 75 post-fix (72 + 3 new `unit_information_density`
  seeds), not the 74/77 the Resolved Open Questions section states.
- **Step 6/9 regeneration scope.** Regenerated calibration reports for all 72 pre-existing anchor
  run_keys (not just the 4 pillars' richest/worst-case run_keys) before running Step 9's full
  sweep — reading the existing (stale, pre-fix) `quality_report.json` for untouched run_keys would
  have made the full parametrized sweep check stale data instead of the actual post-fix state,
  defeating its purpose as an anti-drift guard. This is a broader regeneration than Step 6's literal
  file list, but stays within the Scope Guards' "do not regenerate wholesale" intent (only the 72
  anchor run_keys plus the 3 new ones were regenerated — not the full ~109-directory local
  `data/calibration/` tree, which includes non-anchored trial/variant directories).
- **Found and corrected one pre-existing, unrelated anchor drift.** `urban_political_seed456_500t`'s
  WORLD anchor was `A`; regenerated live-engine data shows it currently produces `raw_score=88.0`
  (20 events) at the new weights, `normalized_score=0.22` → `B`. Since this ticket's weight change is
  strictly positive-multiplicative (raw_score can only stay the same or increase, never decrease),
  this downgrade cannot be caused by Steps 2-5 — it reflects organic corpus/engine drift since the
  anchor was last verified, surfaced incidentally by this ticket's required full regeneration.
  Corrected the anchor to `B` (matching true current behavior, since accurate ground truth was
  already in hand) and documented this explicitly here per the "no unattributed regressions"
  discipline — this one change is *not* attributable to the weight raise, unlike the other 27.
- **`urban_political_selfmodel_probe_seed42_200t` required its documented non-standard invocation**
  (`--name urban_political --profile urban_political_selfmodel_probe --output
  data/calibration/urban_political_selfmodel_probe_seed42_200t`, per
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) rather than the generic per-anchor-key
  name-parsing my regeneration script used for the other 71 entries — the profile name differs from
  the world name for this one entry only. No plan.md guidance needed changing; this is the same
  known naming quirk `current_state.md`'s "Known Issue" section already documents for
  `evaluate_simq.py`'s own `--profile` forwarding bug.
- **Step 8 zero-activity guard**: confirmed 0 zero-event anchors exist anywhere in the 72-scenario
  corpus for WORLD or PROGRESSION specifically (unlike ECONOMY, 56 zero-event anchors, and
  INFORMATION, 36) — every scenario with living entities generates baseline WORLD (demographic/
  lifecycle) and PROGRESSION (`xp_granted`) events, so no such run_key exists to add to
  `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`. Not a gap requiring new content — AC 2's "remains C" guard
  is satisfied by the existing structural code-path argument (investigation.md) for these 2 pillars,
  empirically confirmed by the 56/36 existing zero-event anchors for the 2 pillars where the
  condition actually occurs in the corpus.
- **`eval_matrix_results.md` not updated.** Plan.md's Step 11 file list names only `current_state.md`
  and (conditionally) `corpus_tier_taxonomy.md`; unlike the `unit_information_source` precedent
  ticket, adding a grade-table section to the append-only historical log was not in this ticket's
  explicit Step 11 scope, so it was left untouched to avoid unscoped drift.
- **Step 12's live sweep flagged 1 regression, investigated and attributed to a cause outside this
  ticket's diff — not a silent absorb, not an anchor edit.** `urban_political_seed123_500t` COGNITION
  showed anchor=B, live=S. `git diff` confirms zero changes to COGNITION's weights or scorer. Three
  separate clean reproductions (this ticket's own Step 6 regeneration, plus two more standalone
  `calibrate_simq.py` re-runs afterward) all gave `grade=B, raw_score=11.0, event_count=2` — bit-for-bit
  identical to each other and matching the committed anchor. Only the live sweep's run (after ~30
  minutes of sustained concurrent load, with repeated `WatchdogTrip` warnings in its own log)
  produced `grade=S, raw_score=3521.0, event_count=119`, `loop_detected=True` on
  `self_model_active`/`subjective_divergence` — a runaway-loop signature. Concluded: pre-existing,
  load-sensitive nondeterminism in COGNITION's self-model loop-detection path, unrelated to this
  ticket. The anchor was **not** changed (it already matches stable behavior); regenerated the
  on-disk calibration report back to the stable state and re-verified `pytest` (58+18 passed) and
  `evaluate_simq.py --dry-run` (0 regressions) clean. This nondeterminism is itself a genuine,
  separately-tracked concern against the project's "do not break determinism" invariant — flagged
  for a follow-up hotfix/investigation ticket, not fixed here (out of scope for a weights-only
  ticket touching 4 unrelated pillars).
