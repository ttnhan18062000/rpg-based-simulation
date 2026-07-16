---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Investigation — TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP

## Current Behavior

### `tests/simulation_quality/test_grade_regression.py` — score-tolerance mechanism (baseline verified this session)

- `SCORE_TOLERANCE_ABS_FLOOR = 0.05`, `SCORE_TOLERANCE_REL_PCT = 0.20` (lines 46-47) — global
  defaults.
- `SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float]` (lines 75-79) — **confirmed by
  direct read this session to be exactly 3 entries**, matching the ticket's baseline
  assumption and the orchestrator's pre-confirmation:
  - `("urban_political_seed123_1000t", "ECONOMY"): 0.2878`
  - `("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351`
  - `("urban_political_seed123_1000t", "NARRATIVE"): 0.3197`
- `_score_tolerance_kwargs(run_key, pillar)` (lines 82-86) — returns `{"abs_floor": ...}` if a
  `(run_key, pillar)` pair is in the table, else `{}` (module defaults apply).
- `_within_score_tolerance(actual_score, anchor_score, abs_floor=..., rel_pct=...)` (lines
  212-225) — `True` iff `abs(actual - anchor) <= max(abs_floor, rel_pct * abs(anchor))`.
- `test_grade_within_anchor_band` (line 269) / `test_grade_within_anchor_band_long_run` (line
  322, `@pytest.mark.slow`) both call `_within_score_tolerance(actual_score, anchor_score,
  **_score_tolerance_kwargs(run_key, pillar))` — the call site any new table entry is
  automatically wired into (no code change beyond the table itself).
- `test_score_tolerance_override_table_scoped_to_named_pillars` (lines 616-635) — hard-coded
  `set(SCORE_TOLERANCE_OVERRIDES.keys()) == {...}` (3-tuple set today) **must be updated** to
  whatever final entry set this ticket lands, or the test fails immediately.
- `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (lines 638-652) —
  self-adjusting; no edit required regardless of table size.
- `SLOW_ANCHOR_KEYS` (line 174) includes `"urban_political_seed123_1000t"` — the parametrized
  long-run case is real and collected, not hypothetical.

### `tests/unit/worldassembly/test_corpus_diversity.py` — existing guard coverage for this anchor

- `test_urban_political_seed123_1000t_social_economy_grade_stability` (line 933) is the **only**
  `grade_stability`-style guard for this anchor — covers exactly `{"SOCIAL": abs_floor=2.9568,
  "ECONOMY": abs_floor=0.2878}` (lines 995-998). Confirmed via the parent ticket's grep and
  independently re-confirmed this session (`grep -n "urban_political_seed123_1000t"` in this
  file returns only this one guard function).
- Per `tickets/done/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP.md` and
  `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md:61,116,124-125`,
  this anchor's **originally-scoped pillars in the 14-anchor sweep were ECONOMY and SOCIAL
  only** — COMBAT, PROGRESSION, WORLD, and COGNITION were never checked for this anchor before
  this ticket's investigation (NARRATIVE was added by the immediate parent ticket
  `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`). AGENCY and INFORMATION were never
  named as at-risk by any prior ticket in this chain.

### `src/simulation_quality/scorers/` — pillar scorer mechanism confirmation

- `src/simulation_quality/scorers/cognition.py` — `CognitionScorer.EVENT_TYPES` (line 17)
  includes `"decision_divergence_detected"` (line 21), handled at `score()` line 95. This
  scorer is a pure per-event accumulator — no internal randomness, no wall-clock dependency.
- `src/observability/event_extractor.py:477-496` — **`decision_divergence_detected`'s
  construction confirmed read this session**: unlike `hero_death_unrecorded` (a
  this-tick-vs-prior-tick state-transition diff), `decision_divergence_detected` is
  **re-evaluated fresh every tick** from the entity's *current* strategic state alone (`if
  _top_urgency > 0.7 and _top_kind == "danger": ... if _pk2 in _NON_SURVIVAL_PROJECT_KINDS:
  events.append(...)`) — there is no prior-tick comparison and no dedup/one-shot gate. This
  directly confirms `INFRA-273`'s explicit distinction between COGNITION's "refire" mechanism
  (mechanism 1: no dedup gate, re-evaluated every tick) and the "cascading divergence"
  mechanism (mechanism 2: this-tick-vs-prior-tick diff, applies to SOCIAL/COMBAT/PROGRESSION/
  NARRATIVE/WORLD only). **COGNITION's variance is architecturally unbounded per-tick refire,
  not bounded per-transition cascading — a materially different shape from the 5 pillars
  `INFRA-273` already names.** See Risks and Open Questions below for why this matters for the
  remedy choice.
- `src/simulation_quality/scorers/social.py` — `SocialScorer.PILLAR_ID = PillarId.SOCIAL` (line
  17); confirmed present, read-only reference, no defect found.

### `tools/calibrate_simq.py` — calibration draw generation (used directly this session)

- `--name`, `--seed`, `--ticks`, `--output` CLI args (lines 296-311) confirmed functional;
  `--output <path>` redirects only the `quality_report.json` write location, not the
  intermediate `data/runs/run_<ts>_<pid>/` engine-run JSONL directory (always written under
  the default `data/runs/` regardless of `--output`).

### `src/engine/kernel.py` — F6 root cause (read-only reference, confirmed out of scope, not modified)

- Tick-budget watchdog (`kernel.py:420-442`) and mid-tick emergency throttle
  (`kernel.py:574-601`) — real wall-clock (`time.perf_counter_ns()`) per-tick budget
  enforcement; drops resolution-queue work items when a tick exceeds budget. Confirmed present
  at cited line ranges via `docs/audits/D06_longrun_health.md` §F6 (cross-checked, not
  independently re-read line-by-line this session since it is explicitly out of scope and the
  parent ticket's investigation already verified these line numbers).

## Fresh Evidence Gathered This Session — 8 Independent Draws (exceeds the 5+ AC minimum)

All 8 draws run via `.venv/bin/python3 tools/calibrate_simq.py --name urban_political --seed
123 --ticks 1000 --output <distinct scratch path>` (real throttled `Kernel`, no `audit_mode`),
each to a non-colliding output path, inspected, then `data/runs/` cleaned afterward (`--output`
does not write to `data/calibration/`, so no manual cleanup was needed there — confirmed
`data/calibration/urban_political_seed123_1000t/` already existed pre-session from the parent
ticket's own Step 1 regen and was left untouched, not overwritten or deleted).

### Per-draw, per-pillar `normalized_score` table

| Pillar | Anchor | Draw1 | Draw2 | Draw3 | Draw4 | Draw5 | Draw6 | Draw7 | Draw8 |
|---|---|---|---|---|---|---|---|---|---|
| COGNITION | 0.0440 | 0.0120 | 0.0120 | **0.4380** | 0.0120 | 0.0120 | **1.6159** | 0.0120 | 0.0120 |
| AGENCY | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| COMBAT | 0.1090 | 0.1140 | 0.1150 | 0.1130 | 0.1170 | 0.1140 | 0.1180 | 0.1150 | 0.1130 |
| FACTION | 0.5800 | 0.5800 | 0.5800 | 0.5800 | 0.5800 | 0.5800 | 0.5800 | 0.5800 | 0.5800 |
| ECONOMY | 0.6564 | 0.5239 | 0.5327 | 0.5327 | 0.6564 | 0.6564 | 0.5150 | 0.6564 | 0.6564 |
| PROGRESSION | 0.4451 | 0.4451 | 0.4451 | 0.4451 | 0.4602 | 0.4451 | 0.4602 | 0.4602 | 0.4451 |
| SOCIAL | 17.9655 | 20.3390 | 15.6840 | 21.1790 | 18.2660 | 16.1090 | 15.4620 | 17.5040 | 16.0330 |
| INFORMATION | 0.0400 | 0.0400 | 0.0400 | 0.0400 | 0.0400 | 0.0400 | 0.0400 | 0.0400 | 0.0400 |
| WORLD | 0.1540 | 0.1460 | 0.1500 | 0.1420 | 0.1540 | 0.1580 | 0.1500 | 0.1540 | 0.1580 |
| NARRATIVE | 0.6603 | 0.5461 | 0.5060 | 0.5800 | 0.6002 | 0.5411 | 0.6603 | 0.5802 | 0.5661 |

Bold = exceeds anchor by a magnitude qualitatively distinct from the rest of that pillar's
sample (COGNITION draws 3 and 6 only — see below). All grade values stayed within ±1
`GRADE_ORDER` band of their anchor grade on every draw for every pillar (verified directly;
zero band failures across all 80 pillar/draw data points) — consistent with every prior ticket
in this chain's finding that the band check has never been the failure mode for this anchor.

### Per-pillar deviation-vs-tolerance determination

Current tolerance = override `abs_floor` if one exists for `(run_key, pillar)`, else
`max(0.05, 0.20 * |anchor|)`. Max deviation computed against the 8 fresh draws above (and,
where relevant, combined with previously-recorded independent evidence for the same
`(run_key, pillar)` pair — cited explicitly per pillar below).

| Pillar | Current tolerance | Max deviation (this session, draw) | Fails current tolerance? | Verdict |
|---|---|---|---|---|
| COGNITION | 0.0500 (default) | 1.5719 (draw6) | **YES** — 2/8 draws (draw3: 0.394, draw6: 1.5719) | **NEEDS REMEDY — see Open Question #1, not a plain override** |
| AGENCY | 0.0500 (default) | 0.0000 (all) | No | PASS — no override needed |
| COMBAT | 0.0500 (default) | 0.0090 (draw6) | No | PASS — no override needed |
| FACTION | 0.1160 (default) | 0.0000 (all, bit-identical every draw) | No | PASS — no override needed |
| ECONOMY | 0.2878 (existing override) | 0.1414 (draw6) | No | PASS — existing override remains adequate, untouched |
| PROGRESSION | 0.0890 (default) | 0.0151 (draw4/6/7) | No | PASS — no override needed |
| SOCIAL | 3.5931 (default) | 3.2135 (draw3), **3.8485 combined with 3 historical draws from `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`'s investigation.md** | This session alone: No (3.2135 < 3.5931). Combined 11-draw evidence: **YES** | **NEEDS OVERRIDE — see below** |
| INFORMATION | 0.0500 (default) | 0.0000 (all) | No | PASS — no override needed |
| WORLD | 0.0500 (default) | 0.0120 (draw3) | No | PASS — no override needed |
| NARRATIVE | 0.3197 (existing override) | 0.1543 (draw2) | No | PASS — existing override remains adequate, untouched |

**Evidence pointers**: raw `quality_report.json` files for all 8 draws were generated this
session at `.venv/bin/python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks
1000 --output <scratch>/draw{1..8}`, inspected via direct `normalized_score` extraction, then
`data/runs/` was cleaned (`rm -rf data/runs/*`) per the environment note; the underlying
`quality_report.json` files themselves are in the session's scratch directory, not the repo, so
a re-run is required to independently re-verify (deterministic seed/ticks but **not**
deterministic *output*, per F6 — a re-run will show similar-but-not-identical numbers).

### COMBAT, PROGRESSION, WORLD — confirmed FINE despite `INFRA-273` naming them

`INFRA-273` names COMBAT, PROGRESSION, and WORLD (alongside SOCIAL and NARRATIVE) as sharing the
confirmed cascading-divergence mechanism. This sweep is the first time any of these three has
actually been checked against real fresh draws for **this specific anchor**
(`urban_political_seed123_1000t`). All three show small, well-bounded deviation (max 0.009,
0.0151, 0.012 respectively) safely inside the default tolerance — `INFRA-273`'s mechanism claim
is architecture-level (event_extractor.py's delta-gating applies to all 5 pillars' event types
uniformly), but this anchor's specific *magnitude* of exposure for these 3 pillars is small.
This is a real, useful negative result, not an absence of investigation.

### SOCIAL — combined evidence across 2 independent sessions

This session's 8 fresh draws alone do **not** reproduce the exceedance the parent ticket
(`TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`) disclosed (max deviation 3.2135,
under the 3.5931 default width). However, that parent ticket's own investigation.md recorded 3
independent fresh draws with SOCIAL deltas `1.8805` (pass), `1.0275` (pass), and **`3.8485`
(fail — exceeds the then-and-now-unchanged default width of 3.5931 by 0.2554)**. Combining all
11 known independent draws for this `(run_key, pillar)` pair (3 historical + 8 this session),
the max deviation is **3.8485**, from the historical draw. Per the ticket's own Scope
instruction to check "against grade_anchors.json... default or already-overridden" using "real
evidence," and consistent with how the existing NARRATIVE override was itself derived by
combining 3 historical + 3 fresh draws (6 total) rather than only the most-recent session's
data, the responsible evidence-based determination is: **SOCIAL genuinely needs an override**,
using the combined 11-draw evidence base, not just this session's 8-draw subset in isolation.

`abs_floor = round(1.3 * 3.8485, 4) = 5.003` (anchor not re-centered — matches the ECONOMY/
NARRATIVE precedent on this same anchor, not the frontier_marches-NARRATIVE re-centered
precedent; the original anchor 17.9655 is not itself an outlier relative to the 11-draw spread).
`default_width` for this anchor/pillar is `3.5931`; `5.003 > 3.5931` — satisfies the anti-drift
guard's widen-only invariant.

Cross-check: does `5.003` also satisfy the existing `grade_stability` guard's own SOCIAL
`abs_floor=2.9568` (`test_corpus_diversity.py:996`)? No comparison needed — that guard checks a
**3-trial mean**, not a single-draw max deviation; the two floors serve different statistical
purposes (mirrors how ECONOMY's guard `abs_floor=0.2878` and the override table's identical
`0.2878` value happen to coincide only because ECONOMY's derivation reused the guard's floor
verbatim — SOCIAL's guard floor was derived differently and is not expected to match this
override's single-draw-oriented floor).

## Mechanics / Engine Constraints

- `docs/audits/D06_longrun_health.md` §F6 (confirmed present, cross-checked against parent
  ticket's line citations `kernel.py:420-442`, `kernel.py:574-601`) — documented, intentional
  engine behavior: wall-clock tick-budget watchdog/throttle drops resolution-queue work items
  under real timing pressure, independent of seed/RNG. Not contradicted or extended by this
  investigation's findings; COGNITION's refire mechanism and the cascading-divergence mechanism
  are both downstream consequences of the *same* root throttle behavior, just through two
  architecturally different event-construction shapes in `event_extractor.py`.
- `docs/engine/kernel.md` §"Emergency Throttling" — canonical hash `"SKIPPED"` in `DEGRADED`
  mode; this class of non-determinism is contract-known, not newly revealed by this
  investigation.
- `docs/parity_ledger/infrastructure.yaml::INFRA-273` — see Parity Ledger Overlap below; this
  investigation's COGNITION finding is the first evidence that the mechanism `INFRA-273`
  documents for COGNITION specifically (mechanism 1: no-dedup-gate refire) can manifest at
  large magnitude (up to 36x the anchor's own value) on a previously-unswept anchor/tier
  combination, not just the smaller "event-count anomalies" `INFRA-272` mentions were left
  unreconciled from the original 76-anchor scan.

## Parity Ledger Overlap

- **`INFRA-272`** (status: `verified`, priority: `P1`) — the append-only disclosure/resolution
  chain this ticket continues. Already contains: (1) the original 14-anchor load-sensitivity
  finding, (2) the ECONOMY/frontier_marches-NARRATIVE `RESOLVED` paragraph, (3) the
  urban_political-NARRATIVE `HONEST DISCLOSURE` → `RESOLVED` pair, and (4) a still-open mention
  of this ticket by name as the SOCIAL follow-up. **This entry needs a new appended paragraph**
  reporting this sweep's full 10-pillar result: SOCIAL and COGNITION need overrides (evidence
  above); AGENCY, COMBAT, FACTION, INFORMATION, PROGRESSION, WORLD confirmed to need none;
  ECONOMY and NARRATIVE's existing overrides confirmed still adequate. Not a `P0` entry — no
  hard test_path gate beyond what is already true (the long-run parametrized test already needs
  to pass, which is this ticket's own AC).
- **`INFRA-273`** (status: `verified`, priority: `P2`) — names SOCIAL/COMBAT/PROGRESSION/
  NARRATIVE/WORLD as sharing the cascading-divergence mechanism. This investigation's evidence
  is **consistent with** that claim for COMBAT/PROGRESSION/WORLD (small, bounded variance,
  confirmed fine) and SOCIAL (variance confirmed, override needed). It also surfaces **new**
  evidence outside `INFRA-273`'s named list: **COGNITION**, via a *different*, already-partially-
  documented mechanism (the "refire" mechanism `INFRA-273`'s own text separately names as
  "mechanism 1," distinct from "mechanism 2" cascading divergence) — this is not contradicting
  `INFRA-273`, but it does mean `INFRA-273`'s text, which currently frames its confirmed-pillar
  list as SOCIAL/COMBAT/PROGRESSION/NARRATIVE/WORLD (mechanism 2 only), could be read as
  implying COGNITION's mechanism-1 refire is a separate, already-fully-covered concern
  (`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`) — this investigation's finding is the
  first evidence that mechanism-1 refire can also manifest at large single-draw magnitude on an
  anchor/tier that ticket's own investigation never swept. **Recommend an `INFRA-273` update**
  (not just `INFRA-272`) cross-referencing this finding, since it bears on `INFRA-273`'s own
  mechanism-scope claim, not only `INFRA-272`'s anchor-specific tracking. Neither entry is `P0`.

## Prior Work

- `stored_artifacts/TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE/` (`plan.md`,
  `investigation.md`) — immediate parent; established the SOCIAL finding that founded this
  ticket, confirmed the 1.3x-max-observed-deviation derivation methodology in practice (NARRATIVE
  override), and its plan.md's "SOCIAL Finding Decision" section is the direct scoping origin
  of this ticket (verified read in full this session).
- `stored_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` — established the
  `SCORE_TOLERANCE_OVERRIDES` mechanism itself and the original (contradicted-by-later-evidence)
  "SOCIAL needs no override" conclusion.
- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` Section 8 —
  the derivation-methodology precedent (1.3x max-observed-deviation, optional re-centering)
  reused verbatim in this investigation's SOCIAL/COGNITION derivations above. Confirms this
  anchor's originally-scoped pillars were ECONOMY/SOCIAL only (line 61, 116, 124-125).
- `docs/audits/D06_longrun_health.md` §F6 — root-cause documentation, including the "Resolved
  2026-07-11" note that 18/18 `SLOW_ANCHOR_KEYS` anchors were previously found stable at the
  *band* level across 3-trial sweeps — consistent with this investigation's own finding that no
  pillar here failed the band check, only the tighter score-tolerance check.
- `tickets/done/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM.md` (referenced, not
  re-read in full — out of this ticket's scope to re-litigate) — the ticket that first
  characterized COGNITION's no-dedup-gate refire mechanism, for a *different* anchor/tier than
  `urban_political_seed123_1000t`. This investigation's COGNITION finding is new evidence for
  *this* anchor specifically, not a re-derivation of that ticket's own conclusions.

## Risks and Open Questions

1. **[DECISION NEEDED] COGNITION's remedy shape is not a clean fit for a simple tolerance
   override.** Unlike SOCIAL/ECONOMY/NARRATIVE (bounded, this-tick-vs-prior-tick cascading
   divergence — variance stays within a roughly consistent multiple of the anchor), COGNITION's
   `decision_divergence_detected` has no dedup gate and refires every tick the triggering
   condition holds, producing an unbounded-shaped distribution: 6/8 draws landed at exactly
   0.0120 (2 events), while 2/8 landed at 0.4380 (89 events) and 1.6159 (322 events) — a
   ~36x-the-anchor swing on the high end. A `1.3x max-observed-deviation` floor computed from
   only 8 draws (`abs_floor=2.0435`) is not a bound on the *true* maximum this mechanism could
   produce under worse throttle timing (a still-longer refire streak is architecturally
   possible) — mechanically applying the formula produces a floor 46x the anchor's own value
   (`2.0435` against an anchor of `0.0440`), which would accept almost any COGNITION score from
   -2.0 to +2.08, materially weakening this specific check's discriminative power for this
   pillar. Per the ticket's own Assumptions ("If evidence suggests a pillar needs a different
   remedy... that is a deviation requiring explicit justification in Implementation Notes, not a
   silent substitution"), **this is flagged as a planner decision, not resolved here**. Two
   defensible paths, both consistent with real evidence:
   (a) Apply the override anyway (`abs_floor=2.0435`), satisfying the AC's literal instruction
       ("every pillar whose fresh evidence exceeds its current tolerance gets an entry"), with
       an explicit Implementation Notes caveat that this floor is wide and may not generalize to
       a worse-timed draw, matching this session's own honest-uncertainty convention.
   (b) Treat COGNITION as a distinct-mechanism case requiring its own remedy shape (e.g., a
       `grade_stability`-style 3-trial-mean guard, which averages out single-tick refire spikes
       the way it already does for SOCIAL/ECONOMY, rather than a single-draw tolerance floor
       that must accommodate the single worst spike directly) — this would be new scope beyond
       what this ticket's Out of Scope permits ("Adding a new dedicated grade_stability guard
       for any pillar unless this ticket's own investigation evidence specifically shows the
       tolerance-override alone is inadequate" — arguably satisfied here) and would need
       explicit sign-off.
   This investigation's recommendation, if forced to choose one: **(a)**, because it satisfies
   the ticket's literal AC without requiring new scope, and the caveat is honestly documented
   rather than hidden — but this is a judgment call, not a certainty, and the planner should
   weigh it explicitly rather than silently picking (a) by default.
2. **SOCIAL's override is evidence-combined across two sessions, not purely this session's 8
   draws.** This session's 8 draws alone would have concluded "no override needed" (max
   deviation 3.2135 < 3.5931 default). Only by including the 3 historical draws from the
   immediate parent ticket does the max deviation (3.8485) exceed the default tolerance. This
   is methodologically consistent with how the NARRATIVE override was itself derived (6 draws:
   3 historical + 3 fresh) and matches this ticket's own Scope framing ("check... against
   grade_anchors.json... using real evidence" — not scoped to "this session's draws only"), but
   is flagged explicitly since a reviewer re-deriving purely from this session's data alone
   would reach the opposite conclusion.
3. **Sample size for COGNITION (8 draws, 2 spikes) is thinner than ideal for characterizing a
   rare, high-magnitude event.** A 25% observed spike rate (2/8) on a mechanism that depends on
   real wall-clock timing/system load is plausible but not something 8 draws can bound tightly —
   consistent with the project's established "honesty on sample size" convention
   (`isolation_comparison.md`), this is a reasonable evidence base for a floor, not an
   exhaustive one.
4. **AGENCY and INFORMATION are both trivially bit-identical zero/fixed values across all 8
   draws** — this likely reflects the scenario simply never triggering AGENCY-scored events and
   always triggering exactly 1 INFORMATION event (matches other anchors' `grade_anchors.json`
   entries showing `AGENCY: {"grade": "C", "score": 0.0}` broadly across many worlds/scenarios,
   not specific to this anchor) — not evidence of a defect, just structurally inactive pillars
   for this scenario/profile combination. No further action warranted; noted for completeness
   since the ticket's Scope requires checking "every" pillar, not just the historically-flagged
   ones.
5. **FACTION was bit-identical (0.5800) across all 8 draws** — genuinely stable for this anchor,
   unlike its cross-scenario variability seen elsewhere in `grade_anchors.json` (e.g. other
   anchors show FACTION scores from 0.0 to 2.9). No override needed; noted as a positive
   confirmation, not a gap.

## Anti-Drift Hazards

- **`test_score_tolerance_override_table_scoped_to_named_pillars`'s hard-coded `set(...) ==
  {...}` assertion (line 621) will fail the moment any new entry is added** unless updated in
  the same change — intentional anti-drift design, not a bug to route around.
- **Do not touch the 3 existing table entries' keys or values** (`("urban_political_
  seed123_1000t", "ECONOMY"): 0.2878`, `("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351`,
  `("urban_political_seed123_1000t", "NARRATIVE"): 0.3197`) — this session's fresh 8-draw
  evidence independently confirms both `urban_political_seed123_1000t` overrides remain
  adequate (max observed deviation stays well inside each existing floor), so there is no
  evidence-based reason to touch them.
- **Do not touch `grade_anchors.json`** for any pillar — this investigation's recommendation for
  both SOCIAL and COGNITION keeps the anchor un-re-centered (matches the ECONOMY/NARRATIVE
  precedent on this same anchor). Re-centering was considered and rejected for both: neither
  anchor value is itself an outlier relative to the observed spread (SOCIAL's anchor 17.9655
  sits within the 15.46-21.18 fresh-draw range; COGNITION's anchor 0.044 is close to the modal
  0.012 value, not an outlier requiring re-centering — the *spikes*, not the anchor, are the
  atypical data points).
- **Do not silently widen `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`** (module-level
  defaults) — same hard constraint as every ticket in this chain.
- **Do not touch `kernel.py`, the 14 existing `grade_stability` guards, or the CI isolation
  lane** — all confirmed out of scope and unmodified by this investigation's methodology (no
  file in these categories was edited, only read for reference).
- **COGNITION's remedy-shape open question (Risk #1) is the single highest-leverage decision
  point in this investigation** — a planner silently defaulting to "just add the override" without
  reading the caveat, or silently deciding "skip COGNITION, it's a different mechanism" without
  documenting why, would both violate the ticket's explicit instruction against "a silent
  substitution."
