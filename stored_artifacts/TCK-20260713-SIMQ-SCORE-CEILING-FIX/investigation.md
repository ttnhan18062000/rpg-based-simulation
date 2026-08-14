---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-SCORE-CEILING-FIX
artifact_type: investigation
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260713-SIMQ-SCORE-CEILING-FIX

## Current Behavior

### The normalized_score formula (the shared mechanism all 4 pillars run through)

`src/simulation_quality/quality_report.py:101-105`:

```python
last_event_tick = snap.get("last_event_tick", 0)
floor_tick = max(1, effective_tick // 4)
effective_denominator = max(floor_tick, last_event_tick) if last_event_tick > 0 else effective_tick
normalized_score = snap["raw_score"] / effective_denominator
```

This is identical for all 10 pillars — confirmed by `docs/parity_ledger/infrastructure.yaml`
`INFRA-255` (primary formula entry) and its secondary per-pillar refs (`WORLD-110` in
`world_dynamics.yaml`, a COMBAT entry in `combat_movement.yaml` ~line 3034). The formula divides
accumulated `raw_score` by whichever tick the pillar was last active at (floored at 25% of run
length). **This is not itself pillar-specific** — the ceiling is a per-event-weight problem, not a
formula problem, exactly as the ticket's own framing states and as `WORLD-110` independently
confirms: "WORLD does not receive S-inflation because its events fire continuously throughout the
run" (i.e. for continuously-active pillars, `last_event_tick ≈ current_tick`, so the divisor is
large regardless of weight scale).

### Per-pillar weight comparison (`config/simulation_quality/scoring_weights.yaml`)

| Pillar | Positive-signal delta range | Notable high end |
|---|---|---|
| NARRATIVE (reference — reaches A/S routinely, distribution 7 S / 52 A / 9 B / 4 C) | 4 – 15 | `scenario_resolved`=15, `quest_resolved`=10 |
| WORLD | 1 – 8 | `calamity_active`=8, `boss_active`=6 |
| ECONOMY | 1 – 4 | `crafting_active`=4, `harvest_active`=3, `trade_active`=3 |
| PROGRESSION | 1 – 15* | `pillar_trait_milestone`=15, `level_milestone`=8, `skill_growth`=5 — *but* `xp_active`=1 (the highest-frequency event, `+1 per 10 XP`) dominates raw event count and pulls the average down |
| INFORMATION | 2 – 6 | `subjective_divergence`=6, `info_has_impact`=5 |

NARRATIVE's per-event ceiling deltas (10-15) are 2-4x the Phase-1 pillars' typical per-event
deltas (1-4), and NARRATIVE's milestone events (`scenario_resolved`, `quest_resolved`) fire near
the *end* of a run — which, combined with the `last_event_tick` denominator capturing that late
tick, still yields a favorable ratio because the numerator (15, 10) is large relative to even a
large denominator. COMBAT (also "always-on", 1 A / 46 B / 25 C in the corpus) sits between:
smaller per-event deltas (1-3) than NARRATIVE, larger than the Phase-1 pillars in several cases,
and shows the same partial-ceiling shape but with at least one real A anchor — the ticket's own
"not exhibiting the same pattern" framing for COMBAT is corroborated by the corpus distribution,
not just the raw-score spot check.

### Per-pillar scorer logic (all four read `self.weights[...]` — no hardcoded deltas, confirms
§4.8 contract compliance)

- **`src/simulation_quality/scorers/world_dynamics.py`** (`WorldDynamicsScorer`, `EVENT_TYPES` at
  L17-33): 15 event types, all EVENT_TYPES-driven, deltas 1-8. `ecology_cycle_completed` is scored
  here (not `EconomyScorer`) per the `SQ-08` conflict note (`INFRA-246`).
- **`src/simulation_quality/scorers/economy.py`** (`EconomyScorer`, `EVENT_TYPES` at L18-31): 10
  distinct event types (`INFRA-242`), deltas 1-4. Two structural notes relevant to the "must not
  destabilize inert C's" acceptance criterion:
  - **`zero_harvest`/`zero_crafting`/`zero_trade` penalties only fire *on a triggering event of the
    same type*** (e.g. `zero_harvest` at L70-80 only evaluates inside the `resource_harvested`
    branch). A world with **zero** harvest events ever never receives the `zero_harvest` penalty at
    all — it simply accrues `raw_score=0` from that signal, same net effect as if the penalty had
    fired, but through the "no events" path rather than the "penalized" path. This matters for the
    fix: raising the *positive* `harvest_active`/`crafting_active`/`trade_active` weights cannot
    accidentally turn a truly-zero-activity world into a non-zero score, because with zero
    triggering events there is nothing to multiply — `raw_score` stays exactly `0.0`, and
    `normalized_score` falls back to `0 / current_tick = 0.0` (grade C per band, confirmed by the
    72-anchor corpus: 60/72 ECONOMY anchors are already C, consistent with a real content gap, not
    a scoring floor).
  - Same structural pattern in `progression.py` (`all_level_1` only fires on a `level_up` event —
    L61-78), `world_dynamics.py` (`calamity_dormant`/`world_static`/`world_depopulating`/
    `demographics_dormant` all fire on a triggering event of the same family), and
    `information.py` (`belief_system_silent`/`knowledge_economy_dormant` — same pattern). This is a
    load-bearing property for the fix: **raising positive per-event weights is structurally safe
    against inflating zero-activity worlds**, because those worlds never enter the scorer's
    `score()` method for that signal family at all.
- **`src/simulation_quality/scorers/progression.py`** (`ProgressionScorer`, `EVENT_TYPES` at
  L14-23): 8 event types (`INFRA-243`). `xp_active` is the highest-frequency event
  (`xp_granted`, delta = `weights["xp_active"] * max(1, xp_amount // 10)`, L55-59) but has the
  lowest base weight (1.0) — a world with steady small XP grants (the common case) accumulates
  slowly per event even though it fires often.
- **`src/simulation_quality/scorers/information.py`** (`InformationScorer`, `EVENT_TYPES` at
  L17-25): 7 event types (`INFRA-245`), deltas 2-6 — the narrowest positive range of the four, and
  the pillar with the smallest corpus footprint (max observed 0.04 normalized, a single-event run).

### Why the richest observed runs still cap so low — worked example

Ticket's own evidence: ECONOMY's richest run (69 scored events) reached only 0.16 normalized. If
those 69 events were a realistic mix (mostly `harvest_active`=3/`trade_active`=3/`gold_flow`=1,
occasional `crafting_active`=4), a plausible raw_score is on the order of 100-150. For
`normalized_score` to land at 0.16, `effective_denominator` must be roughly 625-940 — i.e. this was
very likely a long run (last_event_tick in that range, well past the 200-500t range most anchors
use). This is consistent with `INFRA-255`'s documented "pure `effective_denom` dilution" pattern
already seen for FACTION (`unit_faction_tension_seed42`: raw_score/event_count byte-identical
145.0/29 across 1000t→2000t; normalized_score halves as floor_tick doubles). **The same dilution
mechanic applies to Phase-1 pillars, but they have no per-event weight margin to absorb it** —
NARRATIVE's 10-15-point milestone events can survive a large denominator and still clear 0.5; the
Phase-1 pillars' 1-4-point events cannot.

## Mechanics / Engine Constraints

- `quality_scoring_contract.md` §4.4 (Normalized Score) — the formula itself, and its own
  documented rationale (`TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`) for why the floor/last-event-tick
  divisor exists (prevents both post-event dilution *and* initialization-burst S-inflation). Any
  weight change must be evaluated against this formula as fixed — the ticket's Out of Scope
  explicitly excludes touching the formula itself, only per-event weights and/or §4.5 thresholds.
- §4.5 (Health Grades) — the grade bands (S >2.0, A 0.5-2.0, B 0.0-0.5, C -0.5-0.0, D -1.0--0.5, F
  <-1.0) are the other lever explicitly in scope. §4.5's own history note records that the initial
  calibration (`TCK-20260630-SIMQ-RECALIBRATE`) validated thresholds only against COMBAT/NARRATIVE/
  PROGRESSION on `sandbox_world` with most pillars producing **zero signal** (pre-P0-A) — i.e. the
  4 Phase-1 pillars' thresholds were never actually calibrated against real per-pillar data; they
  were carried over as "initial estimates" (confirmed by `SIMQ-CALIBRATED-001`'s own text). This
  substantially lowers the risk of touching thresholds for these 4 specifically — they were never
  empirically validated for these pillars in the first place, unlike NARRATIVE/COMBAT which have a
  documented calibration basis.
- §4.8 (Data-Driven Scoring Weights) — hard constraint: weight changes MUST be config-file edits
  (`scoring_weights.yaml`, `grade_thresholds.yaml`), never inline scorer literals. Confirmed: none
  of the four scorer files contain numeric literals for deltas — full compliance already in place,
  so the fix is a pure config edit plus (if needed) a documented threshold edit, no scorer code
  changes anticipated unless investigation during implementation finds a scorer logic bug (none
  found here).
- §14 (Non-Goals) — per-entity profiles, historical run comparison, real-time alerting, ML anomaly
  detection, automated config suggestion are out of scope; not implicated by this ticket.

## Parity Ledger Overlap

All entries below are `status: verified`, `priority: P1` — none are P0, so none strictly *require*
a passing `test_path` as a blocking gate, but all will need `v2_evidence`/`text` updates once
weights or thresholds change, per the Authoritative Mechanics Rule ("if logic changes, update the
... parity ledger entry in the same session").

| ID | File | Why it's touched |
|---|---|---|
| `INFRA-255` | `infrastructure.yaml` | Primary cross-pillar `normalized_score` formula entry. Formula itself is NOT changing (out of scope), but this entry's evidence describes pillar behavior under the *current* weight scale (e.g. its FACTION dilution example) — worth a cross-check note, not necessarily an edit, since the formula text is still accurate. |
| `WORLD-110` | `world_dynamics.yaml` | **Directly contradicted by this ticket's premise if the fix succeeds.** Currently states "WORLD holds B post-fix as expected" for `dungeon_crawl_seed42_500t` (norm=0.440) and frames B as the *correct, expected* ceiling for a continuously-active WORLD pillar. If the fix raises WORLD's ceiling (via weights and/or thresholds) such that this same scenario now grades A/S, this entry's text is stale and must be updated to reflect the new expected grade — this is the single clearest "must-update" parity entry. |
| `INFRA-242` | `infrastructure.yaml` | `EconomyScorer` event-type coverage (§5 rule compliance) — not weight magnitudes. Should remain `verified` unmodified unless scorer logic changes (not anticipated), but flag for cross-check since it's the anchor entry for the pillar under repair. |
| `INFRA-243` | `infrastructure.yaml` | `ProgressionScorer` coverage — same as above. |
| `INFRA-245` | `infrastructure.yaml` | `InformationScorer` coverage — same as above. |
| `INFRA-246` | `infrastructure.yaml` | `WorldDynamicsScorer` coverage — same as above. |
| `SIMQ-CALIBRATED-001` | `infrastructure.yaml` | Explicitly states grade thresholds are "initial estimates" and that "calibration progressively operational" — this is the entry that should absorb the outcome of Phase 1a's threshold-tuning decision (if thresholds change) or be updated to note the 4 pillars are now weight-tuned rather than still "initial estimates" (if only weights change). Likely candidate for a follow-up `text`/`v2_evidence` update regardless of which lever is chosen. |

No P0 entries found in the affected scope — reduces blocking risk, but the Authoritative Mechanics
Rule's "same session" update requirement still applies to whichever entries actually change.

## Prior Work

- **`TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`** (`stored_artifacts/`) — the last time the
  `normalized_score` *formula* itself changed (introduced `floor_tick`/`last_event_tick`). Directly
  relevant precedent for how a shared-formula change requires a full corpus re-anchor — this
  ticket's own Scope section calls that out as a certainty ("shared weight constants can move
  grades corpus-wide"). This ticket does NOT touch the formula, only weights/thresholds, but the
  re-anchor discipline established there (re-run calibration, diff every anchor, document each
  change) is the template to follow.
- **`TCK-20260630-SIMQ-RECALIBRATE`** (referenced in §4.5, not confirmed to have a
  `stored_artifacts/` folder under that exact name in this checkout — the ticket ID referenced in
  the contract doc doesn't appear in the `stored_artifacts/` listing verbatim; likely archived
  under a different ID or folded into an early batch. Flagged as a minor gap — the contract doc's
  citation could not be independently verified against a stored artifact, only against its own
  prose in §4.5.) This was the original threshold-validation pass; its finding that 7 of 10 pillars
  had **zero signal** on the calibration world at the time is the direct historical reason the
  Phase-1 pillars' thresholds were never truly validated against real activity.
- **`TCK-20260713-SIMQ-EVAL-PROFILE-BUG`** — already in `tickets/done/`, hotfix tier (no staging
  artifacts, self-evident per the workflow rule). This was the ticket's own named prerequisite
  ("should land first so this ticket's repeated live-mode sweeps aren't run against a tool with a
  known silent-corruption bug") — **confirmed resolved**, so `tools/evaluate_simq.py` live mode is
  safe to use repeatedly during this ticket's implementation.
- **`docs/simulation_quality/eval_matrix_results.md`** (append-only historical batch log) contains
  concrete per-scenario ECONOMY event-count/grade data points useful as best/worst-case candidates,
  e.g. line ~947: a `0→24 events` ECONOMY jump from C to B ("genuine new economic activity
  accumulating past tick 200 ... not a dilution artifact") and line ~324/1254: multiple confirmed
  zero-ECONOMY-event C anchors (`0 events, all 3 seeds`) — good structurally-inert worst-case
  candidates for the AC's "must remain C" check.
- The **corpus itself already contains named best-case candidates** per `current_state.md`'s
  discriminative-power table: a 69-event ECONOMY run, a 38-event WORLD run, a 46-event PROGRESSION
  run, and (worst case, effectively) a 1-event INFORMATION run — the ticket does not name which
  anchor keys these are; identifying the exact `run_key` for each (cross-referencing
  `data/calibration/*/quality_report.json` event counts against these numbers) is unstarted
  investigation work, flagged below.

## Risks and Open Questions

1. **Blocking / needs implementer decision, not pre-decidable here (per the ticket's own
   Assumptions section):** whether to raise weights, lower thresholds, or both, per pillar. The
   investigation above supports "raise weights" as the lower-risk lever for ECONOMY/PROGRESSION/
   WORLD (structurally safe against inflating zero-activity worlds, per the "penalties only fire on
   a triggering event" finding above) — but does not rule out threshold-lowering for INFORMATION,
   whose positive-delta range (2-6) and observed max (0.04) suggest even a large weight multiplier
   might not be enough on its own if the pillar's real-world event *density* is simply very low
   (1-event runs). This is exactly the "genuinely worst-case scenario" construction the ticket's
   Scope requires and was not done as part of this investigation (requires running/inspecting
   specific calibration reports, an implementation-phase activity, not investigation-phase).
2. **Exact best-case/worst-case `run_key` identification is unstarted.** The 69/38/46/1-event
   numbers are cited in `current_state.md` and the ticket, but neither document names the specific
   anchor key. The implementer's first concrete step should be grepping
   `data/calibration/*/quality_report.json` for `event_count` values matching these numbers per
   pillar (109 calibration directories exist in `data/calibration/`, confirmed present in this
   checkout — not just session-local `tmp/` artifacts, so this is fully reproducible).
3. **`tests/simulation_quality/fixtures/grade_anchors.json` re-anchor scope is corpus-wide, not
   just the 4 pillars.** Because `normalized_score` is per-pillar-independent (each pillar's raw
   score and denominator are its own), changing WORLD/ECONOMY/PROGRESSION/INFORMATION weights only
   affects those 4 pillars' columns in each of the 75 anchor entries (72 scenarios + `_note`,
   confirmed via `json.load` — actually 75 keys total including the `_note` field, so 74 real
   scenario entries, one more than the ticket's stated "72 committed anchor scenarios"; minor
   discrepancy, does not change scope, worth reconciling during implementation). NARRATIVE/COMBAT/
   other pillars' anchors do not need re-verification from this specific change, narrowing the
   "full regression sweep" to those 4 pillars' cells specifically — though the AC's "0 unattributed
   regressions" requirement means the full `evaluate_simq.py` sweep must still run (to catch any
   unexpected cross-pillar interaction), just that manual review can focus on the 4 changed
   columns.
4. **`grade_thresholds.yaml`'s header comment is itself now stale evidence** — it documents the
   2026-06-30 sandbox_world calibration (COMBAT/NARRATIVE/PROGRESSION only, others "0 events").
   Whatever is decided for thresholds, this header comment should be updated or annotated to avoid
   future confusion about what thresholds are actually calibrated against.
5. **`_within_band` gives ±1 letter tolerance** (`test_grade_regression.py` L140-151) — a grade
   that jumps 2+ bands (e.g. C→A) under the fix WILL fail the existing regression test even before
   any anchor is manually updated, which is expected and desired (forces a deliberate anchor edit
   per the AC), but means the implementer should expect `pytest tests/simulation_quality/
   test_grade_regression.py` to fail loudly and immediately after any weight/threshold edit, before
   `grade_anchors.json` is updated — not a bug, the intended detection mechanism.

## Anti-Drift Hazards

- **Do not touch the `normalized_score` formula itself** (`quality_report.py` L101-105) —
  explicitly out of scope per the ticket; the fix is weights (`scoring_weights.yaml`) and/or
  thresholds (`grade_thresholds.yaml`) only. Any temptation to "fix" the floor/denominator instead
  of the weights is scope creep into a decision (`TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`) that was
  deliberately made and is working as intended for other pillars (WORLD-110, INFRA-255).
- **Do not touch ECONOMY's Gini-threshold mechanism, or COMBAT/NARRATIVE's formulas** — explicit
  Out of Scope; these are not exhibiting the ceiling pattern.
- **Do not author new content into any world** — that is `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`
  (currently sitting in `tickets/todos/simq-scoring-improvement/`, depends on this ticket landing
  first). A natural but wrong instinct when looking at ECONOMY's C-heavy distribution is to add
  harvest/craft/trade events to worlds — that is out of scope here.
- **Do not extend `grade_anchors.json`'s schema to store raw scores** — that is
  `TCK-20260713-SIMQ-RAWSCORE-PERSIST` (also in the same todos folder), explicitly sequenced to
  reuse this ticket's re-anchor pass but a separate concern (schema/regression-test change). This
  ticket's re-anchor pass should stay a same-schema letter-grade update.
- **Watch for uniform/blanket weight inflation.** The AC explicitly requires that the fix "move the
  ceiling for genuinely active scenarios, not just inflate every score uniformly" — a
  multiply-every-weight-by-N approach would satisfy the letter of "raises the ceiling" but is
  exactly the kind of undifferentiated change the AC guards against; per-signal, per-pillar
  reasoning (as this investigation began above) is expected, not a single global multiplier.
  Concretely: because zero-activity worlds structurally cannot be affected by raising *positive*
  weights (see Current Behavior's structural note), a uniform multiplier applied only to positive
  deltas would actually satisfy both the letter and spirit of the AC for the "stays C" half — but
  negative/penalty weights must NOT be scaled by the same multiplier without separate
  justification, since several penalties (e.g. `zero_harvest`=-20, `ecology_broken`=-25,
  `conservation_violated`=-50) are calibrated to be catastrophic relative to the *current* positive
  scale; scaling positives up without re-examining the positive:negative ratio could make it harder
  to ever recover from a legitimate dormancy penalty into a real A/S, undermining the discriminative
  power the fix is meant to add.
- **When editing `tests/simulation_quality/fixtures/grade_anchors.json`, edit only the 4 affected
  pillars' entries per anchor** unless the full sweep genuinely shows movement elsewhere — the file
  has 74 scenario entries; a careless full-file regeneration risks silently changing NARRATIVE/
  COMBAT/FACTION/etc. anchors that should be untouched by this fix, defeating the "0 unattributed
  regressions" requirement.
- **`config/simulation_quality/profiles/*.yaml`'s `pillar_weights` block is a distinct mechanism
  from the per-signal weights this ticket edits — verified by reading `weights.py` L109-110 and
  `quality_report.py` L106/119-123.** `ScoringWeights.pillar_weight(pillar_id)` only feeds into
  `overall_score`/`overall_grade` (the cross-pillar weighted-average roll-up, contract §4.6) — it
  does **not** scale into a pillar's own `normalized_score` or per-pillar grade. This means a
  profile like `config/simulation_quality/profiles/dungeon_crawl.yaml` (confirmed contents:
  `COMBAT: 2.0, FACTION: 0.1, SOCIAL: 0.5, INFORMATION: 0.5`) changes how much INFORMATION
  contributes to that scenario's *overall* score, but does not affect whether INFORMATION itself
  grades C vs A under this ticket's fix. Do not conflate the two when reasoning about "will this
  world's INFORMATION grade change" — the answer only depends on `scoring_weights.yaml` (per-signal)
  and `grade_thresholds.yaml`, not on any profile's `pillar_weights` block. (Correcting an initial
  misreading during this investigation — flagged here specifically so the implementer doesn't
  repeat it.)
